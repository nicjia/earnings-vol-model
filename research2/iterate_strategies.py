"""Fixed diagnostic/retest round. All selections use signal-time information."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from research2.historical_jump import build_history
from research2.historical_jump_report import table
ROOT=Path(__file__).resolve().parents[2]/'wrds_studies'
OUT=ROOT/'strategy_iteration'


def enrich():
    c=pd.read_pickle(ROOT/'historical_jump_wide_combined/candidates.pkl').copy()
    history=build_history(ROOT/'historical_jump_data')
    c['strike']=np.nan;c['exdate']=pd.NaT;c['signal_spot']=np.nan;c['history_tail']=np.nan
    for year,g in c.groupby('year'):
        data=ROOT/('strategy_lab_data' if year==2020 else 'research2_2025_data' if year==2025 else f'historical_jump_data_{year}')
        stocks=pd.read_pickle(data/'stocks.pkl');stocks.date=pd.to_datetime(stocks.date);stocks=stocks.set_index(['secid','date'])
        for sid,z in g.groupby('sid'):
            q=pd.read_pickle(data/f'normalized_{sid}.pkl').set_index(['date','optionid'])
            for index,row in z.iterrows():
                first=int(row.ids.split(',')[0]);quote=q.loc[(pd.Timestamp(row.signal),first)]
                c.loc[index,'strike']=quote.strike;c.loc[index,'exdate']=quote.exdate
                c.loc[index,'signal_spot']=float(stocks.loc[(sid,pd.Timestamp(row.signal)),'close'])
            for event,zz in z.groupby('event'):
                past=history[history.sid.eq(sid)&history.available.lt(zz.signal.iloc[0])].sort_values('available').tail(8)
                c.loc[zz.index,'history_tail']=float(past.log_move.abs().max())
    c['edge']=c.current_market_hybrid-c.signal_mid
    c['relative_edge']=c.edge/c.signal_mid
    c['agreement']=np.sign(c.edge)==np.sign(c.current_market_only-c.signal_mid)
    c['liquid']=(c.signal_mid>=1)&(c.signal_relative_spread<=.10)
    c.to_pickle(OUT/'enriched_candidates.pkl');return c


def position(rows,signs,family,version,weight=1.):
    first=rows.iloc[0];signs=np.asarray(signs,float)
    scored=rows.status.eq('scored').all()
    return dict(sid=int(first.sid),name=first['name'],event=first.event,year=int(first.year),family=family,version=version,
        side='long' if np.all(signs>0) else 'short' if np.all(signs<0) else 'pair',ids=';'.join(rows.ids),
        selected=True,status='scored' if scored else 'unresolved',weight=weight,legs=int(rows.legs.sum()),
        option_pnl=float(signs@rows.option_move),hedge_pnl=float(signs@rows.hedge_move),
        # Net stock hedge for a paired trade, not sum of separate stock legs.
        stock_cost=float(abs(signs@rows.delta)/max(float(rows.delta.abs().sum()),1e-12)*rows.stock_cost.sum()) if len(rows)>1 else float(rows.stock_cost.iloc[0]),
        commission=float(rows.commission.sum()),entry_halfspread=float((rows.entry_relative_spread*rows.entry_mid/2).sum()),
        exit_halfspread=float((rows.spread_cost-rows.entry_relative_spread*rows.entry_mid/2).sum()),
        premium=float(rows.entry_mid.sum()),signal_premium=float(rows.signal_mid.sum()),
        notional=float(rows.legs.sum()*first.signal_spot),signal_relative_spread=float((rows.signal_relative_spread*rows.signal_mid).sum()/rows.signal_mid.sum()),
        signal_edge=float(signs@rows.edge),history_tail=float(first.history_tail))


def build_positions(c):
    records=[]
    for (sid,event),g in c.groupby(['sid','event']):
        singles=g[g.kind.eq('single')]
        for version in ['baseline','adjusted']:
            sel=singles[singles.relative_edge.abs()>.2] if version=='baseline' else singles[(singles.relative_edge.abs()>.05)&singles.liquid&singles.agreement&(singles.edge.abs()>singles.signal_relative_spread*singles.signal_mid+.013)]
            for _,row in sel.iterrows():records.append(position(row.to_frame().T,[np.sign(row.edge)],'single_residual',version))
            # At most one pair per family/event, determined before outcomes.
            for family,keys in [('vertical_relative_value',['exdate','cp_flag']),('calendar_relative_value',['strike','cp_flag'])]:
                pool=singles if version=='baseline' else singles[singles.liquid&singles.agreement]
                best=None;best_score=-np.inf
                for _,a in pool.groupby(keys):
                    cheap=a[a.edge>0];rich=a[a.edge<0]
                    for _,buy in cheap.iterrows():
                        for _,sell in rich.iterrows():
                            gap=buy.edge-sell.edge;prem=buy.signal_mid+sell.signal_mid
                            if gap/prem<=.05:continue
                            if version=='adjusted' and gap<=buy.signal_relative_spread*buy.signal_mid+sell.signal_relative_spread*sell.signal_mid+.026:continue
                            score=gap/prem
                            if score>best_score:best_score=score;best=pd.DataFrame([buy,sell])
                if best is not None:records.append(position(best,[1,-1],family,version))
            for _,row in g[g.kind.eq('straddle')].iterrows():
                h=row.historical_variance;q=row.implied_variance
                direction=1 if h>1.25*q else -1 if q>1.25*h else 0
                if direction==0:continue
                if version=='adjusted':
                    forecast_edge=direction*(row.historical_final_anchored-row.signal_mid)
                    if not row.liquid or forecast_edge<=row.signal_relative_spread*row.signal_mid+.026:continue
                weight=min(1.,.05/max(row.history_tail,.05)) if version=='adjusted' else 1.
                records.append(position(row.to_frame().T,[direction],'historical_variance',version,weight))
    p=pd.DataFrame(records);p.to_pickle(OUT/'positions.pkl');return p


def score(p,entry_fraction,exit_fraction,hedged=True):
    gross=p.option_pnl+(p.hedge_pnl if hedged else 0)
    cost=p.commission+(p.stock_cost if hedged else 0)
    return p.weight*(gross-cost-entry_fraction*p.entry_halfspread-exit_fraction*p.exit_halfspread)


def ci_week(values,index):
    weeks=pd.to_datetime(index.get_level_values('event')).to_period('W');unique=sorted(set(weeks));rng=np.random.default_rng(913)
    sums=np.array([values[weeks==w].sum() for w in unique]);n=np.array([(weeks==w).sum() for w in unique])
    ix=rng.integers(len(unique),size=(4000,len(unique)))
    return np.quantile(sums[ix].sum(1)/n[ix].sum(1),[.025,.975])


def analyze(c,p):
    universe=c[['sid','event','year']].drop_duplicates().set_index(['sid','event'])
    summary=[];diagnoses=[];fills=[(x,x) for x in [0,.25,.5,.75,1]]+[(0,1),(1,0),(.25,.75),(.75,.25)]
    for (family,version),g in p.groupby(['family','version']):
        for period,years in [('development',range(2016,2022)),('later',range(2022,2026)),('all',range(2016,2026))]:
            z=g[g.year.isin(years)];u=universe[universe.year.isin(years)]
            for hedge in [True,False]:
                for en,ex in fills:
                    v=z[z.status.eq('scored')].copy()
                    if v.empty:continue
                    v['pnl']=score(v,en,ex,hedge);v['ret']=v.pnl/v.notional;v['ret_premium']=v.pnl/v.premium
                    ev=v.groupby(['sid','event']).ret.mean();all_ev=ev.reindex(u.index,fill_value=0)
                    ci=ci_week(all_ev.to_numpy(),all_ev.index)
                    summary.append(dict(family=family,version=version,period=period,hedged=hedge,entry_fraction=en,exit_fraction=ex,selected=len(z),closed=len(v),unresolved=len(z)-len(v),events=len(ev),opportunities=len(u),
                        active_event_bp=10000*ev.mean(),all_event_bp=10000*all_ev.mean(),ci_low_bp=10000*ci[0],ci_high_bp=10000*ci[1],
                        premium_pct=100*v.groupby(['sid','event']).ret_premium.mean().mean(),
                        worst_event_bp=10000*ev.min(),win_event_pct=100*ev.gt(0).mean()))
                    if hedge and en==ex and en in [0,1]:
                        for dim in ['side','name','year']:
                            for label,d in v.groupby(dim):
                                n=d.notional
                                diagnoses.append(dict(family=family,version=version,period=period,fill=en,dimension=dim,label=str(label),trades=len(d),events=len(d[['sid','event']].drop_duplicates()),
                                    option_bp=10000*(d.weight*d.option_pnl/n).mean(),hedge_bp=10000*(d.weight*d.hedge_pnl/n).mean(),
                                    fees_bp=10000*(d.weight*(d.commission+d.stock_cost)/n).mean(),spread_bp=10000*(d.weight*en*(d.entry_halfspread+d.exit_halfspread)/n).mean(),net_bp=10000*d.ret.mean()))
    pd.DataFrame(summary).to_csv(OUT/'summary.csv',index=False);pd.DataFrame(diagnoses).to_csv(OUT/'diagnosis.csv',index=False)
    # Preserve the original 20% premium-normalized fill sensitivity on identical trades.
    g=p[(p.family=='single_residual')&(p.version=='baseline')].copy();sweep=[]
    for en,ex in fills:
        pnl=score(g,en,ex);ev=(pnl/g.premium).groupby([g.sid,g.event]).mean();spot=(pnl/g.notional).groupby([g.sid,g.event]).mean()
        sweep.append(dict(entry_fraction=en,exit_fraction=ex,events=len(ev),premium_pct=100*ev.mean(),spot_bp=10000*spot.mean()))
    pd.DataFrame(sweep).to_csv(OUT/'fill_sweep.csv',index=False)
    # Concentration is diagnostic only; never remove winners to select entries.
    net=score(g,0,0);ev=(net/g.premium).groupby([g.sid,g.event]).mean().sort_values(ascending=False)
    concentration=[dict(remove_best=n,remaining=len(ev)-n,premium_pct=100*ev.iloc[n:].mean()) for n in [0,1,2,3,5]]
    pd.DataFrame(concentration).to_csv(OUT/'concentration.csv',index=False)


def report():
    s=pd.read_csv(OUT/'summary.csv');d=pd.read_csv(OUT/'diagnosis.csv');f=pd.read_csv(OUT/'fill_sweep.csv')
    main=s[((s.hedged&~s.family.eq('protected_earnings'))|(~s.hedged&s.family.eq('protected_earnings')))&s.entry_fraction.eq(s.exit_fraction)&s.entry_fraction.isin([0,.5,1])]
    text='''# Strategy iteration: execution, losses and targeted adjustments

All work is historical simulation. Development is 2016–2021; later comparison is 2022–2025. Both periods have appeared in prior analyses, so later results are not an untouched confirmation. No threshold or configuration was selected by maximizing later-period profit. Four baseline/adjustment families are defined in iteration_plan.json.

## The 20% midpoint result

A midpoint fill pays zero modeled half-spread cost. A fraction of 1 pays the full adverse quoted half-spread at that leg. Fraction 0.5 is halfway from midpoint to the adverse bid/ask, not midpoint itself. Entry and exit fractions can differ. Commissions and stock execution costs remain. Fractions are hypothetical execution assumptions, not fill-rate estimates.

'''+table(f)
    text+='\n\nRemoving top events is diagnostic only:\n\n'+table(pd.read_csv(OUT/'concentration.csv'))
    text+='''

The previous +26% number is a mean of premium-normalized event returns, not account profit. Small option premiums and gains on the associated stock hedge can make this number extreme. The primary metric here is P&L per gross stock notional, allocated equally across selected positions within an event. Untraded event allocations remain idle. It is still not a funded portfolio or a margin return. Pairs net their stock hedge and have two option contracts' gross spot notional. Protective-wing comparisons instead preserve the original core straddle's two stock-notional units and use no stock hedge as primary; adding wings does not mechanically dilute their exposure denominator. The original signal, next-close entry and post-earnings exit remain unchanged.

## Strategies and diagnosis-driven adjustments

1. **Single residual:** baseline requires a 20% hybrid/midpoint discrepancy. Large discrepancies occurred in wide markets and tiny premiums; the initial stock hedge produced major winners/losses. Adjustment permits a 5% discrepancy but requires signal premium >= $1, full spread <= 10%, agreement with market-only pricing, and an edge greater than the estimated full round-trip spread plus commissions. Costs are estimated from signal quotes, not realized exit quotes.
2. **Vertical relative value:** buy an option with positive residual and sell one with negative residual, same expiry and type, different strikes. Select one pair/event by signal gap divided by gross premium, above 5%. Opposite residuals do not guarantee realizable relative value; wide leg spreads can consume the gap. Adjustment requires both legs to pass the same liquidity/agreement screen and the gap to cover signal-estimated crossing costs. The option legs form a vertical but the associated stock hedge means the full portfolio is not claimed to have bounded loss.
3. **Calendar relative value:** equivalent opposite-residual pairing at the same strike and type across expiries. Baseline buys the cheap residual and sells the rich one, with one selected pair/event. Adjustment adds both-leg liquidity/agreement and estimated-cost coverage. Both expiries span the announcement; this compares relative pricing rather than claiming to remove all event exposure.
4. **Historical variance:** buy ATM straddle when forecast variance exceeds implied by 25%, sell for the reverse. Earnings outliers and stale physical variance estimates can dominate. Adjustment requires signal liquidity, historical-adjusted option valuation to agree and cover estimated costs, and caps exposure using the largest absolute completed earnings move in the prior eight events. Scaling reduces both gains and losses; it does not by itself demonstrate forecasting improvement.

The broad diagnosis motivating liquidity adjustments uses previously inspected data. Date separation limits reuse in comparisons but cannot undo prior knowledge of this panel. The earlier known failure of short earnings-volatility positions motivates the tail-aware sizing adjustment.

## Before/after and later-period comparisons

Returns are basis points of allocated gross stock notional; all_event_bp includes zero for untraded events. Weekly bootstrap intervals preserve same-week clustering. They are descriptive and not adjusted for multiple strategies.

'''+table(main[['family','version','period','entry_fraction','closed','events','all_event_bp','ci_low_bp','ci_high_bp','premium_pct']])
    text+='\n\n## Long/short, stock versus option contributions, full bid–ask crossing\n\n'+table(d[d.period.eq('all')&d.fill.eq(1)&d.dimension.eq('side')])
    text+='\n\n## Per-year full-crossing diagnosis\n\n'+table(d[d.period.eq('all')&d.fill.eq(1)&d.dimension.eq('year')][['family','version','label','trades','option_bp','hedge_bp','fees_bp','spread_bp','net_bp']])
    text+='''

Full summaries include no-stock-hedge comparisons and asymmetric entry/exit fills. Trade selection never uses exit spreads or future P&L. One unresolved source candidate is retained; it has not qualified in these strategy selections. These fills do not model queues, adverse selection, latency, funding, borrow, American exercise or assignment. No live orders were sent. No mathematically independent information is created by agreement between two market-interpolation methods.

Outputs: wrds_studies/strategy_iteration/{positions.pkl,enriched_candidates.pkl,summary.csv,diagnosis.csv,fill_sweep.csv,concentration.csv}. Source: research2/iterate_strategies.py. The individual positions and signal-time conditions are reproducible from cached quote data.
'''
    text+="""

## Second and third diagnostic rounds

A separate hedge sensitivity replaces the stock delta calculated on the signal date with the delta observed at entry. Vendor OptionMetrics deltas are the first alternative (four strategy positions lack a usable vendor delta). A second alternative refreshes the original reference-IV method at entry, holding contract selection and option P&L fixed; all 567 baseline/adjusted positions have that reference hedge. The entry reference builder includes 1–100 DTE so contracts do not become unavailable merely by aging through the signal filter. It retains the same reference-strike split, quote-quality filters, eight-reference-per-expiry method and interpolation; it does not use exit information. These simultaneous closing hedge fills remain modeled execution, not guaranteed attainable prices.

For the 156 original 20% trades, the same-reference entry hedge changes midpoint premium-normalized performance from +25.99% to -4.67%. This is a strategy sensitivity, not a retroactive correction to the original intentionally fixed signal-date hedge. Both versions are retained. The original book is negative under equal signal-stock-notional normalization even at midpoint fills. Its top two premium-return events account for more than its total average gain.

The historical-variance development diagnosis favored shorts over longs, so adjusted short-only variants were tested with each hedge rule. They remained negative in the later comparison. A further risk-regime round tests recent 20-session realized variance / 252-session variance <= 1.5, a 60-session drawdown no worse than -20%, and both filters together. These factors use split-adjusted returns available by the signal date. All three fixed filters are reported rather than choosing the best later outcome. None turned the later crossed-quote mean positive. Better early-period averages therefore have not survived the time-separated comparison.

Entry-hedge comparisons, short-only gates and regime variants appear in the tables above. Missing entry deltas are reported as unavailable, not silently filled. The paired vendor comparison is additionally saved in hedge_paired_comparison.csv; regime inputs are in regime_factors.pkl. Retest sources are entry_hedge_retest.py, reference_hedge_retest.py, short_only_retest.py and regime_retest.py.

## Decision from this round

No robust executable edge is established. Partial-spread fills can preserve the old premium-normalized headline only under favorable assumptions: its symmetric break-even is about 42.6% of the full modeled crossing cost, and its fixed-exposure normalization is already negative at midpoint. Refreshed hedges, more liquid residual trades, paired relative-value trades, short-only selection, tail sizing and regime gates have all been evaluated rather than treating a single favorable average as the objective. Any positive subgroup remains an exploratory candidate, not a selected live strategy.
"""
    dest=Path(__file__).resolve().parents[1]/'docs/STRATEGY_ITERATION.md';dest.write_text(text)
    print(f.to_string(index=False));print(main[main.period.eq('later')][['family','version','entry_fraction','closed','events','all_event_bp','ci_low_bp','ci_high_bp']].to_string(index=False));print(dest)

if __name__=='__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    c=enrich();print('enriched',len(c),flush=True);p=build_positions(c);print('positions',len(p),flush=True);analyze(c,p);report()
