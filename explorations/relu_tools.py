"""Quick exploration (not pre-registered) of two ReLU uses, on all research7 events 2018-2025.

A. Arbitrage-free ReLU price curve as a quote cleaner. Each front-expiry chain at P and P-1 is projected
   (spread-weighted least squares, Dykstra) onto call-price curves that are convex, decreasing, with
   slopes in [-1, 0] and never below intrinsic: exactly a non-negative ReLU combination of strikes.
   Its at-the-forward straddle gives M_relu; compare noise and forecasting power with the raw
   nearest-strike straddle M_raw.
B. ReLU payoff design with bid/ask in the objective. At P, value every liquid single option and
   vertical (debit and credit, OTM side) in the release-spanning front expiry under a history-only
   forecast (the name's last 8 release moves plus EWMA diffusion to expiry). Choose the structure with
   the best (model value - executable cost - fees) / risk, hold to expiry, settle from the stock close.
   Repeat choosing and filling at mids to show how much of a mid-based edge is spread.
"""
import bisect
import datetime as dt
import math
from collections import defaultdict
from statistics import NormalDist

from research5 import stats
from research7 import data, engine

CACHE = '/home/user/wrds_studies/research7_cache'
ND = NormalDist()
FEE = 0.65


def mid(b, a):
    return 0.5 * (b + a)


# ---------------------------------------------------------------- A. ReLU curve
def relu_fit(ks, cs, ws, fwd, iters=150):
    """Weighted projection of call prices onto convex, decreasing, slope >= -1, >= intrinsic curves."""
    n = len(ks)
    x = list(cs)
    cons = []  # (indices, coefficients, bound) meaning sum(coef * x[idx]) >= bound
    for i in range(n - 1):
        dk = ks[i + 1] - ks[i]
        cons.append(((i, i + 1), (-1.0, 1.0), -dk))      # slope >= -1
        cons.append(((i, i + 1), (1.0, -1.0), 0.0))      # slope <= 0
    for i in range(n - 2):
        a, b = ks[i + 1] - ks[i], ks[i + 2] - ks[i + 1]
        cons.append(((i, i + 1, i + 2), (1 / a, -(1 / a + 1 / b), 1 / b), 0.0))  # convex
    for i in range(n):
        cons.append(((i,), (1.0,), max(fwd - ks[i], 0.0)))  # >= intrinsic
    inv_w = [1.0 / w for w in ws]
    corr = [[0.0] * len(c[0]) for c in cons]
    for _ in range(iters):
        worst = 0.0
        for j, (idx, coef, bound) in enumerate(cons):
            p = corr[j]
            y = [x[i] + p[t] for t, i in enumerate(idx)]
            val = sum(c * v for c, v in zip(coef, y))
            if val < bound:
                lam = (bound - val) / sum(c * c * inv_w[i] for c, i in zip(coef, idx))
                new = [v + lam * c * inv_w[i] for v, c, i in zip(y, coef, idx)]
                worst = max(worst, bound - val)
            else:
                new = y
            for t, i in enumerate(idx):
                corr[j][t] = y[t] - new[t]
                x[i] = new[t]
        if worst < 1e-7:
            break
    return x


def chain_calls(chain_ex, spot):
    """Forward from ATM parity, then OTM-side quotes as call prices: [(K, call mid, weight)]."""
    both = [k for k, l in chain_ex.items() if None not in (l[0], l[1], l[3], l[4]) and l[1] > 0 and l[4] > 0]
    if not both:
        return None, None
    atm = min(both, key=lambda k: abs(k - spot))
    l = chain_ex[atm]
    fwd = atm + mid(l[0], l[1]) - mid(l[3], l[4])
    pts = []
    for k in sorted(chain_ex):
        l = chain_ex[k]
        side = (3, 4) if k < fwd else (0, 1)
        b, a = l[side[0]], l[side[1]]
        if b is None or a is None or b <= 0 or a < b:
            continue
        c = mid(b, a) + (fwd - k if k < fwd else 0.0)
        pts.append((k, c, 1.0 / max((a - b) / 2, 0.01) ** 2))
    return fwd, pts


def straddle_at_forward(chain_ex, spot, max_strikes=24):
    fwd, pts = chain_calls(chain_ex, spot)
    if not pts or len(pts) < 5:
        return None, None
    pts = sorted(pts, key=lambda p: abs(p[0] - fwd))[:max_strikes]
    pts.sort()
    ks, cs, ws = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
    if not ks[0] < fwd < ks[-1]:
        return None, None
    fit = relu_fit(ks, cs, ws, fwd)
    i = bisect.bisect_right(ks, fwd) - 1
    c_f = fit[i] + (fit[i + 1] - fit[i]) * (fwd - ks[i]) / (ks[i + 1] - ks[i])
    raw = min(((k, l) for k, l in chain_ex.items() if None not in (l[0], l[1], l[3], l[4]) and l[1] > 0 and l[4] > 0),
              key=lambda kl: abs(kl[0] - spot))[1]
    return 2 * c_f / spot, (mid(raw[0], raw[1]) + mid(raw[3], raw[4])) / spot


def spearman(x, y):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos
        return r
    rx, ry = ranks(x), ranks(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return cov / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


def r2_log(m, j):
    xs, ys = [math.log(v) for v in m], [math.log(max(abs(v), 1e-4)) for v in j]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy * sxy / (sxx * syy)


# ---------------------------------------------------------------- B. payoff design
def model_values(spot, ks, moves, s):
    """Expected call and put payoffs under the mixture of release moves plus N(0, s^2) diffusion."""
    calls, puts = {}, {}
    for k in ks:
        c = p = 0.0
        for j in moves:
            fwd = spot * math.exp(j + 0.5 * s * s)
            if s > 0:
                d1 = (math.log(spot / k) + j + s * s) / s
                cv = fwd * ND.cdf(d1) - k * ND.cdf(d1 - s)
            else:
                cv = max(spot * math.exp(j) - k, 0.0)
            c += cv
            p += cv - (fwd - k)
        calls[k], puts[k] = c / len(moves), p / len(moves)
    return calls, puts


def structures(chain_ex, spot, M):
    """Liquid OTM singles and verticals: (name, [(K, cp, qty)])."""
    def ok(k, cp):
        l = chain_ex.get(k)
        if l is None:
            return False
        b, a, oi = (l[0], l[1], l[2]) if cp == 'C' else (l[3], l[4], l[5])
        return b is not None and a is not None and b > 0 and a >= b and oi >= 10 and (a - b) / mid(b, a) <= 0.5
    calls = sorted(k for k in chain_ex if k >= spot and k <= spot * (1 + 2.5 * M) and ok(k, 'C'))
    puts = sorted((k for k in chain_ex if k <= spot and k >= spot * (1 - 2.5 * M) and ok(k, 'P')), reverse=True)
    out = []
    for side, ks, cp in (('call', calls, 'C'), ('put', puts, 'P')):
        for i, k in enumerate(ks):
            out.append((f'long {side}', [(k, cp, 1)]))
            for k2 in ks[i + 1:i + 3]:
                out.append((f'debit {side} spread', [(k, cp, 1), (k2, cp, -1)]))
                out.append((f'credit {side} spread', [(k, cp, -1), (k2, cp, 1)]))
    return out


def price(chain_ex, legs, at_mid):
    total = 0.0
    for k, cp, q in legs:
        l = chain_ex[k]
        b, a = (l[0], l[1]) if cp == 'C' else (l[3], l[4])
        total += q * (mid(b, a) if at_mid else (a if q > 0 else b))
    return total * 100


def main():
    base = data.load_base(CACHE)
    sessions = base['sessions']
    A = {'raw': [], 'relu': [], 'move': [], 'noise_raw': [], 'noise_relu': [], 'gap': []}
    B = {True: [], False: []}
    events = [e for e in base['events'] if 2018 <= e['E'].year <= 2025]
    implied = {}
    for year in range(2018, 2026):
        m = engine.Market(base, data.load_quotes(CACHE, year) | data.load_quotes(CACHE, year - 1, first=dt.date(year - 1, 12, 1)), implied)
        for ev in events:
            if ev['P'].year != year:
                continue
            day = ev['P']
            chain = m.chain(ev['secid'], day)
            st = m.stock(ev['secid'], day)
            if not chain or not st or not st[0]:
                continue
            spot = st[0]
            front = m.pre_release_front(ev, chain, day)
            j = m.release_move(ev)
            if front is None or j is None:
                continue
            relu_m, raw_m = straddle_at_forward(chain[front], spot)
            prev_chain = m.chain(ev['secid'], m.session(ev['P_index'] - 1))
            prev_st = m.stock(ev['secid'], m.session(ev['P_index'] - 1))
            if relu_m and raw_m:
                A['relu'].append(relu_m)
                A['raw'].append(raw_m)
                A['move'].append(j)
                A['gap'].append(abs(raw_m / relu_m - 1))
                if prev_chain and prev_st and front in prev_chain:
                    pr, pw = straddle_at_forward(prev_chain[front], prev_st[0])
                    if pr and pw:
                        A['noise_relu'].append(abs(math.log(relu_m / pr)))
                        A['noise_raw'].append(abs(math.log(raw_m / pw)))
            # ---- B: payoff design held to expiry
            exd = dt.date.fromisoformat(front)
            k_idx = bisect.bisect_right(sessions, exd) - 1
            if k_idx < 0 or sessions[k_idx] > dt.date(2025, 8, 29) or m.has_dividend(ev['secid'], day, exd):
                continue
            settle = m.stock(ev['secid'], sessions[k_idx])
            if not settle or settle[2] != st[2]:
                continue
            earlier = m.earlier(ev, ev['P_index'])
            moves = [x for x in (m.release_move(k) for k in earlier[-8:]) if x is not None]
            sigma = m.background_vol(ev, ev['P_index'], earlier)
            if len(moves) < 6 or not sigma or not raw_m:
                continue
            s = sigma * math.sqrt(max(engine.weekdays_between(day, exd) - 1, 0))
            strs = structures(chain[front], spot, raw_m)
            if not strs:
                continue
            calls, puts = model_values(spot, sorted({k for _, legs in strs for k, _, _ in legs}), moves, s)
            for at_mid in (False, True):
                best = None
                for name, legs in strs:
                    cost = price(chain[front], legs, at_mid)
                    fees = FEE * len(legs)
                    value = sum(q * (calls[k] if cp == 'C' else puts[k]) for k, cp, q in legs) * 100
                    if name.startswith('credit'):
                        width = abs(legs[0][0] - legs[1][0]) * 100
                        risk = width + cost  # cost is negative (credit received)
                    else:
                        risk = cost
                    if risk < 20:
                        continue
                    edge = (value - cost - fees) / risk
                    if best is None or edge > best[0]:
                        best = (edge, name, legs, cost, fees, risk)
                if best is None or best[0] <= 0:
                    continue
                edge, name, legs, cost, fees, risk = best
                payoff = sum(q * max((settle[0] - k) if cp == 'C' else (k - settle[0]), 0.0) for k, cp, q in legs) * 100
                B[at_mid].append({'issuer': ev['issuer'], 'E': ev['E'], 'ret_mid': (payoff - cost - fees) / risk,
                                  'edge': edge, 'name': name, 'period': '2018-21' if ev['E'].year <= 2021 else '2022-25'})
        del m
    n = len(A['raw'])
    print(f'A. ReLU-cleaned implied move vs raw nearest-strike straddle ({n:,} events at P)')
    print(f"   median |raw/relu - 1| = {sorted(A['gap'])[n // 2]:.2%}")
    nn = len(A['noise_raw'])
    print(f"   day-to-day noise (median |log change| P-1 to P, {nn:,} events): raw {sorted(A['noise_raw'])[nn // 2]:.4f}, "
          f"relu {sorted(A['noise_relu'])[nn // 2]:.4f}")
    for label, key in (('raw', 'raw'), ('relu', 'relu')):
        print(f"   forecasting the release move: {label:4s} Spearman(M, |J|) = {spearman(A[key], [abs(v) for v in A['move']]):.4f}, "
              f"R^2(log|J| on log M) = {r2_log(A[key], A['move']):.4f}, mean |J|/M = "
              f"{sum(abs(j) / mm for j, mm in zip(A['move'], A[key])) / n:.3f}")
    print('\nB. Best structure per event under the history-only forecast, held to expiry (return on risk)')
    for at_mid, label in ((False, 'chosen and filled at bid/ask'), (True, 'chosen and filled at mids')):
        for period in ('2018-21', '2022-25'):
            for thr in (0.0, 0.25):
                g = [r for r in B[at_mid] if r['period'] == period and r['edge'] > thr]
                if len(g) < 30:
                    continue
                pts = stats.issuer_events(g)
                mm, se = stats.cluster_mean_se(pts)
                win = sum(r['ret_mid'] > 0 for r in g) / len(g)
                kinds = defaultdict(int)
                for r in g:
                    kinds[r['name']] += 1
                top = ', '.join(f'{k} {v}' for k, v in sorted(kinds.items(), key=lambda x: -x[1])[:3])
                print(f'   {label:28s} {period} model edge>{thr:.2f}: n={len(g):5d} mean={mm:+.3f} (t={mm / se:+5.2f}) '
                      f'win={win:.0%} | {top}')


if __name__ == '__main__':
    main()
