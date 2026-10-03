"""Cross-sectional long-short vol book on the phase 2 records (pre-registered in protocol_xsec.json).

Each calendar week and label, records with a finite signal are ranked; the top quantile (richest vs the stock-only
model) is sold and the bottom quantile bought, equal premium per trade. The week's return is
0.5 x (mean short return + mean long return); weeks without at least 2 x (1/quantile) records are skipped (0).

python -m research8.xsec dev   --model HAR_FHS_shrunk
python -m research8.xsec final --model HAR_FHS_shrunk   (needs committed research8/xsec_frozen.json)
"""
import argparse
import datetime as dt
import json
import os
import pickle

import numpy as np

from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
QUANTS = (3, 5)
SIGNALS = ('rho', 'rho_rel')


def rules():
    return [(lab, st, hedge, sig, q) for lab in R2.LABELS for st in R2.STRUCTURES for hedge in ('hedged', 'unhedged')
            for sig in SIGNALS for q in QUANTS]


def rname(r):
    return '|'.join(str(x) for x in r)


def book(f, rule, sample, cost):
    lab, st, hedge, sig, q = rule
    m = sample & (f['label'] == lab) & (f['structure'] == st) & np.isfinite(f[sig]) & np.isfinite(f['rho'])
    idx = np.where(m)[0]
    hedged = hedge == 'hedged'
    raw = f['payoff'] - f['mkt'] + (f['hedge'] if hedged else 0.0)
    cst = cost * f['half'] + 2 * R2.FEE_PER_SHARE + (f['hcost'] if hedged else 0.0)
    weeks, rets, ntr = [], [], 0
    for w in np.unique(f['week'][idx]):
        ii = idx[f['week'][idx] == w]
        if len(ii) < 2 * q:
            continue
        o = ii[np.argsort(f[sig][ii], kind='stable')]
        k = len(o) // q
        lo, hi = o[:k], o[-k:]
        long_r = (raw[lo] - cst[lo]) / f['mkt'][lo]
        short_r = (-raw[hi] - cst[hi]) / f['mkt'][hi]
        weeks.append(w)
        rets.append(0.5 * (long_r.mean() + short_r.mean()))
        ntr += 2 * k
    return np.array(weeks), np.array(rets), ntr


def evaluate(f, rule, sample, all_weeks, rng):
    out = {'rule': rname(rule)}
    for c in R2.COSTS:
        wk, r, ntr = book(f, rule, sample, c)
        if len(r) < 20:
            return out
        full = np.zeros(len(all_weeks))
        full[np.searchsorted(all_weeks, wk)] = r
        act = np.searchsorted(all_weeks, wk)
        boot = []
        for _ in range(R2.DRAWS):
            b = rng.integers(0, len(r), len(r))
            boot.append(r[b].mean())
        sd = full.std(ddof=1)
        out['n_weeks'], out['n_trades'] = int(len(r)), int(ntr)
        out[f'c{int(c * 100)}'] = {'mean': float(r.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
                                   'sharpe': float(full.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                                   't': float(full.mean() / sd * np.sqrt(len(full))) if sd > 0 else 0.0,
                                   'worst': float(r.min()), 'win': float(np.mean(r > 0))}
        if c == 0.25:
            yrs = np.array([dt.date.fromordinal(int(w) * 7 + 1).year for w in wk])
            out['by_year_c25'] = {str(y): float(r[yrs == y].mean()) for y in sorted(set(yrs))}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--values', default='../wrds_studies/research8_phase2/values.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--model', required=True)
    ap.add_argument('--docs', default='docs/research8/xsec')
    a = ap.parse_args()
    from . import panel as P
    dates = P.load(a.panel)['dates']
    f = R2.frame(pickle.load(open(a.records, 'rb')), pickle.load(open(a.values, 'rb')), a.model, dates)
    tday = np.array([dt.date.fromordinal(int(x)) for x in f['tday']])
    eday = np.array([dt.date.fromordinal(int(x)) for x in f['eday']])
    orig = f['group'] == 'original'
    if a.mode == 'dev':
        samples, rl = {'dev': orig & (eday <= R2.DEV_END)}, rules()
    else:
        path = os.path.join(HERE, 'xsec_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/xsec_frozen.json')
        rl = [tuple(x) for x in json.load(open(path))['rules']]
        samples = {'test': ~orig & (tday >= R2.TEST_START), 'time_holdout': orig & (tday >= R2.TEST_START)}
    os.makedirs(a.docs, exist_ok=True)
    for label, sample in samples.items():
        rng = np.random.default_rng(R2.SEED)
        all_weeks = np.unique(f['week'][sample])
        res = [evaluate(f, r, sample, all_weeks, rng) for r in rl]
        extra = {}
        if label == 'dev':
            named = {rname(r): r for r in rl}
            elig = [x for x in res if 'c25' in x and x['n_weeks'] >= 100 and x['c25']['ci'][0] > 0 and x['c25']['t'] >= 3.0
                    and np.mean([v for k, v in x['by_year_c25'].items() if int(k) <= 2020] or [-1]) > 0
                    and np.mean([v for k, v in x['by_year_c25'].items() if int(k) >= 2021] or [-1]) > 0]
            picks, used = [], set()
            for x in sorted(elig, key=lambda x: -x['c25']['sharpe']):
                r = named[x['rule']]
                if (r[0], r[1]) in used:
                    continue
                used.add((r[0], r[1]))
                picks.append(list(r))
                if len(picks) == 3:
                    break
            extra = {'eligible': len(elig), 'freeze_picks': picks}
            print('eligible', len(elig), 'picks', picks)
        else:
            extra = {'gates': {x['rule']: R2.gates(x) for x in res}}
            for k, g in extra['gates'].items():
                print('GATE', k, g)
        json.dump({'sample': label, 'model': a.model, 'rules': res, **extra},
                  open(os.path.join(a.docs, f'{label}_{a.model}.json'), 'w'), indent=1)
        ok = [x for x in res if 'c25' in x]
        print(f'[{label}] {len(ok)} rules evaluated')
        for x in sorted(ok, key=lambda x: -x['c25']['sharpe'])[:8]:
            c = x['c25']
            print(f"{x['rule']}: weeks={x['n_weeks']} trades={x['n_trades']} mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} "
                  f"[{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] SR {c['sharpe']:.2f} t {c['t']:.2f} c50 {x['c50']['mean']:+.3f}")


if __name__ == '__main__':
    main()
