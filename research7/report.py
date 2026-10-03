"""Write the research7 report from saved outputs (aggregates only)."""
import argparse
import json
import os

from research5 import report as r5report
from research5.report import HEADER, fmt, stage_line


def build(results):
    text = r5report.build(results, 'Research7: release-timed earnings options (I/B/E/S announcement times)')
    ev = json.load(open(os.path.join(results, 'evaluation.json')))
    lines = ['', '## Sample E (untouched expanded universe)', '',
             'Reserved. The frozen policies above and the replications below are evaluated on the expanded names only '
             'after that data is downloaded; no policy can qualify before then.', '',
             '## Frozen policies: pooled out-of-selection samples and release timing', '', HEADER]
    for p in ev['policies']:
        lines.append(stage_line(f"`{p['id']}` B+C+D", p['pooled_BCD']))
        for t, s in p['pooled_BCD_by_timing'].items():
            lines.append(stage_line(f'… {t.replace("_", " ")}', s))
    lines += ['', '## Replications of earlier leads with release-correct timing (pre-registered)', '']
    for name, r in ev['replications'].items():
        lines += [f"### {name}: `{r['candidate']}`", '', HEADER]
        for s in ('A', 'B', 'C', 'D'):
            lines.append(stage_line(s, r['stages'][s]))
        lines.append(stage_line('B+C+D pooled', r['pooled_BCD']))
        for t, s in r['pooled_BCD_by_timing'].items():
            lines.append(stage_line(f'B+C+D {t.replace("_", " ")}', s))
        for s in ('B', 'C', 'D'):
            lines.append(stage_line(f'{s}, decided one session earlier', r['lag_check'][s]))
        lines.append('')
    return text + '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', default='../wrds_studies/research7_results')
    args = parser.parse_args()
    out = os.path.join(args.results, 'REPORT.md')
    with open(out, 'x') as stream:
        stream.write(build(args.results))
    print(out)
