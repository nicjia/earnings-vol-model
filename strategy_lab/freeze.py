"""Create an exclusive, timestamped research freeze outside the public repository.

Reserves prospective outcomes; does not fetch data, place orders, schedule jobs,
or claim that a future test has already happened.
"""
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import zipfile


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(results):
    results=Path(results).resolve(); package=Path(__file__).resolve().parent; repo=package.parent
    protocol=json.loads((package/'followup_protocol.json').read_text())
    decision=json.loads((results/'decision.json').read_text())
    verification=json.loads((results/'verification.json').read_text())
    if not verification.get('passed'): raise ValueError('Verification must pass before freeze')
    now=dt.datetime.now(dt.timezone.utc)
    if dt.date.fromisoformat(protocol['future_window'][0])<=now.date():
        raise ValueError('Prospective reservation must begin after the freeze date')
    dest=results/('freeze_'+now.strftime('%Y%m%dT%H%M%SZ')); dest.mkdir(exist_ok=False)
    code=sorted(package.glob('*.py'))+sorted(package.glob('*.json'))
    code += [repo/name for name in ['cos_pricer.py','earnings_mixture.py','variance_clock.py','clocked_pricer.py']]
    source_hashes={str(p.relative_to(repo)):digest(p) for p in code}
    artifacts=['REPORT.md','decision.json','verification.json','pricing_summary.csv','strategy_comparison.csv',
               'boundary_summary.csv','weekend_diagnosis.json','analysis_plan_timestamp.json','boundary_plan.json']
    inputs=results.parent/'strategy_lab_data'
    input_hashes={p.name:digest(p) for p in sorted(inputs.glob('*.pkl'))}
    versions={name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','exchange_calendars']}
    record=dict(frozen_at_utc=now.isoformat(),protocol=protocol,decision=decision,
        source_sha256=source_hashes,result_sha256={name:digest(results/name) for name in artifacts},
        input_sha256=input_hashes,runtime_versions=versions,
        universe=['ADBE','AMD','AMZN','GOOGL','NFLX','TSLA'],
        status='Reserved only: future observations and operational data adapters are not yet available.',
        deployment='No qualified trading strategy. Interpolation remains a pricing benchmark, not a validated arbitrage-free executable surface.',
        change_control='Any implementation correction requires a new version and explanation; do not select changes using reserved outcomes.')
    with (dest/'manifest.json').open('x') as f: json.dump(record,f,indent=2)
    with zipfile.ZipFile(dest/'source_snapshot.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in code: z.write(p,str(p.relative_to(repo)))
    for name in artifacts: (dest/name).write_bytes((results/name).read_bytes())
    (dest/'README.md').write_text('Prospective paper-evaluation reservation only. See manifest.json for the exact frozen source, inputs, results, selection and future window. No live orders or scheduler were created.\n')
    print(dest)
    return dest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);a=p.parse_args();freeze(a.results)
