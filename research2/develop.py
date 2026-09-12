"""Evaluate specified pricing candidates and build past-only hedge research data."""
import argparse
import json
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import time
import numpy as np
import pandas as pd
from scipy.special import ndtr
from variance_clock import ClockWeights
from strategy_lab.protocol import Protocol
from strategy_lab.data import MarketData
from strategy_lab.model import prepare_surface,invert_iv,bsm
from strategy_lab.ablation import OverlaySurface
from .smiles import ConvexSmile,call_prior,ssvi_fit


def worker(args):
    sid,data,previous,output,limit=args; output=Path(output); output.mkdir(parents=True,exist_ok=True)
    p=replace(Protocol(),end=json.loads((Path(data)/'manifest.json').read_text())['end']); market=MarketData(data,p.end)
    states=pd.read_pickle(Path(previous)/f'states_{sid}.pkl')
    if limit:states=states[:limit]
    old=pd.read_pickle(Path(previous)/f'predictions_{sid}.pkl'); frames={d:g for d,g in market.quotes(sid).groupby('date')}
    prices=[]; diagnostics=[]; hedges=[]; started=time.monotonic()
    for i,state in enumerate(states):
        date=state['date']; raw=frames[date]; olddate=old[old.date.eq(date)]
        base,ref,event=prepare_surface(raw,sid,date,market,p,ClockWeights(1,1,1))
        base.parameters,base.fit_rmse=state['variants']['calendar_heston_jump']; overlay=OverlaySurface(base,ref)
        target=raw[raw.optionid.isin(olddate.optionid)]
        for exp,g in ref.groupby('exdate'):
            r,q=base.carry[exp]; T=market.exposure(date,exp).calendar_time; F=base.spot*np.exp((r-q)*T); D=np.exp(-r*T)
            x=g.strike.to_numpy()/F; logm,iv=base.baseline_iv[exp]
            call=g.mid.to_numpy()/(D*F)+np.where(g.cp_flag.eq('P'),1-x,0.)
            scale=np.maximum(g.halfspread.to_numpy()/(D*F),.00005)
            group=target[target.exdate.eq(exp)].copy(); xt=group.strike.to_numpy()/F
            outputrow=group[['date','secid','optionid','exdate','strike','cp_flag','mid','best_bid','best_offer']].copy()
            outputrow['spot']=base.spot
            priors={'pchip':call_prior(logm,iv,T),'linear_iv':call_prior(logm,iv,T,'linear')}
            def structural_prior(xx):
                rows=pd.DataFrame(dict(strike=xx*F,exdate=exp,cp_flag='C'))
                return overlay.prices(rows).to_numpy()/(D*F)
            priors['hybrid']=structural_prior
            iv_scale=scale/np.maximum(np.sqrt(T)*np.exp(-.5*(logm/np.maximum(iv*np.sqrt(T),.001))**2)/np.sqrt(2*np.pi),.005)
            ssvi,ok=ssvi_fit(logm,iv,T,iv_scale)
            values={'pchip':priors['pchip'](xt),'linear_iv':priors['linear_iv'](xt),
                    'ssvi':bsm(1.,xt,T,0,ssvi(np.log(xt)),True)}
            grids=np.linspace(.5,1.5,301)
            for name,prior in priors.items():
                for weight in [0.1,1.,10.]:
                    start=time.monotonic(); smile=ConvexSmile(x,call,scale,prior,weight)
                    label=f'convex_{name}_{weight:g}'; values[label]=smile(xt)
                    marks=smile(grids); slopes=np.diff(marks)/np.diff(grids)
                    valid=bool(smile.ok and (np.diff(slopes)>=-1e-6).all() and (slopes>=-1-1e-6).all() and (slopes<=1e-6).all())
                    diagnostics.append(dict(sid=sid,date=date,exdate=exp,variant=label,solver_ok=smile.ok,
                        grid_ok=valid,seconds=time.monotonic()-start))
            for name,value in values.items():
                outputrow[name]=D*F*(value-np.where(group.cp_flag.eq('P'),1-xt,0.))
            prices.append(outputrow)
        # One-session hedge outcomes: all information in deltas/features is
        # observable at the initial close. Reference contracts train; withheld
        # contracts evaluate. Trades/quotes at the next close supply outcomes.
        nxt=market.shift(date,1)
        if nxt in frames and nxt<=pd.Timestamp(p.end):
            rows=pd.concat([ref.assign(reference=True),target.assign(reference=False)]).drop_duplicates('optionid')
            rows=rows[(rows.best_bid>0)&(rows.halfspread/rows.mid<.2)&(rows.mid>.05)].copy()
            rows['delta_model']=base.deltas(rows)
            other=frames[nxt].set_index('optionid').reindex(rows.optionid)
            s1=float(market.stock.loc[(sid,nxt),'close']); s0=base.spot
            valid=(other.strike.to_numpy()==rows.strike.to_numpy()) & other.best_bid.ge(0).to_numpy() & other.best_offer.ge(other.best_bid).to_numpy()
            valid &= market.stock.loc[(sid,date),'cfadj']==market.stock.loc[(sid,nxt),'cfadj']
            rows['actual_change']=np.where(valid,(other.mid.to_numpy()-rows.mid.to_numpy())/s0,np.nan)
            rows['stock_change']=(s1-s0)/s0; rows['target_date']=nxt;rows['sid']=sid
            future_events=[pd.Timestamp(e) for e in market.events[sid] if pd.Timestamp(e)>date]
            distance=(min(future_events)-date).days if future_events else 999
            rows['days_to_event']=distance
            for exp,g in rows.groupby('exdate'):
                r,q=base.carry[exp];T=market.exposure(date,exp).calendar_time;F=s0*np.exp((r-q)*T)
                iv=invert_iv(F,g.strike.to_numpy(),T,r,g.mid.to_numpy(),g.cp_flag.eq('C').to_numpy())
                d1=(np.log(F/g.strike.to_numpy())+.5*iv*iv*T)/(iv*np.sqrt(T))
                delta=np.exp(-q*T)*(ndtr(d1)-g.cp_flag.eq('P').to_numpy())
                rows.loc[g.index,'delta_bs']=delta
                rows.loc[g.index,'vega_scaled']=np.exp(-q*T)*np.exp(-.5*d1*d1)/np.sqrt(2*np.pi)
                ne=sum(date<pd.Timestamp(e)<=exp for e in market.events[sid])
                # Defined feature, not a claim that the fitted jump variance is true.
                variance=base.parameters[0]**2*T
                rows.loc[g.index,'event_fraction']=ne*.823875*base.parameters[3]**2/max(variance+ne*.823875*base.parameters[3]**2,1e-8)
            cols=['date','target_date','sid','optionid','reference','actual_change','stock_change',
                  'delta_model','delta_bs','vega_scaled','days_to_event','event_fraction','cp_flag']
            hedges.append(rows[cols])
        if i%20==0:print('develop',market.names[sid],i+1,'/',len(states),'seconds',round(time.monotonic()-started),flush=True)
    pd.concat(prices).to_pickle(output/f'pricing_{sid}.pkl');pd.DataFrame(diagnostics).to_pickle(output/f'diagnostics_{sid}.pkl')
    (pd.concat(hedges) if hedges else pd.DataFrame()).to_pickle(output/f'hedges_{sid}.pkl')
    return sid


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--previous',required=True);p.add_argument('--output',required=True)
    p.add_argument('--limit',type=int);p.add_argument('--workers',type=int,default=3);a=p.parse_args()
    sids=[int(f.stem.split('_')[1]) for f in Path(a.previous).glob('states_*.pkl')]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for sid in pool.map(worker,[(s,a.data,a.previous,a.output,a.limit) for s in sids]):print('finished',sid,flush=True)
