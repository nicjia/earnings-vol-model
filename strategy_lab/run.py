"""Run calibration exploration: python -m strategy_lab.run --data PATH --output PATH.

No live orders. The protocol's later evaluation period remains inaccessible.
"""
from pathlib import Path
from dataclasses import asdict
from collections import Counter
import argparse
import hashlib
import json
import time
import numpy as np
import pandas as pd
from variance_clock import ClockWeights
from .protocol import Protocol, STRATEGIES, is_target
from .data import MarketData
from .model import fit_surface
from .strategies import proposals, session_proposals
from .execution import simulate, simulate_session


def score_targets(raw,surface,calendar_surface,protocol):
    q=raw[raw.strike_price.map(lambda k:is_target(surface.sid,k,protocol.target_modulus))].copy()
    q=q[q.exdate.isin(surface.carry)&(q.strike/surface.spot).between(.8,1.2)]
    q=q[(q.best_bid>=0)&(q.best_offer>=q.best_bid)&q.mid.gt(.01)]
    # Metadata-only cap, equal spacing in strike for each expiry/call-put group.
    keep=[]
    for _,g in q.groupby(['exdate','cp_flag']):
        g=g.sort_values('strike')
        ix=np.unique(np.linspace(0,len(g)-1,min(12,len(g))).round().astype(int))
        keep.append(g.iloc[ix])
    if not keep: return pd.DataFrame()
    q=pd.concat(keep)
    assert not set(q.strike_price)&surface.reference_strikes
    q['theory']=surface.prices(q)
    q['baseline']=surface.benchmark(q)
    q['calendar_theory']=calendar_surface.prices(q) if calendar_surface is not None else np.nan
    q['model_delta']=surface.deltas(q)
    q['diffusion_sensitivity']=surface.sensitivity(q,'diffusion')
    q['event_sensitivity']=surface.sensitivity(q,'event')
    old=surface.terms; surface.terms=2*old
    high=surface.prices(q); surface.terms=old
    q['numerical_error']=(high-q.theory).abs()
    q['numerical_ok']=q.numerical_error<=np.maximum(.01,.25*q.halfspread)
    q['spot']=surface.spot
    return q


def run(data_root,output,sids=None,max_dates=None,intraday=None):
    protocol=Protocol(); output=Path(output); output.mkdir(parents=True,exist_ok=True)
    market=MarketData(data_root,protocol.end)
    manifest=dict(protocol=asdict(protocol),protocol_hash=protocol.fingerprint(),
        data_manifest=market.manifest,mode='calibration exploration only',
        target_split='SHA256(secid,strike_price) % 3 == 0; all cp/expiry/date twins withheld',
        execution='one-session-lag close quotes; fixed identities; unresolved exits retained',
        clock='past underlying interval variance ratios; physical prior, not separately estimated Q weights',
        estimator='restricted Heston theta=v0 kappa=2 + fixed core/tail scheduled jump shape',
        source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
        selection_note='six names chosen for non-dividend status during 2020; not a market-wide sample',
        prospectively_untouched_test=False)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    if intraday:
        bars=pd.read_csv(intraday)
        bars['timestamp']=pd.to_datetime(bars.timestamp,utc=True); bars['exdate']=pd.to_datetime(bars.exdate)
        bars=bars[bars.timestamp.dt.date<=pd.Timestamp(protocol.end).date()]
    else: bars=None
    results=[]; predictions=[]; future_predictions=[]; fits=[]; audits=[]
    failures=Counter(); started=time.monotonic()
    for sid in (list(market.names) if sids is None else sids):
        print('loading',market.names[sid],flush=True)
        q=market.quotes(sid)
        q=q[q.date.between(protocol.start,protocol.end)]
        frames={pd.Timestamp(d):g for d,g in q.groupby('date')}
        surfaces={}; candidates=[]; session_candidates=[]
        dates=sorted(frames)
        if max_dates: dates=dates[:max_dates]
        for i,date in enumerate(dates):
            if date.to_datetime64() in market.events[sid]:
                failures['announcement_day_timestamp_unknown']+=1; continue
            prior=market.physical_clock(sid,date,protocol.minimum_history)
            if prior is None:
                failures['insufficient_prior_clock_intervals']+=1; continue
            weights,physical_rate,n_prior=prior
            try:
                model=fit_surface(frames[date],sid,date,market,protocol,weights)
                calendar=fit_surface(frames[date],sid,date,market,protocol,ClockWeights(1,1,1))
            except (ValueError,KeyError,FloatingPointError) as err:
                failures[str(err)]+=1; continue
            scored=score_targets(frames[date],model,calendar,protocol)
            if scored.empty: failures['no_withheld_targets']+=1; continue
            surfaces[date]=model
            fit=dict(sid=sid,date=str(date.date()),sigma=model.parameters[0],xi=model.parameters[1],
                rho=model.parameters[2],event_scale=model.parameters[3],fit_rmse=model.fit_rmse,
                converged=model.fit_success,n_references=len(model.reference_ids),n_targets=len(scored),
                prior_intervals=n_prior,**asdict(weights))
            fits.append(fit)
            audits.append(dict(sid=sid,date=str(date.date()),reference_optionids=sorted(model.reference_ids),
                target_optionids=scored.optionid.astype(int).tolist(),
                reference_strikes=sorted(model.reference_strikes),target_strikes=sorted(set(scored.strike_price)),
                reference_latest_timestamp=market.close_time(date).isoformat(),
                clock_data_strictly_before=str(date.date())))
            columns=['date','secid','optionid','exdate','strike','cp_flag','best_bid','best_offer','mid',
                     'halfspread','theory','baseline','calendar_theory','spot','numerical_error','numerical_ok']
            predictions.extend(scored[columns].to_dict('records'))
            accepted=scored[scored.numerical_ok].copy()
            candidates.extend(proposals(accepted,model,protocol))
            session_candidates.extend(session_proposals(accepted,model,protocol,physical_rate))
            # Future repricing: parameters frozen before the outcome, same
            # contracts chosen now. New spot is supplied only at scoring time;
            # explicitly conditional repricing, not a forecast of stock direction.
            next_date=market.shift(date,1)
            if next_date in frames and next_date.to_datetime64() not in market.events[sid]:
                nxt=frames[next_date].set_index('optionid')
                ids=scored.optionid.to_numpy()
                available=nxt.reindex(ids).copy(); available['optionid']=ids
                available=available.reset_index(drop=True)
                meta=scored.reset_index(drop=True).copy()
                new_spot=float(market.stock.loc[(sid,next_date),'close'])
                values=model.prices(meta,date=next_date,spot=new_spot).to_numpy()
                iv_values=model.benchmark(meta,date=next_date,spot=new_spot).to_numpy()
                old_factor=market.stock.loc[(sid,date),'cfadj']; new_factor=market.stock.loc[(sid,next_date),'cfadj']
                for j,row in meta.iterrows():
                    quote=available.iloc[j]
                    valid=(pd.notna(quote.mid) and quote.strike==row.strike and old_factor==new_factor
                           and quote.best_bid>=0 and quote.best_offer>=quote.best_bid)
                    future_predictions.append(dict(sid=sid,prediction_date=date,target_date=next_date,
                        optionid=int(row.optionid),predicted=values[j],actual=float(quote.mid) if valid else np.nan,
                        frozen_reference_iv=iv_values[j],persistence=float(row.mid),spot=new_spot,
                        status='scored' if valid else 'unresolved'))
            if i%15==0:
                print(market.names[sid],str(date.date()),'fits',len(surfaces),'plans',len(candidates),
                      'elapsed_s',round(time.monotonic()-started),flush=True)
        busy={name:pd.Timestamp.min for name in STRATEGIES}
        for plan in sorted(candidates,key=lambda p:(p.signal_date,p.strategy)):
            if plan.signal_date<busy[plan.strategy]:
                failures['overlapping_same_book_signal']+=1; continue
            result=simulate(plan,frames,surfaces,market,protocol)
            results.append(result)
            if result['status']=='closed': busy[plan.strategy]=pd.Timestamp(result['exit_date'])
            elif result['status'] in ['unresolved','censored']: busy[plan.strategy]=pd.Timestamp(protocol.end)
            else: busy[plan.strategy]=plan.entry_date
        if bars is not None:
            for plan in session_candidates: results.append(simulate_session(plan,bars,protocol))
        print('completed',market.names[sid],'daily plans',len(candidates),
              'session signals requiring open quotes',len(session_candidates),flush=True)
        # Checkpoint every name, so a long run can be inspected without rerunning.
        pd.DataFrame(predictions).to_pickle(output/'predictions.pkl')
        pd.DataFrame(future_predictions).to_pickle(output/'future_repricing.pkl')
        pd.DataFrame(fits).to_csv(output/'fits.csv',index=False)
        (output/'trades.json').write_text(json.dumps(results,indent=2,default=str))
        (output/'split_audits.json').write_text(json.dumps(audits,default=str))
        (output/'coverage.json').write_text(json.dumps(dict(failures=failures,
            intraday_status='provided' if bars is not None else 'blocked: opening option quotes absent'),indent=2))
    from .report import write_report
    write_report(output)
    print('report',output/'REPORT.md',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data',required=True); p.add_argument('--output',required=True)
    p.add_argument('--sids',type=int,nargs='+'); p.add_argument('--max-dates',type=int)
    p.add_argument('--intraday-quotes')
    a=p.parse_args(); run(a.data,a.output,a.sids,a.max_dates,a.intraday_quotes)
