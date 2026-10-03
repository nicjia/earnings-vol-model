"""Trial registry for reusing the same data honestly.

Every variant ever evaluated on a dataset is appended to research8/trials.jsonl (name, family, n, mean, t, Sharpe,
source). Significance is then judged against the whole family that touched the data, not the single best result:
Holm-adjusted p-values (normal approximation to the weekly-clustered t) and a Bonferroni t threshold.

python -m research8.registry add-explore5      # log every explore5 variant
python -m research8.registry report [--family explore5]
"""
import argparse
import json
import math
import os

from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, 'trials.jsonl')
ND = NormalDist()


def add(rows):
    seen = set()
    if os.path.exists(PATH):
        seen = {json.loads(l)['name'] for l in open(PATH)}
    with open(PATH, 'a') as s:
        for r in rows:
            if r['name'] not in seen:
                s.write(json.dumps(r) + '\n')


def load(family=None):
    if not os.path.exists(PATH):
        return []
    rows = [json.loads(l) for l in open(PATH)]
    return [r for r in rows if family is None or r['family'] == family]


def holm(rows):
    """Two-sided p from t, Holm step-down adjusted within the given rows (positive and negative results alike)."""
    ps = sorted((2 * (1 - ND.cdf(abs(r['t']))), i) for i, r in enumerate(rows))
    m = len(ps)
    adj = [0.0] * m
    run = 0.0
    for k, (p, i) in enumerate(ps):
        run = max(run, min(1.0, (m - k) * p))
        adj[i] = run
    return adj


def report(family=None):
    rows = [r for r in load(family) if r.get('t') is not None]
    if not rows:
        print('no trials')
        return
    adj = holm(rows)
    m = len(rows)
    tcrit = ND.inv_cdf(1 - 0.025 / m)
    print(f'family={family or "all"}: {m} trials; Bonferroni |t| needed for 5%: {tcrit:.2f}')
    for r, a in sorted(zip(rows, adj), key=lambda z: z[1])[:15]:
        print(f"  Holm p {a:.3f}  t {r['t']:+.2f}  SR {r.get('sharpe', 0):+.2f}  n {r['n']}  {r['name']}")


def from_explore5():
    d = json.load(open(os.path.join(os.path.dirname(HERE), 'docs', 'research8', 'explore5', 'results.json')))
    out = []
    for k, v in d.items():
        if not isinstance(v, dict) or 'all' not in v or 'mean' not in v['all']:
            continue
        a = v['all']
        out.append({'name': 'explore5|' + k, 'family': 'explore5', 'n': a['n'], 'mean': a['mean'], 't': a['t'],
                    'sharpe': a['sharpe'], 'source': 'docs/research8/explore5/results.json', 'basis': 'gross midpoint'})
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cmd', choices=['add-explore5', 'report'])
    ap.add_argument('--family', default=None)
    a = ap.parse_args()
    if a.cmd == 'add-explore5':
        add(from_explore5())
        print('logged', len(load('explore5')), 'explore5 trials')
    else:
        report(a.family)
