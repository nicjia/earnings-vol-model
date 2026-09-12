"""Apply development-supported short-only restriction; diagnose hedge changes."""
import numpy as np
import pandas as pd
from research2.iterate_strategies import OUT,analyze,report,score


def main():
    c=pd.read_pickle(OUT/'enriched_candidates.pkl');p=pd.read_pickle(OUT/'positions.pkl');p=p[~p.version.str.contains('short_only')].copy()
    new=[]
    for version in ['adjusted','adjusted_entry_hedge']:
        g=p[p.family.eq('historical_variance')&p.version.eq(version)&p.side.eq('short')].copy()
        g['version']=version+'_short_only';new.append(g)
    p=pd.concat([p,*new],ignore_index=True);p.to_pickle(OUT/'positions.pkl');analyze(c,p);report()
    comparisons=[]
    for (family,version),g in p[p.version.isin(['baseline_entry_hedge','adjusted_entry_hedge'])].groupby(['family','version']):
        original=p[p.family.eq(family)&p.version.eq(version.replace('_entry_hedge',''))].set_index(['sid','event','ids'])
        revised=g[g.status.eq('scored')].set_index(['sid','event','ids']);original=original.loc[revised.index]
        for period,years in [('development',range(2016,2022)),('later',range(2022,2026)),('all',range(2016,2026))]:
            old=original[original.year.isin(years)];new=revised.loc[old.index]
            if old.empty:continue
            for fraction in [0,1]:
                a=score(old,fraction,fraction);b=score(new,fraction,fraction)
                for label,num,den in [('spot_bp',10000.,old.notional),('premium_pct',100.,old.premium)]:
                    before=(a/den).groupby(level=['sid','event']).mean();after=(b/den).groupby(level=['sid','event']).mean()
                    comparisons.append(dict(family=family,version=version,period=period,fill=fraction,metric=label,positions=len(old),events=len(before),before=num*before.mean(),after=num*after.mean()))
    pd.DataFrame(comparisons).to_csv(OUT/'hedge_paired_comparison.csv',index=False)
    s=pd.read_csv(OUT/'summary.csv');print(s[s.family.eq('historical_variance')&s.version.str.contains('short_only')&s.hedged&s.entry_fraction.eq(1)&s.exit_fraction.eq(1)][['version','period','closed','events','all_event_bp','ci_low_bp','ci_high_bp']].to_string(index=False))

if __name__=='__main__':main()
