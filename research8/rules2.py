"""Phase 2 rules: trade straddles/strangles when the market price departs from the stock-only model value.

python -m research8.rules2 dev   --records ... --values ... --docs docs/research8/phase2
python -m research8.rules2 final --records ... --values ... --docs ...   (needs committed research8/phase2_frozen.json)

Prints and writes aggregates only (means, bootstrap intervals, Sharpe, t-statistics).
"""
import argparse
import datetime as dt
import json
import os
import pickle
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEV_END = dt.date(2022, 12, 30)
TEST_START = dt.date(2023, 1, 3)
FEE_PER_SHARE = 0.65 / 100
COSTS = (0.0, 0.25, 0.5, 1.0)
SELL_T = (1.1, 1.25, 1.5, 2.0)
BUY_T = (0.9, 0.8, 0.67, 0.5)
REL_SELL_T = (1.1, 1.25, 1.5)
REL_BUY_T = (0.9, 0.8, 0.67)
LABELS = ('P-4', 'P-1', 'P', 'Q', 'Q+1')
STRUCTURES = ('straddle', 'strangle')
DRAWS, SEED = 2000, 20261004


def rule_list():
    out = []
    for lab in LABELS:
        for st in STRUCTURES:
            for hedge in ('hedged', 'unhedged'):
                base = (lab, st, hedge)
                out += [base + ('sell', 'all', None), base + ('buy', 'all', None)]
                out += [base + ('sell', 'abs', t) for t in SELL_T] + [base + ('buy', 'abs', t) for t in BUY_T]
                out += [base + ('sell', 'rel', t) for t in REL_SELL_T] + [base + ('buy', 'rel', t) for t in REL_BUY_T]
    return out


def rule_name(r):
    lab, st, hedge, d, kind, t = r
    return f'{lab}|{st}|{hedge}|{d}|{kind}' + ('' if t is None else f'{t:g}')


def frame(recs, values, model, dates):
    """Columns per record: signal inputs and per-share P&L components (no direction applied)."""
    v = values['values'][model]
    n = len(recs)
    f = {k: np.empty(n, dtype=object if k in ('label', 'structure', 'group') else float) for k in
         ('label', 'structure', 'group', 'mkt', 'model', 'half', 'payoff', 'hedge', 'hcost', 'secid', 'week', 'tday', 'eday')}
    for i, r in enumerate(recs):
        L = r['legs']
        f['label'][i], f['structure'][i], f['group'][i] = r['label'], r['structure'], r['group']
        f['mkt'][i] = sum((x['bid'] + x['ask']) / 2 for x in L)
        f['half'][i] = sum((x['ask'] - x['bid']) / 2 for x in L)
        f['payoff'][i] = sum(x['payoff'] for x in L)
        f['hedge'][i] = sum(x['hedge_pnl'] for x in L)
        f['hcost'][i] = sum(x['hedge_cost'] for x in L)
        f['model'][i] = v[i].sum()
        f['secid'][i], f['week'][i] = r['secid'], r['week']
        f['tday'][i], f['eday'][i] = dates[r['t']], dates[r['te']]
    f['rho'] = f['mkt'] / f['model']
    # lagged relative signal: rho / median rho of the same name, label and structure at earlier records
    # whose expiry close is on or before this decision close (needs >= 4)
    f['rho_rel'] = np.full(n, np.nan)
    keys = {}
    for i in np.argsort(f['tday'], kind='stable'):
        keys.setdefault((f['secid'][i], f['label'][i], f['structure'][i]), []).append(i)
    for idx in keys.values():
        for a, i in enumerate(idx):
            prev = [f['rho'][k] for k in idx[:a] if f['eday'][k] <= f['tday'][i] and np.isfinite(f['rho'][k])]
            prev = prev[-8:]
            if len(prev) >= 4:
                f['rho_rel'][i] = f['rho'][i] / np.median(prev)
    return f


def returns(f, mask, direction, hedged, cost):
    pnl = direction * (f['payoff'] - f['mkt'] + (f['hedge'] if hedged else 0.0))
    pnl = pnl - cost * f['half'] - 2 * FEE_PER_SHARE - (f['hcost'] if hedged else 0.0)
    return (pnl / f['mkt'])[mask]


def select(f, r, sample):
    lab, st, hedge, d, kind, t = r
    m = (f['label'] == lab) & (f['structure'] == st) & sample & np.isfinite(f['rho'])
    if kind == 'abs':
        m &= (f['rho'] >= t) if d == 'sell' else (f['rho'] <= t)
    elif kind == 'rel':
        rr = np.nan_to_num(f['rho_rel'], nan=-1 if d == 'sell' else 1e9)
        m &= (rr >= t) if d == 'sell' else (rr <= t)
    return m


def weekly(ret, weeks, all_weeks):
    s = np.bincount(np.searchsorted(all_weeks, weeks), ret, minlength=len(all_weeks))
    c = np.bincount(np.searchsorted(all_weeks, weeks), minlength=len(all_weeks))
    return np.where(c > 0, s / np.maximum(c, 1), 0.0), s, c


def evaluate(f, r, sample, all_weeks, rng_mult):
    lab, st, hedge, d, kind, t = r
    m = select(f, r, sample)
    out = {'rule': rule_name(r), 'n': int(m.sum())}
    if m.sum() < 20:
        return out
    weeks = f['week'][m]
    for c in COSTS:
        ret = returns(f, m, 1 if d == 'buy' else -1, hedge == 'hedged', c)
        w, s, cnt = weekly(ret, weeks, all_weeks)
        boot = (rng_mult @ s) / np.maximum(rng_mult @ cnt, 1)
        sd = w.std(ddof=1)
        key = f'c{int(c * 100)}'
        out[key] = {'mean': float(ret.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
                    'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                    't': float(w.mean() / sd * np.sqrt(len(w))) if sd > 0 else 0.0,
                    'worst': float(ret.min()), 'win': float(np.mean(ret > 0))}
    yrs = np.array([dt.date.fromordinal(int(x)).year for x in f['tday'][m]])
    ret25 = returns(f, m, 1 if d == 'buy' else -1, hedge == 'hedged', 0.25)
    out['by_year_c25'] = {str(y): float(ret25[yrs == y].mean()) for y in sorted(set(yrs))}
    return out


def freeze(res, rules):
    """Protocol freeze rule on dev results."""
    by = {rule_name(r): r for r in rules}
    elig = []
    for x in res:
        c = x.get('c25')
        if not c or x['n'] < 200 or c['mean'] <= 0 or c['ci'][0] <= 0 or c['t'] < 3.0:
            continue
        yrs = x['by_year_c25']
        def half(a, b):
            v = [(yrs[str(y)]) for y in range(a, b + 1) if str(y) in yrs]
            return np.mean(v) if v else -1
        if half(2018, 2020) <= 0 or half(2021, 2022) <= 0:
            continue
        elig.append(x)
    picks, used = [], set()
    for x in sorted(elig, key=lambda x: -x['c25']['sharpe']):
        r = by[x['rule']]
        key = (r[0], r[1], r[3])
        if key in used:
            continue
        used.add(key)
        picks.append(list(r))
        if len(picks) == 5:
            break
    return picks, len(elig)


def gates(x):
    c25, c50 = x.get('c25'), x.get('c50')
    if not c25:
        return {'strong': False, 'weak': False}
    g1 = c25['mean'] > 0 and c25['ci'][0] > 0
    g = {'g1': g1, 'g2': c25['sharpe'] >= 1.0, 'g3': c25['t'] >= 2.0, 'g4': c50['mean'] > 0}
    g['strong'] = all(g.values())
    g['weak'] = g1 and not g['strong']
    return g


def committed(path):
    rel = os.path.relpath(path, os.path.dirname(HERE))
    r = subprocess.run(['git', '-C', os.path.dirname(HERE), 'status', '--porcelain', '--', rel], capture_output=True, text=True)
    t = subprocess.run(['git', '-C', os.path.dirname(HERE), 'ls-files', '--error-unmatch', rel], capture_output=True)
    return t.returncode == 0 and r.stdout.strip() == ''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--values', default='../wrds_studies/research8_phase2/values.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--model', required=True)
    ap.add_argument('--docs', default='docs/research8/phase2')
    a = ap.parse_args()
    from . import panel as P
    dates = [dt.date.fromordinal(int(x)) for x in P.load(a.panel)['dates']]
    recs = pickle.load(open(a.records, 'rb'))
    values = pickle.load(open(a.values, 'rb'))
    f = frame(recs, values, a.model, np.array([d.toordinal() for d in dates]))
    tday = np.array([dt.date.fromordinal(int(x)) for x in f['tday']])
    eday = np.array([dt.date.fromordinal(int(x)) for x in f['eday']])
    if a.mode == 'dev':
        samples = {'dev': (f['group'] == 'original') & (eday <= DEV_END)}
        rules = rule_list()
    else:
        frozen_path = os.path.join(HERE, 'phase2_frozen.json')
        if not committed(frozen_path):
            raise SystemExit('final needs a committed research8/phase2_frozen.json')
        frozen = json.load(open(frozen_path))
        rules = [tuple(x) for x in frozen['rules']]
        samples = {'test': (f['group'] != 'original') & (tday >= TEST_START),
                   'time_holdout': (f['group'] == 'original') & (tday >= TEST_START)}
    os.makedirs(a.docs, exist_ok=True)
    rng = np.random.default_rng(SEED)
    for label, sample in samples.items():
        all_weeks = np.unique(f['week'][sample])
        mult = np.stack([np.bincount(rng.integers(0, len(all_weeks), len(all_weeks)), minlength=len(all_weeks))
                         for _ in range(DRAWS)]).astype(float)
        res = [evaluate(f, r, sample, all_weeks, mult) for r in rules]
        cover = {'records': int(sample.sum()), 'weeks': int(len(all_weeks)),
                 'median_rho_by_label_structure': {f'{l}|{s}': float(np.nanmedian(f['rho'][sample & (f['label'] == l) & (f['structure'] == s)]))
                                                   for l in LABELS for s in STRUCTURES
                                                   if (sample & (f['label'] == l) & (f['structure'] == s)).any()}}
        extra = {}
        if label == 'dev':
            extra['freeze_picks'], extra['eligible'] = freeze(res, rules)
            print('eligible rules:', extra['eligible'], 'frozen picks:', [rule_name(tuple(p)) for p in extra['freeze_picks']])
        else:
            extra['gates'] = {x['rule']: gates(x) for x in res}
            for k, g in extra['gates'].items():
                print('GATE', k, g)
        json.dump({'sample': label, 'model': a.model, 'coverage': cover, 'rules': res, **extra},
                  open(os.path.join(a.docs, f'{label}_{a.model}.json'), 'w'), indent=1)
        ok = [x for x in res if 'c25' in x]
        print(f'[{label}] model {a.model}: {cover["records"]} records, {len(ok)} rules with >= 20 trades')
        print('median rho:', {k: round(v, 3) for k, v in cover['median_rho_by_label_structure'].items()})
        top = sorted(ok, key=lambda x: -x['c25']['sharpe'])[:12]
        for x in top:
            c = x['c25']
            print(f"{x['rule']}: n={x['n']} mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} [{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] "
                  f"SR {c['sharpe']:.2f} t {c['t']:.2f} c50 {x['c50']['mean']:+.3f} c100 {x['c100']['mean']:+.3f} win {c['win']:.2f}")


if __name__ == '__main__':
    main()
