"""
Do we price INDIVIDUAL options right (not just the ATM straddle)?

Test: take the META Dec-18 model calibrated PURELY from the term structure
(diffusion sigma_d = 36.5% from the pre-earnings fit; earnings variance V_earn
read off the 11/20 step) with ZERO per-strike fitting, then price every call/put
across the strike ladder and compare model IV to market IV.
"""
import numpy as np
from earnings_mixture import (MixtureComponent, EarningsMixtureJump,
                              price_option, implied_vol)

d = np.load("/tmp/meta_ts.npy", allow_pickle=True).item()
a, b, V_earn, sigma_d = d["a"], d["b"], d["V_earn"], d["sigma_d"]
S0, r = 616.75, 0.045
tD = (np.datetime64("2026-12-18") - np.datetime64("2026-09-04")).astype(int)/365.0

# Dec OTM marks:  strike -> (price, is_call)
smile = {540:(19.275,False),560:(25.450,False),580:(32.700,False),600:(41.450,False),
         610:(46.350,False),620:(51.375,False),630:(50.375,True),640:(46.175,True),
         660:(38.575,True),680:(32.125,True),700:(26.600,True)}
# ATM calls for the parity forward
atm = {610:(59.400,46.350),620:(55.100,51.375)}
F = float(np.mean([K+np.exp(r*tD)*(c-p) for K,(c,p) in atm.items()]))
q = r - np.log(F/S0)/tD

# model: flat diffusion + earnings mixture, variance-matched to V_earn (asym shape)
w_up,w_dn,asym,phi = 0.45,0.55,0.12,0.35
bu,bd = (1-asym), -(1+asym); su,sd = phi*abs(bu), phi*abs(bd)
mean_b = w_up*bu+w_dn*bd
base_var = w_up*(bu**2+su**2)+w_dn*(bd**2+sd**2)-mean_b**2
kappa = np.sqrt(V_earn/base_var)
jump = EarningsMixtureJump([MixtureComponent(w_up,kappa*bu,kappa*su),
                            MixtureComponent(w_dn,kappa*bd,kappa*sd)])

print("="*74)
print(f"META Dec-18 smile   fwd={F:.2f}  (model = 36.5% diffusion + earnings step,")
print(f"                     calibrated from the TERM STRUCTURE, not these strikes)")
print("="*74)
print(f"{'K':>6} {'side':>5} {'mkt$':>8} {'model$':>8} {'edge$':>7} "
      f"{'mktIV':>7} {'modIV':>7} {'IVgap':>7}")
errs, rows = [], []
for K,(px,isc) in smile.items():
    miv = implied_vol(px, S0, K, tD, r, q, call=isc)
    model = float(price_option(S0, K, tD, r, q, sigma_d, jump, call=isc))
    modiv = implied_vol(model, S0, K, tD, r, q, call=isc)
    errs.append((modiv-miv)*100); rows.append((K,isc,px,model,miv,modiv))
    print(f"{K:>6} {'C' if isc else 'P':>5} {px:>8.2f} {model:>8.2f} {px-model:>+7.2f} "
          f"{miv:>7.2%} {modiv:>7.2%} {(miv-modiv)*100:>+6.2f}")
errs = np.array(errs)
print(f"\nRMS IV error across {len(errs)} individual options: {np.sqrt(np.mean(errs**2)):.2f} vol pts")
print(f"mean signed IV error (skew tell): {errs.mean():+.2f} vol pts   "
      f"[+ = model rich vs mkt]")
# skew diagnostic: does the error slope with strike? (equity put-skew signature)
Ks = np.array([r_[0] for r_ in rows]); slope = np.polyfit(Ks, errs, 1)[0]
print(f"error vs strike slope: {slope*100:+.3f} vol pts per $100 strike   "
      f"[<0 => model misses downside put-skew]")
np.save("/tmp/meta_smile.npy", dict(rows=rows, F=F, errs=errs.tolist()), allow_pickle=True)
