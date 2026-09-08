"""
Demo: price options with the Gaussian-mixture earnings jump, validate the
closed form against Monte Carlo, and show the model-implied vol smile.
"""
import numpy as np
from earnings_mixture import (
    MixtureComponent, EarningsMixtureJump,
    price_option, price_option_mc, implied_vol, black76,
)

# --- market setup ---------------------------------------------------------- #
S0    = 100.0
T     = 7 / 365          # option expires 7 calendar days out
r     = 0.045
q     = 0.0
sig_d = 0.28            # annualized *diffusive* vol (non-event)

# --- earnings jump: ASYMMETRIC two-component mixture ----------------------- #
# up branch: +7% pop, prob 0.45, spread 3%
# down branch: -9% drop, prob 0.55, spread 4%   (misses gap harder & more often)
jump = EarningsMixtureJump([
    MixtureComponent(weight=0.45, mean=+0.07, sd=0.03),
    MixtureComponent(weight=0.55, mean=-0.09, sd=0.04),
])

print("=" * 70)
print("EARNINGS MIXTURE JUMP")
print("=" * 70)
print(f"weights            : {jump.w}")
print(f"raw centres        : {jump.m_raw}")
print(f"compensated centres: {jump.mu.round(5)}   (shifted by {jump.compensator:+.5f})")
print(f"E[e^J]             : {np.sum(jump.w*np.exp(jump.mu+0.5*jump.s**2)):.10f}  (must be 1)")
print(f"expected |move|    : {jump.expected_abs_move()*100:.2f}%")
print()

# --- closed form vs Monte Carlo at a few strikes --------------------------- #
print("=" * 70)
print("CLOSED FORM vs MONTE CARLO  (call prices)")
print("=" * 70)
print(f"{'strike':>7} {'closed':>10} {'MC':>10} {'MC stderr':>10} {'diff':>9} {'E[S]/F':>8}")
for K in [88, 92, 96, 100, 104, 108, 112]:
    cf = float(price_option(S0, K, T, r, q, sig_d, jump, call=True))
    mc, se, fwd_ratio = price_option_mc(S0, K, T, r, q, sig_d, jump,
                                        call=True, n=3_000_000, seed=7)
    flag = "OK" if abs(cf - mc) < 4 * se else "**"
    print(f"{K:>7} {cf:>10.4f} {mc:>10.4f} {se:>10.4f} {cf-mc:>+9.4f} {fwd_ratio:>8.5f} {flag}")

# --- the model-implied vol smile ------------------------------------------- #
print()
print("=" * 70)
print("MODEL-IMPLIED VOL SMILE  (invert model price -> flat BS vol)")
print("=" * 70)
print("Compare to the flat diffusive vol of {:.1%}. The jump manufactures a".format(sig_d))
print("smile/skew that flat Black-Scholes cannot produce.\n")
print(f"{'strike':>7} {'moneyness':>10} {'model IV':>10} {'vs diffusive':>13}")
for K in [86, 90, 94, 98, 100, 102, 106, 110, 114]:
    px = float(price_option(S0, K, T, r, q, sig_d, jump, call=True))
    iv = implied_vol(px, S0, K, T, r, q, call=True)
    print(f"{K:>7} {K/S0-1:>+9.1%} {iv:>9.1%} {iv-sig_d:>+12.1%}")
