"""Build aggregate, redistributable project metrics and figures from private results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def build():
    repo=Path(__file__).resolve().parents[1];private=repo.parent/'wrds_studies'
    metrics={'pricing':[],'transport':[]}
    for year,directory in [(2020,'research2_development_v2'),(2025,'research2_pricing_confirmation')]:
        q=pd.concat([pd.read_pickle(f) for f in (private/directory).glob('pricing_*.pkl')])
        diag=pd.concat([pd.read_pickle(f) for f in (private/directory).glob('diagnostics_*.pkl')])
        for method in ['linear_iv','pchip','ssvi','convex_pchip_10','convex_hybrid_10']:
            e=(q[method]-q.mid).abs();d=diag[diag.variant.eq(method)]
            metrics['pricing'].append(dict(year=year,method=method,quotes=len(q),snapshots=q.groupby(['secid','date']).ngroups,
                names=int(q.secid.nunique()),mae_spot_bp=float((10000*e/q.spot).mean()),mae_dollars=float(e.mean()),
                median_absolute_dollars=float(e.median()),within_bidask_pct=float(100*((q[method]>=q.best_bid)&(q[method]<=q.best_offer)).mean()),
                grid_pass_pct=float(100*d.grid_ok.mean()) if len(d) else None))
    for year,directory in [(2020,'transport_development_v4'),(2025,'transport_external_2025')]:
        q=pd.concat([pd.read_pickle(f) for f in (private/directory).glob('transport_*.pkl')])
        candidates=['sticky_strike','sticky_moneyness','simple_event','local_event','smile_event','model_event','cf_event']
        common=q.dropna(subset=['actual']+candidates);g=common[common.event_crossed.eq(1)]
        for method in candidates:
            e=10000*(g[method]-g.actual).abs()/g.future_spot
            metrics['transport'].append(dict(year=year,method=method,quotes=len(g),events=g.groupby(['secid','date']).ngroups,
                equal_event_mae_spot_bp=float(g.assign(error=e).groupby(['secid','date']).error.mean().mean())))
    metrics['interpretation']=dict(pricing='Reference-conditioned pricing, with target strikes withheld. 2020 development, 2025 historical confirmation through August 29.',
        transport='Conditional on the later observed stock price; fixed two-session announcement bracket. 2025 already used in earlier research, so this is descriptive external-year comparison, not a new untouched confirmation.',
        novelty='Established model families and constrained interpolation; no claim of a new mathematical pricing method.',
        profitability='No robust after-cost trading edge established.')
    (repo/'docs'/'final_metrics.json').write_text(json.dumps(metrics,indent=2))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'font.family':'DejaVu Sans'})
    fig,axes=plt.subplots(1,2,figsize=(12,4.8));colors=['#335c81','#e09f3e'];width=.34
    groups=[('convex_hybrid_10','Structural\nhybrid'),('convex_pchip_10','Market-only\nsmoother'),('pchip','PCHIP\nbenchmark')]
    for j,year in enumerate([2020,2025]):
        vals=[next(r['mae_spot_bp'] for r in metrics['pricing'] if r['year']==year and r['method']==m) for m,_ in groups]
        bars=axes[0].bar(np.arange(len(groups))+(j-.5)*width,vals,width,label=str(year),color=colors[j])
        axes[0].bar_label(bars,fmt='%.2f',padding=3,fontsize=9)
    axes[0].set_xticks(np.arange(len(groups)),[label for _,label in groups]);axes[0].set_ylim(0,6.)
    axes[0].set_ylabel('Mean absolute error / spot, basis points');axes[0].set_title('Pricing withheld contracts');axes[0].legend(frameon=False)
    groups2=[('sticky_strike','Constant-IV\nreference smile'),('cf_event','Structural event\nadjustment'),('local_event','Two-expiry\nevent estimate')]
    for j,year in enumerate([2020,2025]):
        vals=[next(r['equal_event_mae_spot_bp'] for r in metrics['transport'] if r['year']==year and r['method']==m) for m,_ in groups2]
        bars=axes[1].bar(np.arange(len(groups2))+(j-.5)*width,vals,width,color=colors[j])
        axes[1].bar_label(bars,fmt='%.1f',padding=3,fontsize=9)
    axes[1].set_xticks(np.arange(len(groups2)),[label for _,label in groups2]);axes[1].set_ylim(0,110)
    axes[1].set_ylabel('Equal-event mean absolute error, spot bp');axes[1].set_title('Post-earnings conditional repricing')
    fig.suptitle('Market-calibrated option pricing and earnings scenarios',fontsize=14,y=1.02)
    fig.text(.5,-.035,'2020: development. 2025: available January–August history. Right panel supplies the later stock price to every model.',ha='center',fontsize=9,color='#444444')
    fig.tight_layout();fig.savefig(repo/'figures'/'final_project_results.png',dpi=180,bbox_inches='tight');plt.close(fig)
    print('Aggregate metrics and project figure saved.')


if __name__=='__main__':build()
