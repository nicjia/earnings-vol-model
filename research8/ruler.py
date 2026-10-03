"""Approach R (ruler): trade the strangle against the ATM straddle when their market price ratio departs from the
stock-only model ratio. Pre-registered in protocol_ruler.json before any result.

python -m research8.ruler dev   --model <phase-1 best_crps> ...
python -m research8.ruler final --model ... (needs committed research8/ruler_frozen.json)
"""
import argparse
import datetime as dt
import json
import math
import os
import pickle

import numpy as np
from scipy.stats import norm

from . import rules2 as R2

THETAS = (1.1, 1.25, 1.5)
HERE = os.path.dirname(os.path.abspath(__file__))


def vega(s, k, tau, vol):
    sd = vol * math.sqrt(tau)
    d1 = (math.log(s / k) + 0.5 * sd * sd) / sd
    return s * norm.pdf(d1) * math.sqrt(tau)


def pairs(recs, values, model, dates):
    """One row per (event, label) with both structures on the same expiry."""
    v = values['values'][model]
    by = {}
    for i, r in enumerate(recs):
        by.setdefault((r['secid'], r['Q'], r['label']), {})[r['structure']] = i
    rows = []
    for key, d in by.items():
        if 'straddle' not in d or 'strangle' not in d:
            continue
        a, b = recs[d['straddle']], recs[d['strangle']]
        if a['expiry'] != b['expiry']:
            continue
        tau = a['h'] / 252.0
        va = sum(vega(a['spot'], x['strike'], tau, x['iv']) for x in a['legs'])
        vb = sum(vega(b['spot'], x['strike'], tau, x['iv']) for x in b['legs'])
        if va <= 0 or vb <= 0:
            continue
        mid = lambda r: sum((x['bid'] + x['ask']) / 2 for x in r['legs'])
        half = lambda r: sum((x['ask'] - x['bid']) / 2 for x in r['legs'])
        ma, mb = mid(a), mid(b)
        mod_a, mod_b = v[d['straddle']].sum(), v[d['strangle']].sum()
        if not (np.isfinite(mod_a) and np.isfinite(mod_b)) or mod_a <= 0 or mod_b <= 0:
            continue
        beta = vb / va  # straddles per strangle for zero net vega
        rows.append({'label': a['label'], 'group': a['group'], 'week': a['week'], 'tday': dates[a['t']], 'eday': dates[a['te']],
                     'ratio': (mb / ma) / (mod_b / mod_a), 'beta': beta,
                     'gross': mb + beta * ma, 'half': half(b) + beta * half(a),
                     # P&L per strangle sold against beta straddles bought (direction 'sell_wings')
                     'pnl_unhedged': (mb - sum(x['payoff'] for x in b['legs'])) + beta * (sum(x['payoff'] for x in a['legs']) - ma),
                     'hedge': -sum(x['hedge_pnl'] for x in b['legs']) + beta * sum(x['hedge_pnl'] for x in a['legs']),
                     'hcost': sum(x['hedge_cost'] for x in b['legs']) + beta * sum(x['hedge_cost'] for x in a['legs'])})
    return rows


def rules():
    out = []
    for lab in R2.LABELS:
        for hedge in ('hedged', 'unhedged'):
            for t in THETAS:
                out += [(lab, hedge, 'sell_wings', t), (lab, hedge, 'buy_wings', t)]
    return out


def evaluate(rows, rule, sample, all_weeks, mult):
    lab, hedge, d, t = rule
    sel = [r for r, s in zip(rows, sample) if s and r['label'] == lab and
           (r['ratio'] >= t if d == 'sell_wings' else r['ratio'] <= 1 / t)]
    out = {'rule': f'{lab}|{hedge}|{d}|{t:g}', 'n': len(sel)}
    if len(sel) < 20:
        return out
    sign = 1 if d == 'sell_wings' else -1
    weeks = np.array([r['week'] for r in sel])
    for c in R2.COSTS:
        pnl = np.array([sign * (r['pnl_unhedged'] + (r['hedge'] if hedge == 'hedged' else 0.0))
                        - c * r['half'] - (r['hcost'] if hedge == 'hedged' else 0.0) - 4 * R2.FEE_PER_SHARE for r in sel])
        ret = pnl / np.array([r['gross'] for r in sel])
        w, s, cnt = R2.weekly(ret, weeks, all_weeks)
        boot = (mult @ s) / np.maximum(mult @ cnt, 1)
        sd = w.std(ddof=1)
        out[f'c{int(c * 100)}'] = {'mean': float(ret.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
                                   'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                                   't': float(w.mean() / sd * np.sqrt(len(w))) if sd > 0 else 0.0,
                                   'worst': float(ret.min()), 'win': float(np.mean(ret > 0))}
        if c == 0.25:
            yrs = np.array([dt.date.fromordinal(int(r['tday'])).year for r in sel])
            out['by_year_c25'] = {str(y): float(ret[yrs == y].mean()) for y in sorted(set(yrs))}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--values', default='../wrds_studies/research8_phase2/values.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--model', required=True)
    ap.add_argument('--docs', default='docs/research8/ruler')
    a = ap.parse_args()
    from . import panel as P
    dates = P.load(a.panel)['dates']
    rows = pairs(pickle.load(open(a.records, 'rb')), pickle.load(open(a.values, 'rb')), a.model, dates)
    tday = np.array([dt.date.fromordinal(int(r['tday'])) for r in rows])
    eday = np.array([dt.date.fromordinal(int(r['eday'])) for r in rows])
    grp = np.array([r['group'] for r in rows])
    if a.mode == 'dev':
        samples = {'dev': (grp == 'original') & (eday <= R2.DEV_END)}
        rl = rules()
    else:
        path = os.path.join(HERE, 'ruler_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/ruler_frozen.json')
        rl = [tuple(x) for x in json.load(open(path))['rules']]
        samples = {'test': (grp != 'original') & (tday >= R2.TEST_START), 'time_holdout': (grp == 'original') & (tday >= R2.TEST_START)}
    os.makedirs(a.docs, exist_ok=True)
    rng = np.random.default_rng(R2.SEED)
    for label, sample in samples.items():
        weeks = np.unique([r['week'] for r, s in zip(rows, sample) if s])
        mult = np.stack([np.bincount(rng.integers(0, len(weeks), len(weeks)), minlength=len(weeks)) for _ in range(R2.DRAWS)]).astype(float)
        res = [evaluate(rows, r, sample, weeks, mult) for r in rl]
        extra = {}
        if label == 'dev':
            named = {f'{r[0]}|{r[1]}|{r[2]}|{r[3]:g}': r for r in rl}
            elig = [x for x in res if 'c25' in x and x['n'] >= 200 and x['c25']['mean'] > 0 and x['c25']['ci'][0] > 0
                    and x['c25']['t'] >= 3.0
                    and np.mean([v for k, v in x['by_year_c25'].items() if int(k) <= 2020] or [-1]) > 0
                    and np.mean([v for k, v in x['by_year_c25'].items() if int(k) >= 2021] or [-1]) > 0]
            picks, used = [], set()
            for x in sorted(elig, key=lambda x: -x['c25']['sharpe']):
                r = named[x['rule']]
                if (r[0], r[2]) in used:
                    continue
                used.add((r[0], r[2]))
                picks.append(list(r))
                if len(picks) == 3:
                    break
            extra = {'eligible': len(elig), 'freeze_picks': picks}
            print('eligible', len(elig), 'picks', picks)
        else:
            extra = {'gates': {x['rule']: R2.gates(x) for x in res}}
            for k, g in extra['gates'].items():
                print('GATE', k, g)
        json.dump({'sample': label, 'model': a.model, 'pairs': int(sample.sum()), 'rules': res, **extra},
                  open(os.path.join(a.docs, f'{label}_{a.model}.json'), 'w'), indent=1)
        ok = [x for x in res if 'c25' in x]
        print(f'[{label}] {int(sample.sum())} pairs, {len(ok)} rules with >= 20 trades')
        for x in sorted(ok, key=lambda x: -x['c25']['sharpe'])[:8]:
            c = x['c25']
            print(f"{x['rule']}: n={x['n']} mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} [{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] "
                  f"SR {c['sharpe']:.2f} t {c['t']:.2f} c50 {x['c50']['mean']:+.3f}")


if __name__ == '__main__':
    main()
