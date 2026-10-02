"""Weekly calendars, diagonals and post-event option trades (research6 protocol).

Reuses the research5 Market (as-of data access and historical-only signals)
and its liquidity, fee and quote conventions without modifying them.
"""
import bisect
import datetime as dt
import math

from research5.engine import (FEE, MULT, Market, implied_vol, leg_quote, liquidity, mid, offset,
                              weekdays_between)

CALENDARS = ('atm_call_calendar', 'atm_put_calendar', 'atm_straddle_calendar', 'double_calendar_put',
             'double_calendar_0.75', 'double_calendar_straddle', 'double_calendar_1.25',
             'double_calendar_straddle_2w', 'double_diagonal_put', 'double_diagonal_straddle')
REVERSE = ('reverse_straddle_calendar',)
POST = ('post_iron_fly', 'post_momentum_vertical', 'post_reversal_vertical')
DIRECTIONAL = ('hist_drift_vertical',)
FAMILIES = CALENDARS + REVERSE + POST + DIRECTIONAL

CAL_TIMINGS = (('E-1', 'E+1'), ('E-1', 'hold_front'), ('E-1', 'after_release'), ('E-2', 'E+1'), ('E-2', 'hold_front'))
POST_TIMINGS = (('E+1', 'E+2'), ('E+1', 'E+3'))
DIR_TIMINGS = (('E-1', 'E+1'), ('E-1', 'after_release'), ('E-1', 'E+3'))


def timings(family):
    if family in CALENDARS or family in REVERSE:
        return CAL_TIMINGS
    if family in POST:
        return POST_TIMINGS
    return DIR_TIMINGS


def _date(ex):
    return dt.date.fromisoformat(ex)


def first_expiry(chain, low, high, after):
    for ex in sorted(chain):
        d = _date(ex)
        if low <= d <= high and d > after:
            return ex
    return None


def expiry_gap(chain, front, lo_days, hi_days):
    fd = _date(front)
    for ex in sorted(chain):
        if lo_days <= (_date(ex) - fd).days <= hi_days:
            return ex
    return None


def edge_strikes(strikes, spot, d):
    calls = [k for k, v in strikes.items() if v[1] is not None and k >= spot * (1 + d)]
    puts = [k for k, v in strikes.items() if v[4] is not None and k <= spot * (1 - d)]
    if not calls or not puts:
        return None, None
    return min(calls), max(puts)


def further(strikes, k, side):
    """Next quoted strike beyond k on the OTM side."""
    if side == 'C':
        out = [x for x, v in strikes.items() if x > k and v[1] is not None]
        return min(out) if out else None
    out = [x for x, v in strikes.items() if x < k and v[4] is not None]
    return max(out) if out else None


def has(chain, ex, k, cp):
    leg = chain.get(ex, {}).get(k)
    return leg is not None and leg[1 if cp == 'C' else 4] is not None


def atm_iv(chain, ex, k, spot, entry_day):
    t = max(weekdays_between(entry_day, _date(ex)), 1) / 252.0
    leg = chain[ex].get(k)
    if leg is None:
        return None, t
    vals = []
    if leg[0] is not None and leg[1] is not None and leg[1] > 0:
        vals.append(implied_vol(mid(leg[0], leg[1]), spot, k, t, True))
    if leg[3] is not None and leg[4] is not None and leg[4] > 0:
        vals.append(implied_vol(mid(leg[3], leg[4]), spot, k, t, False))
    vals = [v for v in vals if v]
    return (sum(vals) / len(vals) if vals else None), t


def last_session_on_or_before(market, day):
    i = bisect.bisect_right(market.sessions, day) - 1
    return market.sessions[i] if i >= 0 else None


def build(family, chain, spot, atm, M, front, back, direction=None):
    """Legs [(exdate, strike, cp, qty, role)] or a skip-reason string."""
    if family == 'atm_call_calendar':
        return [(front, atm, 'C', -1, 'core'), (back, atm, 'C', 1, 'core')] if has(chain, back, atm, 'C') else 'no_back_strike'
    if family == 'atm_put_calendar':
        return [(front, atm, 'P', -1, 'core'), (back, atm, 'P', 1, 'core')] if has(chain, back, atm, 'P') else 'no_back_strike'
    if family in ('atm_straddle_calendar', 'reverse_straddle_calendar'):
        if not (has(chain, back, atm, 'C') and has(chain, back, atm, 'P')):
            return 'no_back_strike'
        s = -1 if family == 'atm_straddle_calendar' else 1
        return [(front, atm, 'C', s, 'core'), (front, atm, 'P', s, 'core'),
                (back, atm, 'C', -s, 'core'), (back, atm, 'P', -s, 'core')]
    if family.startswith('double_'):
        tag = family.split('_')[2]
        d = {'put': None, '0.75': 0.75 * M, 'straddle': M, '1.25': 1.25 * M}[tag]
        if d is None:
            leg = chain[front][atm]
            d = mid(leg[3], leg[4]) / spot
        kc, kp = edge_strikes(chain[front], spot, d)
        if kc is None:
            return 'no_edge_strike'
        if family.startswith('double_calendar'):
            bc, bp = kc, kp
        else:
            bc, bp = further(chain[back], kc, 'C'), further(chain[back], kp, 'P')
            if bc is None or bp is None:
                return 'no_back_strike'
        if not (has(chain, back, bc, 'C') and has(chain, back, bp, 'P')):
            return 'no_back_strike'
        return [(front, kc, 'C', -1, 'core'), (front, kp, 'P', -1, 'core'),
                (back, bc, 'C', 1, 'core'), (back, bp, 'P', 1, 'core')]
    if family == 'post_iron_fly':
        straddle = M * spot
        kp = _beyond_nearest(chain[front], atm - straddle, 'P', atm)
        kc = _beyond_nearest(chain[front], atm + straddle, 'C', atm)
        if kp is None or kc is None:
            return 'no_wing'
        return [(front, atm, 'C', -1, 'core'), (front, atm, 'P', -1, 'core'),
                (front, kc, 'C', 1, 'wing'), (front, kp, 'P', 1, 'wing')]
    if family in ('post_momentum_vertical', 'post_reversal_vertical', 'hist_drift_vertical'):
        if not direction:
            return 'no_direction'
        cp = 'C' if direction > 0 else 'P'
        target = spot * (1 + M) if cp == 'C' else spot * (1 - M)
        k2 = _beyond_nearest(chain[front], target, cp, atm)
        if k2 is None:
            return 'no_strike'
        return [(front, atm, cp, 1, 'core'), (front, k2, cp, -1, 'core')]
    raise ValueError(family)


def _beyond_nearest(strikes, target, cp, beyond):
    best = None
    for k, leg in strikes.items():
        if leg[1 if cp == 'C' else 4] is None:
            continue
        if (cp == 'C' and k <= beyond) or (cp == 'P' and k >= beyond):
            continue
        if best is None or abs(k - target) < abs(best - target):
            best = k
    return best


def risk_of(family, legs, mids):
    value = sum(leg[3] * m for leg, m in zip(legs, mids)) * MULT
    if family == 'reverse_straddle_calendar':
        if value >= 0:
            return None, 'non_positive_credit'
        risk = sum(m for leg, m in zip(legs, mids) if leg[3] < 0) * MULT
    elif family == 'post_iron_fly':
        if value >= 0:
            return None, 'non_positive_credit'
        calls = sorted(leg[1] for leg in legs if leg[2] == 'C')
        puts = sorted(leg[1] for leg in legs if leg[2] == 'P')
        risk = max(calls[-1] - calls[0], puts[-1] - puts[0]) * MULT + value
    else:
        if value <= 0:
            return None, 'non_positive_debit'
        risk = value
        if family.startswith('double_diagonal'):
            gaps = []
            for cp in ('C', 'P'):
                ks = [leg[1] for leg in legs if leg[2] == cp]
                gaps.append(max(ks) - min(ks))
            risk += max(gaps) * MULT
    if risk < 20:
        return None, 'risk_below_20'
    return risk, None


def plan(market, ev, family, entry_label, exit_label):
    entry_day = market.session(ev, offset(entry_label))
    if entry_day is None:
        return None, 'no_session'
    chain = market.chain(ev['secid'], entry_day)
    row = market.stock(ev['secid'], entry_day)
    if not chain:
        return None, 'no_entry_quotes'
    if row is None or row[0] is None or row[0] < 10:
        return None, 'spot_below_10_or_missing'
    spot = row[0]
    e1 = market.session(ev, 1)
    e3 = market.session(ev, 3)
    if e1 is None or e3 is None:
        return None, 'no_session'
    feats = {}
    direction = None
    back = None
    if family in POST:
        exit_day = market.session(ev, offset(exit_label))
        front = first_expiry(chain, exit_day + dt.timedelta(days=1), exit_day + dt.timedelta(days=21), entry_day)
    elif family in DIRECTIONAL:
        exit_rel = market.release_timing(ev, entry_day) if exit_label == 'after_release' else exit_label
        if exit_rel is None:
            return None, 'no_release_history'
        exit_day = market.session(ev, offset(exit_rel))
        front = market.front_expiry(ev, chain, exit_day, entry_day)
    else:
        front = first_expiry(chain, e1, ev['E'] + dt.timedelta(days=10), entry_day)
        if front is None:
            return None, 'no_front_expiry'
        back = expiry_gap(chain, front, 13, 15) if family.endswith('_2w') else expiry_gap(chain, front, 6, 8)
        if back is None:
            return None, 'no_back_expiry'
        if exit_label == 'hold_front':
            exit_day = last_session_on_or_before(market, min(_date(front), e3))
        elif exit_label == 'after_release':
            rel = market.release_timing(ev, entry_day)
            if rel is None:
                return None, 'no_release_history'
            exit_day = market.session(ev, offset(rel))
        else:
            exit_day = market.session(ev, offset(exit_label))
    if front is None:
        return None, 'no_front_expiry'
    if exit_day is None or exit_day <= entry_day or exit_day > _date(front):
        return None, 'exit_after_front_expiry'
    atm = market.atm_strike(chain[front], spot)
    if atm is None or chain[front][atm][1] <= 0 or chain[front][atm][4] <= 0:
        return None, 'no_atm'
    leg = chain[front][atm]
    M = (mid(leg[0], leg[1]) + mid(leg[3], leg[4])) / spot

    if family in POST:
        r0 = market.log_return(ev['secid'], market.session(ev, 0))
        r1 = market.log_return(ev['secid'], e1)
        m_pre = market.straddle_move(ev)
        if r0 is None or r1 is None:
            return None, 'no_event_move'
        j = r0 + r1
        feats['JM'] = abs(j) / m_pre if m_pre else None
        if family == 'post_momentum_vertical':
            direction = 1 if j > 0 else -1 if j < 0 else None
        elif family == 'post_reversal_vertical':
            direction = -1 if j > 0 else 1 if j < 0 else None
    base = market.features(ev, entry_day, front, back, spot, atm, chain)
    feats.update({k: base[k] for k in ('M', 'R', 'HR', 'H')})
    if family in DIRECTIONAL:
        earlier = market.earlier_events(ev, entry_day, 1)[-8:]
        moves = [m[0] for m in (market.event_move(k) for k in earlier) if m is not None]
        if len(moves) >= 6 and base['H']:
            drift = sum(moves) / len(moves)
            feats['DRIFT'] = abs(drift) / base['H']
            direction = 1 if drift > 0 else -1 if drift < 0 else None
    if back is not None:
        ivf, tf = atm_iv(chain, front, atm, spot, entry_day)
        ivb, tb = atm_iv(chain, back, atm, spot, entry_day)
        if ivf and ivb:
            feats['TSw'] = ivf / ivb
            if tb > tf:
                var_d = (ivb * ivb * tb - ivf * ivf * tf) / (tb - tf)
                sigma = market.background_vol(ev, entry_day, market.earlier_events(ev, entry_day, 1))
                if var_d > 0 and sigma:
                    feats['D'] = math.sqrt(var_d) / (sigma * math.sqrt(252.0))
    legs = build(family, chain, spot, atm, M, front, back, direction)
    if isinstance(legs, str):
        return None, legs
    last_expiry = max(_date(leg[0]) for leg in legs)
    if market.has_dividend(ev['secid'], entry_day, last_expiry):
        return None, 'dividend_in_window'
    return {'legs': legs, 'entry_day': entry_day, 'exit_day': exit_day, 'front': front, 'back': back,
            'spot': spot, 'features': feats}, None


def execute(market, ev, family, p):
    entry_chain = market.chain(ev['secid'], p['entry_day'])
    quotes = [leg_quote(entry_chain, leg) for leg in p['legs']]
    if any(q is None for q in quotes):
        return None, 'missing_entry_quote'
    tiers = [t for t in ('standard', 'tight') if liquidity(quotes, p['legs'], t)]
    if not tiers:
        return None, 'illiquid'
    mids = [mid(b, a) for b, a, _ in quotes]
    risk, why = risk_of(family, p['legs'], mids)
    if risk is None:
        return None, why
    entry_row = market.stock(ev['secid'], p['entry_day'])
    exit_row = market.stock(ev['secid'], p['exit_day'])
    if exit_row is None or entry_row[2] != exit_row[2]:
        return None, 'split_or_missing_stock_in_window'
    trade = {'tiers': tiers, 'risk': risk, 'legs': len(p['legs'])}
    exit_chain = market.chain(ev['secid'], p['exit_day'])
    exit_iso = p['exit_day'].isoformat()
    exit_vals, exit_half = [], []
    settled = 0
    for leg in p['legs']:
        if leg[0] == exit_iso:
            k, s = leg[1], exit_row[0]
            exit_vals.append(max(s - k, 0.0) if leg[2] == 'C' else max(k - s, 0.0))
            exit_half.append(0.0)
            settled += 1
            continue
        q = leg_quote(exit_chain, leg)
        if q is None:
            trade['status'] = 'unresolved'
            return trade, None
        exit_vals.append(mid(q[0], q[1]))
        exit_half.append((q[1] - q[0]) / 2)
    gross = sum(leg[3] * (x - e) for leg, e, x in zip(p['legs'], mids, exit_vals)) * MULT
    half = sum(abs(leg[3]) * ((a - b) / 2 + h) for leg, (b, a, _), h in zip(p['legs'], quotes, exit_half)) * MULT
    # Settled legs pay no exit commission.
    fees = FEE * sum(abs(leg[3]) for leg in p['legs']) * 2 - FEE * settled
    trade.update(status='closed', fees=fees, half_spreads=half, settled_legs=settled,
                 pnl_mid=gross - fees, pnl_c25=gross - fees - 0.25 * half, pnl_c50=gross - fees - 0.5 * half)
    for c in ('mid', 'c25', 'c50'):
        trade['ret_' + c] = trade['pnl_' + c] / risk
    trade['exit_stock_move'] = math.log(exit_row[0] / entry_row[0]) if entry_row[0] > 0 and exit_row[0] > 0 else None
    return trade, None


def simulate_event(market, ev):
    out = []
    for family in FAMILIES:
        for entry_label, exit_label in timings(family):
            rec = {'secid': ev['secid'], 'issuer': ev['issuer'], 'ticker': ev['ticker'], 'E': ev['E'],
                   'family': family, 'entry': entry_label, 'exit': exit_label}
            p, why = plan(market, ev, family, entry_label, exit_label)
            if p is None:
                rec['status'] = 'skip:' + why
                out.append(rec)
                continue
            trade, why = execute(market, ev, family, p)
            if trade is None:
                rec['status'] = 'skip:' + why
                out.append(rec)
                continue
            rec.update(trade)
            rec.update({'entry_day': p['entry_day'], 'exit_day': p['exit_day'], 'front': p['front'],
                        'back': p['back'], 'spot': p['spot']})
            rec.update({'f_' + k: v for k, v in p['features'].items()})
            out.append(rec)
    return out
