"""Aggregate all fixed-rule jump experiments and export a self-contained report."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research2.historical_jump import summarize

ROOT=Path(__file__).resolve().parents[2]/'wrds_studies'

def table(frame):
    f=frame.copy()
    for col in f.select_dtypes(include='number'):
        f[col]=f[col].map(lambda x:f'{x:.2f}' if isinstance(x,float) else str(x))
    lines=['| '+' | '.join(f.columns)+' |','|'+'|'.join(['---']*len(f.columns))+'|']
    lines.extend('| '+' | '.join(map(str,row))+' |' for row in f.itertuples(index=False,name=None))
    return '\n'.join(lines)

def main():
    out=ROOT/'historical_jump_combined';out.mkdir(exist_ok=True)
    c=pd.concat([pd.read_pickle(ROOT/f'historical_jump_{y}/candidates.pkl').assign(year=y) for y in range(2020,2026)],ignore_index=True)
    c.to_pickle(out/'candidates.pkl');summarize(out)
    coverage=pd.concat([pd.read_csv(ROOT/f'historical_jump_{y}/coverage.csv').assign(year=y) for y in range(2020,2026)],ignore_index=True)
    coverage.to_csv(out/'coverage.csv',index=False)
    t=pd.read_pickle(out/'trades.pkl');s=pd.read_csv(out/'summary.csv')
    # Independent accounting checks: mirrored directions and exact quote crossing.
    index=['year','sid','event','kind','ids','hedged']
    long=t[t.model.eq('always_long')&t.fill.eq('mid_gross')].set_index(index)
    short=t[t.model.eq('always_short')&t.fill.eq('mid_gross')].set_index(index)
    np.testing.assert_allclose(long.pnl_share,-short.pnl_share,atol=1e-10)
    idx=index+['model','threshold']
    mid=t[t.fill.eq('mid_net')].set_index(idx);cross=t[t.fill.eq('bidask_net')].set_index(idx)
    np.testing.assert_allclose(mid.pnl_share-cross.pnl_share,mid.spread_cost,atol=1e-10)
    assert (pd.to_datetime(c.history_last)<pd.to_datetime(c.signal)).all()
    assert (pd.to_datetime(c.fit_date)<=pd.to_datetime(c.signal)).all()
    assert (pd.to_datetime(c.signal)<pd.to_datetime(c.entry)).all()
    assert (pd.to_datetime(c.entry)<pd.to_datetime(c.event)).all()
    assert (pd.to_datetime(c.event)<pd.to_datetime(c.exit)).all()
    # Equal event opportunities, equal premium allocation across candidate contracts;
    # an unselected contract's allocation remains idle rather than redistributed.
    comparisons=[];rng=np.random.default_rng(1729)
    for kind in ['single','straddle']:
        base=t[t.model.eq('always_short')&t.hedged&t.fill.eq('bidask_net')&t.kind.eq(kind)].copy()
        counts=base.groupby(['sid','event']).size()
        baseline=base.groupby(['sid','event']).return_premium.mean()
        week=pd.to_datetime(baseline.index.get_level_values('event')).to_period('W')
        weeks=sorted(set(week));cluster=np.array([weeks.index(w) for w in week]);n=len(weeks)
        draws=rng.integers(n,size=(5000,n));weights=np.array([(cluster==i).sum() for i in range(n)])
        for model in ['frozen_market_structural','historical_structural','historical_final_anchored','current_market_hybrid']:
            g=t[t.model.eq(model)&t.threshold.eq(.1)&t.hedged&t.fill.eq('bidask_net')&t.kind.eq(kind)]
            result=g.groupby(['sid','event']).return_premium.sum().reindex(counts.index,fill_value=0)/counts
            difference=result-baseline
            sums=np.array([difference.to_numpy()[cluster==i].sum() for i in range(n)])
            boot=sums[draws].sum(axis=1)/weights[draws].sum(axis=1)
            ci=np.quantile(boot,[.025,.975])
            comparisons.append(dict(kind=kind,model=model,opportunities=len(counts),trading_events=g[['sid','event']].drop_duplicates().shape[0],
                allocated_premium_pct=100*result.mean(),always_short_pct=100*baseline.mean(),difference_pct=100*difference.mean(),
                weekly_ci_low_pct=100*ci[0],weekly_ci_high_pct=100*ci[1]))
    comp=pd.DataFrame(comparisons);comp.to_csv(out/'benchmark_comparison.csv',index=False)
    selected=s[s.threshold.eq(.1)&s.hedged&s.side.eq('all')&s.fill.isin(['mid_net','bidask_net'])]
    years=[]
    for y in range(2020,2026):
        a=pd.read_csv(ROOT/f'historical_jump_{y}/summary.csv');a=a[a.threshold.eq(.1)&a.hedged&a.side.eq('all')&a.fill.eq('bidask_net')].copy();a['year']=y;years.append(a)
    years=pd.concat(years,ignore_index=True);years.to_csv(out/'year_summary.csv',index=False)
    checks=dict(eligible_events=c[['sid','event']].drop_duplicates().shape[0],single_candidates=int(c.kind.eq('single').sum()),straddle_candidates=int(c.kind.eq('straddle').sum()),
        unresolved=int(c.status.ne('scored').sum()),past_only_history=True,delayed_execution=True,midpoint_and_crossed_same_trades=True,mirrored_pnl_check=True,
        candidate_entry_relative_spread_median_pct=100*c.entry_relative_spread.median(),candidate_entry_relative_spread_p90_pct=100*c.entry_relative_spread.quantile(.9),
        historical_anchor_variance_floor_positions=int(c.variance_floor.sum()))
    (out/'validation.json').write_text(json.dumps(checks,indent=2))
    text='''# Historical earnings-jump trading experiments

## Findings

The 112-event comparison did not establish a profitable historical-jump replacement. At the specified 10% threshold with a fixed stock hedge, direct historical replacement earned +4.47% at midpoint fills after modeled costs and +1.54% crossing quotes for 77 straddles, versus -2.07% / -5.35% for 439 single options. The straddle event-bootstrap interval after crossing quotes spans roughly -10% to +12%. Anchoring the replacement to the delivered market curve returned -2.82% / -5.90% for 63 straddles and -6.27% / -9.72% for 346 singles. Both long and short sides of that anchored strategy lost on average.

The delivered market hybrid itself generated no 10% or 20% signals in the selected candidate set. At 5%, it generated six individual-option trades across four events: +11.45% at midpoint fills after costs, -1.57% crossing quotes. This tiny sample does not establish midpoint profitability. The older uncorrected structural model gave positive 10% averages, but its intervals included losses. Unhedged outcomes differ and are reported below; a positive unhedged result should not be labeled an isolated volatility edge.

Results vary materially by year. The direct historical straddle strategy's crossed means were +23.12%, -10.34%, -20.18%, +1.13%, +20.31%, and -2.21% for 2020 through 2025 respectively. Its worst individual result was a short NFLX straddle around January 2022, losing approximately 206% of entry option premium, including its fixed stock hedge and modeled costs. None of the paired comparisons with always-short exposure established an improvement using the calendar-week intervals.

## What was tested

Five recurring names (ADBE, AMD, AMZN, NFLX, TSLA), plus GOOGL in 2020, across 2020–2025. The expanded 2021–2024 panels were requested before their results were inspected. No winning threshold was selected afterward. 2020 and 2025 had been examined in earlier project work; this is historical research, not a prospective live result.

Historical jump variance uses the own-name last eight completed earnings events, minimum six. Each historical outcome is the compounded stock return from the close before the reported announcement to the close after it. Subtract the estimate of two ordinary sessions' variance (last 60 non-event observations), average the excess squares, and floor the final variance at zero. Map that variance into the existing compensated mixture, keeping its shape and zero risk-neutral multiplicative drift. This is a physical-history-informed valuation hypothesis, not a known true price or a fully historical distribution fit.

The latest identifiable reference-only Heston/jump calibration, at most 30 days old and referring to the same upcoming announcement, supplies frozen structural parameters. The signal-date spot, carry, and reference quotes are observed at the signal. The implied jump is replaced without refitting diffusion, stochastic-volatility parameters, or the replacement jump to the option target. Expansion years use anchor snapshots 15 and 10 sessions before earnings; earlier panels use their existing eligible anchors.

Methods: frozen_market_structural is the original frozen structural fit; historical_structural changes only its jump scale. historical_reference_anchored begins at linear reference-IV pricing and adds the change in implied total variance caused by replacing the structural jump. current_market_hybrid and current_market_only call the delivered constrained MarketSlice API, with and without the structural prior. historical_final_anchored applies the same jump-variance change to the delivered hybrid. Reference correction is computed before replacement, never refitted to erase the historical signal. The adjusted historical forecast curves are not claimed to retain every strike constraint of the market curve.

Signal three sessions before the reported earnings date; entry at the following close (two sessions before); exit at the first close after the date. This fixed exit captures both morning and evening releases without choosing the largest return day. Thresholds are 0%, 5%, 10%, 20% of the signal midpoint, with 10% the designated main comparison. Long if prediction exceeds midpoint by the threshold, short for the symmetric shortfall. The signal is not recomputed using next-close execution quotes.

At the earliest eligible 8–45 day expiry, choose the nearest three held-out strikes per call/put, and separately one nearest held-out ATM call/put straddle. Target signal bids must be positive, each leg midpoint at least $0.25; target relative spreads are not screened away. Identical contracts are followed at entry and exit, with no exit-delta filtering. Current-market reference filters are unchanged from the existing pricing pipeline.

Both unhedged and fixed initial reference-IV delta-hedged positions are evaluated. No hedge rebalancing occurs. Mid gross assumes midpoint fills with no costs. Mid net adds $0.65 per contract per side and 2 bp per side of stock traded. Crossed net buys at ask and sells at bid, adding the same costs. There is no extra option slippage on top of the requested fill scenarios.

**All percentage performance tables below divide P&L by entry option midpoint premium. They are not account returns, annual returns, or returns on short-option margin. Individual contracts are averaged within each company-earnings event, then events equally weighted. Positive short returns do not measure capital efficiency.** Different strategy rows overlap and must not be added as a portfolio.

## Coverage and checks

'''+json.dumps(checks,indent=2)+'\n\n'+table(coverage.groupby(['year','status']).size().rename('events').reset_index())
    text+='\n\n## Main 10% threshold, fixed stock hedge\n\n'+table(selected[['model','kind','fill','closed','events','equal_event_pct','ci_low_pct','ci_high_pct']])
    text+='\n\nIntervals above resample company-earnings events and are descriptive, not multiple-testing-adjusted. A separate paired calendar-week resampling against always-short appears below. Sparse subgroups do not support precise inference.\n\n## Long versus short, 10%, crossed quotes, stock hedge\n\n'+table(s[s.threshold.eq(.1)&s.hedged&s.fill.eq('bidask_net')][['model','kind','side','closed','events','equal_event_pct']])
    text+='\n\n## Threshold sensitivity, stock hedge, crossed quotes\n\n'+table(s[s.hedged&s.side.eq('all')&s.fill.eq('bidask_net')][['model','threshold','kind','closed','events','equal_event_pct']])
    text+='\n\n## Without the stock hedge, 10%\n\n'+table(s[~s.hedged&s.side.eq('all')&s.threshold.eq(.1)&s.fill.ne('mid_gross')][['model','kind','fill','closed','events','equal_event_pct','ci_low_pct','ci_high_pct']])
    text+='\n\n## Per-year 10% results, stock hedge, crossed quotes\n\n'+table(years[['year','model','kind','closed','events','equal_event_pct']])
    text+='\n\n## Comparison with unconditional short exposure\n\nEach candidate receives equal option-premium allocation within an event; unselected allocations remain idle. This makes participation comparable on all eligible events. The paired intervals resample calendar weeks, keeping names with announcements in the same week together. These allocations remain research normalization, not a funded margin portfolio.\n\n'+table(comp)
    text+='''

## Earnings data and limitations

Historical earnings dates are queried and cached from I/B/E/S via the existing WRDS connection; stock returns and option quotes use OptionMetrics. No manual parsing of release dates is required. Actual historical announcement dates do not establish when the schedule became known to a trader. A live implementation requires an as-of scheduled calendar, revisions, and release timestamps. The 2025 quote sample ends in August, so later 2025 dates are unavailable.

Midpoints and crossed daily quotes are fill scenarios, not evidence of attainable fills or sufficient size. Borrow, financing, margin, assignment, American early exercise, and intraday execution are not modeled. Multiple strikes per event are not independent observations. Historical earnings variance includes estimation error, changing company risk, and incomplete separation from ordinary variance. Inserting it into a risk-neutral model does not remove risk premia or prove market mispricing. The historical-adjustment variance floor was recorded rather than silently dropping those positions.

## Files

Source: research2/historical_jump.py. Fixed rules: research2/historical_jump_plan.json. Local licensed-data outputs: wrds_studies/historical_jump_combined/{candidates.pkl,trades.pkl,summary.csv,year_summary.csv,benchmark_comparison.csv,coverage.csv,validation.json}. The candidate/trade ledger preserves dates, contract IDs, history cutoff, fitted anchor, implied/historical variance, signal discrepancies, quoted spreads, stock hedge, costs, and both execution scenarios.
'''
    dest=Path(__file__).resolve().parents[1]/'docs/HISTORICAL_JUMP_TRADING.md';dest.write_text(text)
    print(selected[['model','kind','fill','closed','events','equal_event_pct']].to_string(index=False));print(comp.to_string(index=False));print('report',dest)

if __name__=='__main__':main()
