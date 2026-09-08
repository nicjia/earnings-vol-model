"""
Gaussian-mixture earnings-jump option pricer.

Model
-----
Between events the underlying diffuses (Black-Scholes). At a *known* event time
(earnings) the price takes a discrete multiplicative jump  Y = e^J, where the
jump log-return J is drawn from a K-component Gaussian mixture:

    f(x) = sum_i  w_i * Normal(x ; mu_i, s_i^2)

Earnings almost never produce a ~0% move, so a single Normal centred at 0 is the
worst possible shape (its peak sits on the least-likely outcome). A two-component
mixture with humps near +-(expected move) is bimodal and captures beat/miss.

Key property: because each component is Gaussian in log-space, its variance simply
*adds* to the ongoing diffusion variance. So the price is a weighted sum of
Black-76 prices -- one per mixture component -- with a shifted forward and an
inflated vol. The binary/point-mass model is the s_i -> 0 limit.

No-arbitrage (risk-neutral martingale) requires  E[e^J] = 1, i.e.
    sum_i w_i * exp(mu_i + 0.5 s_i^2) = 1.
We take the *shape* the user specifies (raw centres + spreads) and shift every
centre by a single compensator c so the constraint holds -- this preserves the
shape exactly (relative spacing and widths are unchanged).

Everything is priced in forward (Black-76) space to keep drift/dividend
bookkeeping clean.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


# --------------------------------------------------------------------------- #
# Black-76 (forward-space Black-Scholes)
# --------------------------------------------------------------------------- #
def black76(F, K, vol, T, r, call=True):
    """European option price given the forward F. vol is annualized."""
    F = np.asarray(F, dtype=float)
    if T <= 0 or vol <= 0:
        intrinsic = np.maximum(F - K, 0.0) if call else np.maximum(K - F, 0.0)
        return np.exp(-r * T) * intrinsic
    sqrtT = np.sqrt(T)
    d1 = (np.log(F / K) + 0.5 * vol * vol * T) / (vol * sqrtT)
    d2 = d1 - vol * sqrtT
    disc = np.exp(-r * T)
    if call:
        return disc * (F * norm.cdf(d1) - K * norm.cdf(d2))
    return disc * (K * norm.cdf(-d2) - F * norm.cdf(-d1))


# --------------------------------------------------------------------------- #
# Mixture specification
# --------------------------------------------------------------------------- #
@dataclass
class MixtureComponent:
    weight: float   # probability weight w_i (weights need not sum to 1; normalized)
    mean: float     # raw centre m_i in log-return space (e.g. +0.06 for a +6% pop)
    sd: float       # within-branch spread s_i in log-return space


class EarningsMixtureJump:
    """A K-component Gaussian mixture jump, drift-compensated so E[e^J] = 1."""

    def __init__(self, components: list[MixtureComponent]):
        w = np.array([c.weight for c in components], dtype=float)
        self.w = w / w.sum()
        self.m_raw = np.array([c.mean for c in components], dtype=float)
        self.s = np.array([c.sd for c in components], dtype=float)
        # martingale compensator: shift all centres by -log(E[e^J_raw])
        E_raw = np.sum(self.w * np.exp(self.m_raw + 0.5 * self.s ** 2))
        self.compensator = np.log(E_raw)
        self.mu = self.m_raw - self.compensator          # compensated centres
        # sanity: E[e^J] must now be 1
        assert abs(np.sum(self.w * np.exp(self.mu + 0.5 * self.s ** 2)) - 1.0) < 1e-12

    # convenience stats on the (compensated) jump distribution ----------------
    def mean_move(self):
        """E[J] of the compensated jump (a small negative number, the drag)."""
        return float(np.sum(self.w * self.mu))

    def expected_abs_move(self, n=400_000, seed=0):
        """E[|e^J - 1|] -- the 'expected move' magnitude implied by the mixture."""
        rng = np.random.default_rng(seed)
        J = self.sample(n, rng)
        return float(np.mean(np.abs(np.exp(J) - 1.0)))

    def sample(self, n, rng):
        comp = rng.choice(len(self.w), size=n, p=self.w)
        return rng.normal(self.mu[comp], self.s[comp])

    def density(self, x):
        x = np.asarray(x, dtype=float)[..., None]
        pdf = self.w * norm.pdf(x, self.mu, self.s)
        return pdf.sum(axis=-1)


# --------------------------------------------------------------------------- #
# The pricer: mixture-of-Black-76 (closed form)
# --------------------------------------------------------------------------- #
def price_option(S0, K, T, r, q, sigma_diff, jump: EarningsMixtureJump | None,
                 call=True):
    """
    Price a European option under diffusion + one earnings mixture jump.

    S0        spot
    K         strike (scalar or array)
    T         year-fraction to expiry
    r, q      risk-free, dividend yield (continuous)
    sigma_diff annualized *diffusive* vol (the non-event vol)
    jump      EarningsMixtureJump, or None for plain Black-Scholes
    """
    F = S0 * np.exp((r - q) * T)                      # pure forward
    if jump is None:
        return black76(F, K, sigma_diff, T, r, call)
    total = np.zeros_like(np.asarray(K, dtype=float))
    for w_i, mu_i, s_i in zip(jump.w, jump.mu, jump.s):
        F_i = F * np.exp(mu_i + 0.5 * s_i ** 2)        # component forward (sum w_i F_i = F)
        var_i = sigma_diff ** 2 * T + s_i ** 2         # diffusion + branch variance
        vol_i = np.sqrt(var_i / T)                     # annualized effective vol
        total = total + w_i * black76(F_i, K, vol_i, T, r, call)
    return total


# --------------------------------------------------------------------------- #
# Monte Carlo validator (independent of the closed form)
# --------------------------------------------------------------------------- #
def price_option_mc(S0, K, T, r, q, sigma_diff, jump: EarningsMixtureJump | None,
                    call=True, n=2_000_000, seed=1):
    rng = np.random.default_rng(seed)
    F = S0 * np.exp((r - q) * T)
    Z = rng.standard_normal(n)
    logST = np.log(F) - 0.5 * sigma_diff ** 2 * T + sigma_diff * np.sqrt(T) * Z
    if jump is not None:
        logST = logST + jump.sample(n, rng)            # E[e^J]=1 keeps forward = F
    ST = np.exp(logST)
    payoff = np.maximum(ST - K, 0.0) if call else np.maximum(K - ST, 0.0)
    disc = np.exp(-r * T)
    price = disc * payoff
    est = price.mean()
    stderr = price.std(ddof=1) / np.sqrt(n)
    return est, stderr, float(ST.mean() / F)           # last = E[S_T]/F, should be ~1


# --------------------------------------------------------------------------- #
# Implied vol: invert a price back to a single flat Black-76 vol (the "smile")
# --------------------------------------------------------------------------- #
def implied_vol(price, S0, K, T, r, q, call=True):
    F = S0 * np.exp((r - q) * T)
    intrinsic = np.exp(-r * T) * (max(F - K, 0.0) if call else max(K - F, 0.0))
    if price <= intrinsic + 1e-12:
        return np.nan
    f = lambda v: black76(F, K, v, T, r, call) - price
    try:
        return brentq(f, 1e-4, 5.0, maxiter=200)
    except ValueError:
        return np.nan
