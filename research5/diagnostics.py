"""Post-freeze diagnostics of the frozen policies (labelled exploratory; not gates).

Pools the out-of-selection samples B+C+D, breaks results down by year, and
decomposes outcomes by the realized stock move relative to the implied move
and by losses beyond the package's theoretical maximum loss.
"""
import argparse
import json
import os
import pickle
from collections import defaultdict

from . import candidates as cand
from . import stats
from .report import fmt


def load(results, sample):
    with open(os.path.join(results, f'records_{sample}.pkl'), 'rb') as stream:
        return pickle.load(stream)['records']


def line(name, s):
    if not s.get('events'):
        return f'| {name} | 0 | | | | | |'
    return (f"| {name} | {s['events']} | {fmt(s['mean'])} | [{fmt(s.get('ci_low_boot'))}, {fmt(s.get('ci_high_boot'))}] | "
            f"{fmt(s['mean_c25'])} | {fmt(s.get('without_best5'))} | {s['win_rate'] * 100:.0f}% |")


HEAD = '| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |\n|---|---|---|---|---|---|---|'


def build(results, title='Research5 post-freeze diagnostics'):
    frozen = json.load(open(os.path.join(results, 'frozen_policies.json')))
    records = {s: load(results, s) for s in ('A', 'B', 'C', 'D')}
    lines = ['# ' + title, '',
             'Exploratory breakdowns of the five frozen policies after all stages were evaluated. None of these '
             'groupings was pre-registered as a gate, and none can change the frozen set or the verdict.', '']
    for policy in frozen['policies']:
        trades = {s: cand.members(policy, records[s])[0] for s in records}
        oos = trades['B'] + trades['C'] + trades['D']
        lines += [f"## `{policy['id']}`", '', HEAD,
                  line('B+C+D pooled (out of selection)', stats.summarize(oos, bootstrap=True))]
        by_year = defaultdict(list)
        for s in ('A', 'B', 'C', 'D'):
            for t in trades[s]:
                by_year[(t['E'].year, 'A' if s == 'A' else 'out')].append(t)
        for (year, kind), group in sorted(by_year.items()):
            lines.append(line(f'{year} {"selection" if kind == "A" else "out-of-selection"}', stats.summarize(group, bootstrap=True)))
        ratio = defaultdict(list)
        for t in oos:
            move, implied = t.get('exit_stock_move'), t.get('f_M')
            if move is None or not implied:
                continue
            r = abs(move) / implied
            ratio['|move| < 0.5 x implied' if r < 0.5 else '0.5-1 x implied' if r < 1 else '|move| >= 1 x implied'].append(t)
        lines += ['', 'Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:', '', HEAD]
        for name in ('|move| < 0.5 x implied', '0.5-1 x implied', '|move| >= 1 x implied'):
            lines.append(line(name, stats.summarize(ratio[name], bootstrap=True)))
        beyond = [t for t in oos if t['ret_mid'] < -1.0]
        capped = []
        for t in oos:
            u = dict(t)
            floor = -(1.0 + t['fees'] / t['risk'])
            for c in ('mid', 'c25', 'c50'):
                u['ret_' + c] = max(t['ret_' + c], floor)
            capped.append(u)
        lines += ['', f'Trades losing more than 100% of risk at exit midpoints: {len(beyond)} of {len(oos)} '
                  '(exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical '
                  'maximum loss plus fees, as holding to expiry would allow:', '', HEAD,
                  line('B+C+D capped', stats.summarize(capped, bootstrap=True)), '']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='../wrds_studies/research5_results')
    parser.add_argument('--title', default='Research5 post-freeze diagnostics')
    args = parser.parse_args()
    out = os.path.join(args.results, 'DIAGNOSTICS.md')
    text = build(args.results, args.title)
    with open(out, 'x') as stream:
        stream.write(text)
    print(text)
