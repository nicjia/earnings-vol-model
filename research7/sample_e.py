"""Evaluate sample E (the untouched expanded universe) for the rules fixed in e_hypotheses.json.

python -m research7.sample_e build    --source ../wrds_studies/research7_expanded --cache ../wrds_studies/research7_cache_e
python -m research7.sample_e evaluate --cache ../wrds_studies/research7_cache_e --results ../wrds_studies/research7_results

Refuses to run if the research7 frozen sources, grid or selection records changed, or if e_hypotheses.json
differs from the version committed before the expanded data existed. Uses the research7 engine unchanged.
"""
import argparse
import bisect
import datetime as dt
import glob
import json
import os
import pickle
import subprocess
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from statistics import NormalDist

from research5 import candidates as c5
from research5 import run as r5
from research5 import stats

from . import candidates as cand
from . import data, engine
from . import run as r7

HERE = os.path.dirname(os.path.abspath(__file__))
HYPOTHESES_COMMIT = 'ec109b9'
GROUP_START = {'expanded_2017': dt.date(2018, 1, 1), 'added_2020': dt.date(2021, 1, 1)}


def build(source, output):
    """Same parsing and release-timing rules as research7.data, for the expanded files."""
    os.makedirs(output, exist_ok=True)
    rows = data.rows
    sessions = sorted(data.day(r['date']) for r in rows(os.path.join(source, 'sessions.csv')))
    index = {d: i for i, d in enumerate(sessions)}
    stocks = defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(source, 'stocks', 'stocks_expanded_*.csv.gz'))):
        for r in rows(path):
            stocks[int(float(r['secid']))][data.day(r['date'])] = (data.fnum(r['close']), data.fnum(r['return']),
                                                                   data.fnum(r['cfadj']), data.fnum(r['volume']))
    universe = {int(float(r['secid'])): r for r in rows(os.path.join(source, 'universe.csv')) if r['group'] in GROUP_START}
    consensus = defaultdict(list)
    for r in rows(os.path.join(source, 'ibes_consensus_expanded.csv.gz')):
        if data.fnum(r['meanest']) is not None:
            consensus[(r['ticker'], r['pends'] if 'pends' in r else r['fpedats'][:10])].append(
                (data.day(r['statpers']), data.fnum(r['meanest']), data.fnum(r['stdev']), data.fnum(r['numest'])))
    for v in consensus.values():
        v.sort()
    events, skipped, seen = [], Counter(), set()
    for r in rows(os.path.join(source, 'events_expanded.csv.gz')):
        sid = int(float(r['secid']))
        if sid not in universe:
            skipped['not_expanded_universe'] += 1
            continue
        ann = data.day(r['anndats'])
        p, q, cls = data.release_timing(ann, r['anntims'], sessions, index)
        if p is None:
            skipped[cls] += 1
            continue
        if (sid, q) in seen:
            skipped['duplicate_release_session'] += 1
            continue
        seen.add((sid, q))
        cons = None
        for statpers, mean, sd, n in reversed(consensus.get((r['ticker'], r['pends'][:10]), [])):
            if statpers <= sessions[p]:
                cons = {'statpers': statpers, 'mean': mean, 'stdev': sd, 'numest': n}
                break
        e_i = bisect.bisect_left(sessions, ann)
        events.append({'secid': sid, 'ticker': universe[sid]['ticker'], 'issuer': universe[sid]['issuer'],
                       'group': universe[sid]['group'], 'ibes_ticker': r['ticker'], 'announce': ann,
                       'anntims': r['anntims'], 'timing': cls, 'E': sessions[e_i] if e_i < len(sessions) else None,
                       'P_index': p, 'Q_index': q, 'P': sessions[p], 'Q': sessions[q], 'eps': data.fnum(r['value']),
                       'consensus': cons})
    events.sort(key=lambda x: (x['Q'], x['secid']))
    dividends = defaultdict(list)
    for r in rows(os.path.join(source, 'distributions_expanded.csv.gz')):
        if r.get('cancel_flag') != '1' and r['ex_date']:
            dividends[int(float(r['secid']))].append(data.day(r['ex_date']))
    for v in dividends.values():
        v.sort()
    files = sorted(glob.glob(os.path.join(source, 'options', 'quotes_expanded_*.csv.gz')))
    by_year = defaultdict(list)
    for f in files:
        by_year[os.path.basename(f).split('_')[2]].append(f)
    audit = {'events': len(events), 'skipped': dict(skipped), 'timing': dict(Counter(e['timing'] for e in events)),
             'groups': dict(Counter(e['group'] for e in events))}
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        for year in sorted(by_year):
            snaps = {}
            for _, n, part in pool.imap_unordered(data.parse_quotes, by_year[year]):
                for key, chain in part.items():
                    if key in snaps:
                        for ex, strikes in chain.items():
                            snaps[key].setdefault(ex, {}).update(strikes)
                    else:
                        snaps[key] = chain
            with open(os.path.join(output, f'quotes_{year}.pkl'), 'xb') as stream:
                pickle.dump(snaps, stream, protocol=pickle.HIGHEST_PROTOCOL)
            audit[f'quote_snapshots_{year}'] = len(snaps)
    base = {'sessions': sessions, 'stocks': dict(stocks), 'events': events, 'dividends': dict(dividends),
            'issuer_of': {s: u['issuer'] for s, u in universe.items()}}
    with open(os.path.join(output, 'base.pkl'), 'xb') as stream:
        pickle.dump(base, stream, protocol=pickle.HIGHEST_PROTOCOL)
    with open(os.path.join(output, 'data_audit.json'), 'x') as stream:
        json.dump(audit, stream, indent=2, default=str)
    print(json.dumps(audit, indent=1, default=str))


def check_preconditions(results):
    frozen = r7.verify_frozen(results)
    committed = subprocess.run(['git', 'show', f'{HYPOTHESES_COMMIT}:research7/e_hypotheses.json'], cwd=os.path.dirname(HERE),
                               capture_output=True, text=True, check=True).stdout
    current = open(os.path.join(HERE, 'e_hypotheses.json')).read()
    if json.loads(committed) != json.loads(current):
        sys.exit('e_hypotheses.json differs from the version committed before the expanded data existed.')
    hyp = json.loads(current)
    if hyp['evaluation_sha256'] != r5.sha256_file(os.path.join(results, 'evaluation.json')):
        sys.exit('research7 evaluation.json changed since the hypothesis list was written.')
    return frozen, hyp


def simulate_e(cache, out_dir, lag=0):
    path = os.path.join(out_dir, f'records_E{"_lag" if lag else ""}.pkl')
    if os.path.exists(path):
        with open(path, 'rb') as stream:
            return pickle.load(stream)['records']
    base = data.load_base(cache)
    implied = r7.implied_table(cache, out_dir, base)
    events = [ev for ev in base['events'] if ev['E'] and ev['E'] >= GROUP_START[ev['group']] and ev['E'].year <= 2025]
    records = []
    for year in sorted({ev['E'].year for ev in events}):
        m = engine.Market(base, r7.quotes_for_year(cache, year), implied)
        for ev in events:
            if ev['E'].year == year:
                for rec in engine.simulate_event(m, ev, lag):
                    rec['group'] = ev['group']
                    records.append(rec)
        del m
    with open(path, 'xb') as stream:
        pickle.dump({'records': records, 'events': len(events), 'source_hashes': r7.source_hashes()}, stream,
                    protocol=pickle.HIGHEST_PROTOCOL)
    r5.write_new(path.replace('.pkl', '_coverage.json'), json.dumps(
        {'events': len(events), 'status': dict(sorted(Counter(f"{r['family']}|{r['status']}" for r in records).items()))}, indent=1))
    r5.export_trades(records, path.replace('.pkl', '_trades.csv.gz'))
    return records


def gates(s):
    failed = []
    if not (s.get('ci_low_boot') is not None and s['ci_low_boot'] > 0):
        failed.append('bootstrap lower bound not > 0')
    if not ((s.get('mean_c25') or -1) > 0):
        failed.append('mean at 25% half-spread not > 0')
    if not ((s.get('without_best5') or -1) > 0):
        failed.append('mean excluding best 5 not > 0')
    if s.get('events', 0) < 100 or s.get('issuers', 0) < 40:
        failed.append('fewer than 100 events or 40 issuers')
    return failed


def evaluate(cache, results):
    frozen, hyp = check_preconditions(results)
    out_dir = os.path.join(results, 'E')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'evaluation_E.json')
    if os.path.exists(out_path):
        sys.exit('Sample E evaluation already written.')
    records = simulate_e(cache, out_dir)
    lag = simulate_e(cache, out_dir, lag=1)
    ids = cand.by_id()
    rules = ([('frozen', p) for p in hyp['frozen_policies']] + [('replication', v) for v in hyp['replications'].values()]
             + [('post-hoc', p) for p in hyp['post_hoc_candidates']])
    out = {'evaluated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'rules': []}
    for kind, cid in rules:
        closed, unresolved = c5.members(ids[cid], records)
        s = stats.summarize(closed, unresolved, bootstrap=True)
        row = {'kind': kind, 'id': cid, 'E': s, 'failed_gates': gates(s)}
        if s.get('se'):
            row['t_cluster'] = s['mean'] / s['se']
            row['p_one_sided'] = 1 - NormalDist().cdf(row['t_cluster'])
        row['by_group'] = {g: stats.summarize([t for t in closed if t['group'] == g], bootstrap=True) for g in GROUP_START}
        row['by_timing'] = {t: stats.summarize([x for x in closed if x['timing'] == t], bootstrap=True)
                            for t in ('before_open', 'after_close')}
        lc, lu = c5.members(ids[cid], lag)
        row['lag_check'] = stats.summarize(lc, lu, bootstrap=True)
        out['rules'].append(row)
    post = sorted((r for r in out['rules'] if r['kind'] == 'post-hoc' and 'p_one_sided' in r), key=lambda r: r['p_one_sided'])
    m = len(hyp['post_hoc_candidates'])
    running = 0.0
    for i, r in enumerate(post):
        running = max(running, min(1.0, (m - i) * r['p_one_sided']))
        r['holm_p'] = running
    for r in out['rules']:
        r['passed'] = not r['failed_gates'] and (r['kind'] != 'post-hoc' or r.get('holm_p', 1) < 0.05)
    by_year = defaultdict(list)
    for r in records:
        by_year[r['E'].year].append(r)
    choices, oos = r5.walk_forward(by_year, cand.grid())
    out['walk_forward'] = {'years': choices, 'oos': stats.summarize(oos, 0, bootstrap=True),
                           'portfolio_mid': r5.portfolio(oos, 'pnl_mid'), 'portfolio_c25': r5.portfolio(oos, 'pnl_c25')}
    r5.write_new(out_path, json.dumps(out, indent=2, default=str))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'evaluate'))
    parser.add_argument('--source', default='../wrds_studies/research7_expanded')
    parser.add_argument('--cache', default='../wrds_studies/research7_cache_e')
    parser.add_argument('--results', default='../wrds_studies/research7_results')
    args = parser.parse_args()
    if args.command == 'build':
        build(args.source, args.cache)
    else:
        out = evaluate(args.cache, args.results)
        print(json.dumps([(r['kind'], r['id'], r['passed']) for r in out['rules']], indent=1))


if __name__ == '__main__':
    main()
