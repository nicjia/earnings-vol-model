"""Same-reference/same-target calibration ablations, with no return tuning.

Run as a module. Outputs belong outside the public repository.
"""
import argparse
import copy
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from variance_clock import ClockWeights
from .data import MarketData
from .model import prepare_surface, cos_batch, invert_iv, bsm
from .protocol import Protocol


def fit_variant(surface, chosen, fit_event, flat, events, weights, protocol,upper_bounds=None):
    """Precompute metadata once, not on every optimizer evaluation."""
    s=copy.copy(surface); s.weights=weights
    groups=[]
    for exp,g in chosen.groupby('exdate',sort=False):
        x=s.market.exposure(s.date,exp); r,q=s.carry[exp]
        n=sum(s.date<pd.Timestamp(e)<=exp for e in s.market.events[s.sid]) if events else 0
        groups.append((g.strike.to_numpy(),g.cp_flag.eq('C').to_numpy(),x.calendar_time,
                       x.variance_time(weights),r,q,n,g.mid.to_numpy(),
                       np.maximum(g.halfspread.to_numpy(),s.spot*.0005)))
    indices=([0] if flat else [0,1,2])+([3] if events and fit_event else [])
    base=np.array([.4,.5,-.4,0.]); base[3]=.04 if 3 in indices else 0.
    low=np.array([.05,.03,-.95,.0001]); high=np.array([2.,2.5,.3,.4])
    if upper_bounds is not None: high=np.asarray(upper_bounds,dtype=float)
    def unpack(p):
        full=base.copy(); full[indices]=p; return full
    def residual(p,scaled=True):
        par=unpack(p)
        return np.concatenate([(cos_batch(s.spot,K,c,T,tv,r,q,par,n,protocol.cos_terms,flat)-mid)
                               /(scale if scaled else 1.) for K,c,T,tv,r,q,n,mid,scale in groups])
    fit=least_squares(residual,base[indices],bounds=(low[indices],high[indices]),
        max_nfev=protocol.max_fit_evaluations,loss='soft_l1',ftol=1e-5,xtol=1e-5,gtol=1e-5)
    s.parameters=unpack(fit.x); s.fit_rmse=float(np.sqrt(np.mean(residual(fit.x,False)**2)))
    return s,dict(converged=bool(fit.success),evaluations=int(fit.nfev),
        bound_hits=int(np.sum(np.minimum(abs(fit.x-low[indices]),abs(fit.x-high[indices]))<1e-4)))


def variant_prices(s,rows,flat=False,events=True,terms=None):
    out=pd.Series(np.nan,index=rows.index)
    for exp,g in rows.groupby('exdate'):
        x=s.market.exposure(s.date,exp); r,q=s.carry[exp]
        n=sum(s.date<pd.Timestamp(e)<=exp for e in s.market.events[s.sid]) if events else 0
        out.loc[g.index]=cos_batch(s.spot,g.strike.to_numpy(),g.cp_flag.eq('C').to_numpy(),
            x.calendar_time,x.variance_time(s.weights),r,q,s.parameters,n,terms or s.terms,flat)
    return out


class OverlaySurface:
    """Reference IV residual correction; structural sensitivities retained.

    This interpolation is not guaranteed arbitrage-free. Its parameters and
    corrections are determined only by reference contracts at the signal time.
    """
    def __init__(self,base,chosen,hybrid=True):
        self.base=base; self.hybrid=hybrid; self.corrections={}
        if hybrid:
            marks=base.prices(chosen)
            for exp,g in chosen.groupby('exdate'):
                r,q=base.carry[exp]; T=base.market.exposure(base.date,exp).calendar_time
                F=base.spot*np.exp((r-q)*T)
                model_iv=invert_iv(F,g.strike.to_numpy(),T,r,marks.loc[g.index].to_numpy(),g.cp_flag.eq('C').to_numpy())
                m,iv=base.baseline_iv[exp]
                self.corrections[exp]=(m,iv-model_iv)

    def __getattr__(self,key): return getattr(self.base,key)

    def prices(self,rows,date=None,spot=None,**kwargs):
        if not self.hybrid: return self.base.benchmark(rows,date,spot)
        date=self.base.date if date is None else pd.Timestamp(date)
        spot=self.base.spot if spot is None else spot
        out=self.base.prices(rows,date,spot,**kwargs)
        for exp,g in rows.groupby('exdate'):
            if exp not in self.corrections: continue
            if self.market.expiry_time(exp)<=self.market.close_time(date): continue
            r,q=self.carry[exp]; T=self.market.exposure(date,exp).calendar_time
            F=spot*np.exp((r-q)*T); K=g.strike.to_numpy(); call=g.cp_flag.eq('C').to_numpy()
            iv=invert_iv(F,K,T,r,out.loc[g.index].to_numpy(),call)
            m,c=self.corrections[exp]
            out.loc[g.index]=bsm(F,K,T,r,np.maximum(.001,iv+np.interp(np.log(K/F),m,c)),call)
        return out

    def deltas(self,rows):
        eps=self.spot*.001
        return (self.prices(rows,spot=self.spot+eps)-self.prices(rows,spot=self.spot-eps))/(2*eps)

    def sensitivity(self,rows,component): return self.base.sensitivity(rows,component)


def grid_check(s):
    failures=0; total=0
    for exp,(m,_) in s.baseline_iv.items():
        r,q=s.carry[exp]; T=s.market.exposure(s.date,exp).calendar_time
        F=s.spot*np.exp((r-q)*T)
        K=np.linspace(F*np.exp(min(m)),F*np.exp(max(m)),101)
        rows=pd.DataFrame(dict(strike=K,exdate=exp,cp_flag='C'))
        p=s.prices(rows).to_numpy(); tol=1e-7*s.spot
        # Necessary strike restrictions only; not a full American/calendar audit.
        bad=(np.diff(p)>tol).any() or (np.diff(p,2)<-tol).any()
        bad=bad or (p<np.maximum(s.spot*np.exp(-q*T)-K*np.exp(-r*T),0)-tol).any()
        failures+=int(bad); total+=1
    return failures,total


def worker(args):
    sid,data,old,output,limit=args
    protocol=Protocol(); market=MarketData(data,protocol.end)
    fits=pd.read_csv(Path(old)/'fits.csv'); fits=fits[fits.sid.eq(sid)]
    if limit: fits=fits.head(limit)
    previous=pd.read_pickle(Path(old)/'predictions.pkl'); previous=previous[previous.secid.eq(sid)]
    quotes=market.quotes(sid); frames={d:g for d,g in quotes.groupby('date')}
    predictions=[]; records=[]; states=[]; grids=[]
    for i,f in enumerate(fits.itertuples()):
        date=pd.Timestamp(f.date); raw=frames[date]
        weights=ClockWeights(f.overnight,f.weekend,f.holiday)
        base,chosen,event=prepare_surface(raw,sid,date,market,protocol,weights)
        ids=previous.loc[previous.date.eq(date),'optionid']
        targets=raw[raw.optionid.isin(ids)].copy()
        assert len(targets)==len(ids) and not set(targets.strike_price)&base.reference_strikes
        row=targets[['date','secid','optionid','exdate','strike','cp_flag','mid','best_bid','best_offer','halfspread']].copy()
        row['spot']=base.spot
        state=dict(sid=sid,date=date,weights=weights,variants={})
        for clock,w in [('calendar',ClockWeights(1,1,1)),('physical',weights)]:
            for flat in [True,False]:
                for events in [False,True]:
                    name=f'{clock}_{"flat" if flat else "heston"}_{"jump" if events else "no_jump"}'
                    s,diag=fit_variant(base,chosen,event,flat,events,w,protocol)
                    px=variant_prices(s,targets,flat,events)
                    hi=variant_prices(s,targets,flat,events,2*protocol.cos_terms)
                    row[name]=px; row[name+'_numerical_ok']=(px-hi).abs()<=np.maximum(.01,.25*targets.halfspread)
                    records.append(dict(sid=sid,date=date,variant=name,fit_rmse=s.fit_rmse,
                        sigma=s.parameters[0],xi=s.parameters[1],rho=s.parameters[2],event_scale=s.parameters[3],
                        event_identified=event,**diag))
                    state['variants'][name]=(s.parameters,s.fit_rmse)
                    if not flat and events:
                        overlay=OverlaySurface(s,chosen)
                        row[clock+'_hybrid']=overlay.prices(targets)
                        bad,n=grid_check(overlay)
                        grids.append(dict(sid=sid,date=date,variant=clock+'_hybrid',bad=bad,total=n))
            # Interpolation uses the identical references and forwards for both clocks.
        row['interpolation']=base.benchmark(targets)
        bad,n=grid_check(OverlaySurface(base,chosen,False))
        grids.append(dict(sid=sid,date=date,variant='interpolation',bad=bad,total=n))
        predictions.append(row); states.append(state)
        if i%30==0: print(market.names[sid],i+1,'/',len(fits),flush=True)
    output=Path(output); output.mkdir(parents=True,exist_ok=True)
    pd.concat(predictions).to_pickle(output/f'predictions_{sid}.pkl')
    pd.DataFrame(records).to_pickle(output/f'fits_{sid}.pkl')
    pd.DataFrame(grids).to_pickle(output/f'grids_{sid}.pkl')
    pd.to_pickle(states,output/f'states_{sid}.pkl')
    return sid


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--data',required=True); p.add_argument('--old',required=True)
    p.add_argument('--output',required=True); p.add_argument('--limit',type=int); p.add_argument('--workers',type=int,default=3)
    a=p.parse_args(); sids=pd.read_csv(Path(a.old)/'fits.csv').sid.unique()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for sid in pool.map(worker,[(int(s),a.data,a.old,a.output,a.limit) for s in sids]): print('complete',sid,flush=True)
