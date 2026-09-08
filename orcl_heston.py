"""
Re-fit the ORCL 5-day earnings smile with COS Heston + earnings jump, and compare
to the flat-diffusion + jump model that could not lift the wings (best ~3.6% RMS).

Capacity test (in-sample): can each model SHAPE-match the real smile at all?
  Model A: flat diffusion + earnings mixture   (fit sigma_d, jump scale)
  Model B: Heston diffusion + earnings mixture  (fit v0, xi, rho, jump scale), priced by COS
"""
import numpy as np
from scipy.optimize import minimize
from earnings_mixture import (MixtureComponent, EarningsMixtureJump,
                              price_option, implied_vol)
from cos_pricer import price_heston_jump

S0, r = 158.765, 0.045
T = 7/365                      # marks 2026-09-04, expiry 2026-09-11
chain = {145:(17.125,3.275),146:(16.325,3.450),147:(15.675,3.950),148:(14.975,4.225),
         149:(14.375,4.650),150:(13.775,5.000),152.5:(12.325,6.075),155:(11.050,7.275),
         157.5:(9.875,8.575),160:(8.725,9.825),162.5:(7.725,11.450),165:(6.500,12.700),
         167.5:(5.925,14.350),170:(5.200,16.475),172.5:(4.550,18.325)}
Ks = np.array(sorted(chain))
F = float(np.mean([K+np.exp(r*T)*(chain[K][0]-chain[K][1]) for K in [157.5,160]]))
q = r - np.log(F/S0)/T
mkt_iv = np.array([implied_vol(chain[K][0] if K>=F else chain[K][1], S0,K,T,r,q,call=(K>=F))
                   for K in Ks])
is_call = Ks >= F

def build_jump(kj, a=0.15, w_up=0.45, phi=0.35):
    w_dn=1-w_up; bu,bd=(1-a),-(1+a)
    return EarningsMixtureJump([MixtureComponent(w_up,kj*bu,kj*phi*bu),
                                MixtureComponent(w_dn,kj*bd,kj*phi*abs(bd))])

def model_iv_flat(p):
    sig, kj = p; j=build_jump(kj)
    out=[]
    for K,c in zip(Ks,is_call):
        px=float(price_option(S0,K,T,r,q,sig,j,call=bool(c)))
        out.append(implied_vol(px,S0,K,T,r,q,call=bool(c)))
    return np.array(out)

def model_iv_heston(p):
    v0,xi,rho,kj,asym = p; j=build_jump(kj, a=asym)
    hp=dict(v0=v0,kappa=2.0,theta=v0,xi=xi,rho=rho)
    out=[]
    for K,c in zip(Ks,is_call):
        px=float(price_heston_jump(S0,K,T,r,q,hp,j,call=bool(c),N=256,L=12))
        out.append(implied_vol(px,S0,K,T,r,q,call=bool(c)))
    return np.array(out)

def rms(iv): return np.sqrt(np.nanmean((iv-mkt_iv)**2))

# --- fit Model A (flat + jump) --------------------------------------------- #
rA = minimize(lambda p: rms(model_iv_flat(p)), x0=[0.5,0.11],
              bounds=[(0.1,1.5),(0.03,0.30)], method="L-BFGS-B")
ivA = model_iv_flat(rA.x)
# --- fit Model B (Heston + jump) ------------------------------------------- #
rB = minimize(lambda p: rms(model_iv_heston(p)),
              x0=[0.30,1.2,-0.5,0.10,0.0],
              bounds=[(0.03,1.5),(0.1,3.0),(-0.95,0.6),(0.03,0.30),(-0.6,0.6)], method="L-BFGS-B")
ivB = model_iv_heston(rB.x)

print("="*78)
print(f"ORCL 5-day smile  fwd={F:.2f}   (in-sample capacity test)")
print("="*78)
print(f"Model A flat+jump (2p)         : sigma_d={rA.x[0]:.1%}  jumpk={rA.x[1]:.3f}"
      f"   RMS={rms(ivA)*100:.2f} vol pts")
print(f"Model B Heston+jump, free-skew : v0={rB.x[0]:.3f}(vol {np.sqrt(rB.x[0]):.0%}) "
      f"xi={rB.x[1]:.2f} rho={rB.x[2]:+.2f} jumpk={rB.x[3]:.3f} asym={rB.x[4]:+.2f}"
      f"   RMS={rms(ivB)*100:.2f} vol pts")
print(f"\n{'K':>7}{'side':>5}{'mktIV':>8}{'flatIV':>8}{'A err':>7}{'hestIV':>8}{'B err':>7}")
for i,K in enumerate(Ks):
    s='C' if is_call[i] else 'P'
    print(f"{K:>7.1f}{s:>5}{mkt_iv[i]:>8.1%}{ivA[i]:>8.1%}{(ivA[i]-mkt_iv[i])*100:>+7.1f}"
          f"{ivB[i]:>8.1%}{(ivB[i]-mkt_iv[i])*100:>+7.1f}")
# wing focus
wing = (Ks<=148)|(Ks>=167.5)
print(f"\nWING-only RMS (K<=148 or K>=167.5):  flat+jump={np.sqrt(np.mean((ivA[wing]-mkt_iv[wing])**2))*100:.2f}"
      f"  Heston+jump={np.sqrt(np.mean((ivB[wing]-mkt_iv[wing])**2))*100:.2f} vol pts")
np.save("/tmp/orcl_heston.npy", dict(Ks=Ks,mkt=mkt_iv,ivA=ivA,ivB=ivB,F=F,
        rmsA=rms(ivA),rmsB=rms(ivB)),allow_pickle=True)
