"""Approach T (direct trader): walk-forward boosted regression of the hedged/unhedged short-premium return on
decision-time features; trade when the prediction clears costs plus a margin. Pre-registered in protocol_trader.json.

python -m research8.trader dev   --model <phase-1 best_crps>
python -m research8.trader final --model ...   (needs committed research8/trader_frozen.json)
"""
import argparse
import datetime as dt
import json
import os
import pickle

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

from . import rules2 as R2

MARGINS = (0.0, 0.05, 0.10, 0.20)
HERE = os.path.dirname(os.path.abspath(__file__))
LAB = {l: i for i, l in enumerate(R2.LABELS)}
TIM = {'before_open': 0, 'after_close': 1, 'non_session_date': 2}


def features(recs, f, dates):
    n = len(recs)
    X = np.full((n, 14), np.nan)
    mid_sell = (f['mkt'] - f['payoff']) / f['mkt']
    hed_sell = (f['mkt'] - f['payoff'] - f['hedge']) / f['mkt']
    past = {}
    order = np.argsort(f['tday'], kind='stable')
    lag_h, lag_u, lag_n = np.full(n, np.nan), np.full(n, np.nan), np.zeros(n)
    for i in order:
        key = (f['secid'][i], f['label'][i], f['structure'][i])
        prev = [k for k in past.get(key, []) if f['eday'][k] <= f['tday'][i]][-8:]
        if prev:
            lag_h[i], lag_u[i], lag_n[i] = np.mean(hed_sell[prev]), np.mean(mid_sell[prev]), len(prev)
        past.setdefault(key, []).append(i)
    for i, r in enumerate(recs):
        ivs = np.mean([x['iv'] for x in r['legs']])
        X[i] = [LAB[r['label']], r['structure'] == 'strangle', TIM.get(r['timing'], 3), r['h'], r['M'],
                np.log(f['rho'][i]) if f['rho'][i] > 0 else np.nan, f['rho_rel'][i], f['half'][i] / f['mkt'][i],
                np.log(r['spot']), ivs, lag_h[i], lag_u[i], lag_n[i], np.log(f['model'][i] / r['spot'])]
    return X, hed_sell, mid_sell


def fit_predict(X, y, train, test):
    m = HistGradientBoostingRegressor(loss='absolute_error', max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                      min_samples_leaf=100, random_state=0)
    ok = train & np.isfinite(y)
    # columns with < 2 distinct finite values in the training rows (e.g. lagged features in the first year) are dropped
    keep = [c for c in range(X.shape[1]) if len(np.unique(X[ok, c][np.isfinite(X[ok, c])])) >= 2]
    m.fit(X[ok][:, keep], y[ok])
    return m.predict(X[test][:, keep])


def trade_returns(f, idx, pred, hedged, margin, cost):
    """Sell when pred > entry cost + margin, buy when -pred > entry cost + margin. Returns (returns, week, tday)."""
    est = (0.25 * f['half'][idx] + 2 * R2.FEE_PER_SHARE) / f['mkt'][idx]
    d = np.where(pred > est + margin, -1, np.where(-pred > est + margin, 1, 0))
    k = d != 0
    i2 = idx[k]
    pnl = d[k] * (f['payoff'][i2] - f['mkt'][i2] + (f['hedge'][i2] if hedged else 0.0))
    pnl = pnl - cost * f['half'][i2] - 2 * R2.FEE_PER_SHARE - (f['hcost'][i2] if hedged else 0.0)
    return pnl / f['mkt'][i2], f['week'][i2], f['tday'][i2], d[k]


def stats(ret, weeks, all_weeks, mult):
    w, s, cnt = R2.weekly(ret, weeks, all_weeks)
    boot = (mult @ s) / np.maximum(mult @ cnt, 1)
    sd = w.std(ddof=1)
    return {'mean': float(ret.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
            'sharpe': float(w.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0,
            't': float(w.mean() / sd * np.sqrt(len(w))) if sd > 0 else 0.0, 'worst': float(ret.min()),
            'win': float(np.mean(ret > 0))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['dev', 'final'])
    ap.add_argument('--records', default='../wrds_studies/research8_phase2/records.pkl')
    ap.add_argument('--values', default='../wrds_studies/research8_phase2/values.pkl')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--model', required=True)
    ap.add_argument('--docs', default='docs/research8/trader')
    a = ap.parse_args()
    from . import panel as P
    dates = P.load(a.panel)['dates']
    recs = pickle.load(open(a.records, 'rb'))
    f = R2.frame(recs, pickle.load(open(a.values, 'rb')), a.model, dates)
    X, y_h, y_u = features(recs, f, dates)
    tday = np.array([dt.date.fromordinal(int(x)) for x in f['tday']])
    eday = np.array([dt.date.fromordinal(int(x)) for x in f['eday']])
    tyear = np.array([d.year for d in tday])
    orig = f['group'] == 'original'
    if a.mode == 'dev':
        years, label = range(2019, 2023), 'dev'
        in_sample = orig & (eday <= R2.DEV_END)
        pool = in_sample
        rules = [(h, m) for h in ('hedged', 'unhedged') for m in MARGINS]
    else:
        path = os.path.join(HERE, 'trader_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/trader_frozen.json')
        rules = [tuple(x) for x in json.load(open(path))['rules']]
        years, label = range(2023, 2026), 'test'
        in_sample = ~orig & (tday >= R2.TEST_START)
        pool = np.ones(len(recs), bool)
    preds = {h: np.full(len(recs), np.nan) for h in ('hedged', 'unhedged')}
    for y in years:
        cut = dt.date(y, 1, 1)
        train = pool & (eday < cut)
        test = in_sample & (tyear == y)
        if not test.any():
            continue
        for h, yy in (('hedged', y_h), ('unhedged', y_u)):
            preds[h][test] = fit_predict(X, yy, train, test)
        print(y, 'train', int(train.sum()), 'predict', int(test.sum()), flush=True)
    idx_all = np.where(in_sample & np.isfinite(preds['hedged']))[0]
    all_weeks = np.unique(f['week'][idx_all])
    rng = np.random.default_rng(R2.SEED)
    mult = np.stack([np.bincount(rng.integers(0, len(all_weeks), len(all_weeks)), minlength=len(all_weeks))
                     for _ in range(R2.DRAWS)]).astype(float)
    res = []
    for h, m in rules:
        out = {'rule': f'{h}|margin{m:g}', 'hedge': h, 'margin': m}
        for c in R2.COSTS:
            ret, wk, td, d = trade_returns(f, idx_all, preds[h][idx_all], h == 'hedged', m, c)
            if len(ret) < 20:
                break
            out['n'], out['n_sell'] = int(len(ret)), int((d < 0).sum())
            out[f'c{int(c * 100)}'] = stats(ret, wk, all_weeks, mult)
            if c == 0.25:
                yrs = np.array([dt.date.fromordinal(int(x)).year for x in td])
                out['by_year_c25'] = {str(yv): float(ret[yrs == yv].mean()) for yv in sorted(set(yrs))}
        res.append(out)
    extra = {}
    if label == 'dev':
        elig = [x for x in res if 'c25' in x and x['n'] >= 200 and x['c25']['ci'][0] > 0 and x['c25']['t'] >= 3.0
                and np.mean([v for k, v in x['by_year_c25'].items() if int(k) <= 2020] or [-1]) > 0
                and np.mean([v for k, v in x['by_year_c25'].items() if int(k) >= 2021] or [-1]) > 0]
        picks = [[x['hedge'], x['margin']] for x in sorted(elig, key=lambda x: -x['c25']['sharpe'])[:2]]
        extra = {'eligible': len(elig), 'freeze_picks': picks}
        print('eligible', len(elig), 'picks', picks)
    else:
        extra = {'gates': {x['rule']: R2.gates(x) for x in res}}
        for k, g in extra['gates'].items():
            print('GATE', k, g)
    os.makedirs(a.docs, exist_ok=True)
    json.dump({'sample': label, 'model': a.model, 'rules': res, **extra},
              open(os.path.join(a.docs, f'{label}_{a.model}.json'), 'w'), indent=1)
    for x in res:
        if 'c25' in x:
            c = x['c25']
            print(f"{x['rule']}: n={x['n']} (sell {x['n_sell']}) mid {x['c0']['mean']:+.3f} c25 {c['mean']:+.3f} "
                  f"[{c['ci'][0]:+.3f},{c['ci'][1]:+.3f}] SR {c['sharpe']:.2f} t {c['t']:.2f} c50 {x['c50']['mean']:+.3f}")


if __name__ == '__main__':
    main()
