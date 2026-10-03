"""Build standard-library caches from the research7 WRDS release (CSV, no pandas).

Outputs (private directory, never in Git):
  base.pkl          sessions, stocks, events with release timing and consensus, dividends, issuers
  quotes_<year>.pkl {(secid, 'YYYY-MM-DD'): {exdate: {strike: [cbid, cask, coi, pbid, pask, poi]}}}
  data_audit.json   coverage, exclusions and timing checks
"""
import argparse
import bisect
import csv
import datetime as dt
import glob
import gzip
import json
import os
import pickle
from collections import Counter, defaultdict
from multiprocessing import Pool


def rows(path):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', newline='') as stream:
        yield from csv.DictReader(stream)


def fnum(v):
    return float(v) if v not in ('', None) else None


def day(v):
    return dt.date.fromisoformat(v[:10])


def parse_quotes(path):
    snaps = {}
    n = 0
    for r in rows(path):
        n += 1
        if fnum(r['cfadj']) != 1.0:
            continue
        key = (int(float(r['secid'])), r['date'][:10])
        chain = snaps.setdefault(key, {}).setdefault(r['exdate'][:10], {})
        strike = round(float(r['strike_price']) / 1000.0, 4)
        leg = chain.setdefault(strike, [None] * 6)
        base = 0 if r['cp_flag'] == 'C' else 3
        oi = fnum(r['open_interest']) or 0.0
        if leg[base + 1] is not None and oi < leg[base + 2]:
            continue  # duplicate contract: keep the one with more open interest
        leg[base:base + 3] = [fnum(r['best_bid']), fnum(r['best_offer']), oi]
    return os.path.basename(path), n, snaps


def release_timing(anndate, anntims, sessions, index):
    """(P index, Q index, class) or (None, None, reason)."""
    i = index.get(anndate)
    if i is None:
        j = bisect.bisect_left(sessions, anndate)
        if j == 0 or j >= len(sessions):
            return None, None, 'outside_calendar'
        return j - 1, j, 'non_session_date'
    if not anntims:
        return None, None, 'missing_time'
    h, m = int(anntims[:2]), int(anntims[3:5])
    minutes = h * 60 + m
    if minutes < 9 * 60 + 30:
        return i - 1, i, 'before_open'
    if minutes >= 16 * 60:
        if i + 1 >= len(sessions):
            return None, None, 'outside_calendar'
        return i, i + 1, 'after_close'
    return None, None, 'during_session'


def build(source, output):
    os.makedirs(output, exist_ok=True)
    audit = {}
    sessions = sorted(day(r['date']) for r in rows(os.path.join(source, 'sessions.csv')))
    index = {d: i for i, d in enumerate(sessions)}
    stocks = defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(source, 'stocks', 'stocks_original_*.csv.gz'))):
        for r in rows(path):
            ret = fnum(r['return'])
            stocks[int(float(r['secid']))][day(r['date'])] = (fnum(r['close']), ret, fnum(r['cfadj']), fnum(r['volume']))
    audit['sessions'] = [str(sessions[0]), str(sessions[-1]), len(sessions)]

    universe = {int(float(r['secid'])): r for r in rows(os.path.join(source, 'universe.csv')) if r['group'] == 'original'}
    consensus = defaultdict(list)
    for r in rows(os.path.join(source, 'ibes_consensus_original.csv.gz')):
        if fnum(r['meanest']) is None:
            continue
        consensus[(r['ticker'], r['fpedats'][:10])].append((day(r['statpers']), fnum(r['meanest']), fnum(r['stdev']), fnum(r['numest'])))
    for v in consensus.values():
        v.sort()

    events, skipped = [], Counter()
    seen = set()
    for r in rows(os.path.join(source, 'events_original.csv.gz')):
        sid = int(float(r['secid']))
        if sid not in universe:
            skipped['not_original_universe'] += 1
            continue
        ann = day(r['anndats'])
        p, q, cls = release_timing(ann, r['anntims'], sessions, index)
        if p is None:
            skipped[cls] += 1
            continue
        if (sid, q) in seen:
            skipped['duplicate_release_session'] += 1
            continue
        seen.add((sid, q))
        p_day = sessions[p]
        cons = None
        for statpers, mean, sd, n in reversed(consensus.get((r['ticker'], r['pends'][:10]), [])):
            if statpers <= p_day:
                cons = {'statpers': statpers, 'mean': mean, 'stdev': sd, 'numest': n}
                break
        events.append({'secid': sid, 'ticker': universe[sid]['ticker'], 'issuer': universe[sid]['issuer'],
                       'ibes_ticker': r['ticker'], 'announce': ann, 'anntims': r['anntims'], 'timing': cls,
                       'E': sessions[bisect.bisect_left(sessions, ann)] if bisect.bisect_left(sessions, ann) < len(sessions) else None,
                       'P_index': p, 'Q_index': q, 'P': p_day, 'Q': sessions[q], 'eps': fnum(r['value']), 'consensus': cons})
    events.sort(key=lambda x: (x['Q'], x['secid']))
    audit['events'] = {'kept': len(events), 'skipped': dict(skipped), 'timing': dict(Counter(e['timing'] for e in events)),
                       'with_consensus': sum(e['consensus'] is not None for e in events)}

    dividends = defaultdict(list)
    for r in rows(os.path.join(source, 'distributions_original.csv.gz')):
        if r.get('cancel_flag') == '1' or not r['ex_date']:
            continue
        dividends[int(float(r['secid']))].append(day(r['ex_date']))
    for v in dividends.values():
        v.sort()

    files = sorted(glob.glob(os.path.join(source, 'options', 'quotes_original_*.csv.gz')))
    by_year = defaultdict(list)
    for f in files:
        by_year[os.path.basename(f).split('_')[2]].append(f)
    total = 0
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        for year in sorted(by_year):
            snaps = {}
            for name, n, part in pool.imap_unordered(parse_quotes, by_year[year]):
                total += n
                for key, chain in part.items():
                    if key in snaps:
                        for ex, strikes in chain.items():
                            snaps[key].setdefault(ex, {}).update(strikes)
                    else:
                        snaps[key] = chain
            with open(os.path.join(output, f'quotes_{year}.pkl'), 'xb') as stream:
                pickle.dump(snaps, stream, protocol=pickle.HIGHEST_PROTOCOL)
            audit[f'quote_snapshots_{year}'] = len(snaps)
            del snaps
    audit['quote_rows'] = total

    base = {'sessions': sessions, 'stocks': dict(stocks), 'events': events, 'dividends': dict(dividends),
            'issuer_of': {s: u['issuer'] for s, u in universe.items()}}
    with open(os.path.join(output, 'base.pkl'), 'xb') as stream:
        pickle.dump(base, stream, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(output, 'data_audit.json'), 'x') as stream:
        json.dump(audit, stream, indent=2, default=str)
    return audit


def load_base(cache):
    with open(os.path.join(cache, 'base.pkl'), 'rb') as stream:
        return pickle.load(stream)


def load_quotes(cache, year, first=None, last=None):
    """One year's snapshots, optionally restricted to dates in [first, last]."""
    path = os.path.join(cache, f'quotes_{year}.pkl')
    if not os.path.exists(path):
        return {}
    with open(path, 'rb') as stream:
        snaps = pickle.load(stream)
    if first or last:
        lo, hi = (first or dt.date.min).isoformat(), (last or dt.date.max).isoformat()
        snaps = {k: v for k, v in snaps.items() if lo <= k[1] <= hi}
    return snaps


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='../wrds_studies/research7_data')
    parser.add_argument('--output', default='../wrds_studies/research7_cache')
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output), indent=2, default=str))
