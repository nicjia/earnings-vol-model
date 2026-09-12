"""Prepare earlier identifiable reference calibrations without using hedge outcomes."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
import pandas as pd
from variance_clock import ClockWeights
from strategy_lab.protocol import Protocol
from strategy_lab.data import MarketData
from strategy_lab.model import prepare_surface
from strategy_lab.ablation import fit_variant


def worker(args):
    sid,data,output,end=args;p=replace(Protocol(),end=end);m=MarketData(data,end)
    frames={d:g for d,g in m.quotes(sid).groupby('date')};states=[];failures=Counter()
    for date,raw in frames.items():
        if date>pd.Timestamp(end) or date.to_datetime64() in m.events[sid]:continue
        # The event-hedging rule only transports anchors from this past window.
        if not any(0<(pd.Timestamp(e)-date).days<=40 for e in m.events[sid]):continue
        try:
            base,ref,event=prepare_surface(raw,sid,date,m,p,ClockWeights(1,1,1))
            fit,diagnostic=fit_variant(base,ref,event,False,True,ClockWeights(1,1,1),p)
            if not diagnostic['converged']:failures['optimizer_not_converged']+=1;continue
            states.append(dict(sid=sid,date=date,weights=ClockWeights(1,1,1),
                variants={'calendar_heston_jump':(fit.parameters,fit.fit_rmse)}))
        except ValueError as err:failures[str(err)]+=1
    Path(output).mkdir(parents=True,exist_ok=True);pd.to_pickle(states,Path(output)/f'states_{sid}.pkl')
    print('confirmation states',m.names[sid],len(states),dict(failures),flush=True)
    return sid


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--output',required=True);p.add_argument('--end',default='2025-12-31')
    a=p.parse_args();m=MarketData(a.data,a.end)
    with ProcessPoolExecutor(max_workers=3) as pool:
        for sid in pool.map(worker,[(s,a.data,a.output,a.end) for s in m.names]):print('states complete',sid,flush=True)
