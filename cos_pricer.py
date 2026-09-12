"""
COS-method pricer (Fang & Oosterlee 2008) for a Heston stochastic-vol diffusion
combined with an independent, calendar-driven jump.

Why this engine: the earnings/overnight jumps are independent of the diffusion,
so the TOTAL characteristic function is a product,
      phi_total(u) = phi_Heston(u) * phi_jump(u),
and independent jumps just multiply in. COS then inverts phi_total to a price in
O(N) cosine terms - no simulation, no strike-by-strike integration. This one
engine gives us (a) Heston skew+smile for the diffusion, and (b) any number of
Gaussian-mixture jumps, priced together.

phi_jump for our drift-compensated mixture (E[e^J]=1) is
      phi_jump(u) = sum_i w_i * exp(i*u*mu_i - 0.5*u^2*s_i^2),
which satisfies phi_jump(-i)=1, so multiplying keeps the martingale E[e^y]=e^{(r-q)T}.
"""
import numpy as np
from earnings_mixture import implied_vol, black76


# --------------------------------------------------------------------------- #
# characteristic functions of the log-return  y = ln(S_T / S_0)
# --------------------------------------------------------------------------- #
def heston_cf(u, T, r, q, v0, kappa, theta, xi, rho):
    """CF of the Heston log-return (little-trap / Albrecher form, stable)."""
    u = np.asarray(u, dtype=complex)
    xi2 = xi * xi
    m = kappa - rho * xi * 1j * u
    d = np.sqrt(m * m + xi2 * (1j * u + u * u))
    g = (m - d) / (m + d)
    edt = np.exp(-d * T)
    C = ((r - q) * 1j * u * T
         + (kappa * theta / xi2) * ((m - d) * T - 2.0 * np.log((1 - g * edt) / (1 - g))))
    D = ((m - d) / xi2) * ((1 - edt) / (1 - g * edt))
    return np.exp(C + D * v0)


def mixture_cf(u, jump):
    """CF of a drift-compensated Gaussian-mixture jump (EarningsMixtureJump)."""
    u = np.asarray(u, dtype=complex)
    out = np.zeros_like(u)
    for w, mu, s in zip(jump.w, jump.mu, jump.s):
        out = out + w * np.exp(1j * u * mu - 0.5 * (u ** 2) * (s ** 2))
    return out


def independent_jumps_cf(u, jumps):
    """O(N * sum(K_i)) work for N frequencies; no Cartesian mixture expansion.

    Requires independent jump distributions. State-dependent or correlated
    weekend/earnings jumps need a different joint model.
    """
    out = np.ones_like(np.asarray(u, dtype=complex))
    for jump in jumps:
        out *= mixture_cf(u, jump)
    return out


# --------------------------------------------------------------------------- #
# COS pricing
# --------------------------------------------------------------------------- #
def _chi_psi(k, a, b, c, d):
    """COS payoff-integral helpers on [c,d] within truncation [a,b]."""
    bma = b - a
    kpi = k * np.pi / bma
    # psi
    psi = np.zeros_like(k, dtype=float)
    psi[0] = d - c
    nz = k > 0
    psi[nz] = (np.sin(kpi[nz] * (d - a)) - np.sin(kpi[nz] * (c - a))) / kpi[nz]
    # chi
    chi = (1.0 / (1.0 + kpi ** 2)) * (
        np.cos(kpi * (d - a)) * np.exp(d) - np.cos(kpi * (c - a)) * np.exp(c)
        + kpi * np.sin(kpi * (d - a)) * np.exp(d)
        - kpi * np.sin(kpi * (c - a)) * np.exp(c))
    return chi, psi


def cos_price(S0, K, T, r, q, cf_return, call=True, N=512, L=14, extra_pad=0.0):
    """
    Price a European option by COS given cf_return = phi of y=ln(S_T/S_0).
    cf_return must be a callable u -> complex array.
    """
    K = np.atleast_1d(np.asarray(K, dtype=float))
    # truncation range in x = ln(S_T/K), using rough cumulants + padding
    # rough total std from cf via finite difference of the cumulant gen. function
    h = 1e-4
    psi0 = np.log(cf_return(np.array([0.0, h, -h, 2*h, -2*h])))
    c1 = float(np.imag(psi0[1] - psi0[2]) / (2*h))
    c2 = float(np.real(-(psi0[1] + psi0[2] - 2*psi0[0]) / h**2))
    c2 = max(c2, 1e-6)
    sd = np.sqrt(c2) + extra_pad
    prices = np.empty_like(K)
    k = np.arange(N)
    for i, Ki in enumerate(K):
        x0 = np.log(S0 / Ki)
        a = x0 + c1 - L * sd
        b = x0 + c1 + L * sd
        u = k * np.pi / (b - a)
        # phi of x=ln(S_T/K) = phi_return(u) * exp(i u x0)
        phi = cf_return(u) * np.exp(1j * u * x0)
        unit = np.real(phi * np.exp(-1j * u * a))
        unit[0] *= 0.5
        # Bounded put payoff avoids cancellation from exp(b) in the call payoff.
        # Obtain calls by parity, assuming the supplied CF preserves the forward.
        if a < 0:
            chi, psi = _chi_psi(k, a, b, a, min(0.0, b))
            Uk = (2.0 / (b - a)) * (-chi + psi)
        else:
            Uk = np.zeros_like(k, dtype=float)
        prices[i] = Ki * np.exp(-r * T) * np.sum(unit * Uk)
        if call:
            prices[i] += S0 * np.exp(-q*T) - Ki * np.exp(-r*T)
    return prices if prices.size > 1 else float(prices[0])


def _events(jump, jumps):
    events = tuple(jumps)
    if jump is not None:
        if events:
            raise ValueError("Supply jump or jumps, not both")
        events = (jump,)
    return events


def _jump_tail_pad(events, L):
    """Include remote low-weight components missed by a variance-only interval.

    Conservative eight-standard-deviation component padding; still a numerical
    truncation, not an error guarantee for arbitrary parameters.
    """
    if L <= 0:
        raise ValueError("COS truncation multiplier must be positive")
    centers = sum(float(np.max(np.abs(j.mu-j.mean_move()))) for j in events)
    widths = np.sqrt(sum(float(np.max(j.s**2)) for j in events))
    return (centers + 8*widths) / L


def price_diffusion_jumps(S0, K, T, r, q, sigma_diff, jumps=(), call=True,
                          *, variance_time=None, **kw):
    """Flat diffusion with any number of independent jumps, using COS.

    Calendar T controls carry/discount; variance_time controls background risk.
    Events must already be filtered to (valuation, expiry].
    """
    from earnings_mixture import price_option
    tv = T if variance_time is None else variance_time
    if not np.isfinite([T, tv, sigma_diff]).all() or min(T, tv, sigma_diff) < 0:
        raise ValueError("Times and diffusion volatility must be finite and nonnegative")
    events = tuple(jumps)
    if not events or T == 0:
        return price_option(S0, K, T, r, q, sigma_diff, None, call, variance_time=tv)
    v = sigma_diff**2 * tv
    def cf(u):
        u = np.asarray(u, dtype=complex)
        return np.exp(1j*u*((r-q)*T - v/2) - v*u*u/2) * independent_jumps_cf(u, events)
    kw.setdefault("extra_pad", _jump_tail_pad(events, kw.get("L", 14)))
    return cos_price(S0, K, T, r, q, cf, call=call, **kw)


def price_heston_jump(S0, K, T, r, q, hp, jump=None, call=True,
                      *, variance_time=None, jumps=(), **kw):
    """Heston evolution in variance-clock years; carry in calendar years.

    Non-calendar clocks require refitting Heston parameters in the new time unit.
    """
    tv = T if variance_time is None else variance_time
    if not np.isfinite([T, tv]).all() or min(T, tv) < 0:
        raise ValueError("Times must be finite and nonnegative")
    if T == 0:
        return black76(S0, K, 0, 0, r, call)
    events = _events(jump, jumps)
    def cf(u):
        u = np.asarray(u, dtype=complex)
        c = np.ones_like(u) if tv == 0 else heston_cf(
            u, tv, 0, 0, hp["v0"], hp["kappa"], hp["theta"], hp["xi"], hp["rho"])
        return c * np.exp(1j*u*(r-q)*T) * independent_jumps_cf(u, events)
    kw.setdefault("extra_pad", _jump_tail_pad(events, kw.get("L", 14)))
    return cos_price(S0, K, T, r, q, cf, call=call, **kw)
