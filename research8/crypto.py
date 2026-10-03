"""Weekly crypto option premium selling on Deribit public data (pre-registered in protocol_crypto.json).

python -m research8.crypto pull  --out ../wrds_studies/deribit
python -m research8.crypto dev   --data ../wrds_studies/deribit
python -m research8.crypto final --data ...   (needs committed research8/crypto_frozen.json)
"""
import argparse
import datetime as dt
import json
import os
import time
import urllib.request

import numpy as np
import pandas as pd

from . import rules2 as R2

HERE = os.path.dirname(os.path.abspath(__file__))
COINS = ('BTC', 'ETH')
RULES = [(c, inst, th) for c in COINS for inst in ('straddle', 'put') for th in (None, 1.1, 1.25, 1.5)]
FIRST, DEV_END, TEST_START = dt.date(2019, 1, 4), dt.date(2022, 12, 31), dt.date(2023, 1, 1)
BLOCK = 8


def get(url, tries=5):
    for k in range(tries):
        try:
            return json.load(urllib.request.urlopen(url, timeout=60))
        except Exception:
            time.sleep(2 ** k)
    raise RuntimeError('failed: ' + url)


def ms(d):
    return int(d.timestamp() * 1000)


def pull(out):
    os.makedirs(out, exist_ok=True)
    for coin in COINS:
        c = get('https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name='
                f'{coin}-PERPETUAL&start_timestamp={ms(dt.datetime(2018, 1, 1, tzinfo=dt.timezone.utc))}'
                f'&end_timestamp={ms(dt.datetime.now(dt.timezone.utc))}&resolution=1D')['result']
        pd.DataFrame({'t': c['ticks'], 'close': c['close']}).to_csv(os.path.join(out, f'{coin}_perp_daily.csv'), index=False)
        rows, off = [], 0
        while True:
            d = get(f'https://www.deribit.com/api/v2/public/get_delivery_prices?index_name={coin.lower()}_usd&offset={off}&count=1000')['result']
            rows += d['data']
            off += len(d['data'])
            if not d['data'] or off >= d['records_total']:
                break
        pd.DataFrame(rows).to_csv(os.path.join(out, f'{coin}_delivery.csv'), index=False)
        path = os.path.join(out, f'{coin}_trades.csv.gz')
        done = set()
        if os.path.exists(path):
            done = set(pd.read_csv(path, usecols=['friday'])['friday'].unique())
        fri = FIRST
        today = dt.date.today()
        while fri < today:
            if fri.isoformat() not in done:
                start = dt.datetime(fri.year, fri.month, fri.day, 8, tzinfo=dt.timezone.utc)
                end = start + dt.timedelta(hours=2)
                t0, trades = ms(start), []
                while True:
                    r = get('https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time?'
                            f'currency={coin}&kind=option&start_timestamp={t0}&end_timestamp={ms(end)}&count=1000&sorting=asc')['result']
                    trades += r['trades']
                    if not r.get('has_more') or not r['trades']:
                        break
                    t0 = r['trades'][-1]['timestamp'] + 1
                df = pd.DataFrame(trades)
                if len(df):
                    df = df.drop_duplicates('trade_id')[['timestamp', 'instrument_name', 'price', 'amount', 'direction', 'iv', 'index_price']]
                    df['friday'] = fri.isoformat()
                    df.to_csv(path, mode='a', header=not os.path.exists(path), index=False, compression='gzip')
                print(coin, fri, len(df), flush=True)
            fri += dt.timedelta(days=7)


def har_sigma(daily):
    """daily: Series of closes indexed by date (00:00 UTC). Returns Series sigma_hat (annualized, 365) per date."""
    r = np.log(daily).diff().dropna()
    x = r.values ** 2
    n = len(x)
    c = np.concatenate([[0], np.cumsum(x)])

    def back(w):
        out = np.full(n, np.nan)
        out[w - 1:] = (c[w:] - c[:-w]) / w
        return out
    F = np.column_stack([np.log(np.maximum(back(w), 1e-10)) for w in (1, 7, 30, 90)])
    fwd = np.full(n, np.nan)
    fwd[:n - 7] = (c[8:] - c[1:n - 6]) / 7
    y = np.log(np.maximum(fwd, 1e-10))
    idx = r.index
    end = pd.Series(idx).shift(-7).values
    sig = np.full(n, np.nan)
    for year in range(idx[0].year + 1, idx[-1].year + 1):
        cut = pd.Timestamp(year, 1, 1)
        tr = np.isfinite(F).all(1) & np.isfinite(fwd) & (pd.Series(end) < cut).values
        if tr.sum() < 500:
            continue
        A = np.c_[np.ones(tr.sum()), F[tr]]
        beta, *_ = np.linalg.lstsq(A, y[tr], rcond=None)
        smear = np.mean(np.exp(y[tr] - A @ beta))
        sel = (idx >= cut) & (idx < pd.Timestamp(year + 1, 1, 1)) & np.isfinite(F).all(1)
        sig[sel] = np.sqrt(365 * np.exp(np.c_[np.ones(sel.sum()), F[sel]] @ beta) * smear)
    return pd.Series(sig, index=idx)


def weeks(data, coin):
    tr = pd.read_csv(os.path.join(data, f'{coin}_trades.csv.gz'))
    perp = pd.read_csv(os.path.join(data, f'{coin}_perp_daily.csv'))
    perp['date'] = pd.to_datetime(perp['t'], unit='ms').dt.normalize()
    sig = har_sigma(perp.set_index('date')['close'])
    dl = pd.read_csv(os.path.join(data, f'{coin}_delivery.csv'))
    dl = dict(zip(pd.to_datetime(dl['date']).dt.date, dl['delivery_price']))
    parts = tr['instrument_name'].str.split('-', expand=True)
    tr['expiry'] = pd.to_datetime(parts[1], format='%d%b%y').dt.date
    tr['strike'] = parts[2].astype(float)
    tr['cp'] = parts[3]
    rows, skipped = [], 0
    for fri, g in tr.groupby('friday'):
        f = dt.date.fromisoformat(fri)
        nxt = f + dt.timedelta(days=7)
        g = g[(g['expiry'] == nxt) & (g['direction'] == 'sell')]
        S0 = tr.loc[tr['friday'] == fri, 'index_price'].median()
        if not len(g) or nxt not in dl:
            skipped += 1
            continue
        ok = g.groupby('strike')['cp'].nunique()
        ks = ok[ok == 2].index.values
        if not len(ks):
            skipped += 1
            continue
        K = ks[np.argmin(np.abs(ks - S0))]
        D = dl[nxt]
        legs = {}
        for cp in ('C', 'P'):
            h = g[(g['strike'] == K) & (g['cp'] == cp)]
            p = float(np.average(h['price'], weights=h['amount']))
            fee = min(0.0003, 0.125 * p) + 0.00015
            pay = max(D - K, 0) / D if cp == 'C' else max(K - D, 0) / D
            legs[cp] = {'pnl': p - pay - fee, 'iv': float(np.average(h['iv'], weights=h['amount']))}
        s = sig.asof(pd.Timestamp(f))
        rows.append({'friday': f, 'straddle': legs['C']['pnl'] + legs['P']['pnl'], 'put': legs['P']['pnl'],
                     'ratio_straddle': (legs['C']['iv'] + legs['P']['iv']) / 200 / s if np.isfinite(s) else np.nan,
                     'ratio_put': legs['P']['iv'] / 100 / s if np.isfinite(s) else np.nan})
    return pd.DataFrame(rows), skipped


def block_boot(x, rng, draws=2000):
    n = len(x)
    nb = int(np.ceil(n / BLOCK))
    st = rng.integers(0, max(n - BLOCK, 1), (draws, nb))
    idx = (st[:, :, None] + np.arange(BLOCK)).reshape(draws, -1)[:, :n]
    return x[np.minimum(idx, n - 1)].mean(1)


def series(df, inst, th):
    hold = np.ones(len(df), bool) if th is None else (df[f'ratio_{inst}'] >= th).fillna(False).values
    return np.where(hold, df[inst].values, 0.0), int(hold.sum())


def stats(x, dates, rng):
    boot = block_boot(x, rng)
    sd = x.std(ddof=1)
    yrs = pd.Series(x, index=pd.to_datetime(dates)).groupby(lambda d: d.year)
    eq = np.cumsum(x)
    return {'weeks': int(len(x)), 'mean': float(x.mean()), 'ci': np.percentile(boot, [2.5, 97.5]).tolist(),
            'sharpe': float(x.mean() / sd * np.sqrt(52)) if sd > 0 else 0.0, 't_block': float(x.mean() / boot.std(ddof=1)),
            'worst_week': float(x.min()), 'mean_annual': float(yrs.sum().mean()),
            'by_year_mean': {str(k): float(v) for k, v in yrs.mean().items()},
            'max_drawdown': float(np.max(np.maximum.accumulate(eq) - eq))}


def rname(r):
    return f"{r[0]}|{r[1]}|{'always' if r[2] is None else '>=' + str(r[2])}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['pull', 'dev', 'final'])
    ap.add_argument('--out', default='../wrds_studies/deribit')
    ap.add_argument('--data', default='../wrds_studies/deribit')
    ap.add_argument('--docs', default='docs/research8/crypto')
    a = ap.parse_args()
    if a.mode == 'pull':
        pull(a.out)
        return
    rng = np.random.default_rng(20261010)
    W = {}
    for c in COINS:
        df, skipped = weeks(a.data, c)
        W[c] = df
        print(c, 'weeks', len(df), 'skipped', skipped)
    if a.mode == 'dev':
        rl = RULES
        sel = {c: W[c][(W[c]['friday'] >= dt.date(2020, 1, 1)) & (W[c]['friday'] <= DEV_END)] for c in COINS}
    else:
        path = os.path.join(HERE, 'crypto_frozen.json')
        if not R2.committed(path):
            raise SystemExit('final needs a committed research8/crypto_frozen.json')
        rl = [tuple(x) for x in json.load(open(path))['rules']]
        sel = {c: W[c][W[c]['friday'] >= TEST_START] for c in COINS}
    res = {}
    for r in rl:
        df = sel[r[0]]
        x, held = series(df, r[1], r[2])
        res[rname(r)] = {'held': held, **stats(x, df['friday'].values, rng)}
    out = {'sample': a.mode, 'rules': res}
    if a.mode == 'dev':
        picks = []
        for c in COINS:
            for inst in ('straddle', 'put'):
                cell = [r for r in RULES if r[0] == c and r[1] == inst]
                best = max(cell, key=lambda r: res[rname(r)]['sharpe'])
                if res[rname(best)]['t_block'] >= 2.0:
                    picks.append(list(best))
        out['freeze_picks'] = picks
        print('frozen', picks)
    else:
        port = []
        for r in rl:
            df = sel[r[0]]
            x, _ = series(df, r[1], r[2])
            port.append(pd.Series(x, index=pd.to_datetime(df['friday'].values)))
        gates = {}
        if port:
            p = pd.concat(port, axis=1).fillna(0).mean(1)
            res['portfolio'] = {'held': None, **stats(p.values, p.index.values, rng)}
        for k, v in res.items():
            g = {'g1': v['ci'][0] > 0, 'g2': v['sharpe'] >= 1.0, 'g3': v['t_block'] >= 2.0,
                 'g4': v['worst_week'] >= -3 * v['mean_annual'],
                 'g5': sum(v['by_year_mean'].get(str(y), -1) > 0 for y in (2023, 2024, 2025)) >= 2}
            g['strong'] = all(g.values())
            gates[k] = g
            print('GATE', k, g)
        out['gates'] = gates
    os.makedirs(a.docs, exist_ok=True)
    json.dump(out, open(os.path.join(a.docs, f'{a.mode}.json'), 'w'), indent=1, default=str)
    for k, v in res.items():
        print(f"{k}: weeks {v['weeks']} held {v['held']} mean {v['mean'] * 100:+.3f}% of notional SR {v['sharpe']:.2f} "
              f"t {v['t_block']:.2f} worst {v['worst_week'] * 100:+.1f}% maxDD {v['max_drawdown'] * 100:.1f}% years {v['by_year_mean']}")


if __name__ == '__main__':
    main()
