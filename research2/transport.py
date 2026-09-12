"""Conditional next-close repricing with event-preserving variance transport.

Refresh today's smile from reference quotes. Supply tomorrow's observed stock
price equally to every method at scoring time. No stock-direction forecast is
claimed. An older identifiable event estimate is transported, never backfilled.
"""
import argparse
import json
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from scipy.optimize import nnls
from strategy_lab.protocol import Protocol,is_target
from strategy_lab.data import MarketData
from strategy_lab.model import prepare_surface,bsm,invert_iv
from variance_clock import ClockWeights


def transport_variance(w,T0,T1,event_variance,n0,n1,clock_ratio=None):
    event0=np.minimum(n0*event_variance,.99*w)
    effective=event0/max(n0,1)
    ratio=T1/T0 if clock_ratio is None else clock_ratio
    return np.maximum((w-event0)*ratio+n1*effective,1e-8)


def worker(args):
    sid,data,states_dir,output=args;output=Path(output);output.mkdir(parents=True,exist_ok=True)
    end=json.loads((Path(data)/'manifest.json').read_text())['end'];p=replace(Protocol(),end=end)
    m=MarketData(data,end);states=pd.read_pickle(Path(states_dir)/f'states_{sid}.pkl')
    frames={d:g for d,g in m.quotes(sid).groupby('date')};results=[];coverage={}
    for i,(date,raw) in enumerate(frames.items()):
        events=[pd.Timestamp(e) for e in m.events[sid]]
        if date in events:continue
        nxt=m.shift(date,1)
        # With date-only releases, use a fixed two-session bracket around
        # announcements; never choose the larger realized return day.
        if nxt in events:nxt=m.shift(nxt,1)
        if nxt not in frames or nxt>pd.Timestamp(end):continue
        try:base,ref,_=prepare_surface(raw,sid,date,m,p,ClockWeights(1,1,1),False)
        except ValueError:continue
        previous=[s for s in states if s['date']<=date and (date-s['date']).days<=30]
        if not previous:continue
        state=max(previous,key=lambda s:s['date'])
        events=[pd.Timestamp(e) for e in m.events[sid]]
        # The stored event estimate must refer to the same next announcement.
        then=[e for e in events if e>state['date']];now=[e for e in events if e>date]
        if not then or not now or min(then)!=min(now):continue
        base.parameters=state['variants']['calendar_heston_jump'][0].copy()
        model_j=.823875*base.parameters[3]**2
        design=[];observed=[]
        for exp,(logm,iv) in base.baseline_iv.items():
            T=m.exposure(date,exp).calendar_time;n=sum(date<e<=exp for e in events)
            design.append([T,n]);observed.append(np.interp(0,logm,iv)**2*T)
        variance_rate,simple_j=nnls(np.asarray(design),np.asarray(observed))[0]
        targets=raw[raw.strike_price.map(lambda k:is_target(sid,k)) & raw.exdate.isin(base.carry)
                    & (raw.strike/base.spot).between(.8,1.2) & raw.best_bid.ge(0) & raw.best_offer.ge(raw.best_bid) & raw.mid.gt(.01)]
        keep=[]
        for _,g in targets.groupby(['exdate','cp_flag']):
            g=g.sort_values('strike');ix=np.unique(np.linspace(0,len(g)-1,min(12,len(g))).round().astype(int));keep.append(g.iloc[ix])
        if not keep:continue
        targets=pd.concat(keep);future=frames[nxt].set_index('optionid').reindex(targets.optionid)
        stock=float(m.stock.loc[(sid,nxt),'close']);valid=(future.strike.to_numpy()==targets.strike.to_numpy())
        valid &= future.best_bid.ge(0).to_numpy() & future.best_offer.ge(future.best_bid).to_numpy()
        valid &= m.stock.loc[(sid,date),'cfadj']==m.stock.loc[(sid,nxt),'cfadj']
        targets=targets.copy();targets['actual']=np.where(valid,future.mid.to_numpy(),np.nan)
        targets['future_spot']=stock;targets['target_date']=nxt;targets['fit_age_days']=(date-state['date']).days
        targets['days_to_event']=(min(now)-date).days;targets['event_crossed']=int(any(date<e<=nxt for e in events))
        targets['model_j']=model_j;targets['simple_j']=simple_j
        for exp,g in targets.groupby('exdate'):
            x0=m.exposure(date,exp);x1=m.exposure(nxt,exp);T0=x0.calendar_time;T1=x1.calendar_time
            if T1<=0:continue
            r,q=base.carry[exp];F0=base.spot*np.exp((r-q)*T0);F1=stock*np.exp((r-q)*T1)
            logm,iv=base.baseline_iv[exp];K=g.strike.to_numpy();cp=g.cp_flag.eq('C').to_numpy()
            fixed=np.interp(np.log(K/F0),logm,iv);moving=np.interp(np.log(K/F1),logm,iv)
            n0=sum(date<e<=exp for e in events);n1=sum(nxt<e<=exp for e in events)
            target_w=fixed*fixed*T0
            predictions={'sticky_strike':bsm(F1,K,T1,r,fixed,cp),'sticky_moneyness':bsm(F1,K,T1,r,moving,cp)}
            # A market-only benchmark uses the nearest two maturities with
            # the same event count. The candidate estimates a strike-dependent
            # event term using the whole reference term structure.
            local_points=[(row[0],value) for row,value in zip(design,observed) if row[1]==1]
            if len(local_points)>=2:
                (ta,wa),(tb,wb)=sorted(local_points)[:2]
                local_j=max(0.,(tb*wa-ta*wb)/max(tb-ta,1e-8))
            else:local_j=simple_j
            smile_j=[]
            for logstrike in np.log(K/F0):
                ws=[]
                for ex,(mm,vv) in base.baseline_iv.items():
                    tt=m.exposure(date,ex).calendar_time
                    ws.append(float(np.interp(logstrike,mm,vv))**2*tt)
                smile_j.append(nnls(np.asarray(design),np.asarray(ws))[0][1])
            smile_j=np.asarray(smile_j)
            price_on=base.prices(g).to_numpy();par=base.parameters.copy();par[3]=0.
            price_off=base.prices(g,parameters=par).to_numpy()
            iv_on=invert_iv(F0,K,T0,r,price_on,cp);iv_off=invert_iv(F0,K,T0,r,price_off,cp)
            cf_j=np.maximum((iv_on*iv_on-iv_off*iv_off)*T0/max(n0,1),0.)
            for label,J in [('simple_event',simple_j),('model_event',model_j),
                            ('local_event',local_j),('smile_event',smile_j),('cf_event',cf_j)]:
                variance=transport_variance(target_w,T0,T1,J,n0,n1)
                predictions[label]=bsm(F1,K,T1,r,np.sqrt(variance/T1),cp)
            for label,value in predictions.items():targets.loc[g.index,label]=value
        cols=['date','target_date','secid','optionid','exdate','cp_flag','actual','future_spot','fit_age_days',
              'days_to_event','event_crossed','model_j','simple_j','sticky_strike','sticky_moneyness','simple_event','model_event','local_event','smile_event','cf_event']
        results.append(targets[cols])
        if i%50==0:print('transport',m.names[sid],i,flush=True)
    pd.concat(results).to_pickle(output/f'transport_{sid}.pkl');return sid


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--states',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();sids=json.loads((Path(a.data)/'manifest.json').read_text())['names'].values()
    with ProcessPoolExecutor(max_workers=3) as pool:
        for sid in pool.map(worker,[(s,a.data,a.states,a.output) for s in sids]):print('transport complete',sid,flush=True)
