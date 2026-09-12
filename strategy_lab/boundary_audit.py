"""Post-ablation diagnostic: do original parameter caps confound clock comparison?

Not a candidate in the frozen selection rule and not used to tune trading rules.
Both clocks receive the same wider domain; this does not identify Q clock weights.
"""
import argparse
from pathlib import Path
from dataclasses import replace
import numpy as np
import pandas as pd
from variance_clock import ClockWeights
from .protocol import Protocol
from .data import MarketData
from .model import prepare_surface
from .ablation import fit_variant,variant_prices


def run(data,results):
    out=Path(results); p=replace(Protocol(),max_fit_evaluations=100)
    m=MarketData(data,p.end); records=[]; fits=[]
    for file in sorted(out.glob('states_*.pkl')):
        sid=int(file.stem.split('_')[1]); states=pd.read_pickle(file)
        pred=pd.read_pickle(out/f'predictions_{sid}.pkl'); frames={d:g for d,g in m.quotes(sid).groupby('date')}
        for i,state in enumerate(states):
            d=state['date']; old=pred[pred.date.eq(d)]; raw=frames[d]; target=raw[raw.optionid.isin(old.optionid)]
            base,ref,event=prepare_surface(raw,sid,d,m,p,state['weights'])
            for clock,w in [('calendar',ClockWeights(1,1,1)),('physical',state['weights'])]:
                s,diag=fit_variant(base,ref,event,False,True,w,p,upper_bounds=[4.,12.,.3,.4])
                px=variant_prices(s,target); hi=variant_prices(s,target,terms=512)
                for index,r in target.iterrows():
                    records.append(dict(sid=sid,date=d,optionid=r.optionid,clock=clock,mae_bp=10000*abs(px.loc[index]-r.mid)/s.spot,
                        numerical_ok=abs(px.loc[index]-hi.loc[index])<=max(.01,.25*r.halfspread)))
                fits.append(dict(sid=sid,date=d,clock=clock,sigma=s.parameters[0],xi=s.parameters[1],fit_rmse=s.fit_rmse,**diag))
            if i%60==0: print('boundary',m.names[sid],i+1,'/',len(states),flush=True)
        pd.DataFrame(records).to_pickle(out/'boundary_predictions.pkl');pd.DataFrame(fits).to_csv(out/'boundary_fits.csv',index=False)
    q=pd.DataFrame(records); f=pd.DataFrame(fits)
    summary=q.groupby('clock').agg(n=('mae_bp','size'),mae_bp=('mae_bp','mean'),numerical_pass=('numerical_ok','mean'))
    summary['converged']=f.groupby('clock').converged.mean();summary['bound_rate']=f.groupby('clock').bound_hits.apply(lambda x:x.gt(0).mean())
    summary.to_csv(out/'boundary_summary.csv'); print(summary.to_string(),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--data',required=True);p.add_argument('--results',required=True)
    a=p.parse_args();run(a.data,a.results)
