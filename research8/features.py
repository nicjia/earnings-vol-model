"""Per-origin inputs for the phase 1 distribution models (all computed from data up to the origin close).

Everything here is a pure function of the panel (research8.panel) and the protocol; nothing is fitted to
targets except the pooled GARCH parameters (fit_garch), which use returns dated before a refit date only.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

HORIZONS = (1, 2, 5, 10, 21, 42, 63)
EWMA_LAMBDA, SEED_N = 0.94, 20
KNOWN_DAYS, PROJECT_DAYS, MAX_FCST_RELEASES = 30, 91, 3
HIST_EVENTS, MIN_NAME_EVENTS, K0 = 8, 4, 4.0
LR_WINDOW, LR_MIN = 504, 252


def ewma(r):
    """Variance state after each close; NaN returns (missing or release sessions) leave it unchanged."""
    T, N = r.shape
    out = np.full((T, N), np.nan)
    var = np.full(N, np.nan)
    cnt = np.zeros(N)
    ssum = np.zeros(N)
    for t in range(T):
        x = r[t] ** 2
        ok = ~np.isnan(x)
        seeded = cnt >= SEED_N
        upd = seeded & ok
        var[upd] = EWMA_LAMBDA * var[upd] + (1 - EWMA_LAMBDA) * x[upd]
        add = ~seeded & ok
        ssum[add] += x[add]
        cnt[add] += 1
        new = add & (cnt >= SEED_N)
        var[new] = ssum[new] / SEED_N
        out[t] = var
    return out


def trailing_mean(x, window, min_count):
    """Mean of non-NaN values over the last `window` rows up to and including each row."""
    v = np.where(np.isnan(x), 0.0, x)
    c = (~np.isnan(x)).astype(float)
    cv, cc = np.cumsum(v, 0), np.cumsum(c, 0)
    cv[window:] = cv[window:] - cv[:-window].copy()
    cc[window:] = cc[window:] - cc[:-window].copy()
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(cc >= min_count, cv / np.maximum(cc, 1), np.nan)


def forward_sum(x, h):
    """Sum of x over the h rows after each row (NaN if any is NaN or the window runs past the end)."""
    T = x.shape[0]
    v = np.where(np.isnan(x), 0.0, x)
    bad = np.isnan(x).astype(float)
    cv = np.vstack([np.zeros((1,) + x.shape[1:]), np.cumsum(v, 0)])
    cb = np.vstack([np.zeros((1,) + x.shape[1:]), np.cumsum(bad, 0)])
    out = np.full(x.shape, np.nan)
    if h < T:
        s = cv[h + 1:] - cv[1:T - h + 1]
        b = cb[h + 1:] - cb[1:T - h + 1]
        out[:T - h] = np.where(b == 0, s, np.nan)
    return out


def forward_count(x, h):
    """Count of non-NaN values among the h rows after each row (0 past the end)."""
    T = x.shape[0]
    c = np.vstack([np.zeros((1,) + x.shape[1:]), np.cumsum(~np.isnan(x), 0)])
    out = np.zeros(x.shape)
    if h < T:
        out[:T - h] = c[h + 1:] - c[1:T - h + 1]
    return out


def std_t_logpdf(z, nu):
    return (gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(np.pi * (nu - 2))
            - (nu + 1) / 2 * np.log1p(z * z / (nu - 2)))


def garch_filter(rd, lr, theta, last=None):
    """GJR-GARCH(1,1) with variance targeting to lr. State after close t (one-step variance for t+1).

    rd: diffusion returns (NaN on release/missing). The state starts at lr when lr first exists.
    Returns states and, if `last` is given, the quasi log-likelihood of returns at rows < last.
    """
    a, g, b, nu = theta
    p = a + g / 2 + b
    T, N = rd.shape
    out = np.full((T, N), np.nan)
    var = np.full(N, np.nan)
    ll, n = 0.0, 0
    for t in range(T):
        x = rd[t]
        if last is not None and t < last:
            ok = ~np.isnan(x) & ~np.isnan(var)
            if ok.any():
                z = x[ok] / np.sqrt(var[ok])
                ll += float(np.sum(std_t_logpdf(z, nu) - 0.5 * np.log(var[ok])))
                n += int(ok.sum())
        L = lr[t]
        start = np.isnan(var) & ~np.isnan(L)
        var[start] = L[start]
        has = ~np.isnan(var) & ~np.isnan(L)
        ok = has & ~np.isnan(x)
        nxt = (1 - p) * L + p * var
        shock = (a + g * (x < 0)) * x * x + b * var
        nxt = np.where(ok, (1 - p) * L + shock, nxt)
        var = np.where(has, nxt, var)
        out[t] = var
    return out, (ll / max(n, 1) if last is not None else None)


def fit_garch(rd, lr, last):
    """Pooled quasi-ML over all columns given, rows < last."""
    def nll(th):
        if th[0] + th[1] / 2 + th[2] >= 0.999:
            return 1e3
        return -garch_filter(rd, lr, th, last)[1]
    res = minimize(nll, x0=[0.05, 0.05, 0.88, 6.0], method='L-BFGS-B',
                   bounds=[(0.0, 0.3), (0.0, 0.3), (0.5, 0.995), (2.1, 60.0)], options={'maxiter': 200})
    return [float(v) for v in res.x], float(-res.fun)


def garch_horizon(state, lr, theta, h, nd_frac):
    """Sum of multi-step variance forecasts over h sessions, scaled by the diffusion-session fraction."""
    a, g, b, _ = theta
    p = a + g / 2 + b
    geo = h if p == 1 else (1 - p ** h) / (1 - p)
    return (h * lr + geo * (state - lr)) * nd_frac


def release_inputs(panel, t_idx, j_idx):
    """For origins (t, j): up to 3 forecast release offsets (known or projected, <= 63 sessions ahead),
    the last 8 realized release returns, and their count."""
    dates = panel['dates']
    T = len(dates)
    r = panel['r']
    ev_j, ev_ann, ev_q = panel['ev_j'], panel['ev_ann'], panel['ev_q']
    offs = np.full((len(t_idx), MAX_FCST_RELEASES), np.nan)
    hist = np.full((len(t_idx), HIST_EVENTS), np.nan)
    hmax = max(HORIZONS)
    order = np.argsort(j_idx, kind='stable')
    bounds = np.searchsorted(ev_j, np.arange(len(panel['names']) + 1))
    for j in np.unique(j_idx):
        rows = order[np.searchsorted(j_idx[order], j):np.searchsorted(j_idx[order], j, 'right')]
        lo, hi = bounds[j], bounds[j + 1]
        q = ev_q[lo:hi]
        ann = ev_ann[lo:hi]
        srt = np.argsort(ann, kind='stable')
        q_by_ann, ann_sorted = q[srt], ann[srt]
        jr = r[q, j]
        for row in rows:
            t = t_idx[row]
            d = dates[t]
            k = np.searchsorted(ann_sorted, d + KNOWN_DAYS, 'right')
            known = q_by_ann[:k]
            fut = [int(x) for x in known[(known > t) & (known <= t + hmax)]]
            if k > 0:
                last_ann = ann_sorted[k - 1]
                for m in range(1, 4):
                    s = int(np.searchsorted(dates, last_ann + m * PROJECT_DAYS))
                    if t < s <= t + hmax and s < T and s not in fut:
                        fut.append(s)
            fut = sorted(set(fut))[:MAX_FCST_RELEASES]
            offs[row, :len(fut)] = np.array(fut) - t
            past = jr[(q <= t) & ~np.isnan(jr)]
            past = past[-HIST_EVENTS:]
            hist[row, :len(past)] = past
    return offs, hist

