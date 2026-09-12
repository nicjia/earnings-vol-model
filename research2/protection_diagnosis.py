import pandas as pd
from research2.iterate_strategies import OUT,score
from research2.historical_jump_report import table

def main():
    p=pd.read_pickle(OUT/'positions.pkl');p=p[p.family.eq('protected_earnings')];base=p[p.version.eq('naked_straddle')].set_index(['sid','event'])
    out=[]
    for version in ['ironfly_5','ironfly_10','ironfly_5_cost_budget','ironfly_10_cost_budget']:
        selected=p[p.version.eq(version)].set_index(['sid','event'])
        for label,years in [('development',range(2016,2022)),('later',range(2022,2026)),('all',range(2016,2026))]:
            b=selected[selected.year.isin(years)];a=base.loc[b.index]
            for fill in [0,.5,1]:
                x=score(a,fill,fill,False)/a.notional;y=score(b,fill,fill,False)/b.notional
                out.append(dict(version=version,period=label,fill=fill,matched_events=len(b),naked_mean_bp=10000*x.mean(),protected_mean_bp=10000*y.mean(),naked_worst_bp=10000*x.min(),protected_worst_bp=10000*y.min(),naked_sd_bp=10000*x.std(),protected_sd_bp=10000*y.std()))
    df=pd.DataFrame(out);df.to_csv(OUT/'protection_comparison.csv',index=False);print(df[df.period.eq('later')&df.fill.eq(1)].to_string(index=False))

if __name__=='__main__':main()
