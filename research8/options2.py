"""Phase 2 option records: straddles and strangles around releases, held to expiry, unhedged and delta-hedged.

python -m research8.options2 --cache ../wrds_studies/research7_cache --cache-e ../wrds_studies/research7_cache_e \
    --panel ../wrds_studies/research8_phase1/panel.npz --out ../wrds_studies/research8_phase2/records.pkl

Uses closing quotes at the decision close only as the price paid (never as model input). Payoffs come from the
stock close on the expiry date; the daily delta hedge uses stock closes and Black-Scholes deltas at each leg's
entry implied vol (r = 0, trading-session time). Private output (trade-level).
"""
import argparse
import datetime as dt
import math
import os
import pickle
from multiprocessing import Pool

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from research5.engine import leg_quote, mid
from research6 import engine as r6
from research7 import data
from . import panel as P

LABELS = ('P-4', 'P-1', 'P', 'Q', 'Q+1')
HEDGE_COST = 0.0002
SPREAD_LIMIT, MIN_MID, MIN_OI = 0.25, 0.05, 10


def bs_price(s, k, tau, vol, cp):
    if tau <= 0 or vol <= 0:
        return max(s - k, 0.0) if cp == 'C' else max(k - s, 0.0)
    sd = vol * math.sqrt(tau)
    d1 = (math.log(s / k) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    if cp == 'C':
        return s * norm.cdf(d1) - k * norm.cdf(d2)
    return k * norm.cdf(-d2) - s * norm.cdf(-d1)


def implied_vol(price, s, k, tau, cp):
    intrinsic = max(s - k, 0.0) if cp == 'C' else max(k - s, 0.0)
    if price <= intrinsic + 1e-6 or tau <= 0:
        return None
    try:
        return brentq(lambda v: bs_price(s, k, tau, v, cp) - price, 1e-4, 20.0, xtol=1e-6)
    except ValueError:
        return None


def deltas(s, k, tau, vol, cp):
    s, tau = np.asarray(s, float), np.asarray(tau, float)
    out = np.where(s > k, 1.0, 0.0) if cp == 'C' else np.where(s < k, -1.0, 0.0)
    live = tau > 0
    sd = vol * np.sqrt(np.where(live, tau, 1.0))
    d1 = (np.log(s / k) + 0.5 * sd * sd) / sd
    d = norm.cdf(d1) if cp == 'C' else norm.cdf(d1) - 1
    return np.where(live, d, out)


def label_index(ev, label):
    base = ev['P_index'] if label.startswith('P') else ev['Q_index']
    return base + (int(label[1:]) if len(label) > 1 else 0)


def build_event(ev, label, quotes, base, col, close, r, dates_ord):
    i = label_index(ev, label)
    sessions = base['sessions']
    if not 0 <= i < len(sessions):
        return None
    day = sessions[i]
    chain = quotes.get((ev['secid'], day.isoformat()))
    j = col.get(ev['secid'])
    if not chain or j is None:
        return None
    spot = close[i, j]
    if not spot or not np.isfinite(spot) or spot < 10:
        return None
    if label.startswith('P'):
        front = r6.first_expiry(chain, ev['Q'], ev['Q'] + dt.timedelta(days=10), day)
    else:
        front = r6.first_expiry(chain, day + dt.timedelta(days=5), day + dt.timedelta(days=35), day)
    if front is None:
        return None
    exp_day = dt.date.fromisoformat(front)
    te = int(np.searchsorted(dates_ord, exp_day.toordinal(), 'right')) - 1
    if te <= i or te >= len(dates_ord):
        return None
    divs = base['dividends'].get(ev['secid'], [])
    if any(day < d <= exp_day for d in divs):
        return None
    path = close[i:te + 1, j]
    rets = r[i + 1:te + 1, j]
    if not np.isfinite(path).all() or not np.isfinite(rets).all():
        return None
    if abs(math.log(path[-1] / spot) - rets.sum()) > 0.02:
        return None  # split or data break inside the window
    strikes = chain[front]
    atm = None
    for k, leg in strikes.items():
        if None in (leg[0], leg[1], leg[3], leg[4]):
            continue
        if atm is None or abs(k - spot) < abs(atm - spot):
            atm = k
    if atm is None:
        return None
    h = te - i
    tau = (te - np.arange(i, te + 1)) / 252.0
    straddle_mid = mid(strikes[atm][0], strikes[atm][1]) + mid(strikes[atm][3], strikes[atm][4])
    M = straddle_mid / spot
    puts = [k for k, v in strikes.items() if v[4] is not None and k < spot]
    calls = [k for k, v in strikes.items() if v[1] is not None and k > spot]
    structures = {'straddle': [(atm, 'C'), (atm, 'P')]}
    if puts and calls:
        structures['strangle'] = [(min(calls, key=lambda k: abs(k - spot * (1 + 0.5 * M))), 'C'),
                                  (min(puts, key=lambda k: abs(k - spot * (1 - 0.5 * M))), 'P')]
    out = []
    for name, legs in structures.items():
        rec_legs = []
        for k, cp in legs:
            q = leg_quote(chain, (front, k, cp, 1, 'core'))
            if q is None:
                break
            bid, ask, oi = q
            m = mid(bid, ask)
            if bid <= 0 or m < MIN_MID or oi < MIN_OI or (ask - bid) / m > SPREAD_LIMIT:
                break
            vol = implied_vol(m, spot, k, h / 252.0, cp)
            if vol is None:
                break
            dl = deltas(path[:-1], k, tau[:-1], vol, cp)
            hedge = float(-np.sum(dl * np.diff(path)))
            trades = np.abs(np.diff(np.concatenate([[0.0], dl, [0.0]])))
            hcost = float(HEDGE_COST * np.sum(trades * np.concatenate([path[:-1], [path[-1]]])))
            payoff = max(path[-1] - k, 0.0) if cp == 'C' else max(k - path[-1], 0.0)
            rec_legs.append({'strike': k, 'cp': cp, 'bid': bid, 'ask': ask, 'oi': oi, 'iv': vol, 'payoff': payoff,
                             'hedge_pnl': hedge, 'hedge_cost': hcost, 'delta0': float(dl[0])})
        if len(rec_legs) != len(legs):
            continue
        out.append({'secid': ev['secid'], 'j': j, 'issuer': ev['issuer'], 'group': ev.get('group', 'original'),
                    'Q': ev['Q'], 'timing': ev['timing'], 'label': label, 'structure': name, 't': i, 'te': te,
                    'h': h, 'expiry': front, 'spot': float(spot), 'M': M, 'spot_T': float(path[-1]),
                    'legs': rec_legs, 'week': (dates_ord[i] - 1) // 7})
    return out


def year_job(args):
    cache, year, events, col_items, panel_path = args
    base = data.load_base(cache)
    quotes = data.load_quotes(cache, year)
    pan = P.load(panel_path)
    col = dict(col_items)
    out = []
    for ev in events:
        for label in LABELS:
            recs = build_event(ev, label, quotes, base, col, pan['close'], pan['r'], pan['dates'])
            if recs:
                out.extend(recs)
    return year, out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', default='../wrds_studies/research7_cache')
    ap.add_argument('--cache-e', default='../wrds_studies/research7_cache_e')
    ap.add_argument('--panel', default='../wrds_studies/research8_phase1/panel.npz')
    ap.add_argument('--out', default='../wrds_studies/research8_phase2/records.pkl')
    a = ap.parse_args()
    pan = P.load(a.panel)
    col = [(int(s), j) for j, s in enumerate(pan['names'])]
    jobs = []
    for cache in (a.cache, a.cache_e):
        base = data.load_base(cache)
        by_year = {}
        for ev in base['events']:
            # quotes for the decision close live in the year file of that close; Q+1 can cross into January
            for y in {base['sessions'][min(label_index(ev, l), len(base['sessions']) - 1)].year for l in LABELS}:
                by_year.setdefault(y, []).append(ev)
        for y, evs in sorted(by_year.items()):
            jobs.append((cache, y, evs, col, a.panel))
    records = []
    with Pool(2) as pool:
        for y, recs in pool.imap_unordered(year_job, jobs):
            records.extend(recs)
            print(y, len(recs), flush=True)
    # an event-label can be built from two year files only if its decision close is in both; dedupe
    seen, uniq = set(), []
    for rec in records:
        key = (rec['secid'], rec['Q'], rec['label'], rec['structure'])
        if key not in seen:
            seen.add(key)
            uniq.append(rec)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, 'wb') as s:
        pickle.dump(uniq, s, protocol=pickle.HIGHEST_PROTOCOL)
    print('records', len(uniq))


if __name__ == '__main__':
    main()
