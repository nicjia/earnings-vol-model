"""Record, before sample E exists, every rule that sample E will test (written once, never overwritten).

E tests: the frozen policies, the pre-registered replications, and the post-hoc candidates that were
positive at 25% half-spread cost and excluding their best 5 events in all of A-D (>= 50 events each),
using the same criterion as the report. The post-hoc list was found after seeing B-D, which is why it
is fixed here before any expanded-universe data is downloaded.
"""
import argparse
import csv
import datetime as dt
import json
import os

from research5.run import sha256_file


def num(row, key):
    v = row.get(key)
    return float(v) if v not in (None, '', 'None') else None


def consistent(results):
    tables = {'A': os.path.join(results, 'candidates_A.csv')}
    tables.update({s: os.path.join(results, f'diagnostic_candidates_{s}.csv') for s in 'BCD'})
    keyed = {s: {r['id']: r for r in csv.DictReader(open(p, newline=''))} for s, p in tables.items()}
    out = []
    for cid in keyed['A']:
        rows = [keyed[s].get(cid) for s in 'ABCD']
        if all(r and (num(r, 'events') or 0) >= 50 and (num(r, 'mean_c25') or -1) > 0 and (num(r, 'without_best5') or -1) > 0
               for r in rows):
            out.append(cid)
    return sorted(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='../wrds_studies/research7_results')
    parser.add_argument('--output', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'e_hypotheses.json'))
    args = parser.parse_args()
    frozen = json.load(open(os.path.join(args.results, 'frozen_policies.json')))
    doc = {
        'written_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'expanded_universe_downloaded': False,
        'frozen_policies': [p['id'] for p in frozen['policies']],
        'replications': frozen['replications'],
        'post_hoc_candidates': consistent(args.results),
        'walk_forward': 'The research5 walk-forward selector, run on the expanded universe with selection on years before Y',
        'evaluation_sha256': sha256_file(os.path.join(args.results, 'evaluation.json')),
        'gates': 'Per rule in E: weekly-bootstrap lower 95% bound > 0 at midpoint, mean > 0 at 25% half-spread cost, '
                 'mean > 0 excluding best 5, >= 100 events and >= 40 issuers. Report all rules; the post-hoc list is '
                 'adjusted by Holm over its own size.',
    }
    with open(args.output, 'x') as stream:
        json.dump(doc, stream, indent=2)
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in doc.items()}, indent=1))


if __name__ == '__main__':
    main()
