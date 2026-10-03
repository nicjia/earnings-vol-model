#!/usr/bin/env python3
"""Budget-filtered hourly option quote snapshots from Databento OPRA (run locally with your API key).

Cost control:
  1. Contracts come from the cheap daily `definition` schema, filtered to the nearest N Friday expiries and to strikes
     within z standard deviations of the previous close (band widens with days to expiry):  |ln(K/S)| <= z*vol*sqrt(T)
  2. Quotes are requested as `cbbo-1m` but only for one-minute windows at fixed times each day (default 10:00-15:00 ET
     hourly), so you pay for ~6 of the 390 minutes per contract.
  3. `estimate` prices a sample of days with metadata.get_cost and extrapolates BEFORE anything is downloaded.

  export DATABENTO_API_KEY=...
  python data_pulls/databento_pull.py estimate --start 2023-10-02 --end 2026-10-02 --contracts contracts_by_day.csv.gz
  python data_pulls/databento_pull.py pull     --start 2023-10-02 --end 2026-10-02 --out ~/stock/databento_hourly

Outputs (pull): one CSV.gz per underlying per month of quote snapshots (ts, symbol, expiry, strike, cp, bid, ask,
bid_sz, ask_sz) plus the daily underlying closes used for filtering. Resumable: finished days are skipped.
Names of datasets/schemas follow Databento's docs at the time of writing; if a request errors, check them there.
"""
import argparse
import datetime as dt
import math
import os
import random
import sys
import time
from zoneinfo import ZoneInfo

import pandas as pd

OPRA = 'OPRA.PILLAR'
EQUITY = 'XNAS.ITCH'          # underlying daily bars for the strike filter (SPY and these names all trade on Nasdaq)
UNDERLYINGS = ('SPY', 'AAPL', 'NVDA', 'TSLA', 'AMZN', 'META')
ET = ZoneInfo('America/New_York')
CHUNK = 2000                  # symbols per request


def client():
    import databento as db
    key = os.environ.get('DATABENTO_API_KEY')
    if not key:
        sys.exit('set DATABENTO_API_KEY')
    return db.Historical(key)


def closes(c, start, end):
    """Daily closes and trailing 20-day realized vol per underlying."""
    df = c.timeseries.get_range(dataset=EQUITY, schema='ohlcv-1d', symbols=list(UNDERLYINGS),
                                start=(start - dt.timedelta(days=45)).isoformat(), end=end.isoformat()).to_df()
    df = df.reset_index()
    df['date'] = pd.to_datetime(df['ts_event']).dt.tz_convert(ET).dt.date
    out = {}
    for sym, g in df.groupby('symbol'):
        s = g.set_index('date')['close'].astype(float).sort_index()
        vol = (s.apply(math.log).diff().rolling(20).std() * math.sqrt(252)).bfill()
        out[sym] = pd.DataFrame({'close': s, 'vol': vol.clip(lower=0.10)})
    return out


_LIST = None


def listed(args):
    """Optional WRDS-built list (data_pulls/wrds_contract_list.py): {date: [symbols]}; saves the definition requests."""
    global _LIST
    if _LIST is None:
        _LIST = {}
        if args.contracts:
            df = pd.read_csv(os.path.expanduser(args.contracts))
            _LIST = {d: g['symbol'].tolist() for d, g in df.groupby('date')}
    return _LIST


def contracts(c, day, prev, args):
    """OPRA raw symbols to request for one day: from the WRDS list when it covers the day, else from Databento
    definitions filtered by expiry and DTE-scaled moneyness."""
    lst = listed(args)
    if day.isoformat() in lst:
        return lst[day.isoformat()]
    d0 = dt.datetime.combine(day, dt.time(0), ET)
    df = c.timeseries.get_range(dataset=OPRA, schema='definition', stype_in='parent',
                                symbols=[f'{u}.OPT' for u in UNDERLYINGS],
                                start=d0.isoformat(), end=(d0 + dt.timedelta(hours=10)).isoformat()).to_df()
    if df.empty:
        return []
    df = df.reset_index().drop_duplicates('raw_symbol')
    df['exp'] = pd.to_datetime(df['expiration']).dt.tz_convert(ET).dt.date
    df = df[(df['exp'] > day) & (pd.to_datetime(df['exp']).dt.weekday == 4)]  # Friday expiries only
    keep = []
    for u in UNDERLYINGS:
        g = df[df['underlying'] == u]
        if g.empty or u not in prev:
            continue
        S, vol = prev[u]
        exps = sorted(g['exp'].unique())[:args.expiries]
        g = g[g['exp'].isin(exps)]
        T = (pd.to_datetime(g['exp']) - pd.Timestamp(day)).dt.days.clip(lower=1) / 365.0
        band = args.z * vol * T.apply(math.sqrt)
        m = (g['strike_price'].astype(float) / S).apply(math.log).abs() <= band.clip(lower=args.min_band)
        keep += g.loc[m, 'raw_symbol'].tolist()
    return keep


def windows(day, times):
    for hhmm in times:
        h, m = map(int, hhmm.split(':'))
        a = dt.datetime.combine(day, dt.time(h, m), ET)
        yield a, a + dt.timedelta(minutes=1)


def trading_days(start, end, cl):
    days = sorted(set().union(*[set(v.index) for v in cl.values()]))
    return [d for d in days if start <= d <= end]


def prev_state(cl, day):
    out = {}
    for u, v in cl.items():
        p = v[v.index < day]
        if len(p):
            out[u] = (float(p['close'].iloc[-1]), float(p['vol'].iloc[-1]))
    return out


def estimate(args):
    c = client()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    cl = closes(c, start, end)
    days = trading_days(start, end, cl)
    sample = sorted(random.Random(0).sample(days, min(args.sample, len(days))))
    cost, n = 0.0, 0
    for day in sample:
        syms = contracts(c, day, prev_state(cl, day), args)
        n += len(syms)
        for a, b in windows(day, args.times):
            for i in range(0, len(syms), CHUNK):
                cost += c.metadata.get_cost(dataset=OPRA, schema='cbbo-1m', stype_in='raw_symbol', symbols=syms[i:i + CHUNK],
                                            start=a.isoformat(), end=b.isoformat())
        print(f'{day}: {len(syms)} contracts', flush=True)
    per_day = cost / len(sample)
    print(f'\navg contracts/day {n / len(sample):.0f}; est quote cost/day ${per_day:.3f}; '
          f'{len(days)} days -> est total ${per_day * len(days):.2f} (+ definitions and daily bars, usually small)')


def pull(args):
    c = client()
    start, end = dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end)
    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)
    cl = closes(c, start, end)
    pd.concat({u: v for u, v in cl.items()}).to_csv(os.path.join(out, 'underlying_daily.csv.gz'))
    done_path = os.path.join(out, 'done_days.txt')
    done = set(open(done_path).read().split()) if os.path.exists(done_path) else set()
    for day in trading_days(start, end, cl):
        if day.isoformat() in done:
            continue
        syms = contracts(c, day, prev_state(cl, day), args)
        parts = []
        for a, b in windows(day, args.times):
            for i in range(0, len(syms), CHUNK):
                for attempt in range(4):
                    try:
                        df = c.timeseries.get_range(dataset=OPRA, schema='cbbo-1m', stype_in='raw_symbol',
                                                    symbols=syms[i:i + CHUNK], start=a.isoformat(), end=b.isoformat()).to_df()
                        break
                    except Exception as e:  # transient API errors: back off and retry
                        print('retry', day, a.time(), e, flush=True)
                        time.sleep(2 ** attempt)
                else:
                    raise RuntimeError(f'failed {day} {a}')
                if len(df):
                    df = df.reset_index()
                    df['slot'] = a.strftime('%H:%M')
                    parts.append(df)
        if parts:
            df = pd.concat(parts)
            keep = [x for x in ('ts_event', 'slot', 'symbol', 'bid_px_00', 'ask_px_00', 'bid_sz_00', 'ask_sz_00', 'price')
                    if x in df.columns]
            df = df[keep]
            df['date'] = day.isoformat()
            for u in UNDERLYINGS:
                g = df[df['symbol'].str.startswith(u.ljust(6))]
                if len(g):
                    path = os.path.join(out, f'{u}_{day:%Y-%m}.csv.gz')
                    g.to_csv(path, mode='a', header=not os.path.exists(path), index=False, compression='gzip')
        with open(done_path, 'a') as s:
            s.write(day.isoformat() + '\n')
        print(day, len(syms), 'contracts', sum(len(p) for p in parts), 'rows', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['estimate', 'pull'])
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--out', default='~/stock/databento_hourly')
    ap.add_argument('--expiries', type=int, default=8, help='nearest N Friday expiries')
    ap.add_argument('--z', type=float, default=2.0, help='strike band in standard deviations of the move to expiry')
    ap.add_argument('--min-band', type=float, default=0.03, help='minimum |ln K/S| band for very short expiries')
    ap.add_argument('--times', nargs='+', default=['10:00', '11:00', '12:00', '13:00', '14:00', '15:00'],
                    help='ET snapshot minutes')
    ap.add_argument('--sample', type=int, default=8, help='days priced by estimate')
    ap.add_argument('--contracts', default=None, help='WRDS contract list (contracts_by_day.csv.gz); days it covers skip definitions')
    a = ap.parse_args()
    estimate(a) if a.mode == 'estimate' else pull(a)
