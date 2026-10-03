"""Model-timed index put-writing on CBOE public data (pre-registered in protocol_putwrite.json).

python -m research8.putwrite dev   --data ../wrds_studies/public
python -m research8.putwrite final --data ...   (needs committed research8/putwrite_frozen.json)
"""
import argparse
import datetime as dt
import json
import os

import numpy as np
import pandas as pd

from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
THETAS = (1.0, 1.1, 1.2, 1.3, 1.5)
COSTS = (0.0, 0.0005, 0.0015)
BLOCK = 6


def load(path):
    def series(name, col):
        d = pd.read_csv(os.path.join(path, f'{name}.csv'))
        d['DATE'] = pd.to_datetime(d['DATE'])
        return d.set_index('DATE')[col].astype(float)
    spx, vix, put = series('SPX', 'SPX'), series('VIX', 'CLOSE'), series('PUT', 'PUT')
    tb = pd.read_csv(os.path.join(path, 'DTB3.csv'))
    tb['observation_date'] = pd.to_datetime(tb['observation_date'])
    tb = pd.to_numeric(tb.set_index('observation_date')['DTB3'], errors='coerce').ffill()
    return spx, vix, put, tb


def har_sigma(spx):
    r = np.log(spx).diff().dropna()
    x = r.values ** 2
    idx = r.index
    n = len(x)

    def back(w):
        c = np.concatenate([[0], np.cumsum(x)])
        out = np.full(n, np.nan)
        out[w - 1:] = (c[w:] - c[:-w]) / w
        return out
    feats = np.column_stack([np.log(np.maximum(back(w), 1e-10)) for w in (1, 5, 22, 66)])
    c = np.concatenate([[0], np.cumsum(x)])
    fwd = np.full(n, np.nan)
    fwd[:n - 21] = (c[22:] - c[1:n - 20]) / 21
    y = np.log(np.maximum(fwd, 1e-10))
    end_date = pd.Series(idx).shift(-21).values
    sig = np.full(n, np.nan)
    for year in range(1977, idx[-1].year + 1):
        cut = pd.Timestamp(year, 1, 1)
        tr = np.isfinite(feats).all(1) & np.isfinite(fwd) & (pd.Series(end_date) < cut).values
        if tr.sum() < 500:
            continue
        A = np.c_[np.ones(tr.sum()), feats[tr]]
        beta, *_ = np.linalg.lstsq(A, y[tr], rcond=None)
        smear = np.mean(np.exp(y[tr] - A @ beta))
        sel = (idx >= cut) & (idx < pd.Timestamp(year + 1, 1, 1)) & np.isfinite(feats).all(1)
        sig[sel] = np.sqrt(252 * np.exp(np.c_[np.ones(sel.sum()), feats[sel]] @ beta) * smear)
    return pd.Series(sig, index=idx)


def ewma_sigma(spx):
    r = np.log(spx).diff().dropna()
    v = np.empty(len(r))
    var = np.mean(r.values[:20] ** 2)
    for i, x in enumerate(r.values):
        var = 0.94 * var + 0.06 * x * x
        v[i] = var
    return pd.Series(np.sqrt(252 * v), index=r.index)


def roll_dates(put):
    days = put.index
    out = []
    for (y, m), _ in put.groupby([days.year, days.month]):
        first = pd.Timestamp(y, m, 1)
        fri = first + pd.Timedelta(days=(4 - first.weekday()) % 7 + 14)
        ok = days[days <= fri]
        if len(ok) and ok[-1].month == m:
            out.append(ok[-1])
    return out


def monthly(spx, vix, put, tb):
    rolls = roll_dates(put)
    sig = {'HAR': har_sigma(spx), 'EWMA': ewma_sigma(spx)}
    rows = []
    for a, b in zip(rolls[:-1], rolls[1:]):
        if a not in vix.index:
            continue
        rf = tb.asof(a) / 100 * (b - a).days / 360
        rows.append({'start': a, 'end': b, 'ex': put[b] / put[a] - 1 - rf,
                     'ratio_HAR': vix[a] / 100 / sig['HAR'].asof(a), 'ratio_EWMA': vix[a] / 100 / sig['EWMA'].asof(a)})
    return pd.DataFrame(rows)


def rules():
    return [('always', None, None)] + [('ratio', m, t) for m in ('HAR', 'EWMA') for t in THETAS]


def rname(r):
    return 'always' if r[0] == 'always' else f'{r[1]}>={r[2]:g}'


def block_boot(x, rng, draws=2000):
    n = len(x)
    nb = int(np.ceil(n / BLOCK))
    st = rng.integers(0, max(n - BLOCK, 1), (draws, nb))
    idx = (st[:, :, None] + np.arange(BLOCK)).reshape(draws, -1)[:, :n]
    return x[np.minimum(idx, n - 1)].mean(1)


def evaluate(df, rule, rng):
    hold = np.ones(len(df), bool) if rule[0] == 'always' else (df[f'ratio_{rule[1]}'] >= rule[2]).values
    out = {'rule': rname(rule), 'months': int(len(df)), 'months_held': int(hold.sum())}
    for c in COSTS:
        x = np.where(hold, df['ex'].values - c, 0.0)
        boot = block_boot(x, rng)
        eq = np.cumsum(x)
        out[f'c{c * 1e4:g}bp'] = {'mean_month': float(x.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
                                  'sharpe': float(x.mean() / x.std(ddof=1) * np.sqrt(12)) if x.std() > 0 else 0.0,
                                  't_block': float(x.mean() / boot.std(ddof=1)), 'worst_month': float(x.min()),
                                  'max_drawdown': float(np.max(np.maximum.accumulate(eq) - eq))}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--data', default='../wrds_studies/public')
    ap.add_argument('--docs', default='docs/research8/putwrite')
    a = ap.parse_args()
    df = monthly(*load(a.data))
    if a.mode == 'dev':
        df = df[(df['start'] >= '2007-01-01') & (df['end'] <= '2015-12-31')]
        rl = rules()
    else:
        path = os.path.join(HERE, 'putwrite_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/putwrite_frozen.json')
        rl = [('always', None, None)] + [tuple(x) for x in json.load(open(path))['rules']]
        df = df[df['start'] >= '2016-01-01']
    rng = np.random.default_rng(20261007)
    res = [evaluate(df, r, rng) for r in rl]
    key = 'c15bp'
    base = res[0][key]
    extra = {}
    if a.mode == 'dev':
        elig = [x for x in res[1:] if x[key]['t_block'] >= 2.0 and x[key]['sharpe'] > base['sharpe']]
        picks, used = [], set()
        for x in sorted(elig, key=lambda x: -x[key]['sharpe']):
            r = next(r for r in rl if rname(r) == x['rule'])
            if r[1] in used:
                continue
            used.add(r[1])
            picks.append(list(r))
        extra = {'eligible': len(elig), 'freeze_picks': picks[:2]}
        print('eligible', len(elig), 'picks', picks[:2])
    else:
        extra['gates'] = {}
        for x in res[1:]:
            c = x[key]
            g = {'g1': c['ci'][0] > 0, 'g2': c['sharpe'] >= 1.0, 'g3': c['t_block'] >= 2.0, 'g4': c['sharpe'] > base['sharpe'],
                 'g5': c['max_drawdown'] <= base['max_drawdown']}
            g['strong'] = all(g.values())
            g['weak'] = g['g1'] and not g['strong']
            extra['gates'][x['rule']] = g
            print('GATE', x['rule'], g)
    os.makedirs(a.docs, exist_ok=True)
    json.dump({'sample': a.mode, 'rules': res, **extra}, open(os.path.join(a.docs, f'{a.mode}.json'), 'w'), indent=1, default=str)
    for x in res:
        c = x[key]
        print(f"{x['rule']}: months {x['months']} held {x['months_held']} | 15bp: mean {c['mean_month'] * 100:+.2f}%/mo "
              f"SR {c['sharpe']:.2f} t {c['t_block']:.2f} worst {c['worst_month'] * 100:+.1f}% maxDD {c['max_drawdown'] * 100:.1f}% "
              f"| 0bp SR {x['c0bp']['sharpe']:.2f}")


if __name__ == '__main__':
    main()
