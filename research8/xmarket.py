"""Synthetic model-timed premium selling on NDX/VXN and EURUSD/EVZ (protocol_xmarket.json).

python -m research8.xmarket dev   --data ../wrds_studies/public
python -m research8.xmarket final --data ...   (needs committed research8/xmarket_frozen.json)
"""
import argparse
import json
import math
import os

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import putwrite as W
from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
MARKETS = {'NDX': ('NASDAQ100', 'VXNCLS', 0.88), 'EURUSD': ('DEXUSEU', 'EVZCLS', 0.97)}
COST = 0.03
SPLIT = pd.Timestamp('2015-01-01')


def fred(path, sid):
    d = pd.read_csv(os.path.join(path, f'fred_{sid}.csv'))
    d['observation_date'] = pd.to_datetime(d['observation_date'])
    return pd.to_numeric(d.set_index('observation_date')[sid], errors='coerce').dropna()


def bs(s, vol, T, cp):
    sd = vol * math.sqrt(T)
    d1 = 0.5 * sd
    call = s * (norm.cdf(d1) - norm.cdf(d1 - sd))
    return call if cp == 'C' else call  # ATM with r = 0: put = call


def periods(path, market, kshift=0.0):
    px_id, iv_id, k = MARKETS[market]
    px, iv = fred(path, px_id), fred(path, iv_id)
    sig = W.har_sigma(px)
    days = px.index
    rows = []
    start = max(iv.index[0], sig.dropna().index[0])
    i = int(np.searchsorted(days, start))
    while i + 21 < len(days):
        a, b = days[i], days[i + 21]
        if a in iv.index and np.isfinite(sig.get(a, np.nan)):
            s0, s1 = px[a], px[b]
            vol = (k + kshift) * iv[a] / 100
            prem = bs(s0, vol, 21 / 252, 'C')
            rows.append({'start': a, 'ratio': iv[a] / 100 / sig[a],
                         'straddle': (2 * prem - abs(s1 - s0)) / s0 - COST * 2 * prem / s0,
                         'put': (prem - max(s0 - s1, 0)) / s0 - COST * prem / s0})
        i += 21
    return pd.DataFrame(rows)


def series(df, inst, th):
    hold = np.ones(len(df), bool) if th is None else (df['ratio'] >= th).values
    return np.where(hold, df[inst].values, 0.0), int(hold.sum())


def stats(x, rng):
    boot = W.block_boot(x, rng)
    eq = np.cumsum(x)
    sd = x.std(ddof=1)
    return {'mean': float(x.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
            'sharpe': float(x.mean() / sd * np.sqrt(12)) if sd > 0 else 0.0, 't_block': float(x.mean() / boot.std(ddof=1)),
            'worst': float(x.min()), 'max_drawdown': float(np.max(np.maximum.accumulate(eq) - eq))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--data', default='../wrds_studies/public')
    ap.add_argument('--docs', default='docs/research8/xmarket')
    a = ap.parse_args()
    rng = np.random.default_rng(20261009)
    data = {m: periods(a.data, m) for m in MARKETS}
    out, picks = {}, {}
    if a.mode == 'final':
        path = os.path.join(HERE, 'xmarket_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/xmarket_frozen.json')
        picks = json.load(open(path))['frozen']
    for m, df in data.items():
        df = df[df['start'] < SPLIT] if a.mode == 'dev' else df[df['start'] >= SPLIT]
        for inst in ('straddle', 'put'):
            res = {}
            for th in (None, 1.2, 1.5):
                x, held = series(df, inst, th)
                res['always' if th is None else f'>={th}'] = {'periods': len(x), 'held': held, **stats(x, rng)}
            out[f'{m}|{inst}'] = res
            if a.mode == 'dev':
                cand = [k for k in ('>=1.2', '>=1.5') if res[k]['t_block'] >= 2.0 and res[k]['sharpe'] > res['always']['sharpe']]
                if cand:
                    picks[f'{m}|{inst}'] = max(cand, key=lambda k: res[k]['sharpe'])
            for k, v in res.items():
                print(f"{a.mode} {m} {inst} {k}: periods {v['periods']} held {v['held']} mean {v['mean'] * 100:+.3f}% "
                      f"SR {v['sharpe']:.2f} t {v['t_block']:.2f} worst {v['worst'] * 100:+.1f}% maxDD {v['max_drawdown'] * 100:.1f}%")
    extra = {}
    if a.mode == 'dev':
        extra['freeze_picks'] = picks
        print('frozen', picks)
    else:
        gates = {}
        for cell, rule in picks.items():
            r, b = out[cell][rule], out[cell]['always']
            g = {'g1': r['ci'][0] > 0, 'g2': r['sharpe'] >= 1.0, 'g3': r['t_block'] >= 2.0, 'g4': r['sharpe'] > b['sharpe'],
                 'g5': r['max_drawdown'] <= b['max_drawdown']}
            g['strong'] = all(g.values())
            gates[cell] = g
            print('GATE', cell, rule, g)
        for inst in ('straddle', 'put'):
            cells = [c for c in picks if c.endswith(inst)]
            if len(cells) == 2:
                parts, base = [], []
                for c in cells:
                    m = c.split('|')[0]
                    df = data[m][data[m]['start'] >= SPLIT].set_index('start')
                    th = float(picks[c][2:])
                    parts.append(pd.Series(np.where(df['ratio'] >= th, df[inst], 0.0), index=df.index).resample('M').sum())
                    base.append(df[inst].resample('M').sum())
                port = pd.concat(parts, axis=1).fillna(0).mean(1).values
                pb = pd.concat(base, axis=1).fillna(0).mean(1).values
                r, b = stats(port, rng), stats(pb, rng)
                g = {'g1': r['ci'][0] > 0, 'g2': r['sharpe'] >= 1.0, 'g3': r['t_block'] >= 2.0, 'g4': r['sharpe'] > b['sharpe'],
                     'g5': r['max_drawdown'] <= b['max_drawdown']}
                g['strong'] = all(g.values())
                gates[f'portfolio|{inst}'] = g
                out[f'portfolio|{inst}'] = {'frozen': r, 'always': b}
                print('GATE portfolio', inst, g, f"SR {r['sharpe']:.2f} t {r['t_block']:.2f} vs always SR {b['sharpe']:.2f}")
        extra['gates'] = gates
        sens = {}
        for ks in (-0.05, 0.05):
            for m in MARKETS:
                df = periods(a.data, m, ks)
                df = df[df['start'] >= SPLIT]
                for inst in ('straddle', 'put'):
                    for th in (None, 1.2, 1.5):
                        x, _ = series(df, inst, th)
                        sens[f'k{ks:+.2f}|{m}|{inst}|{th}'] = stats(x, rng)['sharpe']
        extra['sensitivity_sharpe_not_selection'] = sens
    os.makedirs(a.docs, exist_ok=True)
    json.dump({'sample': a.mode, 'results': out, **extra}, open(os.path.join(a.docs, f'{a.mode}.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
