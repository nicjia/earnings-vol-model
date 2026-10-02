"""Write the research5 report from saved outputs (aggregates only, no quote data)."""
import argparse
import csv
import json
import os
from collections import defaultdict


def fmt(x, pct=True, digits=1):
    if x is None or x == '':
        return 'n/a'
    x = float(x)
    return f'{x * 100:+.{digits}f}%' if pct else f'{x:.{digits}f}'


def read_csv(path):
    with open(path, newline='') as stream:
        return list(csv.DictReader(stream))


def num(row, key):
    v = row.get(key)
    return float(v) if v not in (None, '', 'None') else None


def stage_line(name, s):
    if not s or not s.get('events'):
        return f'| {name} | 0 | | | | | | | | |'
    return (f"| {name} | {s['events']} | {s['issuers']} | {fmt(s['mean'])} | "
            f"[{fmt(s.get('ci_low_boot'))}, {fmt(s.get('ci_high_boot'))}] | {fmt(s['mean_c25'])} | {fmt(s['mean_c50'])} | "
            f"{fmt(s.get('without_best5'))} | {s['win_rate'] * 100:.0f}% | {fmt(s['worst'])} |")


HEADER = ('| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | '
          'Excl. best 5 | Win rate | Worst |\n|---|---|---|---|---|---|---|---|---|---|')


def build(results, title='Research5: autonomous earnings-options strategy study'):
    frozen = json.load(open(os.path.join(results, 'frozen_policies.json')))
    ev = json.load(open(os.path.join(results, 'evaluation.json')))
    lines = ['# ' + title, '',
             f"Frozen {frozen['frozen_at']} on sample A; evaluated {ev['evaluated_at']}. "
             f"Protocol sha256 `{frozen['protocol_sha256'][:16]}`, grid sha256 `{frozen['grid_sha256'][:16]}`.", '',
             'Returns are equal-risk event returns on max-loss risk (debit for long premium and calendars), closing midpoint '
             'fills unless stated, $0.65/contract/side fees. Samples: A = 2018-2021 name half A (selection), '
             'B = 2018-2021 name half B, C = 2022-2023, D = 2024-2025 (quotes end 2025-08-26).', '']
    qualified = [p for p in ev['policies'] if p['qualified']]
    lines += ['## Verdict', '',
              f"{len(qualified)} of {len(ev['policies'])} frozen policies qualified under the pre-registered gates "
              f"({frozen['eligible']} of {frozen['candidates']} candidates were eligible on sample A).", '']

    lines += ['## Frozen policies', '']
    for p, fp in zip(ev['policies'], frozen['policies']):
        lines += [f"### `{p['id']}`", '', f"Stage-A max-t adjusted p = {fmt(fp.get('max_t_p'), pct=False, digits=3)}. "
                  f"Qualified: **{'yes' if p['qualified'] else 'no'}**.", '', HEADER]
        for s in ('A', 'B', 'C', 'D'):
            lines.append(stage_line(s + (' (selection)' if s == 'A' else ''), p['stages'][s]))
        lines += ['', 'Signal one session earlier (contracts fixed at decision, executed next close):', '', HEADER]
        for s in ('B', 'C', 'D'):
            lc = p['lag_check'][s]
            lines.append(stage_line(s, lc) if 'note' not in lc else f"| {s} | {lc['note']} | | | | | | | | |")
        lines += ['', 'Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):', '',
                  '| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |',
                  '|---|---|---|---|---|---|']
        for s in ('A', 'B', 'C', 'D'):
            pm, pc = p['portfolio'][s]['mid'], p['portfolio'][s]['c25']
            if pm.get('trades'):
                lines.append(f"| {s} | {pm['trades']} | {fmt(pm['total_return'])} | {fmt(pm['max_drawdown'])} | "
                             f"{fmt(pc['total_return'])} | {fmt(pc['max_drawdown'])} |")
        lines += ['', 'Failed gates: ' + ('; '.join(p['failed_gates']) or 'none'), '']

    wf = ev['walk_forward']
    lines += ['## Autonomous walk-forward selector', '',
              'Each year the same eligibility rule and objective pick one candidate from all earlier years; it then trades '
              'that year untouched.', '',
              '| Year | Policy chosen from earlier years | Train lower bound | OOS events | OOS mean (mid) | OOS mean 25% cost | OOS win rate |',
              '|---|---|---|---|---|---|---|']
    for y in wf['years']:
        if not y.get('policy'):
            lines.append(f"| {y['year']} | none eligible | | 0 | | | |")
            continue
        lines.append(f"| {y['year']} | `{y['policy']}` | {fmt(y['train_ci_low_normal'])} | {y.get('oos_events', 0)} | "
                     f"{fmt(y.get('oos_mean'))} | {fmt(y.get('oos_mean_c25'))} | "
                     f"{(y['oos_win_rate'] * 100 if y.get('oos_win_rate') is not None else 0):.0f}% |")
    lines += ['', HEADER, stage_line('2020-2025 OOS', wf['oos']), stage_line('2022-2025 OOS', wf['oos_2022_2025']), '',
              f"Illustrative account over the walk-forward trades: {fmt(wf['portfolio_mid'].get('total_return'))} at mid "
              f"(max drawdown {fmt(wf['portfolio_mid'].get('max_drawdown'))}), "
              f"{fmt(wf['portfolio_c25'].get('total_return'))} at 25% cost.", '']

    # Post-freeze diagnostics across every candidate.
    tables = {'A': read_csv(os.path.join(results, 'candidates_A.csv'))}
    for s in ('B', 'C', 'D'):
        tables[s] = read_csv(os.path.join(results, f'diagnostic_candidates_{s}.csv'))
    lines += [f"## Post-freeze diagnostics (all {frozen['candidates']:,} candidates; cannot change the frozen set)", '',
              '| Sample | Candidates with >=100 events | Mean > 0 | Normal lower bound > 0 | Mean 25% cost > 0 |',
              '|---|---|---|---|---|']
    for s, rows in tables.items():
        big = [r for r in rows if (num(r, 'events') or 0) >= 100]
        lines.append(f"| {s} | {len(big)} | {sum((num(r, 'mean') or 0) > 0 for r in big)} | "
                     f"{sum((num(r, 'ci_low_normal') or -1) > 0 for r in big)} | {sum((num(r, 'mean_c25') or 0) > 0 for r in big)} |")
    keyed = {s: {r['id']: r for r in rows} for s, rows in tables.items()}
    consistent = []
    for cid, a in keyed['A'].items():
        rows = [keyed[s].get(cid) for s in ('A', 'B', 'C', 'D')]
        if all(r and (num(r, 'events') or 0) >= 50 and (num(r, 'mean_c25') or -1) > 0 and (num(r, 'without_best5') or -1) > 0
               for r in rows):
            consistent.append((min(num(r, 'ci_low_normal') or -9 for r in rows), cid, rows))
    consistent.sort(reverse=True)
    lines += ['', f"Candidates positive at 25% cost and excluding their best 5 events in all four samples (>=50 events each): "
              f"{len(consistent)}. These are found after seeing B/C/D and are hypotheses for new data, not validated results.", '']
    if consistent:
        lines += ['| Candidate | A mean / lower | B mean / lower | C mean / lower | D mean / lower |', '|---|---|---|---|---|']
        for _, cid, rows in consistent[:15]:
            lines.append(f'| `{cid}` | ' + ' | '.join(f"{fmt(num(r, 'mean'))} / {fmt(num(r, 'ci_low_normal'))} (n={int(num(r, 'events'))})"
                                                    for r in rows) + ' |')
    lines += ['', '### Unfiltered base strategies by sample (standard liquidity, midpoint mean / 25%-cost mean, events)', '',
              '| Family | Timing | A | B | C | D |', '|---|---|---|---|---|---|']
    for cid, a in sorted(keyed['A'].items()):
        if '|none|standard' not in cid:
            continue
        family, timing = cid.split('|')[:2]
        cells = []
        for s in ('A', 'B', 'C', 'D'):
            r = keyed[s].get(cid)
            cells.append(f"{fmt(num(r, 'mean'))} / {fmt(num(r, 'mean_c25'))} ({int(num(r, 'events') or 0)})" if r and num(r, 'events') else 'n/a')
        lines.append(f'| {family} | {timing} | ' + ' | '.join(cells) + ' |')
    by_family = defaultdict(list)
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='../wrds_studies/research5_results')
    parser.add_argument('--output')
    parser.add_argument('--title', default='Research5: autonomous earnings-options strategy study')
    args = parser.parse_args()
    text = build(args.results, args.title)
    out = args.output or os.path.join(args.results, 'REPORT.md')
    with open(out, 'x') as stream:
        stream.write(text)
    print(out)
