"""Before-announcement residual convergence, with fixed diagnostic adjustments."""
import numpy as np
import pandas as pd
from research2.iterate_strategies import ROOT,ci_week
from research2.historical_jump_report import table

OUT=ROOT/'pre_event_combined';OUT.mkdir(exist_ok=True)

def main():
    c=pd.concat([pd.read_pickle(ROOT/f'pre_event_results_{y}/candidates.pkl').assign(year=y) for y in range(2016,2026)],ignore_index=True)
    c=c[c.kind.eq('single')].copy();c['signal_spot']=np.nan
    for year,g in c.groupby('year'):
        stock=pd.read_pickle(ROOT/f'pre_event_data_{year}/stocks.pkl');stock.date=pd.to_datetime(stock.date);stock=stock.set_index(['secid','date'])
        c.loc[g.index,'signal_spot']=[float(stock.loc[(sid,date),'close']) for sid,date in zip(g.sid,g.signal)]
    c['relative_edge']=c.current_market_hybrid/c.signal_mid-1;c['direction']=np.sign(c.relative_edge)
    c['liquid']=c.signal_mid.ge(1)&c.signal_relative_spread.le(.1)
    c['cost_covered']=(c.current_market_hybrid-c.signal_mid).abs().gt(c.signal_relative_spread*c.signal_mid+.013)
    c['agreement']=np.sign(c.current_market_only-c.signal_mid).eq(c.direction)
    c.to_pickle(OUT/'candidates.pkl');summary=[];diag=[];trades=[]
    universe=c[['sid','event','year']].drop_duplicates().set_index(['sid','event'])
    for threshold in [.05,.1,.2]:
        base=c[c.relative_edge.abs()>threshold]
        for version in ['baseline','liquid_cost','entry_limit']:
            g=base.copy()
            if version=='liquid_cost':g=g[g.liquid&g.cost_covered&g.agreement]
            if version=='entry_limit':
                limit=g.current_market_hybrid/(1+g.direction*threshold)
                ask=g.entry_mid*(1+g.entry_relative_spread/2);bid=g.entry_mid*(1-g.entry_relative_spread/2)
                g=g[np.where(g.direction>0,ask<=limit,bid>=limit)]
            for hedge in ['none','signal','entry']:
                for frac in [0,.25,.5,1]:
                    z=g.copy();z['version']=version;z['threshold']=threshold;z['hedge']=hedge;z['fraction']=frac
                    if hedge=='entry':
                        z.loc[~np.isfinite(z.entry_quote_delta),'status']='missing_entry_delta'
                        stock_pnl=-z.entry_quote_delta*z.stock_change;stock_cost=z.entry_quote_delta.abs()*z.stock_roundtrip_rate
                    elif hedge=='signal':stock_pnl=z.hedge_move;stock_cost=z.stock_cost
                    else:stock_pnl=0.;stock_cost=0.
                    z['pnl']=z.direction*(z.option_move+stock_pnl)-z.commission-stock_cost-frac*z.spread_cost
                    z['ret']=z.pnl/z.signal_spot;z['ret_premium']=z.pnl/z.entry_mid
                    trades.append(z)
                    for period,years in [('development',list(range(2016,2022))),('later',list(range(2022,2026))),('all',list(range(2016,2026)))]:
                        selected=z[z.year.isin(years)];v=selected[selected.status.eq('scored')];u=universe[universe.year.isin(years)]
                        if v.empty:continue
                        ev=v.groupby(['sid','event']).ret.mean();all_ev=ev.reindex(u.index,fill_value=0);ci=ci_week(all_ev.to_numpy(),all_ev.index)
                        summary.append(dict(threshold=threshold,version=version,hedge=hedge,fraction=frac,period=period,selected=len(selected),closed=len(v),unresolved=len(selected)-len(v),events=len(ev),opportunities=len(u),
                            all_event_bp=10000*all_ev.mean(),active_event_bp=10000*ev.mean(),ci_low_bp=10000*ci[0],ci_high_bp=10000*ci[1],premium_pct=100*v.groupby(['sid','event']).ret_premium.mean().mean()))
                        if frac==1 and hedge=='entry':
                            for side,q in v.groupby('direction'):
                                diag.append(dict(threshold=threshold,version=version,period=period,side='long' if side>0 else 'short',trades=len(q),option_bp=10000*(q.direction*q.option_move/q.signal_spot).mean(),stock_bp=10000*(-q.direction*q.entry_quote_delta*q.stock_change/q.signal_spot).mean(),cost_bp=10000*((q.commission+q.entry_quote_delta.abs()*q.stock_roundtrip_rate+q.spread_cost)/q.signal_spot).mean(),net_bp=10000*q.ret.mean()))
    s=pd.DataFrame(summary);s.to_csv(OUT/'summary.csv',index=False);pd.DataFrame(diag).to_csv(OUT/'diagnosis.csv',index=False);pd.concat(trades,ignore_index=True).to_pickle(OUT/'trades.pkl')
    assert (pd.to_datetime(c.exit)<pd.to_datetime(c.event)).all()
    text='''# Pre-earnings convergence test

This experiment avoids holding through the announcement. Signal ten sessions before earnings, enter at the next close, exit six sessions before earnings. Options still expire after the announcement, so earnings remains priced throughout the holding period. The initial 2021–2024 test was expanded with fixed rules to 2016–2020 and 2025, reusing cached quotes and automatically downloading missing dates for the recurring names. GOOGL appears only in 2020. The initial result is preserved in PRE_EARNINGS_INITIAL.md and the corresponding private initial-result directory. Historical dates are retrospective, and closing quotes do not establish actual fills.

The same current hybrid prices held-out strikes. Thresholds are 5%, 10%, 20%. The fixed adjustment requires signal midpoint >= $1, full signal spread <=10%, model-only and hybrid directional agreement, and the gap to cover the signal-estimated full round-trip spread plus fees. A separate entry-limit variant requires the actual entry ask/bid to preserve the signal-price threshold under the frozen dollar valuation; it uses entry quotes, never exit outcomes. Agreement between two interpolators is not independent information.

Three hedge choices are reported: none, fixed signal-date reference delta, and vendor entry-date delta. Missing vendor deltas are counted as unavailable; no P&L is inferred for them. Entry/exit fractions of 0, .25, .5, 1 span midpoint to fully adverse quoted fills. Reported all_event_bp averages P&L/stock-notional across all eligible events, with unselected allocations idle. Premium-normalized returns are supplementary, not account returns. 2016–2021 is the development partition; 2022–2025 is a later historical comparison, not an untouched prospective test.

'''
    text+=f'Candidates: {len(c)} individual contracts across {len(universe)} company-earnings events.\n\n'
    text+=table(s[s.hedge.eq('entry')&s.fraction.isin([0,1])][['threshold','version','fraction','period','closed','unresolved','events','all_event_bp','ci_low_bp','ci_high_bp','premium_pct']])
    text+='\n\n## Side and cost diagnosis\n\n'+table(pd.DataFrame(diag))
    text+='\n\nAll hedge/fill comparisons are retained in wrds_studies/pre_event_combined/summary.csv; candidate and trade ledgers are saved alongside it. The original holding-through-earnings experiments are unchanged.\n'
    path=ROOT.parent/'event-clock/docs/PRE_EARNINGS_CONVERGENCE.md';path.write_text(text)
    print(s[s.hedge.eq('entry')&s.period.eq('later')&s.fraction.isin([0,1])][['threshold','version','fraction','closed','events','all_event_bp','ci_low_bp','ci_high_bp']].to_string(index=False));print('coverage',len(c),len(universe));print(path)

if __name__=='__main__':main()
