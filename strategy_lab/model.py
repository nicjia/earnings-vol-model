"""Reference-only Heston + scheduled-mixture calibration and held-strike pricing.

Restricted Heston: theta=v0, kappa=2; fit sigma, xi, rho, event scale. Jump shape
is fixed in the protocol (85% core, 15% wider downside component). This is a
specified candidate model, not a claim of optimal parameterization.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.special import ndtr
from cos_pricer import heston_cf, mixture_cf
from earnings_mixture import EarningsMixtureJump, MixtureComponent
from variance_clock import ClockWeights
from .protocol import is_target


def bsm(F,K,T,r,iv,call):
    sd=np.maximum(np.asarray(iv)*np.sqrt(T),1e-10)
    d1=(np.log(F/K)+sd*sd/2)/sd; d2=d1-sd
    c=np.exp(-r*T)*(F*ndtr(d1)-K*ndtr(d2))
    return np.where(call,c,c-np.exp(-r*T)*(F-K))


def invert_iv(F,K,T,r,prices,call):
    lo=np.full(len(K),.001); hi=np.full(len(K),4.)
    for _ in range(40):
        mid=(lo+hi)/2; px=bsm(F,K,T,r,mid,call)
        lo=np.where(px<prices,mid,lo); hi=np.where(px>=prices,mid,hi)
    return (lo+hi)/2


def jump(scale):
    return EarningsMixtureJump([MixtureComponent(.85,0,.6*scale),
                               MixtureComponent(.15,-.5*scale,1.8*scale)])


def cos_batch(S,K,call,T,tv,r,q,parameters,n_events,N=128,flat=False):
    """Vectorized bounded-put COS; same model as the public Heston/jump engine."""
    sig,xi,rho,j=parameters
    def cf(u):
        value=(np.exp(-.5*sig*sig*tv*(u*u+1j*u)) if flat else
               heston_cf(u,tv,0,0,sig*sig,2.,sig*sig,xi,rho)) * np.exp(1j*u*(r-q)*T)
        if n_events and j>0: value*=mixture_cf(u,jump(j))**n_events
        return value
    h=1e-4; z=np.log(cf(np.array([h,-h])))
    mean=float(np.imag(z[0]-z[1])/(2*h))
    var=max(float(-np.real(z.sum())/(h*h)),1e-7)
    width=12*np.sqrt(var)+n_events*6*j
    a,b=mean-width,mean+width
    k=np.arange(N); u=k*np.pi/(b-a)
    density=np.real(cf(u)*np.exp(-1j*u*a)); density[0]*=.5
    upper=np.clip(np.log(K/S),a,b)[:,None]
    uu=u[None,:]; angle=uu*(upper-a)
    psi=np.zeros((len(K),N)); psi[:,0]=upper[:,0]-a
    psi[:,1:]=np.sin(angle[:,1:])/uu[:,1:]
    chi=(np.exp(upper)*(np.cos(angle)+uu*np.sin(angle))-np.exp(a))/(1+uu*uu)
    put=np.exp(-r*T)*2/(b-a)*((K[:,None]*psi-S*chi)@density)
    return np.where(call,put+S*np.exp(-q*T)-K*np.exp(-r*T),put)


@dataclass
class Surface:
    date: pd.Timestamp
    sid: int
    spot: float
    parameters: np.ndarray
    weights: ClockWeights
    carry: dict
    reference_ids: frozenset
    reference_strikes: frozenset
    baseline_iv: dict
    fit_rmse: float
    market: object
    terms: int

    def prices(self,rows,date=None,spot=None,parameters=None,weights=None):
        date=self.date if date is None else pd.Timestamp(date)
        spot=self.spot if spot is None else spot
        out=pd.Series(np.nan,index=rows.index,dtype=float)
        par=self.parameters if parameters is None else parameters
        for exp,g in rows.groupby('exdate'):
            if exp not in self.carry: continue
            if self.market.expiry_time(exp)<=self.market.close_time(date):
                out.loc[g.index]=np.where(g.cp_flag.eq('C'),np.maximum(spot-g.strike,0),np.maximum(g.strike-spot,0)); continue
            x=self.market.exposure(date,exp); T=x.calendar_time
            r,q=self.carry[exp]
            n=sum(date<pd.Timestamp(e)<=exp for e in self.market.events[self.sid])
            out.loc[g.index]=cos_batch(spot,g.strike.to_numpy(),g.cp_flag.eq('C').to_numpy(),
                T,x.variance_time(self.weights if weights is None else weights),r,q,par,n,self.terms)
        return out

    def deltas(self,rows):
        eps=self.spot*.001
        return (self.prices(rows,spot=self.spot+eps)-self.prices(rows,spot=self.spot-eps))/(2*eps)

    def sensitivity(self,rows,component):
        p=self.parameters.copy(); index=0 if component=='diffusion' else 3
        h=.001; p[index]+=h
        return (self.prices(rows,parameters=p)-self.prices(rows))/h

    def benchmark(self,rows,date=None,spot=None):
        date=self.date if date is None else pd.Timestamp(date)
        spot=self.spot if spot is None else spot
        out=pd.Series(np.nan,index=rows.index)
        for exp,g in rows.groupby('exdate'):
            if exp not in self.baseline_iv: continue
            r,q=self.carry[exp]; T=self.market.exposure(date,exp).calendar_time
            F=spot*np.exp((r-q)*T)
            m,iv=self.baseline_iv[exp]
            interp=np.interp(np.log(g.strike/F),m,iv)
            out.loc[g.index]=bsm(F,g.strike.to_numpy(),T,r,interp,g.cp_flag.eq('C').to_numpy())
        return out


def prepare_surface(raw,sid,date,market,protocol,weights,require_event_identification=True):
    # Split BEFORE every filtering/calibration operation. Targets cannot affect
    # forwards, initialization, fit weights, selected expirations or parameters.
    ref=raw[~raw.strike_price.map(lambda k:is_target(sid,k,protocol.target_modulus))].copy()
    spot=float(market.stock.loc[(sid,date),'close'])
    ref=ref[(ref.best_bid>0)&(ref.best_offer>=ref.best_bid)&(ref.halfspread/ref.mid<.25)]
    ref=ref[(ref.strike/spot).between(.75,1.25)]
    ref=ref[(ref.exdate-date).dt.days.between(protocol.min_dte,protocol.max_dte)]
    ref=ref[~ref.exdate.isin(market.events[sid])]
    carry={}; groups=[]; baseline={}
    for exp,g in ref.groupby('exdate'):
        pair=g.pivot_table(index='strike',columns='cp_flag',values='mid',aggfunc='first').dropna()
        if not {'C','P'}.issubset(pair.columns) or len(pair)<3: continue
        T=market.exposure(date,exp).calendar_time; r=market.rate(date,T)
        near=pair.iloc[np.argsort(abs(pair.index.to_numpy()/spot-1))[:5]]
        F=float(np.median(near.index.to_numpy()+np.exp(r*T)*(near.C-near.P)))
        if not .9< F/spot <1.1: continue
        q=r-np.log(F/spot)/T
        g=g[((g.cp_flag=='C')&(g.strike>=F))|((g.cp_flag=='P')&(g.strike<F))].sort_values('strike')
        if len(g)<4: continue
        ix=np.unique(np.linspace(0,len(g)-1,min(len(g),protocol.max_references_per_expiry)).round().astype(int))
        g=g.iloc[ix].copy()
        iv=invert_iv(F,g.strike.to_numpy(),T,r,g.mid.to_numpy(),g.cp_flag.eq('C').to_numpy())
        carry[exp]=(r,q); baseline[exp]=(np.log(g.strike.to_numpy()/F),iv)
        groups.append((exp,g))
    if len(groups)>protocol.max_expirations:
        ix=np.unique(np.linspace(0,len(groups)-1,protocol.max_expirations).round().astype(int)); groups=[groups[i] for i in ix]
    if len(groups)<protocol.minimum_expirations: raise ValueError('insufficient reference expirations')
    chosen=pd.concat([g for _,g in groups])
    if len(chosen)<protocol.minimum_references: raise ValueError('insufficient reference quotes')
    carry={exp:carry[exp] for exp,_ in groups}; baseline={exp:baseline[exp] for exp,_ in groups}
    surface=Surface(date,sid,spot,np.array([.4,.5,-.4,.04]),weights,carry,
        frozenset(chosen.optionid.astype(int)),frozenset(ref.strike_price.astype(int)),baseline,0.,market,protocol.cos_terms)
    has_event=any(date<pd.Timestamp(e)<=max(carry) for e in market.events[sid])
    # Event parameter not identified without an expiry before and after the next event.
    next_events=[pd.Timestamp(e) for e in market.events[sid] if pd.Timestamp(e)>date]
    identified=bool(next_events and min(carry)<min(next_events)<max(carry))
    fit_event=has_event and identified
    # If all reference expiries contain an event, do not invent its decomposition.
    if has_event and not identified and require_event_identification: raise ValueError('event variance not separately identified')
    return surface, chosen, fit_event


def fit_surface(raw,sid,date,market,protocol,weights):
    surface,chosen,fit_event=prepare_surface(raw,sid,date,market,protocol,weights)
    spot=surface.spot
    initial=np.array([.4,.5,-.4,.04] if fit_event else [.4,.5,-.4])
    lows=[.05,.03,-.95]+([.0001] if fit_event else [])
    highs=[2.,2.5,.3]+([.4] if fit_event else [])
    scale=np.maximum(chosen.halfspread.to_numpy(),spot*.0005)
    def resid(par):
        full=np.r_[par,0.] if not fit_event else par
        return (surface.prices(chosen,parameters=full).to_numpy()-chosen.mid.to_numpy())/scale
    fit=least_squares(resid,initial,bounds=(lows,highs),max_nfev=protocol.max_fit_evaluations,
                      loss='soft_l1',ftol=1e-5,xtol=1e-5,gtol=1e-5)
    surface.parameters=np.r_[fit.x,0.] if not fit_event else fit.x
    surface.fit_rmse=float(np.sqrt(np.mean((surface.prices(chosen)-chosen.mid)**2)))
    if not np.isfinite(surface.parameters).all(): raise ValueError('nonfinite fit')
    # Calibration convergence is recorded by caller; a finite truncated solve is
    # permitted as a specified research estimator, not labeled an exact optimum.
    surface.fit_success=bool(fit.success)
    return surface
