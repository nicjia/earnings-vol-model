"""
EMPIRICAL STUDY: are earnings-day moves discrete jumps, and is their distribution
bimodal (beat/miss) as the pricing model assumes? Realized data only (yfinance).

For each name, last 8 earnings events:
  reaction return  (after-close report -> close[D]->close[D+1]; before-open -> close[D-1]->close[D])
  baseline daily vol = std of NON-earnings daily returns
  z = reaction / baseline_vol   (how many 'normal days' the earnings move equals)
  EWMA(0.94) 1-day vol forecast as-of the day before -> jump/forecast ratio

Findings:
 1. jump size: median |move| and |move| / baseline-day move
 2. variance concentration: share of annual variance from the ~4 earnings days
 3. distribution shape: GMM(1) vs (2) vs (3) by BIC on pooled standardized z
 4. asymmetry / drift
"""
import pickle, numpy as np, pandas as pd
from sklearn.mixture import GaussianMixture

D = pickle.load(open("/tmp/earn_data.pkl","rb"))
N_LAST = 8

def reaction_returns(hist, earn):
    idx = hist.index
    close = hist["Close"].values
    dates = idx.normalize()
    events = []
    for e in earn.index:
        edate = e.normalize()
        try: hour = e.hour
        except Exception: hour = 16
        pm = hour >= 12
        # last trading-day position with date <= edate
        pos = int(dates.searchsorted(edate, side="right")) - 1
        if pos < 1 or pos >= len(close)-1: continue
        if dates[pos] != edate and dates[pos] < edate and (edate - dates[pos]).days > 4:
            pass  # report date maybe holiday; still use surrounding closes
        if pm:
            i0, i1 = pos, pos+1
        else:
            i0, i1 = pos-1, pos
        if i1 >= len(close) or i0 < 0: continue
        r = close[i1]/close[i0] - 1.0
        if not np.isfinite(r): continue
        events.append((e, i0, i1, r))
    return events

rows, pooled_z, pooled_move, per_name = [], [], [], []
nonearn_z = []
for sym, d in D.items():
    hist, earn = d["hist"], d["earn"]
    ev = reaction_returns(hist, earn)
    if len(ev) < 4: continue
    close = hist["Close"].values
    logret = np.diff(np.log(close))
    # mask ±1 around every earnings reaction index for baseline
    mask = np.ones(len(logret), dtype=bool)
    for _,i0,i1,_ in ev:
        for j in (i0-1,i0,i1,i1+1):
            k=j-1
            if 0<=k<len(logret): mask[k]=False
    base_sd = np.std(logret[mask])                    # daily baseline vol
    # EWMA vol series (lambda 0.94) on baseline-ish returns
    lam=0.94; ewv=np.empty(len(logret)); v=base_sd**2
    for t,x in enumerate(logret):
        ewv[t]=np.sqrt(v); v=lam*v+(1-lam)*x*x
    last = sorted(ev, key=lambda t:t[0])[-N_LAST:]     # most recent N
    # variance share: earnings-reaction-day variance / total variance over full sample
    ev_var = np.sum([r*r for *_,r in ev]); tot_var = np.sum(logret**2)
    var_share = ev_var/tot_var
    name_moves=[]
    for e,i0,i1,r in last:
        z = r/base_sd
        fc = ewv[i0-1] if i0-1>=0 else base_sd
        rows.append(dict(sym=sym, date=str(e.date()), move=r, absmove=abs(r),
                         z=z, ratio=abs(r)/fc))
        pooled_z.append(z); pooled_move.append(abs(r)); name_moves.append(abs(r))
    # sample of non-earnings standardized daily returns for a control
    ne = logret[mask]/base_sd
    nonearn_z.extend(list(np.random.default_rng(len(sym)).choice(ne, size=min(60,len(ne)), replace=False)))
    per_name.append(dict(sym=sym, n=len(last), med_move=np.median(name_moves),
                         var_share=var_share, base_sd=base_sd))

df = pd.DataFrame(rows); pn = pd.DataFrame(per_name)
z = np.array(pooled_z); mv = np.array(pooled_move)
print("="*76)
print(f"EARNINGS-JUMP EMPIRICAL STUDY   {len(pn)} names, {len(df)} events "
      f"(last {N_LAST} each)")
print("="*76)
# 1. jump size
base_day = np.median([r["base_sd"] for r in per_name])
print("\n[1] JUMP SIZE")
print(f"  median earnings-day |move|      : {np.median(mv):.2%}")
print(f"  median normal-day  |move|(~0.67σ): {0.6745*base_day:.2%}")
print(f"  ratio (earnings vs normal day)  : {np.median(mv)/(0.6745*base_day):.1f}x")
print(f"  median jump / EWMA vol forecast : {df['ratio'].median():.1f}x   "
      f"(diffusion under-predicts the day by this factor)")
# 2. variance concentration
print("\n[2] VARIANCE CONCENTRATION")
print(f"  earnings days are ~{4/252:.1%} of trading days but carry a median of")
print(f"  {pn['var_share'].median():.1%} of each name's total return variance "
      f"(range {pn['var_share'].min():.0%}-{pn['var_share'].max():.0%}).")
# 3. distribution shape (BIC model selection)
print("\n[3] DISTRIBUTION SHAPE  (GMM BIC on pooled standardized moves)")
X = z.reshape(-1,1)
bics={}
for k in (1,2,3):
    g=GaussianMixture(k, covariance_type="full", n_init=8, random_state=0).fit(X)
    bics[k]=g.bic(X)
    mus=sorted(g.means_.ravel())
    print(f"  {k}-component BIC={g.bic(X):8.1f}   means(sd units)={np.round(mus,2)}")
best=min(bics,key=bics.get)
print(f"  --> best by BIC: {best} components  (dBIC vs 1-comp = {bics[1]-bics[best]:.1f})")
# excess kurtosis & control
from scipy import stats
print(f"  excess kurtosis of earnings moves : {stats.kurtosis(z):.1f}  (normal=0)")
print(f"  excess kurtosis of NON-earnings   : {stats.kurtosis(np.array(nonearn_z)):.1f}")
# 4. asymmetry
print("\n[4] ASYMMETRY / DRIFT")
print(f"  mean signed move  : {np.mean([r['move'] for r in rows]):+.2%}  "
      f"(fraction up: {np.mean([r['move']>0 for r in rows]):.0%})")
print(f"  skewness of moves : {stats.skew([r['move'] for r in rows]):+.2f}")
dn=[abs(r['move']) for r in rows if r['move']<0]; up=[abs(r['move']) for r in rows if r['move']>0]
print(f"  median |down move|={np.median(dn):.2%}  vs |up move|={np.median(up):.2%}")

df.to_pickle("/tmp/earn_events.pkl")
np.save("/tmp/earn_pooled.npy", dict(z=z, nonearn=np.array(nonearn_z),
        per_name=per_name, bics=bics), allow_pickle=True)
print("\nsaved events -> /tmp/earn_events.pkl")
