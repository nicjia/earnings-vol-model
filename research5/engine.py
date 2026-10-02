"""Historical-only signals, option packages and midpoint P&L for earnings events.

Every function that builds a decision receives the entry (decision) session and
reads only stock data dated on or before it, option quotes dated on it, and
earlier events whose last used session precedes it.  Exit quotes are touched
only in ``price_exit``.
"""
import bisect
import datetime as dt
import math

FEE = 0.65
MULT = 100.0
SHORT_VOL = ('short_iron_fly_1x', 'short_iron_fly_2x', 'short_iron_condor', 'short_iron_condor_wide',
             'call_calendar', 'straddle_calendar')
LONG_VOL = ('long_straddle', 'long_strangle')
FAMILIES = LONG_VOL + SHORT_VOL
TIMINGS = (('E-2', 'E-1'), ('E-2', 'E'), ('E-2', 'E+1'), ('E-1', 'E'), ('E-1', 'E+1'), ('E-1', 'E+2'),
           ('E-1', 'E+3'), ('E-2', 'after_release'), ('E-1', 'after_release'))
LIMITS = {'standard': {'core': 0.25, 'wing': 0.50}, 'tight': {'core': 0.10, 'wing': 0.25}}


def offset(label):
    return int(label[1:]) if label != 'E' else 0


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def expected_abs(a, s):
    """E|a + sZ| for Z ~ N(0,1)."""
    if s <= 0:
        return abs(a)
    z = a / s
    return s * math.sqrt(2.0 / math.pi) * math.exp(-0.5 * z * z) + a * (1.0 - 2.0 * norm_cdf(-z))


def bs_price(spot, strike, sigma, t, call):
    if sigma <= 0 or t <= 0:
        return max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    v = sigma * math.sqrt(t)
    d1 = (math.log(spot / strike) + 0.5 * v * v) / v
    d2 = d1 - v
    if call:
        return spot * norm_cdf(d1) - strike * norm_cdf(d2)
    return strike * norm_cdf(-d2) - spot * norm_cdf(-d1)


def implied_vol(price, spot, strike, t, call):
    intrinsic = max(spot - strike, 0.0) if call else max(strike - spot, 0.0)
    if t <= 0 or price <= intrinsic + 1e-9 or price >= (spot if call else strike):
        return None
    lo, hi = 1e-4, 6.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if bs_price(spot, strike, mid, t, call) > price:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def weekdays_between(start, end):
    """Weekdays in (start, end]."""
    if end <= start:
        return 0
    days = (end - start).days
    full, rem = divmod(days, 7)
    count = full * 5
    wd = start.weekday()
    for k in range(1, rem + 1):
        if (wd + k) % 7 < 5:
            count += 1
    return count


def mid(bid, ask):
    return 0.5 * (bid + ask)


class Market:
    """Read-only accessors over the caches with an explicit as-of discipline."""

    def __init__(self, base, quotes):
        self.sessions = base['sessions']
        self.session_index = {d: i for i, d in enumerate(self.sessions)}
        self.stocks = base['stocks']
        self.dividends = base['dividends']
        self.quotes = quotes
        self.events = base['events']
        self.events_by_sid = {}
        for ev in self.events:
            self.events_by_sid.setdefault(ev['secid'], []).append(ev)
        self._implied_cache = {}

    def session(self, ev, off):
        j = ev['E_index'] + off
        return self.sessions[j] if 0 <= j < len(self.sessions) else None

    def chain(self, secid, day):
        return self.quotes.get((secid, day.isoformat()))

    def stock(self, secid, day):
        return self.stocks.get(secid, {}).get(day)

    def log_return(self, secid, day):
        row = self.stock(secid, day)
        if row is None or row[1] is None or math.isnan(row[1]) or row[1] <= -1:
            return None
        return math.log1p(row[1])

    # ---- historical-only features -------------------------------------------------
    def earlier_events(self, ev, asof, last_offset):
        """Earlier events of the same security whose session E_k+last_offset is on or before asof."""
        out = []
        for k in self.events_by_sid.get(ev['secid'], []):
            if k['E'] >= ev['E']:
                break
            last = self.session(k, last_offset)
            if last is not None and last <= asof:
                out.append(k)
        return out

    def event_move(self, k):
        r0 = self.log_return(k['secid'], self.session(k, 0))
        r1 = self.log_return(k['secid'], self.session(k, 1))
        if r0 is None or r1 is None:
            return None
        return r0 + r1, abs(r0), abs(r1)

    def background_vol(self, ev, asof, earlier):
        excluded = set()
        for k in earlier:
            for off in (-1, 0, 1):
                d = self.session(k, off)
                if d is not None:
                    excluded.add(d)
        i = self.session_index.get(asof)
        if i is None:
            return None
        rets = []
        j = i
        while j > 0 and len(rets) < 60:
            d = self.sessions[j]
            if d not in excluded:
                r = self.log_return(ev['secid'], d)
                if r is not None:
                    rets.append(r)
            j -= 1
        if len(rets) < 40:
            return None
        rets.reverse()
        var = sum(r * r for r in rets[:20]) / 20.0
        for r in rets[20:]:
            var = 0.94 * var + 0.06 * r * r
        return math.sqrt(var)

    def front_expiry(self, ev, chain, exit_day, entry_day):
        e1 = self.session(ev, 1)
        if e1 is None:
            return None
        floor = max(exit_day + dt.timedelta(days=1), e1)
        cap = ev['E'] + dt.timedelta(days=30)
        for ex in sorted(chain):
            d = dt.date.fromisoformat(ex)
            if floor <= d <= cap and d > entry_day:
                return ex
        return None

    def back_expiry(self, chain, front):
        fd = dt.date.fromisoformat(front)
        for ex in sorted(chain):
            d = dt.date.fromisoformat(ex)
            if fd < d <= fd + dt.timedelta(days=45):
                return ex
        return None

    def atm_strike(self, strikes, spot):
        best = None
        for k, leg in strikes.items():
            if leg[1] is None or leg[4] is None or leg[0] is None or leg[3] is None:
                continue
            if best is None or abs(k - spot) < abs(best - spot):
                best = k
        return best

    def straddle_move(self, ev, entry_off=-1, exit_off=1):
        """Implied move of the standard front straddle at E+entry_off close (used for HR of later events)."""
        key = (ev['secid'], ev['E'], entry_off, exit_off)
        if key in self._implied_cache:
            return self._implied_cache[key]
        value = None
        day = self.session(ev, entry_off)
        exit_day = self.session(ev, exit_off)
        chain = self.chain(ev['secid'], day) if day else None
        row = self.stock(ev['secid'], day) if day else None
        if chain and row and exit_day:
            ex = self.front_expiry(ev, chain, exit_day, day)
            if ex:
                k = self.atm_strike(chain[ex], row[0])
                if k is not None:
                    leg = chain[ex][k]
                    if leg[1] > 0 and leg[4] > 0:
                        value = (mid(leg[0], leg[1]) + mid(leg[3], leg[4])) / row[0]
        self._implied_cache[key] = value
        return value

    def release_timing(self, ev, asof):
        key = ('release', ev['secid'], ev['E'], asof)
        if key not in self._implied_cache:
            self._implied_cache[key] = self._release_timing(ev, asof)
        return self._implied_cache[key]

    def _release_timing(self, ev, asof):
        earlier = self.earlier_events(ev, asof, 1)[-8:]
        votes = []
        for k in earlier:
            m = self.event_move(k)
            if m is not None:
                votes.append(m[1] > m[2])
        if len(votes) < 4:
            return None
        return 'E' if sum(votes) * 2 > len(votes) else 'E+1'

    def features(self, ev, entry_day, front, back, spot, atm, chain):
        key = ('features', ev['secid'], ev['E'], entry_day, front, back, atm)
        if key not in self._implied_cache:
            self._implied_cache[key] = self._features(ev, entry_day, front, back, spot, atm, chain)
        return dict(self._implied_cache[key])

    def _features(self, ev, entry_day, front, back, spot, atm, chain):
        earlier = self.earlier_events(ev, entry_day, 1)
        last8 = earlier[-8:]
        straddle = mid(chain[front][atm][0], chain[front][atm][1]) + mid(chain[front][atm][3], chain[front][atm][4])
        M = straddle / spot
        out = {'M': M, 'R': None, 'TS': None, 'HR': None, 'H': None}
        sigma = self.background_vol(ev, entry_day, earlier)
        moves = [self.event_move(k) for k in last8]
        moves = [m[0] for m in moves if m is not None]
        if sigma is not None and len(moves) >= 6:
            n = weekdays_between(entry_day, dt.date.fromisoformat(front))
            s = sigma * math.sqrt(max(n - 2, 0) / 252.0)
            H = sum(expected_abs(j, s) for j in moves) / len(moves)
            if H > 0:
                out['H'] = H
                out['R'] = M / H
        if back is not None and atm in chain[back]:
            ivs = []
            for ex in (front, back):
                t = max((dt.date.fromisoformat(ex) - entry_day).days, 1) / 365.0
                leg = chain[ex][atm]
                pair = []
                if leg[0] is not None and leg[1] is not None and leg[1] > 0:
                    pair.append(implied_vol(mid(leg[0], leg[1]), spot, atm, t, True))
                if leg[3] is not None and leg[4] is not None and leg[4] > 0:
                    pair.append(implied_vol(mid(leg[3], leg[4]), spot, atm, t, False))
                pair = [p for p in pair if p]
                ivs.append(sum(pair) / len(pair) if pair else None)
            if ivs[0] and ivs[1]:
                out['TS'] = ivs[0] / ivs[1]
        ratios = []
        for k in last8:
            mk = self.straddle_move(k)
            m = self.event_move(k)
            if mk and m is not None:
                ratios.append(abs(m[0]) / mk)
        if len(ratios) >= 4:
            out['HR'] = sum(ratios) / len(ratios)
        return out

    def has_dividend(self, secid, start, end):
        dates = self.dividends.get(secid, [])
        i = bisect.bisect_right(dates, start)
        return i < len(dates) and dates[i] <= end


def _nearest(strikes, target, side, beyond=None):
    """Nearest quoted strike to target of one type, optionally strictly beyond a strike."""
    best = None
    for k, leg in strikes.items():
        quoted = leg[1] is not None if side == 'C' else leg[4] is not None
        if not quoted:
            continue
        if beyond is not None and (k <= beyond if side == 'C' else k >= beyond):
            continue
        if best is None or abs(k - target) < abs(best - target):
            best = k
    return best


def build_package(family, chain, front, back, spot, atm, M):
    """Return legs [(exdate, strike, 'C'|'P', qty, role)] or a skip reason string."""
    strikes = chain[front]
    straddle = M * spot
    if family == 'long_straddle':
        return [(front, atm, 'C', 1, 'core'), (front, atm, 'P', 1, 'core')]
    if family == 'long_strangle':
        kp = _nearest({k: v for k, v in strikes.items() if k < spot}, spot * (1 - 0.5 * M), 'P')
        kc = _nearest({k: v for k, v in strikes.items() if k > spot}, spot * (1 + 0.5 * M), 'C')
        if kp is None or kc is None:
            return 'no_strike'
        return [(front, kc, 'C', 1, 'core'), (front, kp, 'P', 1, 'core')]
    if family in ('short_iron_fly_1x', 'short_iron_fly_2x'):
        w = 1.0 if family.endswith('1x') else 2.0
        kp = _nearest(strikes, atm - w * straddle, 'P', beyond=atm)
        kc = _nearest(strikes, atm + w * straddle, 'C', beyond=atm)
        if kp is None or kc is None:
            return 'no_wing'
        return [(front, atm, 'C', -1, 'core'), (front, atm, 'P', -1, 'core'),
                (front, kc, 'C', 1, 'wing'), (front, kp, 'P', 1, 'wing')]
    if family in ('short_iron_condor', 'short_iron_condor_wide'):
        inner, outer = (0.5, 1.5) if family == 'short_iron_condor' else (1.0, 2.0)
        sp = _nearest({k: v for k, v in strikes.items() if k < spot}, spot * (1 - inner * M), 'P')
        sc = _nearest({k: v for k, v in strikes.items() if k > spot}, spot * (1 + inner * M), 'C')
        if sp is None or sc is None:
            return 'no_strike'
        lp = _nearest(strikes, spot * (1 - outer * M), 'P', beyond=sp)
        lc = _nearest(strikes, spot * (1 + outer * M), 'C', beyond=sc)
        if lp is None or lc is None:
            return 'no_wing'
        return [(front, sc, 'C', -1, 'core'), (front, sp, 'P', -1, 'core'),
                (front, lc, 'C', 1, 'wing'), (front, lp, 'P', 1, 'wing')]
    if family in ('call_calendar', 'straddle_calendar'):
        if back is None or atm not in chain[back]:
            return 'no_back_expiry'
        leg = chain[back][atm]
        legs = [(front, atm, 'C', -1, 'core'), (back, atm, 'C', 1, 'core')]
        if leg[1] is None:
            return 'no_back_strike'
        if family == 'straddle_calendar':
            if leg[4] is None:
                return 'no_back_strike'
            legs += [(front, atm, 'P', -1, 'core'), (back, atm, 'P', 1, 'core')]
        return legs
    raise ValueError(family)


def leg_quote(chain, leg):
    ex, k, cp, _, _ = leg
    row = chain.get(ex, {}).get(k) if chain else None
    if row is None:
        return None
    base = 0 if cp == 'C' else 3
    bid, ask, oi = row[base], row[base + 1], row[base + 2]
    if bid is None or ask is None or ask <= 0 or bid < 0 or ask < bid:
        return None
    return bid, ask, oi


def liquidity(quotes_at_entry, legs, tier):
    lim = LIMITS[tier]
    for (bid, ask, oi), leg in zip(quotes_at_entry, legs):
        m = mid(bid, ask)
        if bid <= 0 or m < 0.05 or oi < 10 or (ask - bid) / m > lim[leg[4]]:
            return False
    return True


def risk_of(family, legs, entry_mids):
    value = sum(leg[3] * m for leg, m in zip(legs, entry_mids)) * MULT
    if family in SHORT_VOL and family not in ('call_calendar', 'straddle_calendar'):
        credit = -value
        if credit <= 0:
            return None, 'non_positive_credit'
        calls = sorted(leg[1] for leg in legs if leg[2] == 'C')
        puts = sorted(leg[1] for leg in legs if leg[2] == 'P')
        width = max(calls[-1] - calls[0], puts[-1] - puts[0]) * MULT
        risk = width - credit
    else:
        risk = value
        if risk <= 0:
            return None, 'non_positive_debit'
    if risk < 20:
        return None, 'risk_below_20'
    return risk, None


def plan_trade(market, ev, family, entry_label, exit_label, decision_off=None):
    """Choose contracts using information at the decision close (default: entry close).

    Returns (plan, None) or (None, skip_reason).  No exit-session data is read.
    """
    entry_off = offset(entry_label)
    decision_off = entry_off if decision_off is None else decision_off
    decision_day = market.session(ev, decision_off)
    entry_day = market.session(ev, entry_off)
    if decision_day is None or entry_day is None:
        return None, 'no_session'
    chain = market.chain(ev['secid'], decision_day)
    row = market.stock(ev['secid'], decision_day)
    if not chain:
        return None, 'no_entry_quotes'
    if row is None or row[0] is None or row[0] < 10:
        return None, 'spot_below_10_or_missing'
    spot = row[0]
    if exit_label == 'after_release':
        exit_rel = market.release_timing(ev, decision_day)
        if exit_rel is None:
            return None, 'no_release_history'
    else:
        exit_rel = exit_label
    exit_day = market.session(ev, offset(exit_rel))
    if exit_day is None:
        return None, 'no_session'
    front = market.front_expiry(ev, chain, exit_day, entry_day)
    if front is None:
        return None, 'no_front_expiry'
    atm = market.atm_strike(chain[front], spot)
    if atm is None:
        return None, 'no_atm'
    atm_leg = chain[front][atm]
    if atm_leg[1] <= 0 or atm_leg[4] <= 0:
        return None, 'no_atm'
    M = (mid(atm_leg[0], atm_leg[1]) + mid(atm_leg[3], atm_leg[4])) / spot
    back = market.back_expiry(chain, front)
    legs = build_package(family, chain, front, back, spot, atm, M)
    if isinstance(legs, str):
        return None, legs
    last_expiry = max(dt.date.fromisoformat(leg[0]) for leg in legs)
    if market.has_dividend(ev['secid'], entry_day, last_expiry):
        return None, 'dividend_in_window'
    feats = market.features(ev, decision_day, front, back, spot, atm, chain)
    return {'legs': legs, 'entry_day': entry_day, 'exit_day': exit_day, 'exit_rule': exit_rel, 'spot': spot,
            'front': front, 'back': back, 'atm': atm, 'features': feats, 'decision_day': decision_day}, None


def execute(market, ev, family, plan):
    """Entry quotes, liquidity tiers, risk, and exit P&L for a planned trade."""
    entry_chain = market.chain(ev['secid'], plan['entry_day'])
    entry_quotes = [leg_quote(entry_chain, leg) for leg in plan['legs']]
    if any(q is None for q in entry_quotes):
        return None, 'missing_entry_quote'
    entry_row = market.stock(ev['secid'], plan['entry_day'])
    if entry_row is None or entry_row[0] < 10:
        return None, 'spot_below_10_or_missing'
    tiers = [t for t in ('standard', 'tight') if liquidity(entry_quotes, plan['legs'], t)]
    if not tiers:
        return None, 'illiquid'
    entry_mids = [mid(b, a) for b, a, _ in entry_quotes]
    risk, why = risk_of(family, plan['legs'], entry_mids)
    if risk is None:
        return None, why
    exit_row = market.stock(ev['secid'], plan['exit_day'])
    if exit_row is None or entry_row[2] != exit_row[2]:
        return None, 'split_or_missing_stock_in_window'
    trade = {'tiers': tiers, 'risk': risk, 'legs': len(plan['legs'])}
    exit_chain = market.chain(ev['secid'], plan['exit_day'])
    exit_quotes = [leg_quote(exit_chain, leg) for leg in plan['legs']]
    if any(q is None for q in exit_quotes):
        trade['status'] = 'unresolved'
        return trade, None
    exit_mids = [mid(b, a) for b, a, _ in exit_quotes]
    gross = sum(leg[3] * (x - e) for leg, e, x in zip(plan['legs'], entry_mids, exit_mids)) * MULT
    half_spreads = sum(abs(leg[3]) * ((qa - qb) / 2 + (xa - xb) / 2)
                       for leg, (qb, qa, _), (xb, xa, _) in zip(plan['legs'], entry_quotes, exit_quotes)) * MULT
    fees = FEE * 2 * sum(abs(leg[3]) for leg in plan['legs'])
    trade.update(status='closed', fees=fees, half_spreads=half_spreads,
                 pnl_mid=gross - fees, pnl_c25=gross - fees - 0.25 * half_spreads,
                 pnl_c50=gross - fees - 0.50 * half_spreads)
    for c in ('mid', 'c25', 'c50'):
        trade['ret_' + c] = trade['pnl_' + c] / risk
    trade['exit_stock_move'] = math.log(exit_row[0] / entry_row[0]) if entry_row[0] > 0 and exit_row[0] > 0 else None
    return trade, None


def simulate_event(market, ev, decision_shift=0):
    """All base trades (family x timing) for one event; decision_shift=-1 decides one session early."""
    out = []
    for family in FAMILIES:
        for entry_label, exit_label in TIMINGS:
            rec = {'secid': ev['secid'], 'issuer': ev['issuer'], 'ticker': ev['ticker'], 'E': ev['E'],
                   'family': family, 'entry': entry_label, 'exit': exit_label}
            decision_off = offset(entry_label) + decision_shift if decision_shift else None
            plan, why = plan_trade(market, ev, family, entry_label, exit_label, decision_off)
            if plan is None:
                rec['status'] = 'skip:' + why
                out.append(rec)
                continue
            trade, why = execute(market, ev, family, plan)
            if trade is None:
                rec['status'] = 'skip:' + why
                out.append(rec)
                continue
            rec.update(trade)
            rec.update({'entry_day': plan['entry_day'], 'exit_day': plan['exit_day'], 'exit_rule': plan['exit_rule'],
                        'front': plan['front'], 'spot': plan['spot']})
            rec.update({'f_' + k: v for k, v in plan['features'].items()})
            out.append(rec)
    return out
