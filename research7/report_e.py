"""Write the sample-E report from evaluation_E.json (aggregates only)."""
import argparse
import json
import os

from research5.report import HEADER, fmt, stage_line


def build(results):
    ev = json.load(open(os.path.join(results, 'E', 'evaluation_E.json')))
    passed = [r for r in ev['rules'] if r['passed']]
    lines = ['# Research7 sample E: untouched expanded universe', '',
             f"Evaluated {ev['evaluated_at']}. Rules were fixed in research7/e_hypotheses.json (commit ec109b9) before the "
             'expanded data was downloaded. Midpoint fills unless stated; gates: weekly-bootstrap lower 95% bound > 0, '
             'mean > 0 at 25% half-spread, mean > 0 excluding best 5, >= 100 events and >= 40 issuers; post-hoc rules '
             'also need Holm-adjusted p < 0.05 over the 14 listed.', '',
             f'**{len(passed)} of {len(ev["rules"])} rules passed.**', '',
             '| Kind | Rule | Events | Mean (mid) | 95% bootstrap | Mean 25% | Mean 50% | Excl. best 5 | t | Holm p | Lag mean | Passed |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in ev['rules']:
        s, lag = r['E'], r['lag_check']
        if not s.get('events'):
            lines.append(f"| {r['kind']} | `{r['id']}` | 0 | | | | | | | | | no |")
            continue
        lines.append(f"| {r['kind']} | `{r['id']}` | {s['events']} | {fmt(s['mean'])} | [{fmt(s['ci_low_boot'])}, "
                     f"{fmt(s['ci_high_boot'])}] | {fmt(s['mean_c25'])} | {fmt(s['mean_c50'])} | {fmt(s['without_best5'])} | "
                     f"{r.get('t_cluster', 0):+.2f} | {fmt(r.get('holm_p'), pct=False, digits=3) if 'holm_p' in r else ''} | "
                     f"{fmt(lag.get('mean')) if lag.get('events') else 'n/a'} | {'**yes**' if r['passed'] else 'no'} |")
    lines += ['', '## Splits by name group and release timing', '', HEADER]
    for r in ev['rules']:
        if r['kind'] == 'post-hoc' and not r['passed']:
            continue
        for g, s in r['by_group'].items():
            lines.append(stage_line(f"`{r['id']}` {g}", s))
        for t, s in r['by_timing'].items():
            lines.append(stage_line(f"`{r['id']}` {t.replace('_', ' ')}", s))
    wf = ev['walk_forward']
    lines += ['', '## Walk-forward selector on sample E', '',
              '| Year | Policy chosen from earlier E years | OOS events | OOS mean (mid) | OOS mean 25% |', '|---|---|---|---|---|']
    for y in wf['years']:
        lines.append(f"| {y['year']} | `{y.get('policy')}` | {y.get('oos_events', 0)} | {fmt(y.get('oos_mean'))} | "
                     f"{fmt(y.get('oos_mean_c25'))} |")
    lines += ['', HEADER, stage_line('2020-2025 OOS', wf['oos']), '',
              f"Illustrative account: {fmt(wf['portfolio_mid'].get('total_return'))} at mid, "
              f"{fmt(wf['portfolio_c25'].get('total_return'))} at 25% cost.", '']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='../wrds_studies/research7_results')
    args = parser.parse_args()
    out = os.path.join(args.results, 'E', 'REPORT_E.md')
    with open(out, 'x') as stream:
        stream.write(build(args.results))
    print(out)
