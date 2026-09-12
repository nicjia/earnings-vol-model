"""Replay original strategy rules with alternative marks, without threshold search."""
import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from variance_clock import ClockWeights
from .ablation import OverlaySurface
from .model import prepare_surface
from .data import MarketData
from .protocol import Protocol
from .strategies import proposals
from .execution import simulate


def worker(args):
    sid,data,results=args; results=Path(results); p=Protocol(); market=MarketData(data,p.end)
    states=pd.read_pickle(results/f'states_{sid}.pkl')
    pred=pd.read_pickle(results/f'predictions_{sid}.pkl')
    quotes=market.quotes(sid); frames={d:g for d,g in quotes.groupby('date')}
    views=['calendar_structural','physical_hybrid','calendar_hybrid','interpolation']
    models={v:{} for v in views}; candidates={v:[] for v in views}; future=[]
    for i,state in enumerate(states):
        date=state['date']; raw=frames[date]; old=pred[pred.date.eq(date)]
        chosen_targets=raw[raw.optionid.isin(old.optionid)].copy()
        bases={}; refs={}
        for clock,w in [('physical',state['weights']),('calendar',ClockWeights(1,1,1))]:
            base,ref,_=prepare_surface(raw,sid,date,market,p,w)
            base.parameters,base.fit_rmse=state['variants'][clock+'_heston_jump']
            bases[clock]=base; refs[clock]=ref
        surfaces=dict(calendar_structural=bases['calendar'],
            physical_hybrid=OverlaySurface(bases['physical'],refs['physical']),
            calendar_hybrid=OverlaySurface(bases['calendar'],refs['calendar']),
            interpolation=OverlaySurface(bases['calendar'],refs['calendar'],False))
        for view,s in surfaces.items():
            models[view][date]=s
            scored=chosen_targets.copy(); scored['theory']=s.prices(scored)
            scored['model_delta']=s.deltas(scored)
            scored['diffusion_sensitivity']=s.sensitivity(scored,'diffusion')
            scored['event_sensitivity']=s.sensitivity(scored,'event')
            # All views use the intersection of the two structural numerical
            # screens. No result-dependent eligibility advantage to a view.
            ok=old.set_index('optionid')[['calendar_heston_jump_numerical_ok','physical_heston_jump_numerical_ok']].all(axis=1)
            scored=scored[scored.optionid.map(ok).fillna(False)]
            candidates[view].extend(proposals(scored,s,p))
            nxt=market.shift(date,1)
            if nxt not in frames or nxt>pd.Timestamp(p.end) or nxt.to_datetime64() in market.events[sid]: continue
            spot=float(market.stock.loc[(sid,nxt),'close'])
            available=frames[nxt].set_index('optionid').reindex(chosen_targets.optionid).reset_index()
            valid=(available.strike.to_numpy()==chosen_targets.strike.to_numpy()) & available.best_bid.ge(0).to_numpy()
            valid &= available.best_offer.ge(available.best_bid).to_numpy()
            valid &= market.stock.loc[(sid,date),'cfadj']==market.stock.loc[(sid,nxt),'cfadj']
            px=s.prices(chosen_targets,date=nxt,spot=spot).to_numpy()
            future.append(pd.DataFrame(dict(sid=sid,date=date,target_date=nxt,view=view,
                optionid=chosen_targets.optionid.to_numpy(),spot=spot,predicted=px,
                actual=np.where(valid,available.mid,np.nan))))
        if i%45==0: print('replay',market.names[sid],i+1,'/',len(states),flush=True)
    trades=[]; skipped=Counter()
    for view in views:
        busy={}
        for plan in sorted(candidates[view],key=lambda p:(p.signal_date,p.strategy)):
            if plan.signal_date<busy.get(plan.strategy,pd.Timestamp.min):
                skipped[view+':overlap']+=1; continue
            result=simulate(plan,frames,models[view],market,p); result['view']=view; trades.append(result)
            busy[plan.strategy]=(pd.Timestamp(result['exit_date']) if result['status']=='closed' else
                pd.Timestamp(p.end) if result['status'] in ['unresolved','censored'] else plan.entry_date)
    (results/f'replay_{sid}.json').write_text(json.dumps(trades,indent=2,default=str))
    pd.concat(future).to_pickle(results/f'future_{sid}.pkl')
    (results/f'replay_coverage_{sid}.json').write_text(json.dumps(skipped,indent=2))
    return sid


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--data',required=True); p.add_argument('--results',required=True)
    p.add_argument('--workers',type=int,default=3); a=p.parse_args()
    sids=[int(x.stem.split('_')[1]) for x in Path(a.results).glob('states_*.pkl')]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for sid in pool.map(worker,[(s,a.data,a.results) for s in sids]): print('replay complete',sid,flush=True)
