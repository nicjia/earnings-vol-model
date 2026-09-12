"""Diagnose and remove extrapolation-driven pre-earnings signals."""
import numpy as np
import pandas as pd
from variance_clock import ClockWeights
from strategy_lab.data import MarketData
from strategy_lab.protocol import Protocol
from strategy_lab.model import prepare_surface
from research2.iterate_strategies import ROOT,ci_week
from research2.historical_jump_report import table


def main():
    records=[];summaries=[]
    for panel,prefix in [('original','pre_event'),('new_names','pre_event_new_names')]:
        out=ROOT/(prefix+'_combined');c=pd.read_pickle(out/'candidates.pkl')
        candidates=c[c.relative_edge.abs().gt(.05)&c.liquid&c.cost_covered&c.agreement]
        for year,g in candidates.groupby('year'):
            m=MarketData(ROOT/f'{prefix}_data_{year}',f'{year}-12-31')
            for sid,z in g.groupby('sid'):
                frames={d:q for d,q in m.quotes(sid).groupby('date')}
                for event,gg in z.groupby('event'):
                    signal=gg.signal.iloc[0];base,ref,_=prepare_surface(frames[signal],sid,signal,m,Protocol(),ClockWeights(1,1,1),False)
                    raw=frames[signal].set_index('optionid')
                    for _,row in gg.iterrows():
                        option=raw.loc[int(row.ids)];r=ref[ref.exdate.eq(option.exdate)]
                        records.append(dict(panel=panel,sid=sid,event=event,ids=row.ids,strike=float(option.strike),reference_min=float(r.strike.min()),reference_max=float(r.strike.max()),within_reference_band=bool(r.strike.min()<=option.strike<=r.strike.max())))
        support=pd.DataFrame([r for r in records if r['panel']==panel])
        trades=pd.read_pickle(out/'trades.pkl');g=trades[trades.version.eq('liquid_cost')&trades.threshold.eq(.05)&trades.hedge.eq('entry')&trades.fraction.isin([0,1])].merge(support,on=['sid','event','ids'],validate='many_to_one')
        for period,years in [('development',range(2016,2022)),('later',range(2022,2026)),('all',range(2016,2026))]:
            u=c[c.year.isin(years)][['sid','event']].drop_duplicates().set_index(['sid','event'])
            for version in ['original_rule','no_extrapolation']:
                for fraction in [0,1]:
                    z=g[g.year.isin(years)&g.fraction.eq(fraction)]
                    if version=='no_extrapolation':z=z[z.within_reference_band]
                    v=z[z.status.eq('scored')]
                    if v.empty:continue
                    ev=v.groupby(['sid','event']).ret.mean();all_ev=ev.reindex(u.index,fill_value=0);ci=ci_week(all_ev.to_numpy(),all_ev.index)
                    summaries.append(dict(panel=panel,period=period,version=version,fraction=fraction,trades=len(v),events=len(ev),all_event_bp=10000*all_ev.mean(),ci_low_bp=10000*ci[0],ci_high_bp=10000*ci[1],premium_pct=100*v.groupby(['sid','event']).ret_premium.mean().mean()))
    out=ROOT/'strategy_iteration';pd.DataFrame(records).to_csv(out/'reference_support.csv',index=False);s=pd.DataFrame(summaries);s.to_csv(out/'support_retest.csv',index=False)
    text='''# Reference-support diagnosis and retest

The frozen pre-earnings liquidity/cost candidate generated four trades across three events in five additional companies. All four lost after crossing quotes. Two VRTX calls had strikes 395 and 405 while the actual fitted reference strikes spanned 450–510. They were extrapolations, despite the signal's acceptable relative spread. The model's inferred forward also differed from the no-dividend carry forward; extrapolation is not the only possible price-error source.

The targeted adjustment keeps only target strikes bracketed by the fitted reference strikes at the signal date. It uses no future prices. It is evaluated on both the original and additional-company panels, but the latter has now been inspected; these adjusted results must not be called fresh validation. The original frozen additional-company result is preserved separately. A positive reduced sample would not establish an executable edge.

'''+table(s)
    text+='\n\n## Signal support audit\n\n'+table(pd.DataFrame(records))
    text+='\n\nUnits are basis points of stock notional averaged across all event opportunities, and supplementary premium-normalized means. The same entry-date delta hedge, fixed pre-earnings exit and execution assumptions are preserved.\n'
    path=ROOT.parent/'event-clock/docs/REFERENCE_SUPPORT_RETEST.md';path.write_text(text);print(s[s.period.eq('later')&s.fraction.eq(1)].to_string(index=False));print(path)

if __name__=='__main__':main()
