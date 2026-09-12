"""Record completed attempts, including failed confirmation tests."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from strategy_lab.followup_report import block_interval


def summarize(root):
    root=Path(root);out=root/'research2_round1';out.mkdir(exist_ok=True)
    findings={}
    lines=['# Research round 1: pricing and hedge improvements','',
        'No selected candidate cleared the recorded confirmation criterion. The goal remains active; these results must not be relabeled as alpha or a novel model.','',
        '## Pricing','', '| Sample | Candidate | Snapshot MAE, spot bp |','|---|---|---:|']
    for label,directory in [('2020 development','research2_development_v2'),('2025 confirmation','research2_pricing_confirmation')]:
        q=pd.concat([pd.read_pickle(f) for f in (root/directory).glob('pricing_*.pkl')])
        models=['linear_iv','pchip','ssvi','convex_pchip_10','convex_hybrid_10'];errors=q[['secid','date']].copy()
        for v in models:
            errors[v]=10000*(q[v]-q.mid).abs()/q.spot
            lines.append(f'| {label} | {v} | {errors.groupby(["secid","date"])[v].mean().mean():.4f} |')
        snap=errors.groupby(['secid','date'])[models].mean();diff=snap.convex_pchip_10-snap.convex_hybrid_10
        findings[label+'_pricing']=dict(quotes=len(q),snapshots=len(snap),
            relative_improvement=1-snap.convex_hybrid_10.mean()/snap.convex_pchip_10.mean(),
            paired_interval=block_interval(diff,snap.index.get_level_values('date')))
    lines+=['','The projected smiles passed all recorded within-expiry strike checks after normalizing constraint rows and retrying failed solves from a feasible curve. This does not guarantee absence of cross-expiry arbitrage. The structural prior adds little versus the identical projection with a PCHIP prior and loses that comparison in confirmation.','',
        '## Earnings hedges','', '| Sample | Hedge | Equal-event MSE | Mean absolute error, spot bp |','|---|---|---:|---:|']
    for label,directory in [('2020 development','research2_development'),('2025 confirmation','research2_confirmation')]:
        q=pd.read_json(root/directory/'event_hedges.json');q=q[q.status.eq('scored')]
        g=q.assign(squared=q.error*q.error,absolute=q.error.abs()).groupby(['sid','event','variant'])[['squared','absolute']].mean()
        for v,r in g.groupby('variant').mean().iterrows():lines.append(f'| {label} | {v} | {r.squared:.9f} | {r.absolute*10000:.3f} |')
        squared=g.squared.unstack();diff=squared.delta_gamma-squared.event_match
        findings[label+'_hedging']=dict(events=len(squared),positions=int(q[q.variant.eq('event_match')].shape[0]),
            relative_improvement=1-squared.event_match.mean()/squared.delta_gamma.mean(),
            paired_interval=block_interval(diff,squared.index.get_level_values('event')))
    lines+=['','The large improvement over delta-vega was mostly explained by the simpler delta-gamma hedge. Event matching improved development MSE by roughly 11%, with an interval spanning zero; confirmation did not establish an advantage. Q-weighted scenario hedging also failed to improve upon gamma hedging.','',
        'These are delayed-entry hedge scenarios with fixed contract identities. Hedge spreads and stock costs are reported separately; the primary errors are midpoint changes before hedge costs and financing. Earnings dates are retrospective, so this is not a point-in-time trading validation. The 2025 quote data stop on August 29, despite the requested full-year pull. The confirmation includes 14 available events across five non-dividend sample names; GOOGL was excluded.','',
        '## Ordinary daily hedge regression','',
        'Past-only reference-contract regressions were tested on 94,197 withheld-contract outcomes in 2020. Adding event/structural features helped the empirical regression relative to its Hull-White-style feature baseline, but it did not beat the practitioner Black-Scholes hedge. Thus this was not selected as a superior risk model.','',
        '## Next research question','',
        'Test event-aware transport of a freshly observed reference smile through time against sticky-strike, sticky-moneyness and simpler term-structure-based event variance. Separate the quality of today\'s mark from the forecast of its subsequent evolution. Do not tune round-1 candidates on confirmation outcomes and rerun that same test as if it were fresh.','',
        'Prior art and the limited originality claims are documented in research2/PRIOR_ART.md. The October 2026–March 2027 prospective reservation remains untouched.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n');(out/'results.json').write_text(json.dumps(findings,indent=2))
    print(json.dumps(findings,indent=2))


if __name__=='__main__':summarize(Path(__file__).resolve().parents[2]/'wrds_studies')
