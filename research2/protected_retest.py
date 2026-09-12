"""Entry-price discipline and protective earnings option wings.

Selection uses signal information except entry limit checks, which use entry
bid/ask only. Exits remain fixed; option protection is tested without stock hedge.
"""
import numpy as np
import pandas as pd
from research2.iterate_strategies import OUT,position,analyze,report


def main():
    c=pd.read_pickle(OUT/'enriched_candidates.pkl');p=pd.read_pickle(OUT/'positions.pkl')
    p=p[~p.family.isin(['entry_limits','protected_earnings'])].copy();new=[];audit=[]
    # Preserve the full same-reference entry hedge comparator.
    old=p[p.family.eq('single_residual')&p.version.eq('baseline_reference_hedge')].copy()
    baseline=old.copy();baseline['family']='entry_limits';baseline['version']='baseline';new.extend(baseline.to_dict('records'))
    lookup=c[c.kind.eq('single')].set_index(['sid','event','ids'])
    for _,r in old.iterrows():
        q=lookup.loc[(r.sid,r.event,r.ids)];en_half=q.entry_relative_spread*q.entry_mid/2
        limit=q.current_market_hybrid/(1.2 if r.side=='long' else .8)
        executable=(q.entry_mid+en_half<=limit) if r.side=='long' else (q.entry_mid-en_half>=limit)
        audit.append(dict(family='entry_limits',sid=r.sid,event=r.event,ids=r.ids,entry_limit=limit,passes_limit=bool(executable)))
        if not executable:continue
        x=r.copy();x['family']='entry_limits';x['version']='limit_only';new.append(x.to_dict())
        if q.liquid and q.entry_mid>=1:
            x=x.copy();x['version']='limit_liquid';new.append(x.to_dict())
    for (sid,event),g in c.groupby(['sid','event']):
        centers=g[g.kind.eq('straddle')]
        if centers.empty:continue
        center=centers.iloc[0]
        if not center.implied_variance>1.25*center.historical_variance:continue
        rows=center.to_frame().T
        raw=position(rows,[-1],'protected_earnings','naked_straddle');raw['signal_credit']=center.signal_mid;raw['max_expiry_loss']=np.nan;new.append(raw)
        pool=g[g.kind.eq('single')&g.exdate.eq(center.exdate)]
        for width in [.05,.10]:
            puts=pool[pool.cp_flag.eq('P')&pool.strike.lt(center.strike)]
            calls=pool[pool.cp_flag.eq('C')&pool.strike.gt(center.strike)]
            if puts.empty or calls.empty:
                audit.append(dict(family='protected_earnings',sid=sid,event=event,width=width,status='missing_wings'));continue
            put=puts.iloc[np.argmin(abs(puts.strike-center.strike*(1-width)))];call=calls.iloc[np.argmin(abs(calls.strike-center.strike*(1+width)))]
            legs=pd.DataFrame([center,put,call]);signs=np.array([-1,1,1]);credit=-float(signs@legs.signal_mid)
            max_width=max(center.strike-put.strike,call.strike-center.strike)
            if credit<=0 or credit>=max_width:
                audit.append(dict(family='protected_earnings',sid=sid,event=event,width=width,status='invalid_signal_credit'));continue
            r=position(legs,signs,'protected_earnings',f'ironfly_{int(width*100)}')
            r.update(notional=2*float(center.signal_spot),signal_credit=credit,max_expiry_loss=max_width-credit,put_width=center.strike-put.strike,call_width=call.strike-center.strike)
            new.append(r)
            # The fix is a signal-time execution-cost budget, not realized cost selection.
            estimated_cost=float((legs.signal_relative_spread*legs.signal_mid).sum()+.013*legs.legs.sum())
            if estimated_cost<=.25*credit:
                z=dict(r,version=r['version']+'_cost_budget');new.append(z)
    full=pd.concat([p,pd.DataFrame(new)],ignore_index=True);full.to_pickle(OUT/'positions.pkl');pd.DataFrame(audit).to_csv(OUT/'protection_audit.csv',index=False)
    analyze(c,full);report()
    s=pd.read_csv(OUT/'summary.csv');focus=s[s.period.eq('later')&s.entry_fraction.eq(s.exit_fraction)&s.entry_fraction.isin([0,1])&((s.family.eq('protected_earnings')&~s.hedged)|(s.family.eq('entry_limits')&s.hedged))]
    print(focus[['family','version','entry_fraction','closed','events','all_event_bp','ci_low_bp','ci_high_bp']].to_string(index=False))

if __name__=='__main__':main()
