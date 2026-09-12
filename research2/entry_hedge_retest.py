"""Second diagnostic retest: refresh stock hedge at entry instead of signal.

Uses the recorded entry-date OptionMetrics delta, only after trade selection.
Daily close fills remain a hypothetical simultaneous execution scenario.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from research2.iterate_strategies import ROOT,OUT,analyze,report


def run():
    c=pd.read_pickle(OUT/'enriched_candidates.pkl');p=pd.read_pickle(OUT/'positions.pkl')
    if p.version.str.contains('entry_hedge').any():p=p[~p.version.str.contains('entry_hedge')].copy()
    revised=[]
    for year,g in p.groupby('year'):
        data=ROOT/('strategy_lab_data' if year==2020 else 'research2_2025_data' if year==2025 else f'historical_jump_data_{year}')
        stocks=pd.read_pickle(data/'stocks.pkl');stocks.date=pd.to_datetime(stocks.date);stocks=stocks.set_index(['secid','date'])
        for sid,z in g.groupby('sid'):
            quotes=pd.read_pickle(data/f'normalized_{sid}.pkl').set_index(['date','optionid'])
            for _,row in z.iterrows():
                source=c[c.sid.eq(sid)&c.event.eq(row.event)].iloc[0]
                groups=row.ids.split(';');signs=([1,-1] if row.side=='pair' else [1 if row.side=='long' else -1])
                delta=0.;valid=True
                for group,sign in zip(groups,signs):
                    for oid in group.split(','):
                        if (source.entry,int(oid)) not in quotes.index:valid=False;continue
                        quote=quotes.loc[(source.entry,int(oid))];d=float(quote.delta)
                        if not np.isfinite(d) or d < -1 or d >1:valid=False;continue
                        delta+=sign*d
                r=row.copy();r['version']=row.version+'_entry_hedge'
                if not valid:r['status']='missing_entry_delta';revised.append(r);continue
                s0=float(stocks.loc[(sid,source.entry),'close']);s1=float(stocks.loc[(sid,source.exit),'close'])
                r['hedge_pnl']=-delta*(s1-s0);r['stock_cost']=abs(delta)*(s0+s1)*.0002
                revised.append(r)
    full=pd.concat([p,pd.DataFrame(revised)],ignore_index=True);full.to_pickle(OUT/'positions.pkl')
    analyze(c,full);report()
    print('entry delta coverage',pd.DataFrame(revised).status.value_counts().to_dict())

if __name__=='__main__':run()
