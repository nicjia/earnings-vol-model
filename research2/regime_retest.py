"""Past-only risk-regime filters for the short historical-variance candidate."""
import numpy as np
import pandas as pd
from research2.iterate_strategies import ROOT,OUT,analyze,report

def main():
    c=pd.read_pickle(OUT/'enriched_candidates.pkl');p=pd.read_pickle(OUT/'positions.pkl');p=p[~p.version.str.startswith('regime_')].copy()
    history=pd.concat([pd.read_pickle(f) for f in (ROOT/'historical_jump_data').glob('stocks_*.pkl')],ignore_index=True)
    history.date=pd.to_datetime(history.date);factors=[]
    for (sid,event),g in c.groupby(['sid','event']):
        signal=g.signal.iloc[0];past=history[history.secid.eq(sid)&history.date.le(signal)].sort_values('date').tail(252)
        r=pd.to_numeric(past['return'],errors='coerce').to_numpy(float);r=np.log1p(r);r=r[np.isfinite(r)]
        if len(r)<126:ratio=draw=np.nan
        else:
            ratio=float(np.mean(r[-20:]**2)/max(np.mean(r**2),1e-12))
            price=np.r_[0,np.cumsum(r[-60:])];draw=float(np.exp(price[-1]-price.max())-1)
        factors.append(dict(sid=sid,event=event,signal=signal,variance_ratio_20_252=ratio,drawdown_60=draw))
    f=pd.DataFrame(factors);f.to_pickle(OUT/'regime_factors.pkl')
    base=p[p.family.eq('historical_variance')&p.version.eq('adjusted_reference_hedge_short_only')].merge(f,on=['sid','event'],validate='many_to_one')
    variants={'regime_volatility':base.variance_ratio_20_252.le(1.5),'regime_drawdown':base.drawdown_60.ge(-.20)}
    variants['regime_both']=variants['regime_volatility']&variants['regime_drawdown']
    new=[]
    for label,mask in variants.items():
        z=base[mask].copy();z['version']=label;new.append(z)
    p=pd.concat([p,*new],ignore_index=True);p.to_pickle(OUT/'positions.pkl');analyze(c,p);report()
    s=pd.read_csv(OUT/'summary.csv');print(s[s.version.str.startswith('regime_')&s.hedged&s.entry_fraction.eq(1)&s.exit_fraction.eq(1)][['version','period','closed','events','all_event_bp','ci_low_bp','ci_high_bp']].to_string(index=False))

if __name__=='__main__':main()
