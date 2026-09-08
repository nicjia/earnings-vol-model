"""
META option term-structure decomposition: pull the earnings event out of the
IV curve using the "known future event" clock, then price the post-earnings
expiries from it.

META reports 2026-10-28 (PM). Expiries through 10/23 contain NO earnings; 11/20
and 12/18 swallow the one event. So total variance W(T) = IV(T)^2 * T should be
~linear in T across the pre-earnings expiries (pure diffusion), then step UP by a
constant V_earn once the event is inside. We:
  1. fit diffusion to the pre-earnings expiries      W_pre(T) = a + b*T
  2. read the earnings variance off the 11/20 step    V_earn = W(11/20) - W_pre
  3. CHECK it predicts 12/18 with the SAME V_earn      (out-of-sample event test)
  4. forecast the post-earnings IV collapse, and price the Dec straddle with a
     mixture-jump calibrated to V_earn.
Marks: 2026-09-04 close; spot 616.75 (contemporaneous).
"""
import numpy as np
from earnings_mixture import (MixtureComponent, EarningsMixtureJump,
                              price_option, implied_vol)

S0, r = 616.75, 0.045
VAL = np.datetime64("2026-09-04")            # valuation date = mark date
EARN = np.datetime64("2026-10-28")
def T(exp): return (np.datetime64(exp) - VAL).astype(int) / 365.0

# expiry -> {strike: (call, put)} ATM marks (610 & 620)
DATA = {
 "2026-09-11": {610:(14.825,7.675),  620:(9.600,12.475)},
 "2026-09-18": {610:(20.125,12.725), 620:(15.075,17.725)},
 "2026-09-25": {610:(24.625,16.875), 620:(19.550,21.925)},
 "2026-10-02": {610:(28.100,19.825), 620:(23.075,25.050)},
 "2026-10-09": {610:(31.550,22.850), 620:(26.375,27.550)},
 "2026-10-16": {610:(34.425,25.250), 620:(29.475,30.300)},
 "2026-10-23": {610:(37.525,26.250), 620:(32.575,33.275)},   # illiquid, wide
 "2026-11-20": {610:(52.800,41.025), 620:(48.000,46.200)},   # contains earnings
 "2026-12-18": {610:(59.400,46.350), 620:(55.100,51.375)},   # contains earnings
}
NOISY = {"2026-10-23"}                        # exclude from the diffusion fit

def forward(marks, t):
    fs = [K + np.exp(r*t)*(c-p) for K,(c,p) in marks.items()]
    return float(np.mean(fs))

def atm_iv(marks, t, F):
    q = r - np.log(F/S0)/t                     # carry that reproduces F from S0
    ks, ivs = [], []
    for K,(c,p) in marks.items():
        iv = implied_vol(c if K>=F else p, S0, K, t, r, q, call=(K>=F))
        if iv==iv: ks.append(K); ivs.append(iv)
    ks, ivs = np.array(ks,float), np.array(ivs)
    return float(np.interp(F, ks, ivs)), q

rows = []
for exp, marks in DATA.items():
    t = T(exp); F = forward(marks, t); iv, q = atm_iv(marks, t, F)
    rows.append(dict(exp=exp, t=t, F=F, iv=iv, W=iv*iv*t, q=q,
                     earn=(np.datetime64(exp) > EARN)))

# --- 1. fit diffusion W = a + b*T on pre-earnings, non-noisy expiries ------ #
pre = [x for x in rows if not x["earn"] and x["exp"] not in NOISY]
Tp = np.array([x["t"] for x in pre]); Wp = np.array([x["W"] for x in pre])
b, a = np.polyfit(Tp, Wp, 1)                   # slope=variance rate, intercept
sigma_d = np.sqrt(b)
def W_diff(t): return a + b*t

# --- 2. earnings variance from the 11/20 step ------------------------------ #
r1120 = next(x for x in rows if x["exp"]=="2026-11-20")
V_earn = r1120["W"] - W_diff(r1120["t"])
earn_move = np.sqrt(V_earn)                     # implied one-day earnings move (log)

# --- 3. out-of-sample check on 12/18 with the SAME V_earn ------------------ #
r1218 = next(x for x in rows if x["exp"]=="2026-12-18")
W1218_pred = W_diff(r1218["t"]) + V_earn
iv1218_pred = np.sqrt(W1218_pred / r1218["t"])

print("="*76)
print(f"META  spot={S0}   earnings 2026-10-28 PM   (marks 2026-09-04)")
print("="*76)
print(f"{'expiry':>12} {'days':>5} {'fwd':>8} {'mktIV':>7} {'diffIV':>7} "
      f"{'event?':>7}")
for x in rows:
    diff_iv = np.sqrt(max(W_diff(x['t']),1e-9)/x['t'])
    tag = "EARN" if x['earn'] else ("(noisy)" if x['exp'] in NOISY else "")
    print(f"{x['exp']:>12} {x['t']*365:>5.0f} {x['F']:>8.2f} {x['iv']:>6.1%} "
          f"{diff_iv:>6.1%} {tag:>7}")

print("\n" + "-"*76)
print(f"fitted diffusion vol (non-event)     : {sigma_d:.1%}   (W = {a:+.5f} + {b:.4f}*T)")
print(f"earnings variance V_earn (from 11/20): {V_earn:.5f}")
print(f"  => implied one-day earnings move   : {earn_move:.2%}")
print(f"\nOUT-OF-SAMPLE event test (predict 12/18 with the SAME V_earn):")
print(f"  model 12/18 ATM IV = {iv1218_pred:.2%}   vs market {r1218['iv']:.2%}"
      f"   (miss {abs(iv1218_pred-r1218['iv'])*1e2:.2f} vol pts)")

# --- 4a. forecast the post-earnings IV collapse ---------------------------- #
iv1218_ex = np.sqrt(W_diff(r1218["t"]) / r1218["t"])
print(f"\nFORECAST: once 10/28 earnings prints, Dec (12/18) ATM IV should fall")
print(f"  from {r1218['iv']:.1%}  ->  {iv1218_ex:.1%}   "
      f"(the event is worth {(r1218['iv']-iv1218_ex)*1e2:.1f} vol pts of today's Dec IV)")

# --- 4b. PRICE the Dec ATM straddle with a mixture jump = V_earn ----------- #
# asymmetric two-component earnings mixture, variance matched to V_earn, then
# ATM-calibrated so it reprices the Dec straddle level.
w_up,w_dn,asym,phi = 0.45,0.55,0.12,0.35
bu,bd = (1-asym), -(1+asym); su,sd = phi*abs(bu), phi*abs(bd)
mean_b = w_up*bu+w_dn*bd
base_var = w_up*(bu**2+su**2)+w_dn*(bd**2+sd**2)-mean_b**2
kappa = np.sqrt(V_earn/base_var)
jumpDec = EarningsMixtureJump([MixtureComponent(w_up,kappa*bu,kappa*su),
                               MixtureComponent(w_dn,kappa*bd,kappa*sd)])
tD, FD, qD = r1218["t"], r1218["F"], r1218["q"]
# model straddle at K=forward: diffusion sigma_d over full T + the one earnings jump
Kd = round(FD/10)*10
cD = float(price_option(S0, Kd, tD, r, qD, sigma_d, jumpDec, call=True))
pD = float(price_option(S0, Kd, tD, r, qD, sigma_d, jumpDec, call=False))
mkt_c, mkt_p = DATA["2026-12-18"][Kd]
print(f"\nPRICE CHECK  Dec {Kd} straddle (diffusion {sigma_d:.1%} + one earnings jump):")
print(f"  model  call {cD:5.2f}  put {pD:5.2f}  straddle {cD+pD:6.2f}")
print(f"  market call {mkt_c:5.2f}  put {mkt_p:5.2f}  straddle {mkt_c+mkt_p:6.2f}")
print(f"  model expected earnings |move| = {jumpDec.expected_abs_move():.2%}")

# stash for the figure
np.save("/tmp/meta_ts.npy", dict(rows=rows, a=a, b=b, sigma_d=sigma_d,
        V_earn=V_earn, earn_move=earn_move, iv1218_ex=iv1218_ex), allow_pickle=True)
