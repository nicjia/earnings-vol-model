"""Report additional events and the separately broadened option screen."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research2.historical_jump import summarize
from research2.historical_jump_report import table
ROOT=Path(__file__).resolve().parents[2]/'wrds_studies'

def main():
    out=ROOT/'historical_jump_expanded';wideout=ROOT/'historical_jump_wide_combined';wideout.mkdir(exist_ok=True)
    wide=pd.concat([pd.read_pickle(ROOT/f'historical_jump_wide_{y}/candidates.pkl').assign(year=y) for y in range(2016,2026)],ignore_index=True)
    wide.to_pickle(wideout/'candidates.pkl');summarize(wideout,wide=True)
    narrow=pd.read_pickle(out/'candidates.pkl');s=pd.read_csv(out/'summary.csv');w=pd.read_csv(wideout/'summary.csv')
    for c in [narrow,wide]:
        assert (pd.to_datetime(c.history_last)<pd.to_datetime(c.signal)).all()
        assert (pd.to_datetime(c.fit_date)<=pd.to_datetime(c.signal)).all()
        assert (pd.to_datetime(c.signal)<pd.to_datetime(c.entry)).all()
        assert not c.duplicated(['sid','event','kind','ids']).any()
    t=pd.read_pickle(wideout/'trades.pkl');ix=['year','sid','event','kind','ids','model','threshold','hedged']
    mid=t[t.fill.eq('mid_net')].set_index(ix);cross=t[t.fill.eq('bidask_net')].set_index(ix)
    np.testing.assert_allclose(mid.pnl_share-cross.pnl_share,mid.spread_cost,atol=1e-10,equal_nan=True)
    counts=[]
    for label,c in [('Original candidate rules, expanded years',narrow),('Broader surface screen',wide)]:
        counts.append(dict(screen=label,events=len(c[['sid','event']].drop_duplicates()),single_candidates=int(c.kind.eq('single').sum()),straddle_candidates=int(c.kind.eq('straddle').sum()),unresolved=int(c.status.ne('scored').sum())))
    selected=s[s.threshold.eq(.1)&s.hedged&s.side.eq('all')&s.fill.ne('mid_gross')&s.model.isin(['historical_structural','historical_final_anchored'])]
    newcurrent=s[s.model.eq('current_market_hybrid')&s.hedged&s.side.eq('all')&s.fill.ne('mid_gross')]
    ws=w[w.hedged&w.side.eq('all')&w.fill.ne('mid_gross')]
    report='''# Expanded earnings testing and option-surface coverage

Added automated I/B/E/S earnings windows for 2016–2019, retaining the original five names and historical forecast/threshold rules. Earlier years have warmup and reference-expiry exclusions; the added usable events are not every reported event. Older and newer panels remain retrospective historical research, with actual announcement dates rather than a verified as-of schedule. 2025 quote coverage ends in August.

The prior six-trade result came from nearest-three held-out strikes per option type at one expiry, one pre-earnings signal date, not the entire surface or every trading day. The separate broader screen now evaluates every held-out strike within 80–120% of spot, across all expiries selected by the existing reference pipeline (up to five) with 8–90 DTE. The same signal bid > 0 and midpoint >= $0.25 screen applies. Reference/calibration strikes remain excluded from targets. No additional relative-spread restriction is imposed on target contracts. It is still not the entire listed surface: far wings, other maturities, reference strikes, and other daily timestamps are outside this experiment.

Both runs keep signal three sessions before earnings, next-close entry, first close after earnings exit, exact option IDs and the same target trades for midpoint versus crossed fills. These are valuation-gap trades through earnings, not trades held to expiry or an automatically capital-constrained portfolio. Adding many contracts creates correlated exposures; contracts are averaged within company-earnings events for the reported mean.

**Returns below are relative to entry option midpoint premium, not account capital or short-option margin. Mid net includes $0.65/contract/side and 2 bp/side of stock costs. Bid–ask net additionally crosses the quoted option spread. Hedged results hold the initial stock delta fixed; unhedged results are also retained. No guaranteed fill, financing, borrow, assignment or margin model is implied.**

## Coverage

'''+table(pd.DataFrame(counts))
    report+='\n\n## Original candidate rules, enlarged event sample: historical jump at 10%\n\n'+table(selected[['model','kind','fill','closed','events','equal_event_pct','ci_low_pct','ci_high_pct']])
    report+='\n\n## Current market hybrid under the original candidate rules\n\n'+table(newcurrent[['threshold','kind','fill','closed','events','equal_event_pct','ci_low_pct','ci_high_pct']])
    report+='\n\n## Broader screen: current market hybrid with fixed initial stock hedge\n\n'+table(ws[['threshold','kind','fill','selected','closed','unresolved','events','equal_event_pct','ci_low_pct','ci_high_pct','mean_entry_spread_pct']])
    report+='\n\n## Broader screen: long versus short, crossed quotes, fixed stock hedge\n\n'+table(w[w.hedged&w.fill.eq('bidask_net')][['threshold','kind','side','closed','events','equal_event_pct']])
    report+='\n\n## Broader screen without stock hedge\n\n'+table(w[~w.hedged&w.side.eq('all')&w.fill.ne('mid_gross')][['threshold','kind','fill','closed','events','equal_event_pct','ci_low_pct','ci_high_pct']])
    report+='''

Intervals are descriptive company-event bootstrap intervals, not corrected for trying multiple specifications and thresholds. Sparse subgroups cannot support precise inference. Missing outcomes are counted and not converted to wins or zero P&L. Summary rows are absent when no trades qualify; absence is not a measured zero return. All candidate predictions and quotes are stored in the ledger, along with spread measures and unresolved status.

Pricing inputs, manual mixture controls, and the distinction between a variance clock and explicit overnight jumps are documented in [MODEL_INPUTS.md](MODEL_INPUTS.md). In particular, the latest trading experiments use calendar-time structural parameters with closure weights equal to one; no automatic nightly jump-mixture calibration is being tested.

Local result directories: wrds_studies/historical_jump_expanded and wrds_studies/historical_jump_wide_combined. Each has candidates.pkl, trades.pkl and summary.csv. Annual subdirectories preserve the original and broader runs separately. Source is research2/historical_jump.py; expansion rules are in research2/expanded_jump_plan.json. Original 112-event results remain in HISTORICAL_JUMP_TRADING.md.
'''
    path=Path(__file__).resolve().parents[1]/'docs/EXPANDED_EARNINGS_TEST.md';path.write_text(report)
    (wideout/'validation.json').write_text(json.dumps(dict(coverage=counts,past_only_history=True,identity_uniqueness=True,midpoint_crossed_spread_identity=True),indent=2))
    print(pd.DataFrame(counts).to_string(index=False));print(ws[['threshold','kind','fill','closed','events','equal_event_pct','ci_low_pct','ci_high_pct']].to_string(index=False));print(path)
if __name__=='__main__':main()
