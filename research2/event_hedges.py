"""Transport the last identifiable event fit into a delayed earnings hedge.

Fixed target + reference option + stock; compare delta-vega, event sensitivity,
and scenario covariance. Scheduled dates are retrospective in these data.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import ndtr
from numpy.polynomial.hermite import hermgauss
from variance_clock import ClockWeights
from strategy_lab.data import MarketData
from strategy_lab.protocol import Protocol,is_target
from strategy_lab.model import prepare_surface,invert_iv,jump


def cov_hedge(stock,option,target,weights):
    X=np.column_stack([stock,option]);X-=weights@X;y=target-weights@target
    scale=np.sqrt(weights@(X*X));scale=np.maximum(scale,1e-8);Z=X/scale
    beta=np.linalg.solve(Z.T@(weights[:,None]*Z)+1e-5*np.eye(2),Z.T@(weights*y))/scale
    return float(beta[0]),float(beta[1])


def run(data,previous,output,end='2020-12-10'):
    from dataclasses import replace
    output=Path(output);output.mkdir(parents=True,exist_ok=True);p=replace(Protocol(),end=end);market=MarketData(data,p.end)
    results=[];counts={};node,weight=hermgauss(16);weight=weight/np.sqrt(np.pi)
    for sid in market.names:
        states=pd.read_pickle(Path(previous)/f'states_{sid}.pkl');frames={d:g for d,g in market.quotes(sid).groupby('date')}
        for ee in market.events[sid]:
            e=pd.Timestamp(ee);signal=market.shift(e,-3);entry=market.shift(e,-2);exit_date=market.shift(e,1)
            if signal not in frames or entry not in frames or exit_date not in frames or exit_date>pd.Timestamp(p.end):continue
            eligible=[s for s in states if s['date']<=signal and (signal-s['date']).days<=30 and s['variants']['calendar_heston_jump'][0][3]>.0001]
            if not eligible:continue
            state=max(eligible,key=lambda s:s['date'])
            base,ref,_=prepare_surface(frames[state['date']],sid,state['date'],market,p,ClockWeights(1,1,1))
            base.parameters,base.fit_rmse=state['variants']['calendar_heston_jump']
            base.date=signal;base.spot=float(market.stock.loc[(sid,signal),'close'])
            raw=frames[signal];raw=raw[raw.exdate.isin(base.carry)&raw.exdate.gt(exit_date)&raw.best_bid.gt(0)&(raw.halfspread/raw.mid<.2)]
            raw=raw[(raw.strike/base.spot).between(.9,1.1)]
            references=raw[~raw.strike_price.map(lambda k:is_target(sid,k))]
            if references.empty:continue
            hedge=references.assign(distance=abs(references.strike/base.spot-1)).sort_values(['exdate','distance','cp_flag']).iloc[0]
            targets=raw[raw.strike_price.map(lambda k:is_target(sid,k)) & raw.exdate.gt(hedge.exdate)].copy()
            if targets.empty:continue
            # Metadata-only cap: nearest three target strikes for each call/put,
            # then earliest target expiry. No target return affects selection.
            targets=targets[targets.exdate.eq(targets.exdate.min())]
            targets=targets.assign(distance=abs(targets.strike/base.spot-1)).sort_values('distance').groupby('cp_flag').head(3)
            rows=pd.concat([hedge.to_frame().T,targets],ignore_index=True)
            rows['strike']=rows.strike.astype(float);rows['mid']=rows.mid.astype(float)
            rows['model_delta']=base.deltas(rows);rows['jump_vega']=base.sensitivity(rows,'event')
            for exp,g in rows.groupby('exdate'):
                r,q=base.carry[exp];T=market.exposure(signal,exp).calendar_time;F=base.spot*np.exp((r-q)*T)
                iv=invert_iv(F,g.strike.to_numpy(),T,r,g.mid.to_numpy(),g.cp_flag.eq('C').to_numpy())
                d1=(np.log(F/g.strike.to_numpy())+.5*iv*iv*T)/(iv*np.sqrt(T))
                rows.loc[g.index,'delta']=np.exp(-q*T)*(ndtr(d1)-g.cp_flag.eq('P').to_numpy())
                rows.loc[g.index,'gamma']=np.exp(-q*T)*np.exp(-.5*d1*d1)/np.sqrt(2*np.pi)/(base.spot*iv*np.sqrt(T))
                rows.loc[g.index,'vega']=base.spot*np.exp(-q*T)*np.exp(-.5*d1*d1)/np.sqrt(2*np.pi)*np.sqrt(T)
            horizon=market.exposure(signal,exit_date).calendar_time
            mix=jump(base.parameters[3]);sigma=base.parameters[0]
            shocks=np.concatenate([np.exp(mu-.5*sigma*sigma*horizon+np.sqrt(2*(sd*sd+sigma*sigma*horizon))*node)
                                   for mu,sd in zip(mix.mu,mix.s)])
            probs=np.concatenate([w*weight for w in mix.w]);scenario_spots=base.spot*shocks
            scenario_values=np.vstack([base.prices(rows,date=exit_date,spot=s).to_numpy() for s in scenario_spots])
            ids=rows.optionid.astype(int).tolist();en=frames[entry].set_index('optionid').reindex(ids);ex=frames[exit_date].set_index('optionid').reindex(ids)
            s0=float(market.stock.loc[(sid,entry),'close']);s1=float(market.stock.loc[(sid,exit_date),'close'])
            for j in range(1,len(rows)):
                h0=rows.iloc[0];t=rows.iloc[j]
                vh=float(t.vega/h0.vega)
                gh=float(t.gamma/h0.gamma)
                eh=float(t.jump_vega/h0.jump_vega) if abs(h0.jump_vega)>1e-6 else vh
                stock,option=cov_hedge(scenario_spots,scenario_values[:,0],scenario_values[:,j],probs)
                positions={'delta':(float(t.delta),0.),'delta_vega':(float(t.delta-vh*h0.delta),vh),
                    'delta_gamma':(float(t.delta-gh*h0.delta),gh),'unit_option':(float(t.delta-h0.delta),1.),
                    'event_match':(float(t.delta-eh*h0.delta),eh),'event_scenario':(stock,option)}
                for variant,(stock,option) in positions.items():
                    record=dict(sid=sid,event=str(e),signal=str(signal),entry=str(entry),exit=str(exit_date),
                        fit_date=str(state['date']),target=int(t.optionid),hedge=int(h0.optionid),variant=variant,
                        stock_hedge=stock,option_hedge=option)
                    valid=(np.isfinite(en.iloc[[0,j]].mid).all() and np.isfinite(ex.iloc[[0,j]].mid).all()
                        and (en.iloc[[0,j]].best_offer>=en.iloc[[0,j]].best_bid).all()
                        and (ex.iloc[[0,j]].best_offer>=ex.iloc[[0,j]].best_bid).all()
                        and np.array_equal(en.strike.to_numpy(),rows.strike.to_numpy())
                        and np.array_equal(ex.strike.to_numpy(),rows.strike.to_numpy())
                        and np.array_equal(en.cp_flag.to_numpy(),rows.cp_flag.to_numpy())
                        and np.array_equal(ex.cp_flag.to_numpy(),rows.cp_flag.to_numpy())
                        and market.stock.loc[(sid,entry),'cfadj']==market.stock.loc[(sid,exit_date),'cfadj'])
                    if not valid:results.append(dict(record,status='unresolved'));continue
                    if abs(option)>5 or abs(stock)>5:results.append(dict(record,status='risk_limit'));continue
                    pnl=(ex.iloc[j].mid-en.iloc[j].mid)-option*(ex.iloc[0].mid-en.iloc[0].mid)-stock*(s1-s0)
                    hedge_cost=abs(option)*(en.iloc[0].halfspread+ex.iloc[0].halfspread+.033)+abs(stock)*(s0+s1)*.0002
                    results.append(dict(record,status='scored',error=float(pnl/s0),hedge_cost=float(hedge_cost/s0)))
        print('event hedges',market.names[sid],len(results),flush=True)
    (output/'event_hedges.json').write_text(json.dumps(results,indent=2))
    frame=pd.DataFrame(results);frame=frame[frame.status.eq('scored')]
    common=frame.groupby(['sid','event','target']).variant.nunique();common=common[common.eq(6)].index
    frame=frame.set_index(['sid','event','target']).loc[common].reset_index()
    summary=[]
    for v,g in frame.groupby('variant'):
        per=g.assign(squared=g.error*g.error,absolute=g.error.abs()).groupby(['sid','event'])[['squared','absolute','hedge_cost']].mean()
        summary.append(dict(variant=v,events=len(per),positions=len(g),event_mse=per.squared.mean(),
            event_mae_bp=10000*per.absolute.mean(),hedge_cost_bp=10000*per.hedge_cost.mean(),p95_abs_bp=10000*g.error.abs().quantile(.95)))
    pd.DataFrame(summary).to_csv(output/'event_hedge_summary.csv',index=False);print(pd.DataFrame(summary).to_string(index=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--previous',required=True);p.add_argument('--output',required=True);p.add_argument('--end',default='2020-12-10')
    a=p.parse_args();run(a.data,a.previous,a.output,a.end)
