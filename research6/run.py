"""research6 pipeline: simulate, select and freeze on A, evaluate B/C/D (outputs never overwritten).

python -m research6.run select   --cache ../wrds_studies/research5_cache --results ../wrds_studies/research6_results
python -m research6.run evaluate --cache ../wrds_studies/research5_cache --results ../wrds_studies/research6_results
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pickle
import sys
from collections import Counter

from research5 import data, stats
from research5 import run as r5
from research5.engine import Market

from . import candidates as cand
from . import engine

HERE = os.path.dirname(os.path.abspath(__file__))
R5 = os.path.join(os.path.dirname(HERE), 'research5')
HASHED = [os.path.join(HERE, n) for n in ('protocol.json', 'engine.py', 'candidates.py', 'run.py')] + \
         [os.path.join(R5, n) for n in r5.HASHED]


def source_hashes():
    return {os.path.relpath(p, os.path.dirname(HERE)): r5.sha256_file(p) for p in HASHED}


def records_path(results, sample):
    return os.path.join(results, f'records_{sample}.pkl')


def simulate(cache, results, sample):
    path = records_path(results, sample)
    if os.path.exists(path):
        with open(path, 'rb') as stream:
            blob = pickle.load(stream)
        if blob['source_hashes'] != source_hashes():
            sys.exit(f'records_{sample} were produced by different sources')
        return blob['records']
    years = r5.SAMPLES[sample][0]
    base = data.load_base(cache)
    market = Market(base, data.load_quotes(cache, [str(y) for y in range(2018, max(years) + 1)]))
    records = []
    for ev in base['events']:
        if r5.in_sample(ev, sample):
            records.extend(engine.simulate_event(market, ev))
    with open(path, 'xb') as stream:
        pickle.dump({'sample': sample, 'records': records, 'source_hashes': source_hashes()}, stream,
                    protocol=pickle.HIGHEST_PROTOCOL)
    coverage = Counter(f"{r['family']}|{r['status']}" for r in records)
    r5.write_new(path.replace('.pkl', '_coverage.json'), json.dumps(dict(sorted(coverage.items())), indent=1))
    r5.export_trades(records, path.replace('.pkl', '_trades.csv.gz'))
    return records


def cmd_select(args):
    frozen_path = os.path.join(args.results, 'frozen_policies.json')
    if os.path.exists(frozen_path):
        sys.exit('A frozen policy file already exists.')
    records = simulate(args.cache, args.results, 'A')
    cands = cand.grid()
    rows, points = r5.candidate_table(records, cands)
    ranked, chosen = r5.choose(rows)
    pvals = stats.max_t_pvalues({r['id']: points[r['id']] for r in ranked}) if ranked else {}
    for r in rows:
        r['max_t_p'] = pvals.get(r['id'])
    r5.write_table(os.path.join(args.results, 'candidates_A.csv'), rows)
    frozen = {
        'frozen_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'protocol_sha256': r5.sha256_file(os.path.join(HERE, 'protocol.json')),
        'grid_sha256': cand.grid_hash(), 'candidates': len(cands), 'eligible': len(ranked),
        'policies': [{k: r[k] for k in ('id', 'family', 'entry', 'exit', 'filter', 'liquidity')}
                     | {'selection': {k: r.get(k) for k in ('events', 'issuers', 'weeks', 'mean', 'ci_low_normal', 'mean_c25',
                                                             'mean_c50', 'without_best5', 'win_rate', 'unresolved_share')},
                        'max_t_p': pvals.get(r['id'])} for r in chosen],
        'records_A_sha256': r5.sha256_file(records_path(args.results, 'A')),
        'source_hashes': source_hashes(),
    }
    r5.write_new(frozen_path, json.dumps(frozen, indent=2, default=str))
    print(json.dumps({'candidates': len(cands), 'eligible': len(ranked), 'frozen': [p['id'] for p in frozen['policies']]}, indent=2))


def verify_frozen(results):
    path = os.path.join(results, 'frozen_policies.json')
    if not os.path.exists(path):
        sys.exit('Run selection first.')
    frozen = json.load(open(path))
    if frozen['source_hashes'] != source_hashes() or frozen['grid_sha256'] != cand.grid_hash():
        sys.exit('Sources or grid changed after freezing; evaluation refused.')
    if r5.sha256_file(records_path(results, 'A')) != frozen['records_A_sha256']:
        sys.exit('Selection records changed after freezing.')
    return frozen


def cmd_evaluate(args):
    frozen = verify_frozen(args.results)
    out_path = os.path.join(args.results, 'evaluation.json')
    if os.path.exists(out_path):
        sys.exit('Evaluation already written.')
    records = {s: simulate(args.cache, args.results, s) for s in ('A', 'B', 'C', 'D')}
    result = {'frozen_at': frozen['frozen_at'], 'evaluated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'policies': []}
    for policy in frozen['policies']:
        entry = {'id': policy['id'], 'stages': {}, 'lag_check': {s: {'note': 'not run in research6'} for s in 'BCD'},
                 'portfolio': {}}
        for s in ('A', 'B', 'C', 'D'):
            closed, unresolved = r5.policy_trades(policy, records[s])
            entry['stages'][s] = stats.summarize(closed, unresolved, bootstrap=True)
            entry['portfolio'][s] = {'mid': r5.portfolio(closed, 'pnl_mid'), 'c25': r5.portfolio(closed, 'pnl_c25')}
        entry['qualified'], entry['failed_gates'] = r5.qualifies(entry['stages'], policy.get('max_t_p'))
        result['policies'].append(entry)
    by_year = {}
    for s in ('A', 'B', 'C', 'D'):
        for r in records[s]:
            by_year.setdefault(r['E'].year, []).append(r)
    cands = cand.grid()
    choices, oos = r5.walk_forward(by_year, cands)
    result['walk_forward'] = {'years': choices, 'oos': stats.summarize(oos, 0, bootstrap=True),
                              'oos_2022_2025': stats.summarize([t for t in oos if t['E'].year >= 2022], 0, bootstrap=True),
                              'portfolio_mid': r5.portfolio(oos, 'pnl_mid'), 'portfolio_c25': r5.portfolio(oos, 'pnl_c25')}
    r5.write_new(out_path, json.dumps(result, indent=2, default=str))
    for s in ('B', 'C', 'D'):
        rows, _ = r5.candidate_table(records[s], cands)
        r5.write_table(os.path.join(args.results, f'diagnostic_candidates_{s}.csv'), rows)
    print(json.dumps({'policies': [(p['id'], p['qualified']) for p in result['policies']],
                      'walk_forward_policies': [c['policy'] for c in choices]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('select', 'evaluate'))
    parser.add_argument('--cache', default='../wrds_studies/research5_cache')
    parser.add_argument('--results', default='../wrds_studies/research6_results')
    args = parser.parse_args()
    os.makedirs(args.results, exist_ok=True)
    cmd_select(args) if args.command == 'select' else cmd_evaluate(args)


if __name__ == '__main__':
    main()
