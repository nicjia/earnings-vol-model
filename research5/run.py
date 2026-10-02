"""Research pipeline: simulate samples, select and freeze on A, evaluate B/C/D.

python -m research5.run simulate --sample A
python -m research5.run select
python -m research5.run evaluate
All outputs are created exclusively under --results; nothing is overwritten.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import pickle
import sys
from collections import Counter

from . import candidates as cand
from . import data, engine, stats

HERE = os.path.dirname(os.path.abspath(__file__))
HASHED = ('protocol.json', 'pickle_compat.py', 'data.py', 'engine.py', 'stats.py', 'candidates.py', 'run.py')
SAMPLES = {
    'A': ((2018, 2019, 2020, 2021), 'A'),
    'B': ((2018, 2019, 2020, 2021), 'B'),
    'C': ((2022, 2023), None),
    'D': ((2024, 2025), None),
}
MIN_EVENTS, MIN_ISSUERS, MAX_UNRESOLVED = 150, 40, 0.01
WF_MIN_EVENTS = 100


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def source_hashes():
    return {name: sha256_file(os.path.join(HERE, name)) for name in HASHED}


def name_half(secid):
    return 'A' if int(hashlib.sha256(str(secid).encode()).hexdigest(), 16) % 2 == 0 else 'B'


def in_sample(ev, sample):
    years, half = SAMPLES[sample]
    return ev['E'].year in years and (half is None or name_half(ev['secid']) == half)


def write_new(path, text):
    with open(path, 'x') as stream:
        stream.write(text)


def records_path(results, sample, shift=0):
    return os.path.join(results, f'records_{sample}{"_lag" if shift else ""}.pkl')


def simulate(cache, results, sample, shift=0):
    path = records_path(results, sample, shift)
    if os.path.exists(path):
        return load_records(results, sample, shift)
    years = SAMPLES[sample][0]
    base = data.load_base(cache)
    # Quotes from later years are never loaded; earlier years feed historical implied moves.
    quote_years = [str(y) for y in range(2018, max(years) + 1)]
    market = engine.Market(base, data.load_quotes(cache, quote_years))
    events = [ev for ev in base['events'] if in_sample(ev, sample)]
    records = []
    for ev in events:
        records.extend(engine.simulate_event(market, ev, decision_shift=shift))
    coverage = Counter(r['status'] for r in records)
    with open(path, 'xb') as stream:
        pickle.dump({'sample': sample, 'shift': shift, 'events': len(events), 'records': records,
                     'source_hashes': source_hashes()}, stream, protocol=pickle.HIGHEST_PROTOCOL)
    write_new(path.replace('.pkl', '_coverage.json'), json.dumps(
        {'events': len(events), 'status': dict(coverage.most_common())}, indent=2))
    export_trades(records, path.replace('.pkl', '_trades.csv.gz'))
    return records


def export_trades(records, path):
    import gzip
    fields = ['secid', 'ticker', 'issuer', 'E', 'family', 'entry', 'exit', 'exit_rule', 'status', 'tiers',
              'entry_day', 'exit_day', 'front', 'spot', 'risk', 'legs', 'fees', 'half_spreads', 'pnl_mid',
              'pnl_c25', 'pnl_c50', 'ret_mid', 'ret_c25', 'ret_c50', 'exit_stock_move',
              'f_M', 'f_H', 'f_R', 'f_TS', 'f_HR']
    with gzip.open(path, 'xt', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in records:
            row = dict(r)
            if 'tiers' in row:
                row['tiers'] = '+'.join(row['tiers'])
            w.writerow(row)


def load_records(results, sample, shift=0):
    with open(records_path(results, sample, shift), 'rb') as stream:
        blob = pickle.load(stream)
    if blob['source_hashes'] != source_hashes():
        sys.exit(f'records_{sample} were produced by different sources; use a new results directory')
    return blob['records']


def candidate_table(records, cands, bootstrap=False):
    by_base = cand.index_records(records)
    rows, points = [], {}
    for c in cands:
        closed, unresolved = cand.members_indexed(c, by_base)
        s = stats.summarize(closed, unresolved, bootstrap=bootstrap)
        s.update({k: c[k] for k in ('id', 'family', 'entry', 'exit', 'filter', 'liquidity')})
        s['eligible'] = eligible(s)
        rows.append(s)
        if closed:
            points[c['id']] = stats.issuer_events(closed, 'ret_mid')
    return rows, points


def eligible(s, min_events=MIN_EVENTS):
    return bool(s.get('events', 0) >= min_events and s.get('issuers', 0) >= MIN_ISSUERS
                and s.get('unresolved_share', 1) <= MAX_UNRESOLVED and (s.get('mean_c25') or 0) > 0
                and (s.get('without_best5') or 0) > 0 and s.get('ci_low_normal') is not None)


def write_table(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, 'x', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def choose(rows, limit=5):
    ranked = sorted((r for r in rows if r['eligible']), key=lambda r: r['ci_low_normal'], reverse=True)
    chosen, families = [], set()
    for r in ranked:
        if r['family'] in families:
            continue
        chosen.append(r)
        families.add(r['family'])
        if len(chosen) == limit:
            break
    return ranked, chosen


def cmd_select(args):
    frozen_path = os.path.join(args.results, 'frozen_policies.json')
    if os.path.exists(frozen_path):
        sys.exit('A frozen policy file already exists; selection is not repeatable in place.')
    records = simulate(args.cache, args.results, 'A')
    cands = cand.grid()
    rows, points = candidate_table(records, cands)
    ranked, chosen = choose(rows)
    pvals = stats.max_t_pvalues({r['id']: points[r['id']] for r in ranked}) if ranked else {}
    for r in rows:
        r['max_t_p'] = pvals.get(r['id'])
    write_table(os.path.join(args.results, 'candidates_A.csv'), rows)
    frozen = {
        'frozen_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'protocol_sha256': sha256_file(os.path.join(HERE, 'protocol.json')),
        'grid_sha256': cand.grid_hash(),
        'candidates': len(cands),
        'eligible': len(ranked),
        'policies': [{k: r[k] for k in ('id', 'family', 'entry', 'exit', 'filter', 'liquidity')}
                     | {'selection': {k: r.get(k) for k in ('events', 'issuers', 'weeks', 'mean', 'ci_low_normal',
                                                             'mean_c25', 'mean_c50', 'without_best5', 'win_rate',
                                                             'unresolved_share')},
                        'max_t_p': pvals.get(r['id'])} for r in chosen],
        'records_A_sha256': sha256_file(records_path(args.results, 'A')),
        'source_hashes': source_hashes(),
    }
    write_new(frozen_path, json.dumps(frozen, indent=2, default=str))
    print(json.dumps({'candidates': len(cands), 'eligible': len(ranked), 'frozen': [p['id'] for p in frozen['policies']]},
                     indent=2))


def verify_frozen(results):
    path = os.path.join(results, 'frozen_policies.json')
    if not os.path.exists(path):
        sys.exit('Run selection first: no frozen policy file.')
    with open(path) as stream:
        frozen = json.load(stream)
    if frozen['source_hashes'] != source_hashes():
        sys.exit('Sources changed after freezing; evaluation refused. Start a new results directory and protocol version.')
    if frozen['grid_sha256'] != cand.grid_hash():
        sys.exit('Candidate grid changed after freezing.')
    if sha256_file(records_path(results, 'A')) != frozen['records_A_sha256']:
        sys.exit('Selection records changed after freezing.')
    return frozen


def portfolio(trades, key='pnl_mid', start=100000.0, risk_fraction=0.02):
    """Illustrative account path: 2% of realized equity at max-loss risk per trade."""
    if not trades:
        return {'trades': 0}
    events = []
    for t in trades:
        events.append((t['entry_day'], 1, t))
        events.append((t['exit_day'], 0, t))
    events.sort(key=lambda x: (x[0], x[1]))  # exits before entries on the same day
    equity, peak, max_dd = start, start, 0.0
    units, curve = {}, []
    for day, kind, t in events:
        tid = id(t)
        if kind == 1:
            units[tid] = equity * risk_fraction / t['risk']
        else:
            equity += units.pop(tid) * t[key]
            peak = max(peak, equity)
            max_dd = max(max_dd, 1 - equity / peak)
            curve.append((day, equity))
    first = min(t['entry_day'] for t in trades)
    last = max(t['exit_day'] for t in trades)
    years = max((last - first).days / 365.25, 1 / 365.25)
    growth = equity / start
    return {'trades': len(trades), 'start': start, 'end': equity, 'total_return': growth - 1,
            'cagr': growth ** (1 / years) - 1 if growth > 0 else -1.0, 'max_drawdown': max_dd,
            'first_entry': str(first), 'last_exit': str(last)}


def policy_trades(policy, records):
    c = dict(policy)
    closed, unresolved = cand.members_indexed(c, cand.index_records(records))
    return closed, unresolved


def qualifies(stage_stats, max_t_p):
    reasons = []
    for st in ('B', 'C', 'D'):
        s = stage_stats.get(st, {})
        if not (s.get('ci_low_boot') is not None and s['ci_low_boot'] > 0):
            reasons.append(f'{st}: bootstrap lower bound not > 0')
        if not ((s.get('mean_c25') or -1) > 0):
            reasons.append(f'{st}: mean at 25% half-spread not > 0')
    d = stage_stats.get('D', {})
    if not ((d.get('without_best5') or -1) > 0):
        reasons.append('D: mean excluding best 5 not > 0')
    if d.get('events', 0) < 100 or d.get('issuers', 0) < 40:
        reasons.append('D: fewer than 100 events or 40 issuers')
    if max_t_p is None or max_t_p >= 0.05:
        reasons.append('A: max-t adjusted p not < 0.05')
    return not reasons, reasons


def walk_forward(records_by_year, cands):
    """Select on all earlier years, trade the following year; returns per-year choices and trades."""
    out, oos = [], []
    for year in range(2020, 2026):
        train = [r for y, recs in records_by_year.items() if y < year for r in recs]
        rows, _ = candidate_table(train, cands)
        for r in rows:
            r['eligible'] = eligible(r, WF_MIN_EVENTS)
        ranked = sorted((r for r in rows if r['eligible']), key=lambda r: r['ci_low_normal'], reverse=True)
        if not ranked:
            out.append({'year': year, 'policy': None, 'trades': 0})
            continue
        best = ranked[0]
        policy = {k: best[k] for k in ('family', 'entry', 'exit', 'filter', 'liquidity')}
        closed, unresolved = policy_trades(policy, records_by_year.get(year, []))
        s = stats.summarize(closed, unresolved)
        out.append({'year': year, 'policy': best['id'], 'train_ci_low_normal': best['ci_low_normal'],
                    'train_mean': best['mean'], 'eligible_in_training': len(ranked), **{('oos_' + k): v for k, v in s.items()}})
        oos.extend(closed)
    return out, oos


def cmd_evaluate(args):
    frozen = verify_frozen(args.results)
    out_path = os.path.join(args.results, 'evaluation.json')
    if os.path.exists(out_path):
        sys.exit('Evaluation already written; outputs are never overwritten.')
    records = {s: simulate(args.cache, args.results, s) for s in ('A', 'B', 'C', 'D')}
    lag = {s: simulate(args.cache, args.results, s, shift=-1) for s in ('B', 'C', 'D')}
    result = {'frozen_at': frozen['frozen_at'], 'evaluated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'policies': []}
    for policy in frozen['policies']:
        entry = {'id': policy['id'], 'stages': {}, 'lag_check': {}, 'portfolio': {}}
        for s in ('A', 'B', 'C', 'D'):
            closed, unresolved = policy_trades(policy, records[s])
            entry['stages'][s] = stats.summarize(closed, unresolved, bootstrap=True)
            entry['portfolio'][s] = {'mid': portfolio(closed, 'pnl_mid'), 'c25': portfolio(closed, 'pnl_c25')}
        for s in ('B', 'C', 'D'):
            if policy['entry'] == 'E-2':
                entry['lag_check'][s] = {'note': 'not available: no option quotes at E-3'}
                continue
            closed, unresolved = policy_trades(policy, lag[s])
            entry['lag_check'][s] = stats.summarize(closed, unresolved, bootstrap=True)
        ok, reasons = qualifies(entry['stages'], policy.get('max_t_p'))
        entry['qualified'] = ok
        entry['failed_gates'] = reasons
        result['policies'].append(entry)

    # Autonomous walk-forward selector across all years.
    by_year = {}
    for s in ('A', 'B', 'C', 'D'):
        for r in records[s]:
            by_year.setdefault(r['E'].year, []).append(r)
    cands = cand.grid()
    choices, oos = walk_forward(by_year, cands)
    result['walk_forward'] = {'years': choices, 'oos': stats.summarize(oos, 0, bootstrap=True),
                              'oos_2022_2025': stats.summarize([t for t in oos if t['E'].year >= 2022], 0, bootstrap=True),
                              'portfolio_mid': portfolio(oos, 'pnl_mid'), 'portfolio_c25': portfolio(oos, 'pnl_c25')}
    write_new(out_path, json.dumps(result, indent=2, default=str))

    # Post-freeze diagnostics: every candidate in every later stage (cannot alter the frozen set).
    for s in ('B', 'C', 'D'):
        rows, _ = candidate_table(records[s], cands)
        write_table(os.path.join(args.results, f'diagnostic_candidates_{s}.csv'), rows)
    print(json.dumps({'policies': [(p['id'], p['qualified']) for p in result['policies']],
                      'walk_forward_policies': [c['policy'] for c in choices]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('simulate', 'select', 'evaluate'))
    parser.add_argument('--sample', choices=tuple(SAMPLES))
    parser.add_argument('--cache', default='../wrds_studies/research5_cache')
    parser.add_argument('--results', default='../wrds_studies/research5_results')
    args = parser.parse_args()
    os.makedirs(args.results, exist_ok=True)
    if args.command == 'simulate':
        if args.sample != 'A':
            verify_frozen(args.results)  # later samples are simulated only after freezing
        simulate(args.cache, args.results, args.sample)
    elif args.command == 'select':
        cmd_select(args)
    else:
        cmd_evaluate(args)


if __name__ == '__main__':
    main()
