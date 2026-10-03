"""Quantile-grid distributions and proper scores for research8 phase 1."""
import numpy as np
from scipy import stats

LEVELS = np.array([0.001, 0.0025, 0.005] + [round(0.01 * k, 2) for k in range(1, 100)] + [0.995, 0.9975, 0.999])
_edges = np.concatenate([[0.0], LEVELS, [1.0]])
WEIGHTS = (_edges[2:] - _edges[:-2]) / 2  # trapezoid weights for integrals over the level grid
TW_WEIGHTS = WEIGHTS * (2 * LEVELS - 1) ** 2
TABLE_DRAWS = 20000
RHO_GRID = np.exp(np.linspace(np.log(0.01), np.log(100.0), 161))


class Shape:
    """Distribution of a standardized diffusion return: 'Gauss', 'T' or 'FHS'."""

    def __init__(self, kind, z):
        z = z[np.isfinite(z)]
        self.kind = kind
        if kind == 'Gauss':
            self.scale = float(np.sqrt(np.mean(z * z)))
        elif kind == 'T':
            sub = z if len(z) <= 50000 else np.random.default_rng(0).choice(z, 50000, replace=False)
            self.df, _, self.scale = (float(v) for v in stats.t.fit(sub, floc=0))
            self.df = max(self.df, 2.05)
        elif kind == 'FHS':
            self.grid = np.linspace(0, 1, 4001)
            self.values = np.quantile(z, self.grid)
        else:
            raise ValueError(kind)

    def ppf(self, u):
        if self.kind == 'Gauss':
            return self.scale * stats.norm.ppf(u)
        if self.kind == 'T':
            return self.scale * stats.t.ppf(u, self.df)
        return np.interp(u, self.grid, self.values)


def stratified(n):
    return (np.arange(n) + 0.5) / n


def jump_table(shape, upool, seed):
    """Quantiles of Z + rho U on RHO_GRID (rows), Z from the shape and U from pooled standardized jumps."""
    rng = np.random.default_rng(seed)
    z = shape.ppf(stratified(TABLE_DRAWS))
    u = rng.permutation(np.quantile(upool, stratified(TABLE_DRAWS)))
    return np.stack([np.quantile(z + rho * u, LEVELS) for rho in RHO_GRID])


def table_lookup(table, rho):
    """Linear interpolation in log rho; rho outside the grid is clipped."""
    x = np.log(np.clip(rho, RHO_GRID[0], RHO_GRID[-1]))
    g = np.log(RHO_GRID)
    k = np.clip(np.searchsorted(g, x) - 1, 0, len(g) - 2)
    w = ((x - g[k]) / (g[k + 1] - g[k]))[:, None]
    return table[k] * (1 - w) + table[k + 1] * w


def sample_quantiles(draws):
    return np.quantile(draws, LEVELS, axis=1).T


def normal_score_interp(levels, q):
    """Full-grid quantiles from a few (sorted) quantiles: linear in standard-normal score, linear tails."""
    s = stats.norm.ppf(levels)
    S = stats.norm.ppf(LEVELS)
    q = np.sort(q, axis=1)
    out = np.empty((q.shape[0], len(LEVELS)))
    k = np.clip(np.searchsorted(s, S) - 1, 0, len(s) - 2)
    w = (S - s[k]) / (s[k + 1] - s[k])
    out[:] = q[:, k] * (1 - w) + q[:, k + 1] * w
    return out


def score(Q, y):
    """Per-forecast CRPS, tail-weighted CRPS, log score, PIT and predicted E|R| from quantiles Q (N x L)."""
    Q = np.sort(Q, axis=1)
    scale = np.maximum(np.abs(Q[:, -1] - Q[:, 0]), 1e-12)
    Q = Q + (scale * 1e-9)[:, None] * np.arange(Q.shape[1])  # break ties so densities stay finite
    y = np.asarray(y, float)
    d = y[:, None] - Q
    pin = d * (LEVELS - (d < 0))
    crps = 2 * pin @ WEIGHTS
    tw = 2 * pin @ TW_WEIGHTS
    eabs = np.abs(Q) @ WEIGHTS
    k = (Q < y[:, None]).sum(1)
    n = len(LEVELS)
    rows = np.arange(len(y))
    dens = np.diff(LEVELS) / np.diff(Q, axis=1)
    ki = np.clip(k - 1, 0, n - 2)
    f_mid = dens[rows, ki]
    F_mid = LEVELS[ki] + (y - Q[rows, ki]) * f_mid
    lam_lo = dens[:, 0] / LEVELS[0]
    lam_hi = dens[:, -1] / (1 - LEVELS[-1])
    with np.errstate(over='ignore', under='ignore'):
        e_lo = np.exp(np.minimum(lam_lo * (y - Q[:, 0]), 0))
        e_hi = np.exp(np.minimum(-lam_hi * (y - Q[:, -1]), 0))
    f = np.where(k == 0, dens[:, 0] * e_lo, np.where(k == n, dens[:, -1] * e_hi, f_mid))
    F = np.where(k == 0, LEVELS[0] * e_lo, np.where(k == n, 1 - (1 - LEVELS[-1]) * e_hi, F_mid))
    logs = np.log(np.maximum(f, 1e-300))
    return {'crps': crps, 'tw': tw, 'log': logs, 'pit': F, 'eabs': eabs}
