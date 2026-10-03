"""Paper-trading decisions for the strategies in STRATEGIES.md (S1-S5 validated, P1 provisional).

Broker-agnostic: callers build a research7-style Market from live data (sessions, stock closes, dividends, the
decision close's option chain, the event calendar with release timing) and call `entries_for` at the decision close
(about 15 minutes before the close) and `exits_due` each session. Decisions reuse research7.engine.plan and the
research5 filter evaluation unchanged, so live trades match the backtested rules exactly. Fills are not simulated
here: the broker adapter places limit orders at the leg mids and records every fill against the quoted bid/ask.
"""
from research5.candidates import passes
from research5.engine import LIMITS, leg_quote, mid
from research7 import engine

# rule id -> (research7 family, entry label, exit label, filter, liquidity tier, status)
RULES = {
    'S1': ('pre:long_strangle', 'P-1', 'P', 'R<=0.9', 'tight', 'validated'),
    'S2': ('pre:long_straddle', 'P-9', 'P', 'none', 'tight', 'validated'),
    'S3': ('pre:long_straddle', 'P-4', 'P', 'HR>=1.0', 'standard', 'validated'),
    'S4': ('pre:long_strangle', 'P-1', 'P', 'HR>=1.0', 'tight', 'validated'),
    'S5': ('pre:long_straddle', 'P-1', 'P', 'R<=0.9', 'tight', 'validated'),
    'P1': ('through:short_iron_fly_2x', 'P-4', 'Q+4', 'none', 'standard', 'provisional'),
}
TRADEABLE_TIMINGS = ('before_open', 'after_close', 'non_session_date')


def _liquid(chain, legs, tier):
    lim = LIMITS[tier]
    for leg in legs:
        q = leg_quote(chain, leg)
        if q is None:
            return False
        bid, ask, oi = q
        m = mid(bid, ask)
        if bid <= 0 or m < 0.05 or oi < 10 or (ask - bid) / m > lim[leg[4]]:
            return False
    return True


def entries_for(market, events, today_index, rules=RULES):
    """Orders to open at today's close: [{'rule', 'event', 'legs', 'limit_mids', 'exit_day', 'features'}].

    `events` are research7-style event dicts (secid, P_index, Q_index, Q, timing, ...) for upcoming releases whose
    timing is known; releases during the session or with unknown time are never traded.
    """
    orders = []
    for ev in events:
        if ev.get('timing') not in TRADEABLE_TIMINGS:
            continue
        for rid, (family, entry, exit_, flt, tier, _) in rules.items():
            if engine.rel_index(ev, entry) != today_index:
                continue
            phase, fam = family.split(':')
            plan, why = engine.plan(market, ev, phase, fam, entry, exit_)
            if plan is None:
                continue
            if not passes(flt, {'f_' + k: v for k, v in plan['features'].items()}):
                continue
            chain = market.chain(ev['secid'], plan['entry_day'])
            if not _liquid(chain, plan['legs'], tier):
                continue
            mids = [mid(*leg_quote(chain, leg)[:2]) for leg in plan['legs']]
            risk, why = engine.risk_of(fam, plan['legs'], mids)
            if risk is None:
                continue
            orders.append({'rule': rid, 'secid': ev['secid'], 'Q': ev['Q'], 'legs': plan['legs'], 'limit_mids': mids,
                           'risk_per_package': risk, 'entry_day': plan['entry_day'], 'exit_day': plan['exit_day'],
                           'features': plan['features']})
    return orders


def exits_due(open_positions, today):
    """Positions whose planned exit close is today (pre-release positions are never held through the release)."""
    return [p for p in open_positions if p['exit_day'] == today]


def size(order, equity, risk_fraction=0.02):
    """Contracts per leg multiple so that the package risk is about risk_fraction of equity (research convention)."""
    return max(int(equity * risk_fraction // order['risk_per_package']), 0)
