"""Attribution, paired comparisons, fixed-trade cost sweeps and decision record."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def block_interval(values,dates,repetitions=4000):
    """Resample calendar weeks jointly across names; each observation equal weight.

    Descriptive calibration uncertainty, not a multiple-testing-adjusted result.
    Serial dependence across weeks and only six issuers limit interpretation.
    """
    data=pd.DataFrame(dict(value=np.asarray(values),week=pd.to_datetime(np.asarray(dates)).to_period('W'))).dropna()
    groups=data.groupby('week').value.agg(['sum','count']).to_numpy()
    if len(groups)<2: return [float('nan'),float('nan')]
    rng=np.random.default_rng(20260909)
    selected=groups[rng.integers(0,len(groups),(repetitions,len(groups)))].sum(axis=1)
    return np.quantile(selected[:,0]/selected[:,1],[.025,.975]).tolist()


def trade_summary(trades):
    records=[]
    for (view,strategy),all_rows in trades.groupby(['view','strategy']):
        g=all_rows[all_rows.status.eq('closed')].copy()
        if not len(g):
            records.append(dict(view=view,strategy=strategy,n=0,other=len(all_rows),qualified=False)); continue
        net=100*g.net_pnl/g.normalizer
        gross=100*(g.option_mid_pnl+g.stock_hedge_pnl)/g.normalizer
        nospread=net+100*g.spread_cost/g.normalizer
        lo,hi=block_interval(net,g.entry_date)
        leave=[float(net[g.sid.ne(s)].mean()) for s in g.sid.unique()]
        qualified=(len(g)>=50 and not all_rows.status.eq('unresolved').any() and net.mean()>0 and lo>0
                   and len(leave)>1 and min(leave)>0)
        records.append(dict(view=view,strategy=strategy,n=len(g),other=len(all_rows)-len(g),
            net_pct=net.mean(),gross_pct=gross.mean(),zero_option_spread_pct=nospread.mean(),
            median_net_pct=net.median(),win_rate=net.gt(0).mean(),lower95_pct=lo,upper95_pct=hi,
            worst_leave_one_name_out_pct=min(leave),qualified=qualified))
    return pd.DataFrame(records)


def weekend_diagnostics(old,output):
    t=pd.DataFrame(json.loads((Path(old)/'trades.json').read_text()))
    t=t[t.strategy.eq('weekend_calendar') & t.status.eq('closed')].copy()
    for name in ['option_mid_pnl','stock_hedge_pnl','spread_cost','commissions','option_slippage','stock_cost','net_pnl']:
        t[name+'_pct']=100*t[name]/t.normalizer
    t['gross_pct']=t.option_mid_pnl_pct+t.stock_hedge_pnl_pct
    t['no_option_spread_pct']=t.net_pnl_pct+t.spread_cost_pct
    t['break_even_spread_fraction']=t.no_option_spread_pct/t.spread_cost_pct
    t['month']=pd.to_datetime(t.entry_date).dt.to_period('M').astype(str)
    cols=['option_mid_pnl_pct','stock_hedge_pnl_pct','gross_pct','spread_cost_pct','no_option_spread_pct','net_pnl_pct']
    by_name=t.groupby('sid')[cols].mean(); by_name['n']=t.groupby('sid').size()
    by_month=t.groupby('month')[cols].mean(); by_month['n']=t.groupby('month').size()
    by_name.to_csv(output/'weekend_by_name.csv'); by_month.to_csv(output/'weekend_by_month.csv')
    t.to_pickle(output/'weekend_trade_diagnostics.pkl')
    sweeps=[]
    for fraction in [0,.25,.5,.75,1.]:
        values=t.no_option_spread_pct-fraction*t.spread_cost_pct
        lo,hi=block_interval(values,t.entry_date)
        sweeps.append(dict(spread_fraction=fraction,mean_pct=values.mean(),median_pct=values.median(),lower95_pct=lo,upper95_pct=hi))
    pd.DataFrame(sweeps).to_csv(output/'weekend_cost_sweep.csv',index=False)
    stress=[]
    for n in [0,1,3,5]:
        g=t.sort_values('net_pnl_pct',ascending=False).iloc[n:]
        stress.append(dict(remove_best_net_trades=n,n=len(g),net_pct=g.net_pnl_pct.mean(),
                           gross_pct=g.gross_pct.mean(),zero_spread_pct=g.no_option_spread_pct.mean()))
    pd.DataFrame(stress).to_csv(output/'weekend_concentration.csv',index=False)
    return dict(n=len(t),components={c:float(t[c].mean()) for c in cols},
        sweeps=sweeps,stress=stress,net95=block_interval(t.net_pnl_pct,t.entry_date),
        zero_spread95=block_interval(t.no_option_spread_pct,t.entry_date),
        aggregate_break_even_spread_fraction=float(t.no_option_spread_pct.mean()/t.spread_cost_pct.mean()),
        dollar_net_total=float(t.net_pnl.sum()),equal_notional_mean_net_pct=float(t.net_pnl_pct.mean()),
        no_hedge_net_excluding_stock_cost_pct=float((t.net_pnl_pct-t.stock_hedge_pnl_pct+t.stock_cost_pct).mean()),
        stock_attribution_note='Removing the hedge is an accounting counterfactual with different exposure, not a matched-risk strategy.')


def build(results,old):
    out=Path(results)
    replay_files=[f for f in out.glob('replay_*.json') if not f.name.startswith('replay_coverage')]
    if len(replay_files)!=6: raise ValueError('Final report requires all six completed replay files')
    pred=pd.concat([pd.read_pickle(p) for p in sorted(out.glob('predictions_*.pkl'))],ignore_index=True)
    fits=pd.concat([pd.read_pickle(p) for p in out.glob('fits_*.pkl')],ignore_index=True)
    grids=pd.concat([pd.read_pickle(p) for p in out.glob('grids_*.pkl')],ignore_index=True)
    variants=list(fits.variant.unique())+['physical_hybrid','calendar_hybrid','interpolation']
    assert len(pred)==118117 and not pred.duplicated(['secid','date','optionid']).any()
    assert pred[variants].notna().all().all()
    pricing=[]; errors=pd.DataFrame({'date':pred.date,'secid':pred.secid})
    for v in variants:
        error=10000*(pred[v]-pred.mid).abs()/pred.spot; errors[v]=error
        signed=10000*(pred[v]-pred.mid)/pred.spot
        snap=errors.groupby(['date','secid'])[v].mean()
        f=fits[fits.variant.eq(v)]; grid=grids[grids.variant.eq(v)]
        pricing.append(dict(variant=v,n=len(pred),mae_bp=error.mean(),equal_snapshot_mae_bp=snap.mean(),
            bias_bp=signed.mean(),within_bidask_pct=100*((pred[v]>=pred.best_bid)&(pred[v]<=pred.best_offer)).mean(),
            convergence_pct=100*f.converged.mean() if len(f) else np.nan,
            any_bound_pct=100*f.bound_hits.gt(0).mean() if len(f) else np.nan,
            numerical_pass_pct=100*pred[v+'_numerical_ok'].mean() if v+'_numerical_ok' in pred else np.nan,
            grid_failure_pct=100*grid.bad.sum()/grid.total.sum() if len(grid) else np.nan))
    pricing=pd.DataFrame(pricing).set_index('variant'); pricing.to_csv(out/'pricing_summary.csv')
    paired=[]
    comparisons=[('physical_heston_jump','calendar_heston_jump'),('calendar_heston_no_jump','calendar_heston_jump'),
                 ('calendar_flat_jump','calendar_heston_jump'),('calendar_heston_jump','interpolation'),
                 ('physical_hybrid','interpolation'),('calendar_hybrid','interpolation')]
    for a,b in comparisons:
        diff=errors[a]-errors[b]; snap=errors.assign(diff=diff).groupby(['date','secid'])['diff'].mean().reset_index()
        lo,hi=block_interval(snap['diff'],snap.date)
        paired.append(dict(a=a,b=b,positive_means_b_better=True,quote_mae_difference_bp=diff.mean(),
            equal_snapshot_difference_bp=snap['diff'].mean(),snapshot_week_lower95=lo,snapshot_week_upper95=hi))
    pd.DataFrame(paired).to_csv(out/'paired_pricing.csv',index=False)
    # Diagnose maturity, call/put and reference-fit limitations without selecting a subgroup.
    errors['dte_bucket']=pd.cut((pred.exdate-pred.date).dt.days,[0,20,45,100])
    errors['cp_flag']=pred.cp_flag
    errors.groupby(['dte_bucket','cp_flag'],observed=True)[variants].mean().to_csv(out/'pricing_by_maturity_side.csv')
    errors.groupby('secid')[variants].mean().to_csv(out/'pricing_by_name.csv')
    baseline=pricing.loc['interpolation']; selected='interpolation'; eligible=[]
    for v in ['physical_hybrid','calendar_hybrid']:
        r=pricing.loc[v]
        if (r.mae_bp<=.95*baseline.mae_bp and r.equal_snapshot_mae_bp<baseline.equal_snapshot_mae_bp
            and r.grid_failure_pct<=baseline.grid_failure_pct): eligible.append(v)
    if eligible: selected=min(eligible,key=lambda v:pricing.loc[v,'mae_bp'])
    original=json.loads((Path(old)/'trades.json').read_text())
    for r in original: r['view']='physical_structural_original'
    replay=[r for f in sorted(out.glob('replay_*.json')) if not f.name.startswith('replay_coverage') for r in json.loads(f.read_text())]
    trades=pd.DataFrame(original+replay); summary=trade_summary(trades)
    summary.to_csv(out/'strategy_comparison.csv',index=False)
    sides=trades[trades.status.eq('closed')].copy()
    sides['net_pct']=100*sides.net_pnl/sides.normalizer
    sides.groupby(['view','strategy','direction']).net_pct.agg(['size','mean','median']).to_csv(out/'sides.csv')
    weekend=weekend_diagnostics(old,out)
    (out/'weekend_diagnosis.json').write_text(json.dumps(weekend,indent=2))
    future_files=list(out.glob('future_*.pkl')); future_stats=[]
    if future_files:
        future=pd.concat([pd.read_pickle(p) for p in future_files],ignore_index=True)
        for v,g in future.groupby('view'):
            valid=g.actual.notna() & g.predicted.notna()
            future_stats.append(dict(view=v,n=int(valid.sum()),unresolved=int((~valid).sum()),
                mae_bp=float((10000*(g.loc[valid,'predicted']-g.loc[valid,'actual']).abs()/g.loc[valid,'spot']).mean())))
    pd.DataFrame(future_stats).to_csv(out/'future_summary.csv',index=False)
    decision=dict(pricing_selection=selected,hybrids_meeting_selection_rule=eligible,
        qualified_strategies=summary.loc[summary.qualified,['view','strategy']].to_dict('records'),
        maker_validation='Not established: no timestamped fills or order-book replay.',
        prospective_window=['2026-10-01','2027-03-31'],prospective_results_available=False)
    (out/'decision.json').write_text(json.dumps(decision,indent=2))
    lines=['# Component ablations and trading diagnosis','',
        'Exploratory calibration only: six names, 2020, 1,068 reference snapshots and 118,117 identical withheld contracts. No fresh-period trading result is claimed.','',
        '## Individual-option pricing','',
        '| Candidate | MAE, spot bp | Within bid/ask | Equal-snapshot MAE |',
        '|---|---:|---:|---:|']
    for v,r in pricing.iterrows(): lines.append(f'| {v} | {r.mae_bp:.3f} | {r.within_bidask_pct:.1f}% | {r.equal_snapshot_mae_bp:.3f} |')
    boundary=pd.read_csv(out/'boundary_summary.csv').set_index('clock')
    lines+=['','### Parameter-limit diagnostic','',
        'The physical-clock Heston/jump fit reaches a parameter boundary on 88.6% of original snapshots, versus 28.9% with calendar time. Therefore the original clock comparison is partly confounded by the parameter domain and fixed Heston time scale. A separately labeled diagnostic widened sigma from 2 to 4 and vol-of-vol from 2.5 to 12, with up to 100 optimizer evaluations instead of 35 for both clocks. It was specified after observing the boundary hits and is not a candidate in the trading-selection rule.','',
        f"With those changes, calendar-clock MAE is {boundary.loc['calendar','mae_bp']:.3f} spot bp and physical-clock MAE is {boundary.loc['physical','mae_bp']:.3f}. Both remain well behind interpolation. All these fits converged and passed the 128-versus-512 COS numerical screen. The check changes bounds and optimization effort together; it does not isolate their individual contributions. kappa remains fixed in each clock's time units. This is evidence of restrictive calibration, not evidence that weekends should be ignored."]
    lines+=['','All variants refit to the same reference contracts with the same robust objective and parameter bounds. Flat/Heston, scheduled jump on/off, and calendar/physical clock form a 2×2×2 design. The physical clock uses past stock-return variance ratios; these are not separately estimated risk-neutral clock weights. Dropping the clock does not mean weekends have no risk.','',
        'The hybrid adds interpolated reference-IV residuals to the structural smile. It is a candidate marking method, not a new estimate of physical fair value. Structural sensitivities are provisional risk proxies, not independently validated event hedges.','',
        f'Pricing selection under the recorded rule: **{selected}**. See pricing_summary.csv for optimizer boundary hits, numerical checks, and necessary strike-grid failures; these grid checks do not prove absence of arbitrage.','',
        '## Later-date conditional repricing','',
        'Reference information and corrections frozen at the preceding close; actual later spot supplied equally to every view. This is conditional repricing, not a prediction of stock direction.','',
        '| View | Scored | Unresolved | MAE, spot bp |','|---|---:|---:|---:|']
    for r in future_stats: lines.append(f"| {r['view']} | {r['n']} | {r['unresolved']} | {r['mae_bp']:.3f} |")
    lines+=['','## Strategy replay','',
        'Original rules, cost assumptions and uncertainty buffers remain fixed. Each view/strategy is a separate book. Hybrids use their corresponding structural sensitivities; interpolation uses calendar-model sensitivities. Changes in marks, deltas, selected trades and exits mean this is a strategy replay, not a pure fixed-position price attribution.','',
        'Percentages are per gross option contract spot notional, not return on premium or margin. Quoted-price scenarios assume delayed execution and include spreads, commissions, option slippage and stock-hedge costs. They omit financing, borrow, margin and assignment. Incomplete outcomes remain disclosed.','',
        '| View / strategy | Closed / other | Gross mid % | Zero option spread % | Net % | Weekly-block 95% net interval |',
        '|---|---:|---:|---:|---:|---:|']
    for r in summary.itertuples():
        if r.n: lines.append(f'| {r.view} / {r.strategy} | {r.n} / {r.other} | {r.gross_pct:+.4f} | {r.zero_option_spread_pct:+.4f} | {r.net_pct:+.4f} | [{r.lower95_pct:+.4f}, {r.upper95_pct:+.4f}] |')
    lines+=['','The calendar structural single-option book has a positive mean, but its interval spans zero and removing one name can turn it negative. Interpolation has only ten resolved single-option trades. Neither qualifies as an established edge. Hybrid/interpolation marks eliminate most apparent discrepancies under the original cost and uncertainty thresholds; that alone does not prove those discrepancies were entirely model error.','',
        '### Long versus short','',
        '| Single-option book | Side | Closed | Mean net % | Median net % |',
        '|---|---|---:|---:|---:|']
    for (view,side),g in sides[sides.strategy.eq('single_convergence')].groupby(['view','direction']):
        lines.append(f'| {view} | {side} | {len(g)} | {g.net_pct.mean():+.4f} | {g.net_pct.median():+.4f} |')
    lines+=['','Original-clock losses are concentrated on shorts, although both original sides have negative means. Calendar-model longs have a positive mean and a negative median, indicating uneven outcomes. These are descriptive subsets selected after the whole-book results, not newly qualified long-only strategies. Side P&L alone cannot establish overpricing or underpricing: stock hedges, move risk, changed model marks, delayed fills and costs also contribute.']
    lines+=['','Strategies absent from a view had no qualifying proposals; session rotation remains blocked by missing real opening option quotes. Intervals resample calendar weeks jointly across names, using 4,000 fixed-seed draws. They are descriptive, do not correct for strategy selection, and may understate dependence across weeks.','',
        '## Original weekend book','',
        f"{weekend['n']} resolved trades. Option marks contributed {weekend['components']['option_mid_pnl_pct']:+.4f}%, stock hedge {weekend['components']['stock_hedge_pnl_pct']:+.4f}%, before costs. Gross was {weekend['components']['gross_pct']:+.4f}%; zero option spread with other costs retained was {weekend['components']['no_option_spread_pct']:+.4f}%; quoted net was {weekend['components']['net_pnl_pct']:+.4f}%.",
        '',f"The equal-notional break-even fraction of actual round-trip option spread costs is {weekend['aggregate_break_even_spread_fraction']:.1%}. This keeps the actual same trades, hedge and non-spread costs; it does not model passive fill probability, adverse selection or repricing of the strategy.",
        '', '| Removed best net trades | Remaining | Gross % | Zero option spread % | Net % |','|---|---:|---:|---:|---:|']
    for r in weekend['stress']: lines.append(f"| {r['remove_best_net_trades']} | {r['n']} | {r['gross_pct']:+.4f} | {r['zero_spread_pct']:+.4f} | {r['net_pct']:+.4f} |")
    lines+=['',f"Actual dollar net sums to ${weekend['dollar_net_total']:,.2f}, while the equal-notional mean is {weekend['equal_notional_mean_net_pct']:+.4f}%. This difference reflects position weighting, not contradictory arithmetic. Neither is a margin-capital return.",
        '', '## Market-making decision and prospective reservation','',
        f"Strategies meeting the recorded calibration gate: {decision['qualified_strategies'] or 'none'}. Passing such a gate would still not validate passive execution.",
        '', 'Existing study inputs are daily quotes. The inspected WRDS Cboe optprice_2020 table has a daily date field and OHLC/bid/ask fields, but no intraday quote timestamps or queue information. The metadata inventory and column inspection are saved separately; this is not an exhaustive statement about every product the institution might license. A maker test requires synchronized option NBBO, sizes, trades and underlying quotes, latency/queue assumptions, partial fills, inventory limits, fees and post-fill markouts. [Cboe quote intervals](https://datashop.cboe.com/option-quote-intervals) supply snapshots; [Cboe option trades](https://datashop.cboe.com/option-trades) supply transaction records and contemporaneous NBBO. Those alone still do not reveal our queue position.',
        '', 'Reserved future window: **2026-10-01 through 2027-03-31**. It has not happened at the freeze date. The frozen selection is a paper-evaluation specification, not a completed forward test or a scheduled job. Point-in-time earnings schedules, dividend/corporate-action eligibility, contract handling and a calendar covering that window must be ready before scoring. Implementation corrections must be versioned and must not be chosen using future outcomes.',
        '', 'The evidence does not establish market efficiency, prove that all pricing residuals are model error, or show that event decomposition is accurate. It identifies which restricted models price held-out quotes better and which tested strategies remain unqualified.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return decision


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--old',required=True)
    a=p.parse_args(); print(json.dumps(build(a.results,a.old),indent=2))
