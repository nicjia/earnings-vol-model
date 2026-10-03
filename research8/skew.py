"""Skew relative value on phase 2 strangle records (pre-registered in protocol_skew.json).

python -m research8.skew dev   --model HAR_FHS_shrunk
python -m research8.skew final --model HAR_FHS_shrunk   (needs committed research8/skew_frozen.json)
"""
import argparse
import datetime as dt
import json
import math
import os
import pickle

import numpy as np

from . import panel as P
from . import rules2 as R2
from .ruler import vega

HERE = os.path.dirname(os.path.abspath(__file__))
THETAS = (1.1, 1.25, 1.5)


def rows(recs, values, model, dates):
    v = values['values'][model]
    out = []
    for i, r in enumerate(recs):
        if r['structure'] != 'strangle':
            continue
        c, p = r['legs']
        vc, vp = v[i]
        if not (np.isfinite(vc) and np.isfinite(vp)) or vc <= 0 or vp <= 0:
            continue
        mc, mp = (c['bid'] + c['ask']) / 2, (p['bid'] + p['ask']) / 2
        tau = r['h'] / 252.0
        gc, gp = vega(r['spot'], c['strike'], tau, c['iv']), vega(r['spot'], p['strike'], tau, p['iv'])
        if gc <= 0 or gp <= 0:
            continue
        out.append({'label': r['label'], 'group': r['group'], 'week': r['week'], 'tday': dates[r['t']], 'eday': dates[r['te']],
                    'skew': (mc / vc) / (mp / vp), 'mc': mc, 'mp': mp, 'gc': gc, 'gp': gp,
                    'hc': (c['ask'] - c['bid']) / 2, 'hp': (p['ask'] - p['bid']) / 2,
                    'pc': c['payoff'], 'pp': p['payoff'], 'dc': c['hedge_pnl'], 'dp': p['hedge_pnl'],
                    'kc': c['hedge_cost'], 'kp': p['hedge_cost']})
    return out


def rules():
    return [(lab, hedge, t) for lab in R2.LABELS for hedge in ('hedged', 'unhedged') for t in THETAS]


def trade(x, hedged, cost):
    """Sell the rich wing (1 contract), buy the cheap wing in vega ratio. Return per gross premium."""
    if x['skew'] >= 1:  # call rich
        ms, ps, ds, ks, hs, mb, pb, db, kb, hb, beta = (x['mc'], x['pc'], x['dc'], x['kc'], x['hc'],
                                                         x['mp'], x['pp'], x['dp'], x['kp'], x['hp'], x['gc'] / x['gp'])
    else:
        ms, ps, ds, ks, hs, mb, pb, db, kb, hb, beta = (x['mp'], x['pp'], x['dp'], x['kp'], x['hp'],
                                                         x['mc'], x['pc'], x['dc'], x['kc'], x['hc'], x['gp'] / x['gc'])
    pnl = (ms - ps) + beta * (pb - mb)
    if hedged:
        pnl += -ds + beta * db - ks - beta * kb
    pnl -= cost * (hs + beta * hb) + (1 + beta) * 2 * R2.FEE_PER_SHARE
    return pnl / (ms + beta * mb)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--values', default='../wrds_studies/research8_phase2/values.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--model', default='HAR_FHS_shrunk')
    ap.add_argument('--docs', default='docs/research8/skew')
    a = ap.parse_args()
    dates = P.load(a.panel)['dates']
    rs = rows(pickle.load(open(a.records, 'rb')), pickle.load(open(a.values, 'rb')), a.model, dates)
    tday = np.array([dt.date.fromordinal(int(x['tday'])) for x in rs])
    eday = np.array([dt.date.fromordinal(int(x['eday'])) for x in rs])
    orig = np.array([x['group'] == 'original' for x in rs])
    if a.mode == 'dev':
        samples, rl = {'dev': orig & (eday <= R2.DEV_END)}, rules()
    else:
        path = os.path.join(HERE, 'skew_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/skew_frozen.json')
        rl = [tuple(x) for x in json.load(open(path))['rules']]
        samples = {'test': ~orig & (tday >= R2.TEST_START), 'time_holdout': orig & (tday >= R2.TEST_START)}
    os.makedirs(a.docs, exist_ok=True)
    rng = np.random.default_rng(R2.SEED)
    for label, sample in samples.items():
        weeks_all = np.unique([x['week'] for x, s in zip(rs, sample) if s])
        mult = np.stack([np.bincount(rng.integers(0, len(weeks_all), len(weeks_all)), minlength=len(weeks_all))
                         for _ in range(R2.DRAWS)]).astype(float)
        res = []
        for lab, hedge, t in rl:
            sel = [x for x, s in zip(rs, sample) if s and x['label'] == lab and (x['skew'] >= t or x['skew'] <= 1 / t)]
            out = {'rule': f'{lab}|{hedge}|{t:g}', 'n': len(sel)}
            if len(sel) >= 20:
                wk = np.array([x['week'] for x in sel])
                yrs = np.array([dt.date.fromordinal(int(x['tday'])).year for x in sel])
                for c in R2.COSTS:
                    ret = np.array([trade(x, hedge == 'hedged', c) for x in sel])
                    w, s, cnt = R2.weekly(ret, wk, weeks_all)
                    boot = (mult @ s) / np.maximum(mult @ cnt, 1)
                    sd = w.std(ddof=1)
                    out[f'c{int(c * 100)}'] = {'mean': float(ret.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
                                               'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                                               't': float(w.mean() / sd * np.sqrt(len(w))) if sd > 0 else 0.0,
                                               'worst': float(ret.min()), 'win': float(np.mean(ret > 0))}
                    if c == 0.25:
                        out['by_year_c25'] = {str(y): float(ret[yrs == y].mean()) for y in sorted(set(yrs))}
            res.append(out)
        extra = {}
        if label == 'dev':
            elig = [x for x in res if 'c25' in x and x['n'] >= 200 and x['c25']['ci'][0] > 0 and x['c25']['t'] >= 3.0
                    and np.mean([v for k, v in x['by_year_c25'].items() if int(k) <= 2020] or [-1]) > 0
                    and np.mean([v for k, v in x['by_year_c25'].items() if int(k) >= 2021] or [-1]) > 0]
            named = {f'{r[0]}|{r[1]}|{r[2]:g}': r for r in rl}
            picks, used = [], set()
            for x in sorted(elig, key=lambda x: -x['c25']['sharpe']):
                r = named[x['rule']]
                if r[0] in used:
                    continue
                used.add(r[0])
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
        print(f'[{label}] {len(ok)} rules')
        for x in sorted(ok, key=lambda x: -x['c25']['sharpe'])[:8]:
            c = x['c25']
            print(f"{x['rule']}: n={x['n']} mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} [{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] "
                  f"SR {c['sharpe']:.2f} t {c['t']:.2f} c50 {x['c50']['mean']:+.3f}")


if __name__ == '__main__':
    main()
