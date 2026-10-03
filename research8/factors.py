"""Weekly long-short stock portfolios from stock-only signals (pre-registered in protocol_factors.json).

python -m research8.factors dev
python -m research8.factors final   (needs committed research8/factors_frozen.json)
"""
import argparse
import datetime as dt
import json
import os

import numpy as np

from . import features as F
from . import panel as P
from . import rules2 as R2
from .stockev import block_boot

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNALS = ('reversal_z', 'reversal_raw', 'lowvol')
DEV_START, DEV_END, TEST_START = dt.date(2016, 1, 4), dt.date(2022, 12, 30), dt.date(2023, 1, 3)
COSTS_BP = (0, 5, 10, 20)


def rules():
    return [(s, w, h) for s in SIGNALS for w in ('all', 'ex_release') for h in (5, 21)]


def portfolio(pan, v, names_mask, rule, start, end):
    sig, win, h = rule
    r, rel, close, dates = pan['r'], pan['rel'], pan['close'], pan['dates']
    mkt = np.nanmean(r, 1)
    ar = np.nan_to_num(r - mkt[:, None])
    car = np.vstack([np.zeros((1, r.shape[1])), np.cumsum(ar, 0)])
    T = r.shape[0]
    cnt = np.cumsum(~np.isnan(r), 0)
    out = []
    for t in range(0, T - h, 5):
        d = dt.date.fromordinal(int(dates[t]))
        if d < start or dt.date.fromordinal(int(dates[t + h])) > end:
            continue
        ok = names_mask & (close[t] >= 5) & (cnt[t] >= 252) & np.isfinite(v[t]) & (v[t] > 0)
        if win == 'ex_release':
            ok &= ~rel[t + 1:t + h + 1].any(0)
        if t < 5:
            continue
        past = car[t + 1] - car[t - 4]
        s = {'reversal_z': -past / np.sqrt(5 * v[t]), 'reversal_raw': -past, 'lowvol': -v[t]}[sig]
        ok &= np.isfinite(s)
        idx = np.where(ok)[0]
        if len(idx) < 50:
            continue
        o = idx[np.argsort(s[idx], kind='stable')]
        k = len(o) // 5
        lo, hi = o[:k], o[-k:]  # hi = highest signal = long
        fwd = car[t + h + 1] - car[t + 1]
        out.append((t, float(fwd[hi].mean() - fwd[lo].mean())))
    return out


def stats(series, dates, h, rng):
    res = {}
    for c in COSTS_BP:
        # full turnover each rebalance on both legs: 2 legs x 2 sides x c, spread over the h/5 overlapping books
        w = np.array([x for _, x in series]) - 4 * c / 1e4
        w = w / (h / 5)  # each weekly book carries 5/h of capital when holds overlap
        boot = block_boot(w, rng)
        sd, bsd = w.std(ddof=1), boot.std(ddof=1)
        res[f'c{c}'] = {'mean': float(w.mean()), 'ci_weekly': np.percentile(boot, [2.5, 97.5]).tolist(),
                        'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
                        't_block': float(w.mean() / bsd) if bsd > 0 else 0.0, 'win': float(np.mean(w > 0))}
        if c == 10:
            yrs = np.array([dt.date.fromordinal(int(dates[t])).year for t, _ in series])
            res['by_year_c10'] = {str(y): float(w[yrs == y].mean()) for y in sorted(set(yrs))}
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--docs', default='docs/research8/factors')
    a = ap.parse_args()
    pan = P.load(a.panel)
    v = F.ewma(np.where(pan['rel'], np.nan, pan['r']))
    orig = pan['group'] == 'original'
    if a.mode == 'dev':
        samples, rl = {'dev': (orig, DEV_START, DEV_END)}, rules()
    else:
        path = os.path.join(HERE, 'factors_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/factors_frozen.json')
        rl = [tuple(x) for x in json.load(open(path))['rules']]
        samples = {'test': (~orig, TEST_START, dt.date(2025, 8, 29)), 'time_holdout': (orig, TEST_START, dt.date(2025, 8, 29))}
    os.makedirs(a.docs, exist_ok=True)
    rng = np.random.default_rng(R2.SEED)
    for label, (mask, s0, s1) in samples.items():
        res = []
        for r in rl:
            ser = portfolio(pan, v, mask, r, s0, s1)
            out = {'rule': '|'.join(map(str, r)), 'n_weeks': len(ser)}
            if len(ser) >= 50:
                out.update(stats(ser, pan['dates'], r[2], rng))
            res.append(out)
        extra = {}
        if label == 'dev':
            elig = [x for x in res if 'c10' in x and x['c10']['ci_weekly'][0] > 0 and x['c10']['t_block'] >= 3.0
                    and np.mean([v_ for k, v_ in x['by_year_c10'].items() if int(k) <= 2019] or [-1]) > 0
                    and np.mean([v_ for k, v_ in x['by_year_c10'].items() if int(k) >= 2020] or [-1]) > 0]
            named = {'|'.join(map(str, r)): r for r in rl}
            picks, used = [], set()
            for x in sorted(elig, key=lambda x: -x['c10']['sharpe']):
                rr = named[x['rule']]
                if rr[0] in used:
                    continue
                used.add(rr[0])
                picks.append(list(rr))
            extra = {'eligible': len(elig), 'freeze_picks': picks[:2]}
            print('eligible', len(elig), 'picks', picks[:2])
        else:
            extra['gates'] = {}
            for x in res:
                c, c2 = x.get('c10'), x.get('c20')
                g = {'g1': bool(c and c['ci_weekly'][0] > 0), 'g2': bool(c and c['sharpe'] >= 1.0),
                     'g3': bool(c and c['t_block'] >= 2.0), 'g4': bool(c2 and c2['mean'] > 0)}
                g['strong'] = all(g.values())
                g['weak'] = g['g1'] and not g['strong']
                extra['gates'][x['rule']] = g
                print('GATE', x['rule'], g)
        json.dump({'sample': label, 'rules': res, **extra}, open(os.path.join(a.docs, f'{label}.json'), 'w'), indent=1)
        for x in sorted([x for x in res if 'c10' in x], key=lambda x: -x['c10']['sharpe'])[:8]:
            c = x['c10']
            print(f"{x['rule']}: weeks={x['n_weeks']} gross {x['c0']['mean'] * 1e4:+.1f}bp/wk c10 {c['mean'] * 1e4:+.1f}bp/wk "
                  f"SR {c['sharpe']:.2f} t {c['t_block']:.2f} c20 {x['c20']['mean'] * 1e4:+.1f}bp/wk")


if __name__ == '__main__':
    main()
