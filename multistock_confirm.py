"""
Multi-name confirmation: does the COS Heston engine capture each name's real
volatility skew, where flat Black-Scholes (one vol) cannot?

For each name: a 5-strike OTM smile at the 2026-10-16 expiry (pre-earnings, pure
diffusion). Market IV per strike via Black-76 (forward from ATM put-call parity).
  - flat BS  : one constant vol  -> RMS = the skew/dispersion it must ignore
  - Heston   : fit v0, xi, rho (kappa=2, theta=v0) by COS -> RMS
Marks: 2026-09-04 close.
"""
import numpy as np
from scipy.optimize import minimize
from earnings_mixture import implied_vol
from cos_pricer import price_heston_jump

r = 0.045
T = 42/365
# name -> (spot, atm_strike, {strike: (mark, is_call)}, atm_call, atm_put)
NAMES = {
 "AAPL": (319.99, 320, {300:(3.400,0),310:(6.025,0),330:(6.850,1),340:(3.900,1)}, 11.350, 9.975),
 "MSFT": (499.68, 500, {450:(2.490,0),475:(6.500,0),525:(7.850,1),550:(3.050,1)}, 17.625, 15.625),
 "NVDA": (230.345,230, {210:(3.350,0),220:(6.000,0),240:(6.850,1),250:(3.975,1)}, 11.225, 10.100),
 "AMZN": (258.51, 260, {240:(3.425,0),250:(6.375,0),270:(6.500,1),280:(3.775,1)}, 10.475, 10.725),
 "GOOGL":(338.50, 340, {320:(5.250,0),330:(8.525,0),350:(8.925,1),360:(5.950,1)}, 13.050, 12.975),
 "TSLA": (353.95, 350, {330:(8.425,0),340:(11.925,0),360:(17.250,1),370:(13.450,1)}, 21.925,16.350),
 "AMD":  (477.45, 480, {450:(18.250,0),470:(26.850,0),490:(27.150,1),510:(20.350,1)},31.700,32.125),
 "NFLX": (78.245, 80,  {70:(0.840,0),75:(2.175,0),85:(1.560,1),90:(0.750,1)}, 3.175, 4.550),
 "JPM":  (358.61, 360, {340:(5.100,0),350:(8.200,0),370:(6.675,1),380:(3.825,1)}, 11.000, 12.475),
}

def fit_name(S0, atmK, strikes, atmC, atmP):
    F = atmK + np.exp(r*T)*(atmC - atmP)
    q = r - np.log(F/S0)/T
    Ks = sorted(set(list(strikes) + [atmK]))
    mkt = {}
    for K in strikes:
        px, isc = strikes[K]
        mkt[K] = implied_vol(px, S0, K, T, r, q, call=bool(isc))
    mkt[atmK] = implied_vol(atmC, S0, atmK, T, r, q, call=True)
    Ks = np.array(sorted(mkt)); miv = np.array([mkt[K] for K in Ks])
    # flat BS: best single vol = mean; RMS = dispersion
    flat_rms = np.sqrt(np.mean((miv - miv.mean())**2))
    # Heston fit (v0, xi, rho); kappa=2, theta=v0
    def hiv(p):
        v0,xi,rho = p; hp=dict(v0=v0,kappa=2.0,theta=v0,xi=xi,rho=rho)
        out=[]
        for K in Ks:
            isc = K>=F
            px=float(price_heston_jump(S0,K,T,r,q,hp,None,call=bool(isc),N=200,L=12))
            out.append(implied_vol(px,S0,K,T,r,q,call=bool(isc)))
        return np.array(out)
    def obj(p): return np.sqrt(np.mean((hiv(p)-miv)**2))
    res = minimize(obj, [miv[len(miv)//2]**2,1.0,-0.6],
                   bounds=[(0.02,1.5),(0.1,3.0),(-0.95,0.3)], method="L-BFGS-B")
    hrms = obj(res.x)
    # skew metric: OTM put wing IV minus OTM call wing IV (lowest vs highest strike)
    skew = (miv[0]-miv[-1])*100
    return F, miv, flat_rms*100, hrms*100, skew, res.x

print("="*82)
print(f"MULTI-NAME SKEW CONFIRMATION  (2026-10-16, ~42d, pre-earnings)   COS Heston vs flat BS")
print("="*82)
print(f"{'name':>6} {'fwd':>8} {'ATM IV':>7} {'put-call skew':>14} {'flatBS RMS':>11} {'Heston RMS':>11}")
rows=[]
for nm,(S0,atmK,st,ac,ap) in NAMES.items():
    F,miv,frms,hrms,skew,hp = fit_name(S0,atmK,st,ac,ap)
    atmiv = miv[np.argmin(np.abs(np.array(sorted(list(st)+[atmK]))-F))]
    rows.append((nm,F,atmiv,skew,frms,hrms,hp))
    print(f"{nm:>6} {F:>8.2f} {atmiv:>6.1%} {skew:>+13.1f} {frms:>10.2f} {hrms:>10.2f}")
fr=np.array([r[4] for r in rows]); hr=np.array([r[5] for r in rows])
print("-"*82)
print(f"{'MEAN':>6} {'':>8} {'':>7} {np.mean([r[3] for r in rows]):>+13.1f} "
      f"{fr.mean():>10.2f} {hr.mean():>10.2f}")
print(f"\nHeston cuts smile-fit error from {fr.mean():.2f} -> {hr.mean():.2f} vol pts "
      f"(mean across {len(rows)} names); flat BS's error IS each name's skew it ignores.")
print("fitted rho (skew direction):  " +
      "  ".join(f"{r[0]}={r[6][2]:+.2f}" for r in rows))
np.save("/tmp/multistock.npy", dict(rows=[(r[0],r[1],float(r[2]),r[3],r[4],r[5]) for r in rows]),
        allow_pickle=True)
