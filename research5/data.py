"""Build standard-library caches from the earnings_vol WRDS cache.

Outputs (private directory, never in Git):
  base.pkl          sessions, stocks, events, dividends, issuers
  quotes_<year>.pkl {(secid, date): {exdate: {strike: [cbid, cask, coi, pbid, pask, poi]}}}
  data_audit.json   coverage and integrity counts
"""
import argparse
import bisect
import csv
import datetime as dt
import glob
import gzip
import json
import math
import os
import pickle
from collections import Counter, defaultdict
from multiprocessing import Pool

from .pickle_compat import load_frame

BID, ASK, OI = 0, 1, 2  # offsets within a call (0..2) or put (3..5) block


def _date(value):
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value)[:10])


def parse_quotes(path):
    snaps = {}
    rows = 0
    with gzip.open(path, 'rt', newline='') as stream:
        for r in csv.DictReader(stream):
            rows += 1
            if r['cfadj'] not in ('1', '1.0'):
                continue
            key = (int(r['secid']), r['date'])
            chain = snaps.setdefault(key, {}).setdefault(r['exdate'], {})
            strike = int(r['strike_price']) / 1000.0
            leg = chain.setdefault(strike, [None] * 6)
            base = 0 if r['cp_flag'] == 'C' else 3
            bid = float(r['best_bid']) if r['best_bid'] != '' else None
            ask = float(r['best_offer']) if r['best_offer'] != '' else None
            oi = float(r['open_interest']) if r['open_interest'] != '' else 0.0
            # Duplicate contracts (e.g. non-standard roots) keep the tighter, more open one.
            if leg[base + ASK] is not None and (oi < leg[base + OI]):
                continue
            leg[base:base + 3] = [bid, ask, oi]
    return os.path.basename(path), rows, snaps


def build(source, output):
    os.makedirs(output, exist_ok=True)
    audit = {}
    stocks = defaultdict(dict)
    sessions = set()
    for path in sorted(glob.glob(os.path.join(source, 'stocks_*.pkl'))):
        _, rows = load_frame(path)
        for r in rows:
            d = _date(r['date'])
            sessions.add(d)
            stocks[int(r['secid'])][d] = (r['close'], r['return'], r['cfadj'], r['volume'])
    sessions = sorted(sessions)
    audit['sessions'] = [str(sessions[0]), str(sessions[-1]), len(sessions)]

    # Integrity: total return should match adjusted close ratio except on distribution days.
    checks = Counter()
    for sid, series in stocks.items():
        dates = sorted(series)
        for a, b in zip(dates, dates[1:]):
            ca, _, fa, _ = series[a]
            cb, rb, fb, _ = series[b]
            if ca and cb and fa and fb and rb is not None and not math.isnan(rb):
                implied = (cb * fb) / (ca * fa) - 1
                checks['ok' if abs(implied - rb) < 0.02 else 'mismatch>2%'] += 1
    audit['stock_return_vs_adjusted_close'] = dict(checks)

    issuer_of, ticker_of = {}, {}
    with open(os.path.join(source, 'universe.csv'), newline='') as stream:
        for r in csv.DictReader(stream):
            issuer_of[int(r['secid'])] = r['issuer']
            ticker_of[int(r['secid'])] = r['ticker']

    events, skipped = [], Counter()
    seen = set()
    with open(os.path.join(source, 'events.csv'), newline='') as stream:
        for r in csv.DictReader(stream):
            sid = int(r['secid'])
            ann = _date(r['event'])
            i = bisect.bisect_left(sessions, ann)
            if i >= len(sessions):
                skipped['after_last_session'] += 1
                continue
            e = sessions[i]
            if (sid, e) in seen:
                skipped['duplicate_session'] += 1
                continue
            seen.add((sid, e))
            events.append({'secid': sid, 'ticker': ticker_of.get(sid, r['ticker']), 'issuer': issuer_of.get(sid, r['issuer']),
                           'announce': ann, 'E': e, 'E_index': i})
    events.sort(key=lambda x: (x['E'], x['secid']))
    audit['events'] = {'kept': len(events), 'skipped': dict(skipped),
                       'moved_to_next_session': sum(1 for x in events if x['announce'] != x['E'])}

    _, drows = load_frame(os.path.join(source, 'distributions.pkl'))
    dividends = defaultdict(list)
    for r in drows:
        if str(r['cancel_flag']) == '1':
            continue
        dividends[int(r['secid'])].append(_date(r['ex_date']))
    for v in dividends.values():
        v.sort()

    files = sorted(glob.glob(os.path.join(source, 'quotes_*.csv.gz')))
    by_year = defaultdict(dict)
    total_rows = 0
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        for name, rows, snaps in pool.imap_unordered(parse_quotes, files):
            total_rows += rows
            year = name.split('_')[1]
            for key, chain in snaps.items():
                if key in by_year[year]:
                    for ex, strikes in chain.items():
                        by_year[year][key].setdefault(ex, {}).update(strikes)
                else:
                    by_year[year][key] = chain
    audit['quote_rows'] = total_rows
    quote_keys = set()
    for year, snaps in sorted(by_year.items()):
        with open(os.path.join(output, f'quotes_{year}.pkl'), 'xb') as stream:
            pickle.dump(snaps, stream, protocol=pickle.HIGHEST_PROTOCOL)
        quote_keys.update((sid, d) for sid, d in snaps)
        audit[f'quote_snapshots_{year}'] = len(snaps)

    offsets = Counter()
    for ev in events:
        for off in range(-2, 4):
            j = ev['E_index'] + off
            if 0 <= j < len(sessions) and (ev['secid'], sessions[j].isoformat()) in quote_keys:
                offsets[off] += 1
    audit['events_with_quotes_by_offset'] = {str(k): offsets[k] for k in sorted(offsets)}
    audit['events_by_year'] = dict(sorted(Counter(ev['E'].year for ev in events).items()))

    base = {'sessions': sessions, 'stocks': dict(stocks), 'events': events, 'dividends': dict(dividends),
            'issuer_of': issuer_of, 'ticker_of': ticker_of}
    with open(os.path.join(output, 'base.pkl'), 'xb') as stream:
        pickle.dump(base, stream, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(output, 'data_audit.json'), 'x') as stream:
        json.dump(audit, stream, indent=2, default=str)
    return audit


def load_base(cache):
    with open(os.path.join(cache, 'base.pkl'), 'rb') as stream:
        return pickle.load(stream)


def load_quotes(cache, years):
    snaps = {}
    for year in years:
        path = os.path.join(cache, f'quotes_{year}.pkl')
        if os.path.exists(path):
            with open(path, 'rb') as stream:
                snaps.update(pickle.load(stream))
    return snaps


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='../wrds_studies/earnings_vol')
    parser.add_argument('--output', default='../wrds_studies/research5_cache')
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2, default=str))
