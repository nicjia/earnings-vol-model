#!/usr/bin/env python3
"""Per-day OPRA contract list from the WRDS daily option panel, for budget Databento requests.

python data_pulls/wrds_contract_list.py --daily ../wrds_studies/research8_daily/daily --start 2023-10-02 \
    --out contracts_by_day.csv.gz

Keeps, per underlying and day: the nearest N Friday expiries, strikes with |ln(K/S)| <= z * IV_atm * sqrt(T)
(min band 3%), and open interest >= min_oi. Writes date, underlying, OSI symbol (OPRA raw_symbol format).
"""
import argparse
import glob
import math
import os

import numpy as np
import pandas as pd

WANT = ('SPY', 'AAPL', 'NVDA', 'TSLA', 'AMZN', 'FB', 'META')


def osi(root, exdate, cp, strike):
    return f"{root:<6}{exdate:%y%m%d}{cp}{int(round(strike * 1000)):08d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--daily', required=True)
    ap.add_argument('--start', default='2023-10-02')
    ap.add_argument('--out', default='contracts_by_day.csv.gz')
    ap.add_argument('--expiries', type=int, default=8)
    ap.add_argument('--z', type=float, default=2.0)
    ap.add_argument('--min-oi', type=float, default=100)
    a = ap.parse_args()
    panel = pd.read_csv(os.path.join(a.daily, 'panel.csv'))
    tick = {int(s): t for s, t in zip(panel['secid'], panel['ticker'])}
    want = {s: t for s, t in tick.items() if t in WANT}
    stocks = pd.concat(pd.read_csv(f) for f in glob.glob(os.path.join(a.daily, 'stocks_daily_*.csv.gz')))
    stocks = stocks[stocks['secid'].isin(want)]
    close = {(int(s), d[:10]): abs(c) for s, d, c in zip(stocks['secid'], stocks['date'], stocks['close'])}
    rows = []
    for f in sorted(glob.glob(os.path.join(a.daily, 'quotes_daily_*.csv.gz'))):
        if int(os.path.basename(f).split('_')[2]) < int(a.start[:4]):
            continue
        q = pd.read_csv(f, usecols=['secid', 'date', 'exdate', 'cp_flag', 'strike_price', 'open_interest', 'impl_volatility', 'cfadj'])
        q = q[q['secid'].isin(want) & (q['date'] >= a.start)]
        if q.empty:
            continue
        q['exd'] = pd.to_datetime(q['exdate'])
        q = q[q['exd'].dt.weekday == 4]
        q['K'] = q['strike_price'] / 1000.0
        for (sid, d), g in q.groupby(['secid', 'date']):
            S = close.get((int(sid), d[:10]))
            if not S:
                continue
            exps = sorted(g['exd'].unique())[:a.expiries]
            g = g[g['exd'].isin(exps)]
            atm = g.iloc[(g['K'] - S).abs().argsort()[:4]]['impl_volatility'].dropna()
            iv = float(atm.mean()) if len(atm) else 0.4
            T = (g['exd'] - pd.Timestamp(d)).dt.days.clip(lower=1) / 365.0
            band = np.maximum(a.z * iv * np.sqrt(T), 0.03)
            g = g[(np.abs(np.log(g['K'] / S)) <= band) & (g['open_interest'] >= a.min_oi)]
            root = 'META' if want[int(sid)] in ('FB', 'META') else want[int(sid)]
            rows += [(d[:10], root, osi(root, e, cp, k)) for e, cp, k in zip(g['exd'], g['cp_flag'], g['K'])]
        print(os.path.basename(f), len(rows), flush=True)
    out = pd.DataFrame(rows, columns=['date', 'underlying', 'symbol']).drop_duplicates()
    out.to_csv(a.out, index=False, compression='gzip')
    per = out.groupby(['date']).size()
    print(f'{len(out)} rows, {out["date"].nunique()} days, median {int(per.median())} contracts/day, range {out["date"].min()}..{out["date"].max()}')


if __name__ == '__main__':
    main()
