"""
Bates surface calibration for META: ONE Heston stochastic-vol diffusion
(v0, kappa, theta, xi, rho) plus a single calendar-driven earnings jump, fit
jointly by COS to the whole surface:
   - the 9-expiry ATM term structure (the earnings kink), and
   - the Dec-18 strike smile (the skew),
with the jump switched on ONLY for expiries after 2026-10-28 earnings.

This unifies the two earlier pieces (linear variance-strip + Heston smile) into
one self-consistent model, and lets the term-structure decomposition carry skew.
"""
import numpy as np
from scipy.optimize import minimize
from earnings_mixture import MixtureComponent, EarningsMixtureJump, implied_vol
from cos_pricer import price_heston_jump

S0, r = 616.75, 0.045
ts = np.load("/tmp/meta_ts.npy", allow_pickle=True).item()["rows"]
sm = np.load("/tmp/meta_smile.npy", allow_pickle=True).item()
tD = (np.datetime64("2026-12-18")-np.datetime64("2026-09-04")).astype(int)/365
FD = sm["F"]; qD = r - np.log(FD/S0)/tD

# ATM targets: (t, F, q, mktIV, earn)
atm = [(x["t"], x["F"], x["q"], x["iv"], x["earn"]) for x in ts]
# Dec smile targets: (K, is_call, mktIV)
dec = [(K, bool(isc), implied_vol(px, S0, K, tD, r, qD, call=bool(isc)))
       for (K, isc, px, *_ ) in sm["rows"]]

def build(kj, a=0.12, w_up=0.45, phi=0.35):
    w_dn=1-w_up; bu,bd=(1-a),-(1+a)
    return EarningsMixtureJump([MixtureComponent(w_up,kj*bu,kj*phi*bu),
                                MixtureComponent(w_dn,kj*bd,kj*phi*abs(bd))])

def model_ivs(p, N=160):
    v0,kappa,theta,xi,rho,kj = p
    hp=dict(v0=v0,kappa=kappa,theta=theta,xi=xi,rho=rho); jump=build(kj)
    a_iv=[]
    for t,F,q,iv,earn in atm:
        j = jump if earn else None
        px=float(price_heston_jump(S0,F,t,r,q,hp,j,call=True,N=N,L=12))
        a_iv.append(implied_vol(px,S0,F,t,r,q,call=True))
    d_iv=[]
    for K,isc,iv in dec:
        px=float(price_heston_jump(S0,K,tD,r,qD,hp,jump,call=isc,N=N,L=12))
        d_iv.append(implied_vol(px,S0,K,tD,r,qD,call=isc))
    return np.array(a_iv), np.array(d_iv)

atm_mkt=np.array([iv for *_,iv,_ in [(0,)+a for a in atm]])  # placeholder
atm_mkt=np.array([a[3] for a in atm]); dec_mkt=np.array([d[2] for d in dec])

def obj(p):
    a_iv,d_iv=model_ivs(p)
    return np.sqrt(np.mean(np.concatenate([a_iv-atm_mkt, d_iv-dec_mkt])**2))

x0=[0.13,2.0,0.14,0.6,-0.3,0.10]
bnds=[(0.02,0.6),(0.5,8.0),(0.03,0.6),(0.1,3.0),(-0.9,0.4),(0.03,0.30)]
res=minimize(obj,x0,bounds=bnds,method="L-BFGS-B",
             options=dict(maxiter=200,eps=1e-4))
v0,kappa,theta,xi,rho,kj=res.x
jump=build(kj)
a_iv,d_iv=model_ivs(res.x,N=320)

print("="*74)
print("BATES SURFACE CALIBRATION — META (one Heston diffusion + one earnings jump)")
print("="*74)
print(f"v0={v0:.4f} (vol {np.sqrt(v0):.1%})  kappa={kappa:.2f}  theta={theta:.4f} "
      f"(vol {np.sqrt(theta):.1%})")
print(f"xi(vol-of-vol)={xi:.2f}  rho={rho:+.2f}  jump_scale={kj:.3f}")
print(f"earnings implied |move| = {jump.expected_abs_move():.2%}   "
      f"(linear-strip earlier: 9.76%)")
print(f"overall surface RMS = {obj(res.x)*100:.2f} vol pts  "
      f"({len(atm)} ATM expiries + {len(dec)} Dec strikes)\n")
print("ATM term structure (the kink):")
print(f"{'expiry':>12}{'days':>5}{'mktIV':>8}{'BatesIV':>9}{'event?':>8}")
for i,((t,F,q,iv,earn),m) in enumerate(zip(atm,a_iv)):
    print(f"{ts[i]['exp']:>12}{t*365:>5.0f}{iv:>8.1%}{m:>8.1%}"
          f"{'EARN' if earn else '':>8}")
print(f"\nDec-18 smile RMS = {np.sqrt(np.mean((d_iv-dec_mkt)**2))*100:.2f} vol pts")
np.save("/tmp/bates.npy", dict(atm=atm, a_iv=a_iv, dec=dec, d_iv=d_iv,
        exps=[x['exp'] for x in ts], params=res.x, FD=FD,
        move=jump.expected_abs_move()), allow_pickle=True)
