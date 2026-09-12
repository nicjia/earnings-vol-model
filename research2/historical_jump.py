"""Frozen earnings-jump replacement with past-only histories and delayed fills."""
import argparse,json
from pathlib import Path
from dataclasses import replace
import numpy as np
import pandas as pd
from scipy.special import ndtr
from strategy_lab.data import MarketData
from strategy_lab.protocol import Protocol,is_target
from strategy_lab.model import prepare_surface,invert_iv,bsm
from variance_clock import ClockWeights
from market_surface import MarketSlice

NAMES={'ADBE':101062,'AMD':101121,'AMZN':101310,'GOOGL':121812,'NFLX':115422,'TSLA':143439}
MIXTURE_VARIANCE=.823875
MODELS=["frozen_market_structural","historical_structural","historical_reference_anchored","reference_only","current_market_hybrid","current_market_only","historical_final_anchored"]

def build_history(root,names=None):
    root=Path(root);stocks=pd.concat([pd.read_pickle(p) for p in sorted(root.glob('stocks_*.pkl'))],ignore_index=True)
    stocks.date=pd.to_datetime(stocks.date);stocks['return']=pd.to_numeric(stocks['return'],errors='coerce')
    events=pd.read_pickle(root/'announcements.pkl');events.anndats=pd.to_datetime(events.anndats)
    records=[]
    for name,sid in (NAMES if names is None else names).items():
        s=stocks[stocks.secid.eq(sid)].sort_values('date').drop_duplicates('date').reset_index(drop=True)
        es=sorted(events.loc[events.oftic.eq(name),'anndats'].unique()); dates=s.date
        # Exclude all reported earnings brackets from ordinary-return estimation.
        ordinary=np.ones(len(s),dtype=bool)
        for e in es:
            j=dates.searchsorted(e);ordinary[j:min(j+2,len(s))]=False
        for e in es:
            j=dates.searchsorted(e)
            if j<61 or j+1>=len(s) or (dates.iloc[j]-pd.Timestamp(e)).days>3:continue
            r=s['return'].iloc[j:j+2].to_numpy(float)
            if not np.isfinite(r).all() or np.any(r<=-1):continue
            past=s.iloc[:j].copy();past= past[ordinary[:j]].tail(60)
            x=np.log1p(past['return'].to_numpy(float));x=x[np.isfinite(x)]
            if len(x)<40:continue
            move=float(np.log1p(r).sum()); noise=float(2*np.mean(x*x))
            records.append(dict(sid=sid,name=name,event=pd.Timestamp(e),available=dates.iloc[j+1],log_move=move,ordinary_variance=noise,excess_square=move*move-noise))
    return pd.DataFrame(records)

def forecast(history,sid,signal):
    h=history[history.sid.eq(sid)&history.available.lt(signal)].sort_values('available').tail(8)
    if len(h)<6:return None
    return dict(history_n=len(h),history_last=h.available.max(),historical_variance=max(float(h.excess_square.mean()),0.),historical_rms=float(np.sqrt(np.mean(h.log_move*h.log_move))))

def run(data,states_dir,history_root,output,wide=False,pre_event=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    end=json.loads((Path(data)/'manifest.json').read_text())['end'];p=replace(Protocol(),end=end)
    m=MarketData(data,end);history=build_history(history_root,{name:sid for sid,name in m.names.items()});history.to_pickle(output/'historical_events.pkl')
    candidates=[];coverage=[]
    for sid,name in m.names.items():
        states=pd.read_pickle(Path(states_dir)/f'states_{sid}.pkl')
        frames={d:g for d,g in m.quotes(sid).groupby('date')}
        for ee in m.events[sid]:
            e=pd.Timestamp(ee)
            if e>pd.Timestamp(end) or e<m.stocks.date.min():continue
            signal,entry,exit_date=(m.shift(e,-10),m.shift(e,-9),m.shift(e,-6)) if pre_event else (m.shift(e,-3),m.shift(e,-2),m.shift(e,1))
            audit=dict(sid=sid,name=name,event=e,signal=signal,entry=entry,exit=exit_date)
            if any(d not in frames for d in [signal,entry,exit_date]):coverage.append(dict(audit,status='missing_date'));continue
            f=forecast(history,sid,signal)
            if f is None:coverage.append(dict(audit,status='insufficient_history'));continue
            eligible=[]
            for s in states:
                if s['date']>signal or (signal-s['date']).days>30:continue
                upcoming=[pd.Timestamp(t) for t in m.events[sid] if pd.Timestamp(t)>s['date']]
                if upcoming and min(upcoming)==e and s['variants']['calendar_heston_jump'][0][3]>.0001:eligible.append(s)
            if not eligible:coverage.append(dict(audit,status='no_identifiable_anchor'));continue
            state=max(eligible,key=lambda s:s['date'])
            try:base,ref,_=prepare_surface(frames[signal],sid,signal,m,p,ClockWeights(1,1,1),False)
            except ValueError as exc:coverage.append(dict(audit,status=str(exc)));continue
            base.parameters=state['variants']['calendar_heston_jump'][0].copy()
            raw=frames[signal]
            targets=raw[raw.strike_price.map(lambda k:is_target(sid,k)) & raw.exdate.isin(base.carry) & raw.exdate.gt(e if pre_event else exit_date)
                & (raw.exdate-signal).dt.days.between(8,90 if wide else 45)&(raw.strike/base.spot).between(.8 if wide else .9,1.2 if wide else 1.1)
                &raw.best_bid.gt(0)&raw.best_offer.ge(raw.best_bid)&raw.mid.ge(.25)].copy()
            if targets.empty:coverage.append(dict(audit,status='no_targets'));continue
            if not wide:targets=targets[targets.exdate.eq(targets.exdate.min())].copy()
            targets['distance']=abs(targets.strike/base.spot-1)
            singles=targets.copy() if wide else targets.sort_values(['distance','strike','cp_flag']).groupby('cp_flag').head(3)
            pairs=targets[targets.exdate.eq(targets.exdate.min())].groupby('strike').filter(lambda g:set(g.cp_flag)=={'C','P'})
            straddle=pairs[pairs.strike.eq(pairs.sort_values('distance').iloc[0].strike)] if len(pairs) else pairs
            rows=pd.concat([singles,straddle]).drop_duplicates('optionid').copy()
            par=base.parameters.copy();par[3]=np.sqrt(f['historical_variance']/MIXTURE_VARIANCE)
            rows['frozen_market_structural']=base.prices(rows)
            rows['historical_structural']=base.prices(rows,parameters=par)
            rows['reference_only']=base.benchmark(rows)
            for exp,g in rows.groupby('exdate'):
                r,q=base.carry[exp];T=m.exposure(signal,exp).calendar_time;F=base.spot*np.exp((r-q)*T)
                K=g.strike.to_numpy();call=g.cp_flag.eq('C').to_numpy()
                vi=invert_iv(F,K,T,r,g.frozen_market_structural.to_numpy(),call)
                vh=invert_iv(F,K,T,r,g.historical_structural.to_numpy(),call)
                vb=invert_iv(F,K,T,r,g.reference_only.to_numpy(),call)
                variance=vb*vb+vh*vh-vi*vi
                rows.loc[g.index,'variance_floor']=variance<=1e-8
                rows.loc[g.index,'historical_reference_anchored']=bsm(F,K,T,r,np.sqrt(np.maximum(variance,1e-8)),call)
                reference=ref[ref.exdate.eq(exp)]
                def callback(kk):return base.prices(pd.DataFrame(dict(strike=kk,exdate=exp,cp_flag='C'))).to_numpy()
                for label,cb in [('current_market_hybrid',callback),('current_market_only',None)]:
                    curve=MarketSlice.fit(base.spot,T,reference.strike,reference.mid,reference.cp_flag.eq('C'),reference.halfspread,
                        rate=r,dividend_yield=q,structural_call_price=cb)
                    rows.loc[g.index,label]=curve.price(K,call)
                vf=invert_iv(F,K,T,r,rows.loc[g.index,'current_market_hybrid'].to_numpy(),call)
                rows.loc[g.index,'historical_final_anchored']=bsm(F,K,T,r,np.sqrt(np.maximum(vf*vf+vh*vh-vi*vi,1e-8)),call)
                d1=(np.log(F/K)+.5*vb*vb*T)/(vb*np.sqrt(T))
                rows.loc[g.index,'hedge_delta']=np.exp(-q*T)*(ndtr(d1)-~call)
            indexed=rows.set_index('optionid');en=frames[entry].set_index('optionid');ex=frames[exit_date].set_index('optionid')
            instruments=[('single',[int(i)]) for i in singles.optionid]
            if len(straddle)==2:instruments.append(('straddle',straddle.optionid.astype(int).tolist()))
            coverage.append(dict(audit,status='eligible',fit_date=state['date'],**f))
            for kind,ids in instruments:
                g=indexed.loc[ids];r0=en.reindex(ids);r1=ex.reindex(ids)
                rec=dict(audit,**f,kind=kind,ids=','.join(map(str,ids)),fit_date=state['date'],implied_variance=MIXTURE_VARIANCE*base.parameters[3]**2,
                    legs=len(ids),cp_flag='straddle' if len(ids)==2 else g.cp_flag.iloc[0],signal_mid=float(g.mid.sum()),
                    signal_relative_spread=float(2*g.halfspread.sum()/g.mid.sum()),variance_floor=bool(g.variance_floor.any()))
                for model in MODELS:
                    rec[model]=float(g[model].sum())
                valid=(r0.mid.notna().all() and r1.mid.notna().all() and r0.best_bid.ge(0).all() and r1.best_bid.ge(0).all()
                    and r0.best_offer.ge(r0.best_bid).all() and r1.best_offer.ge(r1.best_bid).all()
                    and np.array_equal(r0.strike,g.strike) and np.array_equal(r1.strike,g.strike)
                    and np.array_equal(r0.cp_flag,g.cp_flag) and np.array_equal(r1.cp_flag,g.cp_flag)
                    and m.stock.loc[(sid,entry),'cfadj']==m.stock.loc[(sid,exit_date),'cfadj'])
                if not valid:candidates.append(dict(rec,status='unresolved'));continue
                s0=float(m.stock.loc[(sid,entry),'close']);s1=float(m.stock.loc[(sid,exit_date),'close'])
                delta=float(g.hedge_delta.sum());premium=float(r0.mid.sum())
                option_move=float(r1.mid.sum()-premium);hedge_move=-delta*(s1-s0)
                rec.update(status='scored',entry_mid=premium,exit_mid=float(r1.mid.sum()),spot=s0,delta=delta,
                    option_move=option_move,hedge_move=hedge_move,entry_quote_delta=float(r0.delta.sum()) if r0.delta.notna().all() else np.nan,stock_change=s1-s0,stock_roundtrip_rate=(s0+s1)*.0002,spread_cost=float(r0.halfspread.sum()+r1.halfspread.sum()),
                    commission=.013*len(ids),stock_cost=abs(delta)*(s0+s1)*.0002,
                    entry_relative_spread=float(2*r0.halfspread.sum()/premium),exit_relative_spread=float(2*r1.halfspread.sum()/max(r1.mid.sum(),.01)))
                candidates.append(rec)
        print(name,'candidates',len(candidates),'events',len(coverage),flush=True)
    pd.DataFrame(candidates).to_pickle(output/'candidates.pkl');pd.DataFrame(coverage).to_csv(output/'coverage.csv',index=False)
    summarize(output,wide=wide)

def summarize(output,wide=False):
    output=Path(output);c=pd.read_pickle(output/'candidates.pkl');trades=[]
    for model in (['current_market_hybrid'] if wide else MODELS+['always_long','always_short']):
        for threshold in ([.05,.10,.20] if wide else [0,.05,.10,.20]):
            if model.startswith('always_') and threshold!=0:continue
            edge=(pd.Series(1. if model=='always_long' else -1.,index=c.index) if model.startswith('always_') else c[model]/c.signal_mid-1)
            selected=c[edge.abs().gt(threshold)].copy();selected['edge']=edge.loc[selected.index]
            selected['side']=np.where(selected.edge>0,'long','short');selected['direction']=np.sign(selected.edge)
            selected['model']=model;selected['threshold']=threshold
            for hedged in [False,True]:
                t=selected.copy();t['hedged']=hedged
                gross=t.direction*(t.option_move+(t.hedge_move if hedged else 0))
                costs=t.commission+(t.stock_cost if hedged else 0)
                for fill,pnl in [('mid_gross',gross),('mid_net',gross-costs),('bidask_net',gross-costs-t.spread_cost)]:
                    z=t.copy();z['fill']=fill;z['pnl_share']=pnl;z['return_premium']=pnl/t.entry_mid;z['return_spot']=pnl/(t.spot*t.legs);trades.append(z)
    trades=pd.concat(trades,ignore_index=True);trades.to_pickle(output/'trades.pkl');summary=[]
    rng=np.random.default_rng(1729)
    for key,g in trades.groupby(['model','threshold','kind','hedged','fill']):
        for side in ['all','long','short']:
            z=g if side=='all' else g[g.side.eq(side)];v=z[z.status.eq('scored')]
            if v.empty:continue
            ev=v.groupby(['sid','event']).return_premium.mean().to_numpy()
            ci=np.quantile(np.mean(rng.choice(ev,(3000,len(ev))),axis=1),[.025,.975])
            summary.append(dict(zip(['model','threshold','kind','hedged','fill'],key),side=side,selected=len(z),closed=len(v),unresolved=len(z)-len(v),events=len(ev),
                mean_premium_pct=100*v.return_premium.mean(),equal_event_pct=100*ev.mean(),ci_low_pct=100*ci[0],ci_high_pct=100*ci[1],
                median_premium_pct=100*v.return_premium.median(),win_pct=100*v.pnl_share.gt(0).mean(),mean_spot_pct=100*v.return_spot.mean(),
                mean_dollars_per_position=100*v.pnl_share.mean(),mean_entry_spread_pct=100*v.entry_relative_spread.mean()))
    pd.DataFrame(summary).to_csv(output/'summary.csv',index=False)
    print('saved',output,flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--data',required=True);a.add_argument('--states',required=True);a.add_argument('--history',required=True);a.add_argument('--output',required=True)
    a.add_argument('--wide',action='store_true')
    a.add_argument('--pre-event',action='store_true')
    x=a.parse_args();run(x.data,x.states,x.history,x.output,x.wide,x.pre_event)
