"""
Price the real ORCL 2026-09-11 option chain with the Gaussian-mixture earnings
jump, and flag strikes where the model disagrees with the market.

Marks are the 2026-09-04 (Friday) regular-session close, contemporaneous with the
underlying at S0 = 158.765. ORCL reports 2026-09-10 after the close, so the 9/11
weekly is the first expiry that contains the event.

Pipeline
--------
1. Forward per expiry from put-call parity (no dividend guess needed).
2. Market implied vol per strike from Black-76 (OTM side).
3. Diffusive (non-event) vol stripped from the 9/11-vs-9/18 term structure:
   the SAME earnings event sits in both expiries, so the variance *difference*
   is pure diffusion:   sigma_d^2 = (IV2^2*T2 - IV1^2*T1) / (T2 - T1)
4. Earnings jump variance for 9/11 = ATM total variance - diffusion variance.
5. Build an ASYMMETRIC two-component (beat/miss) mixture whose total variance
   equals that stripped jump variance (fork A: size from the market's implied
   move; shape chosen), price the whole chain, invert to model IV, compare.
"""
import numpy as np
from earnings_mixture import (
    MixtureComponent, EarningsMixtureJump, price_option, implied_vol,
)

r = 0.045
TODAY = np.datetime64("2026-09-06")

def yearfrac(exp):
    return (np.datetime64(exp) - TODAY).astype(int) / 365.0

# --- market data: strike -> (call_mark, put_mark) -------------------------- #
S0 = 158.765
chain_0911 = {
    145.0: (17.125, 3.275), 146.0: (16.325, 3.450), 147.0: (15.675, 3.950),
    148.0: (14.975, 4.225), 149.0: (14.375, 4.650), 150.0: (13.775, 5.000),
    152.5: (12.325, 6.075), 155.0: (11.050, 7.275), 157.5: (9.875, 8.575),
    160.0: (8.725, 9.825), 162.5: (7.725, 11.450), 165.0: (6.500, 12.700),
    167.5: (5.925, 14.350), 170.0: (5.200, 16.475), 172.5: (4.550, 18.325),
}
T1 = yearfrac("2026-09-11")

# 9/18 ATM (strike -> call, put) for the diffusive-vol strip
chain_0918_atm = {157.5: (11.500, 9.450), 160.0: (10.000, 10.900)}
T2 = yearfrac("2026-09-18")


def forward_from_parity(chain, T):
    """F = K + e^{rT}(C - P), averaged over the two strikes nearest spot."""
    ks = sorted(chain, key=lambda k: abs(k - S0))[:2]
    fs = [k + np.exp(r * T) * (chain[k][0] - chain[k][1]) for k in ks]
    return float(np.mean(fs))


# price_option/implied_vol take spot S0 and apply carry internally. We instead
# want to feed the *forward* we inferred. Simplest: pass S0 == F and r used only
# for discounting; set q so that S0*e^{(r-q)T} == F  => q = r - ln(F/S0)/T.
def q_for_forward(F, T):
    return r - np.log(F / S0) / T


F1 = forward_from_parity(chain_0911, T1)
F2 = forward_from_parity(chain_0918_atm, T2)
q1 = q_for_forward(F1, T1)

print("=" * 72)
print("ORCL  spot={:.3f}  (marks: 2026-09-04 close)   earnings 2026-09-10 PM"
      .format(S0))
print("=" * 72)
print(f"9/11: T={T1*365:.0f}d  forward(parity)={F1:.3f}")
print(f"9/18: T={T2*365:.0f}d  forward(parity)={F2:.3f}")

# --- market IV per strike -------------------------------------------------- #
iv1 = {K: implied_vol(c if K >= F1 else p, S0, K, T1, r, q1, call=(K >= F1))
       for K, (c, p) in chain_0911.items()}

# ATM total implied vol (interpolate the smile at the forward) for each expiry
def atm_iv(chain, T, F):
    q = q_for_forward(F, T)
    ks, ivs = [], []
    for K, (c, p) in chain.items():
        iv = implied_vol(c if K >= F else p, S0, K, T, r, q, call=(K >= F))
        if iv == iv:  # not nan
            ks.append(K); ivs.append(iv)
    ks, ivs = np.array(ks), np.array(ivs)
    return float(np.interp(F, ks, ivs))

atm1 = atm_iv(chain_0911, T1, F1)
atm2 = atm_iv(chain_0918_atm, T2, F2)

# --- strip diffusive vol from the term structure --------------------------- #
var1, var2 = atm1 ** 2 * T1, atm2 ** 2 * T2
sigma_d = np.sqrt(max((var2 - var1) / (T2 - T1), 1e-6))
V_jump = max(var1 - sigma_d ** 2 * T1, 1e-8)      # earnings jump variance (log)
jump_sd = np.sqrt(V_jump)

print(f"\nATM implied vol : 9/11={atm1:.1%}   9/18={atm2:.1%}")
print(f"stripped diffusive vol (non-event) : {sigma_d:.1%}  annualized")
print(f"earnings jump std (log)            : {jump_sd:.2%}   (implied one-day move)")

# --- build ASYMMETRIC two-component mixture scaled to V_jump ---------------- #
# shape: down move bigger & more likely than up (negative earnings skew)
w_up, w_dn = 0.45, 0.55
a = 0.15                     # magnitude asymmetry (down 15% bigger)
phi = 0.35                   # within-branch spread as fraction of |center|
base_up, base_dn = (1 - a), -(1 + a)
bs_up, bs_dn = phi * abs(base_up), phi * abs(base_dn)
mean_base = w_up * base_up + w_dn * base_dn
base_var = (w_up * (base_up ** 2 + bs_up ** 2) +
            w_dn * (base_dn ** 2 + bs_dn ** 2)) - mean_base ** 2
kappa_var = np.sqrt(V_jump / base_var)     # variance-matched scale (starting point)

def build_jump(kappa):
    return EarningsMixtureJump([
        MixtureComponent(w_up, kappa * base_up, kappa * bs_up),
        MixtureComponent(w_dn, kappa * base_dn, kappa * bs_dn),
    ])

# Fork A: calibrate the jump SIZE so the model reprices the ATM straddle exactly
# (match ATM implied vol). Variance-matching over-prices ATM for a bimodal jump,
# so we solve for kappa on the ATM straddle price instead.
from scipy.optimize import brentq
def atm_iv_gap(kappa):
    px = float(price_option(S0, F1, T1, r, q1, sigma_d, build_jump(kappa), call=True))
    return implied_vol(px, S0, F1, T1, r, q1, call=True) - atm1
kappa = brentq(atm_iv_gap, 0.2 * kappa_var, 1.2 * kappa_var, maxiter=100)
jump = build_jump(kappa)
print(f"\njump scale kappa: variance-match={kappa_var:.4f} -> ATM-calibrated={kappa:.4f}")
print("\nmixture components (compensated):")
for w, mu, s in zip(jump.w, jump.mu, jump.s):
    print(f"   w={w:.2f}  center={mu:+.3f} ({np.exp(mu)-1:+.1%})  spread={s:.3f}")
print(f"   model expected |move| = {jump.expected_abs_move():.2%}")

# --- price the chain, invert to model IV, rank mispricings ----------------- #
print("\n" + "=" * 72)
print("MODEL vs MARKET   (OTM side; edge = market_mark - model_price)")
print("=" * 72)
print(f"{'K':>7} {'side':>5} {'mkt':>8} {'model':>8} {'edge':>7} "
      f"{'mktIV':>7} {'modIV':>7} {'IVgap':>7}")
rows = []
for K, (c, p) in chain_0911.items():
    is_call = K >= F1
    mkt = c if is_call else p
    model = float(price_option(S0, K, T1, r, q1, sigma_d, jump, call=is_call))
    miv = iv1[K]
    modiv = implied_vol(model, S0, K, T1, r, q1, call=is_call)
    edge = mkt - model
    rows.append((K, "C" if is_call else "P", mkt, model, edge, miv, modiv))
    print(f"{K:>7.1f} {'C' if is_call else 'P':>5} {mkt:>8.3f} {model:>8.3f} "
          f"{edge:>+7.3f} {miv:>7.1%} {modiv:>7.1%} {(miv-modiv):>+7.1%}")

print("\nTop mispricings by |edge| (model says these are richest / cheapest):")
for K, side, mkt, model, edge, miv, modiv in sorted(
        rows, key=lambda x: -abs(x[4]))[:5]:
    tag = "market RICH (sell)" if edge > 0 else "market CHEAP (buy)"
    print(f"   {K:>6.1f}{side}  edge={edge:+.3f}  ({tag})   "
          f"mktIV={miv:.1%} vs modIV={modiv:.1%}")
