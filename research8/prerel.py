"""Pre-release exits for phase 2 P-4/P-1 records: quote the same legs at the P close (sell before the release).

python -m research8.prerel build --records ... --out ../wrds_studies/research8_phase2/prerel.pkl
python -m research8.prerel dev   --model HAR_FHS_shrunk
python -m research8.prerel final --model HAR_FHS_shrunk   (needs committed research8/prerel_frozen.json)

Pre-registered in protocol_prerel.json. Aggregates only.
"""
import argparse
import datetime as dt
import json
import os
import pickle

import numpy as np

from research7 import data
from . import options2 as O
from . import panel as P
from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
COSTS = R2.COSTS
BUY_T = (1.0, 0.95, 0.9, 0.85)
REL_T = (1.0, 0.9)


def build(recs, caches, panel_path, out):
    pan = P.load(panel_path)
    close, dates = pan['close'], pan['dates']
    sessions = [dt.date.fromordinal(int(x)) for x in dates]
    want = [i for i, r in enumerate(recs) if r['label'] in ('P-4', 'P-1')]
    # P index = t + 4 or t + 1
    by_year = {}
    for i in want:
        r = recs[i]
        p = r['t'] + (4 if r['label'] == 'P-4' else 1)
        by_year.setdefault(sessions[p].year, []).append((i, p))
    res = {}
    for y, items in sorted(by_year.items()):
        quotes = {}
        for c in caches:
            quotes.update(data.load_quotes(c, y))
        for i, p in items:
            r = recs[i]
            chain = quotes.get((r['secid'], sessions[p].isoformat()))
            if not chain:
                continue
            legs = []
            for x in r['legs']:
                q = O.leg_quote(chain, (r['expiry'], x['strike'], x['cp'], 1, 'core'))
                if q is None:
                    break
                legs.append(q)
            if len(legs) != len(r['legs']):
                continue
            path = close[r['t']:p + 1, r['j']]
            if not np.isfinite(path).all():
                continue
            tau = (r['te'] - np.arange(r['t'], p + 1)) / 252.0
            hedge, hcost = 0.0, 0.0
            for x in r['legs']:
                dl = O.deltas(path[:-1], x['strike'], tau[:-1], x['iv'], x['cp'])
                hedge += float(-np.sum(dl * np.diff(path)))
                tr = np.abs(np.diff(np.concatenate([[0.0], dl, [0.0]])))
                hcost += float(O.HEDGE_COST * np.sum(tr * np.concatenate([path[:-1], [path[-1]]])))
            res[i] = {'exit_mid': sum((b + a) / 2 for b, a, _ in legs), 'exit_half': sum((a - b) / 2 for b, a, _ in legs),
                      'hedge_to_P': hedge, 'hcost_to_P': hcost, 'P': p}
        print(y, len(items), 'exits', sum(1 for i, _ in items if i in res), flush=True)
        del quotes
    with open(out, 'wb') as s:
        pickle.dump(res, s)


def rules():
    out = []
    for lab in ('P-4', 'P-1'):
        for st in R2.STRUCTURES:
            for hedge in ('hedged', 'unhedged'):
                out.append((lab, st, hedge, 'all', None))
                out += [(lab, st, hedge, 'abs', t) for t in BUY_T]
                out += [(lab, st, hedge, 'rel', t) for t in REL_T]
    return out


def rname(r):
    return '|'.join('' if x is None else (f'{x:g}' if isinstance(x, float) else str(x)) for x in r)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['build', 'dev', 'final'])
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--values', default='../wrds_studies/research8_phase2/values.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--caches', default='../wrds_studies/research7_cache,../wrds_studies/research7_cache_e')
    ap.add_argument('--exits', default='../wrds_studies/research8_phase2/prerel.pkl')
    ap.add_argument('--model', default='HAR_FHS_shrunk')
    ap.add_argument('--docs', default='docs/research8/prerel')
    a = ap.parse_args()
    recs = pickle.load(open(a.records, 'rb'))
    if a.mode == 'build':
        build(recs, a.caches.split(','), a.panel, a.exits)
        return
    dates = P.load(a.panel)['dates']
    f = R2.frame(recs, pickle.load(open(a.values, 'rb')), a.model, dates)
    ex = pickle.load(open(a.exits, 'rb'))
    n = len(recs)
    has = np.zeros(n, bool)
    xmid, xhalf, xh, xhc = (np.full(n, np.nan) for _ in range(4))
    for i, e in ex.items():
        has[i] = True
        xmid[i], xhalf[i], xh[i], xhc[i] = e['exit_mid'], e['exit_half'], e['hedge_to_P'], e['hcost_to_P']
    tday = np.array([dt.date.fromordinal(int(x)) for x in f['tday']])
    orig = f['group'] == 'original'
    pday = np.array([dt.date.fromordinal(int(dates[ex[i]['P']])) if i in ex else dt.date.max for i in range(n)])
    if a.mode == 'dev':
        samples, rl = {'dev': orig & (pday <= R2.DEV_END) & has}, rules()
    else:
        path = os.path.join(HERE, 'prerel_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/prerel_frozen.json')
        rl = [tuple(x) for x in json.load(open(path))['rules']]
        samples = {'test': ~orig & (tday >= R2.TEST_START) & has, 'time_holdout': orig & (tday >= R2.TEST_START) & has}
    os.makedirs(a.docs, exist_ok=True)
    rng = np.random.default_rng(R2.SEED)
    for label, sample in samples.items():
        all_weeks = np.unique(f['week'][sample])
        mult = np.stack([np.bincount(rng.integers(0, len(all_weeks), len(all_weeks)), minlength=len(all_weeks))
                         for _ in range(R2.DRAWS)]).astype(float)
        res = []
        for r in rl:
            lab, st, hedge, kind, t = r
            m = sample & (f['label'] == lab) & (f['structure'] == st) & np.isfinite(f['rho'])
            if kind == 'abs':
                m &= f['rho'] <= t
            elif kind == 'rel':
                m &= np.nan_to_num(f['rho_rel'], nan=1e9) <= t
            out = {'rule': rname(r), 'n': int(m.sum())}
            if m.sum() >= 20:
                for c in COSTS:
                    pnl = xmid - f['mkt'] + (xh if hedge == 'hedged' else 0.0)
                    pnl = pnl - c * (f['half'] + xhalf) - 4 * R2.FEE_PER_SHARE - (xhc if hedge == 'hedged' else 0.0)
                    ret = (pnl / f['mkt'])[m]
                    w, s, cnt = R2.weekly(ret, f['week'][m], all_weeks)
                    boot = (mult @ s) / np.maximum(mult @ cnt, 1)
                    sd = w.std(ddof=1)
                    out[f'c{int(c * 100)}'] = {'mean': float(ret.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
                                               'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                                               't': float(w.mean() / sd * np.sqrt(len(w))) if sd > 0 else 0.0,
                                               'worst': float(ret.min()), 'win': float(np.mean(ret > 0))}
                    if c == 0.25:
                        yrs = np.array([d.year for d in tday[m]])
                        out['by_year_c25'] = {str(y): float(ret[yrs == y].mean()) for y in sorted(set(yrs))}
            res.append(out)
        extra = {}
        if label == 'dev':
            named = {rname(r): r for r in rl}
            elig = [x for x in res if 'c25' in x and x['n'] >= 200 and x['c25']['ci'][0] > 0 and x['c25']['t'] >= 3.0
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
        print(f'[{label}] {int(sample.sum())} records, {len(ok)} rules')
        for x in sorted(ok, key=lambda x: -x['c25']['sharpe'])[:10]:
            c = x['c25']
            print(f"{x['rule']}: n={x['n']} mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} [{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] "
                  f"SR {c['sharpe']:.2f} t {c['t']:.2f} c50 {x['c50']['mean']:+.3f} c100 {x['c100']['mean']:+.3f}")


if __name__ == '__main__':
    main()
