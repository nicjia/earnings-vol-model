"""Past-only minimum-variance hedge comparisons on reference/target contracts.

Hedge-error research, not option-trading P&L. Uses observed starting option IV
for the practitioner benchmark. The initial option price is available to a
holder deciding how to hedge, even though it is withheld in pricing tests.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def features(rows,variant):
    delta=rows.delta_bs.to_numpy()+rows.cp_flag.eq('P').to_numpy()
    v=rows.vega_scaled.to_numpy(); event=rows.event_fraction.to_numpy()
    near=np.exp(-rows.days_to_event.to_numpy()/7.)
    columns=[v,v*delta,v*delta*delta]
    if variant in ['event','both']: columns += [v*event,v*event*near]
    if variant in ['structural','both']: columns += [(rows.delta_model-rows.delta_bs).to_numpy()]
    return np.column_stack(columns)


def fit_adjustment(train,variant):
    f=features(train,variant); X=f*train.stock_change.to_numpy()[:,None]
    y=(train.actual_change-train.delta_bs*train.stock_change).to_numpy()
    count=train.groupby(['sid','date']).optionid.transform('size').to_numpy()
    w=1/count; w/=w.sum()
    scale=np.sqrt((w[:,None]*X*X).sum(axis=0));scale=np.maximum(scale,1e-8)
    Z=X/scale
    beta=np.linalg.solve(Z.T@(w[:,None]*Z)+.01*np.eye(X.shape[1]),Z.T@(w*y))/scale
    return beta


def run(output):
    output=Path(output)
    files=list(output.glob('hedges_*.pkl'))
    if len(files)!=6: raise ValueError('All six names required')
    panel=pd.concat([pd.read_pickle(p) for p in files],ignore_index=True)
    panel=panel.dropna(subset=['actual_change','delta_bs','delta_model','vega_scaled'])
    results=[];coefficients=[];counts=[]
    for date,test in panel[~panel.reference].groupby('date'):
        train=panel[panel.reference & (panel.target_date<date) & (panel.date>=date-pd.Timedelta(days=120))]
        if train.date.nunique()<30:continue
        test=test.copy();test['bs']=test.delta_bs;test['model']=test.delta_model
        for variant in ['hw','event','structural','both']:
            beta=fit_adjustment(train,variant)
            delta=test.delta_bs.to_numpy()+features(test,variant)@beta
            lower=np.where(test.cp_flag.eq('P'),-1.,0.);upper=lower+1
            test[variant]=np.clip(delta,lower,upper)
            coefficients.append(dict(date=str(date),variant=variant,beta=beta.tolist(),
                training_last_outcome=str(train.target_date.max()),training_dates=int(train.date.nunique())))
        for variant in ['bs','model','hw','event','structural','both']:
            test[variant+'_error']=test.actual_change-test[variant]*test.stock_change
        results.append(test)
        counts.append(dict(date=date,training_rows=len(train),test_rows=len(test)))
    scored=pd.concat(results,ignore_index=True);scored.to_pickle(output/'hedge_evaluation.pkl')
    (output/'hedge_coefficients.json').write_text(json.dumps(coefficients,indent=2))
    summaries=[]
    for v in ['bs','model','hw','event','structural','both']:
        e=scored[v+'_error']; group=scored.assign(squared=e*e,absolute=e.abs()).groupby(['sid','date'])[['squared','absolute']].mean()
        summaries.append(dict(variant=v,n=len(e),snapshot_mse=group.squared.mean(),snapshot_mae_bp=10000*group.absolute.mean(),
            quote_rmse_bp=10000*np.sqrt(np.mean(e*e)),absolute_error_p95_bp=10000*e.abs().quantile(.95),
            absolute_error_p99_bp=10000*e.abs().quantile(.99)))
    summary=pd.DataFrame(summaries);summary.to_csv(output/'hedge_summary.csv',index=False)
    print(summary.to_string(index=False))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
