"""Same reference-IV delta estimator, refreshed at actual entry date."""
from dataclasses import replace
import numpy as np
import pandas as pd
from scipy.special import ndtr
from variance_clock import ClockWeights
from strategy_lab.data import MarketData
from strategy_lab.protocol import Protocol
from strategy_lab.model import prepare_surface
from research2.iterate_strategies import ROOT,OUT,analyze,report


def main():
    c=pd.read_pickle(OUT/'enriched_candidates.pkl');p=pd.read_pickle(OUT/'positions.pkl');p=p[~p.version.str.contains('reference_hedge')].copy()
    revised=[]
    for year,g in p[p.version.isin(['baseline','adjusted'])].groupby('year'):
        root=ROOT/('strategy_lab_data' if year==2020 else 'research2_2025_data' if year==2025 else f'historical_jump_data_{year}')
        m=MarketData(root,f'{year}-12-31');protocol=replace(Protocol(),min_dte=1,max_dte=100,minimum_expirations=1,minimum_references=4,max_expirations=25)
        for sid,z in g.groupby('sid'):
            frames={d:q for d,q in m.quotes(sid).groupby('date')}
            for event,positions in z.groupby('event'):
                source=c[c.sid.eq(sid)&c.event.eq(event)].iloc[0];date=source.entry
                try:base,ref,_=prepare_surface(frames[date],sid,date,m,protocol,ClockWeights(1,1,1),False)
                except ValueError:base=None
                q=frames[date].set_index('optionid');deltas={}
                for _,row in positions.iterrows():
                    groups=row.ids.split(';');signs=[1,-1] if row.side=='pair' else [1 if row.side=='long' else -1];delta=0.;valid=base is not None
                    for group,sign in zip(groups,signs):
                        for oid in map(int,group.split(',')):
                            if oid not in q.index:valid=False;continue
                            option=q.loc[oid];exp=option.exdate
                            if base is None or exp not in base.carry:valid=False;continue
                            if oid not in deltas:
                                T=m.exposure(date,exp).calendar_time;r,carry=base.carry[exp];F=base.spot*np.exp((r-carry)*T)
                                mm,iv=base.baseline_iv[exp];vol=float(np.interp(np.log(option.strike/F),mm,iv))
                                d1=(np.log(F/option.strike)+.5*vol*vol*T)/(vol*np.sqrt(T))
                                deltas[oid]=float(np.exp(-carry*T)*(ndtr(d1)-(option.cp_flag=='P')))
                            delta+=sign*deltas[oid]
                    r=row.copy();r['version']=row.version+'_reference_hedge'
                    if not valid:r['status']='missing_entry_reference';revised.append(r);continue
                    s0=float(m.stock.loc[(sid,date),'close']);s1=float(m.stock.loc[(sid,source.exit),'close'])
                    r['hedge_pnl']=-delta*(s1-s0);r['stock_cost']=abs(delta)*(s0+s1)*.0002;revised.append(r)
    full=pd.concat([p,pd.DataFrame(revised)],ignore_index=True)
    extra=full[full.family.eq('historical_variance')&full.version.eq('adjusted_reference_hedge')&full.side.eq('short')].copy();extra['version']='adjusted_reference_hedge_short_only';full=pd.concat([full,extra],ignore_index=True)
    full.to_pickle(OUT/'positions.pkl');analyze(c,full);report();print('reference hedge coverage',pd.DataFrame(revised).status.value_counts().to_dict())

if __name__=='__main__':main()
