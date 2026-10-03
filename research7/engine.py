"""Release-timed earnings option trades (research7 protocol).

Every event carries P (last close before the I/B/E/S release) and Q (first close after it).
Decisions read stock data to the decision close, quotes at that close, earlier events whose Q
precedes the decision, and consensus rows dated on or before P. Exit quotes are read only in
``execute``. Package builders and conventions are reused from research5/research6 unchanged.
"""
import bisect
import datetime as dt
import math

from research5 import engine as r5
from research5.engine import FEE, MULT, expected_abs, leg_quote, liquidity, mid, weekdays_between
from research6 import engine as r6

PRE = {'long_straddle': 'long', 'long_strangle': 'long', 'straddle_calendar_1w': 'short', 'short_iron_fly_2x': 'short'}
THROUGH_NONCAL = {'long_straddle': 'long', 'long_strangle': 'long', 'short_iron_fly_1x': 'short',
                  'short_iron_fly_2x': 'short', 'short_iron_condor': 'short', 'short_iron_condor_wide': 'short'}
THROUGH_CAL = ('atm_straddle_calendar_1w', 'atm_put_calendar_1w', 'atm_straddle_calendar_month', 'double_calendar_put_1w',
               'double_calendar_straddle_1w', 'double_calendar_straddle_2w', 'double_diagonal_put_1w')
POST = ('post_iron_fly_1x', 'post_momentum_vertical', 'post_reversal_vertical', 'post_surprise_vertical')

PRE_TIMINGS = (('P-9', 'P'), ('P-4', 'P'), ('P-1', 'P'))
NONCAL_TIMINGS = tuple((a, b) for a in ('P', 'P-1', 'P-4') for b in ('Q', 'Q+2', 'Q+4'))
CAL_TIMINGS = tuple((a, b) for a in ('P', 'P-1', 'P-4') for b in ('Q', 'hold_front'))
POST_TIMINGS = (('Q', 'Q+2'), ('Q', 'Q+4'))

# research7 family -> (builder module, builder family name, back expiry rule)
R6_BUILD = {
    'straddle_calendar_1w': ('atm_straddle_calendar', '1w'), 'atm_straddle_calendar_1w': ('atm_straddle_calendar', '1w'),
    'atm_put_calendar_1w': ('atm_put_calendar', '1w'), 'atm_straddle_calendar_month': ('atm_straddle_calendar', 'month'),
    'double_calendar_put_1w': ('double_calendar_put', '1w'), 'double_calendar_straddle_1w': ('double_calendar_straddle', '1w'),
    'double_calendar_straddle_2w': ('double_calendar_straddle', '2w'), 'double_diagonal_put_1w': ('double_diagonal_put', '1w'),
    'post_iron_fly_1x': ('post_iron_fly', None), 'post_momentum_vertical': ('post_momentum_vertical', None),
    'post_reversal_vertical': ('post_reversal_vertical', None), 'post_surprise_vertical': ('post_momentum_vertical', None),
}


def base_trades():
    """(phase, family, entry, exit) for every base trade, in a fixed order."""
    out = []
    for f in PRE:
        out += [('pre', f, a, b) for a, b in PRE_TIMINGS]
    for f in THROUGH_NONCAL:
        out += [('through', f, a, b) for a, b in NONCAL_TIMINGS]
    for f in THROUGH_CAL:
        out += [('through', f, a, b) for a, b in CAL_TIMINGS]
    for f in POST:
        out += [('post', f, a, b) for a, b in POST_TIMINGS]
    return out


def rel_index(ev, label):
    anchor = ev['P_index'] if label.startswith('P') else ev['Q_index']
    return anchor + (int(label[1:]) if len(label) > 1 else 0)


def _date(ex):
    return dt.date.fromisoformat(ex)


class Market:
    def __init__(self, base, quotes, implied=None):
        self.sessions = base['sessions']
        self.stocks = base['stocks']
        self.dividends = base['dividends']
        self.quotes = quotes
        self.by_sid = {}
        for ev in base['events']:
            self.by_sid.setdefault(ev['secid'], []).append(ev)
        self.implied = implied or {}
        self._memo = {}

    def session(self, i):
        return self.sessions[i] if 0 <= i < len(self.sessions) else None

    def chain(self, secid, day):
        return self.quotes.get((secid, day.isoformat())) if day else None

    def stock(self, secid, day):
        return self.stocks.get(secid, {}).get(day)

    def log_return(self, secid, i):
        row = self.stock(secid, self.session(i))
        if row is None or row[1] is None or math.isnan(row[1]) or row[1] <= -1:
            return None
        return math.log1p(row[1])

    def release_move(self, ev):
        total = 0.0
        for i in range(ev['P_index'] + 1, ev['Q_index'] + 1):
            r = self.log_return(ev['secid'], i)
            if r is None:
                return None
            total += r
        return total

    def earlier(self, ev, decision_index):
        return [k for k in self.by_sid.get(ev['secid'], []) if k['Q'] < ev['Q'] and k['Q_index'] <= decision_index]

    def background_vol(self, ev, decision_index, earlier):
        excluded = set()
        for k in earlier:
            excluded.update(range(k['P_index'] + 1, k['Q_index'] + 1))
        rets, j = [], decision_index
        while j > 0 and len(rets) < 60:
            if j not in excluded:
                r = self.log_return(ev['secid'], j)
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

    def has_dividend(self, secid, start, end):
        dates = self.dividends.get(secid, [])
        i = bisect.bisect_right(dates, start)
        return i < len(dates) and dates[i] <= end

    def pre_release_front(self, ev, chain, decision_day):
        return r6.first_expiry(chain, ev['Q'], ev['Q'] + dt.timedelta(days=10), decision_day)

    def implied_move_at_P(self, ev):
        """M at P with the pre-release front (used as M_k for later events' HR)."""
        day = ev['P']
        chain = self.chain(ev['secid'], day)
        row = self.stock(ev['secid'], day)
        if not chain or not row or not row[0]:
            return None
        front = self.pre_release_front(ev, chain, day)
        if front is None:
            return None
        k = atm_strike(chain[front], row[0])
        if k is None:
            return None
        leg = chain[front][k]
        if leg[1] <= 0 or leg[4] <= 0:
            return None
        return (mid(leg[0], leg[1]) + mid(leg[3], leg[4])) / row[0]

    def features(self, ev, decision_index, front, chain, spot, atm):
        key = (ev['secid'], ev['Q'], decision_index, front, atm)
        if key in self._memo:
            return dict(self._memo[key])
        decision_day = self.session(decision_index)
        leg = chain[front][atm]
        M = (mid(leg[0], leg[1]) + mid(leg[3], leg[4])) / spot
        out = {'M': M, 'R': None, 'H': None, 'HR': None, 'TSw': None, 'D': None}
        earlier = self.earlier(ev, decision_index)
        last8 = earlier[-8:]
        sigma = self.background_vol(ev, decision_index, earlier)
        moves = [m for m in (self.release_move(k) for k in last8) if m is not None]
        if sigma is not None and len(moves) >= 6:
            n = weekdays_between(decision_day, _date(front))
            s = sigma * math.sqrt(max(n - 1, 0) / 252.0)
            H = sum(expected_abs(j, s) for j in moves) / len(moves)
            if H > 0:
                out['H'], out['R'] = H, M / H
        ratios = []
        for k in last8:
            mk, jk = self.implied.get((k['secid'], k['Q'])), self.release_move(k)
            if mk and jk is not None:
                ratios.append(abs(jk) / mk)
        if len(ratios) >= 4:
            out['HR'] = sum(ratios) / len(ratios)
        back = r6.expiry_gap(chain, front, 6, 8)
        if back is not None and atm in chain[back]:
            ivf, tf = r6.atm_iv(chain, front, atm, spot, decision_day)
            ivb, tb = r6.atm_iv(chain, back, atm, spot, decision_day)
            if ivf and ivb:
                out['TSw'] = ivf / ivb
                if tb > tf and sigma:
                    var_d = (ivb * ivb * tb - ivf * ivf * tf) / (tb - tf)
                    if var_d > 0:
                        out['D'] = math.sqrt(var_d) / (sigma * math.sqrt(252.0))
        self._memo[key] = out
        return dict(out)


def atm_strike(strikes, spot):
    best = None
    for k, leg in strikes.items():
        if None in (leg[0], leg[1], leg[3], leg[4]):
            continue
        if best is None or abs(k - spot) < abs(best - spot):
            best = k
    return best


def back_expiry(chain, front, rule):
    if rule == '1w':
        return r6.expiry_gap(chain, front, 6, 8)
    if rule == '2w':
        return r6.expiry_gap(chain, front, 13, 15)
    if rule == 'month':
        fd = _date(front)
        later = sorted(ex for ex in chain if (_date(ex) - fd).days >= 21)
        return later[0] if later else None
    return None


def exit_index(m, ev, exit_label, front):
    if exit_label != 'hold_front':
        return rel_index(ev, exit_label)
    cap = m.session(ev['Q_index'] + 4)
    if cap is None:
        return None
    target = min(_date(front), cap)
    return bisect.bisect_right(m.sessions, target) - 1


def plan(m, ev, phase, family, entry_label, exit_label, lag=0):
    """Contracts and features from the decision close (entry close, or one session earlier if lag=1)."""
    entry_i = rel_index(ev, entry_label)
    decision_i = entry_i - lag
    decision_day, entry_day = m.session(decision_i), m.session(entry_i)
    if decision_day is None or entry_day is None:
        return None, 'no_session'
    if phase == 'post' and decision_i < ev['Q_index']:
        return None, 'decision_before_release'  # the release move and reported EPS are not yet known
    chain = m.chain(ev['secid'], decision_day)
    row = m.stock(ev['secid'], decision_day)
    if not chain:
        return None, 'no_decision_quotes'
    if row is None or not row[0] or row[0] < 10:
        return None, 'spot_below_10_or_missing'
    spot = row[0]
    feats = {}
    direction = None
    back = None
    if phase == 'post':
        exit_i = rel_index(ev, exit_label)
        exit_day = m.session(exit_i)
        if exit_day is None:
            return None, 'no_session'
        front = r6.first_expiry(chain, exit_day + dt.timedelta(days=1), exit_day + dt.timedelta(days=21), decision_day)
    elif phase == 'pre' or family in THROUGH_CAL:
        front = m.pre_release_front(ev, chain, decision_day)
        if front is None:
            return None, 'no_front_expiry'
        exit_i = exit_index(m, ev, exit_label, front)
    else:
        exit_i = rel_index(ev, exit_label)
        exit_day = m.session(exit_i)
        if exit_day is None:
            return None, 'no_session'
        front = r6.first_expiry(chain, max(exit_day, ev['Q']), ev['Q'] + dt.timedelta(days=30), decision_day)
    if front is None:
        return None, 'no_front_expiry'
    exit_day = m.session(exit_i) if exit_i is not None else None
    if exit_day is None or exit_i <= entry_i:
        return None, 'no_exit_session'
    if exit_day > _date(front):
        return None, 'exit_after_front_expiry'
    atm = atm_strike(chain[front], spot)
    if atm is None or chain[front][atm][1] <= 0 or chain[front][atm][4] <= 0:
        return None, 'no_atm'
    feats.update(m.features(ev, decision_i, front, chain, spot, atm))
    M = feats['M']
    if phase == 'post':
        j = m.release_move(ev)
        m_pre = m.implied.get((ev['secid'], ev['Q']))
        if j is None:
            return None, 'no_release_move'
        feats['JM'] = abs(j) / m_pre if m_pre else None
        cons = ev.get('consensus')
        if cons and ev.get('eps') is not None and m.stock(ev['secid'], ev['P']):
            sue = (ev['eps'] - cons['mean']) / m.stock(ev['secid'], ev['P'])[0]
            feats['SUE'], feats['ASUE'] = sue, abs(sue)
        if family == 'post_momentum_vertical':
            direction = (j > 0) - (j < 0)
        elif family == 'post_reversal_vertical':
            direction = (j < 0) - (j > 0)
        elif family == 'post_surprise_vertical':
            sue = feats.get('SUE')
            direction = None if sue is None else (sue > 0) - (sue < 0)
    if family in R6_BUILD:
        name, rule = R6_BUILD[family]
        if rule:
            back = back_expiry(chain, front, rule)
            if back is None:
                return None, 'no_back_expiry'
        legs = r6.build(name, chain, spot, atm, M, front, back, direction or None)
    else:
        legs = r5.build_package(family, chain, front, None, spot, atm, M)
    if isinstance(legs, str):
        return None, legs
    last_expiry = max(_date(leg[0]) for leg in legs)
    if m.has_dividend(ev['secid'], entry_day, last_expiry):
        return None, 'dividend_in_window'
    return {'legs': legs, 'entry_day': entry_day, 'exit_day': exit_day, 'front': front, 'back': back, 'spot': spot,
            'features': feats, 'decision_day': decision_day}, None


def risk_of(family, legs, mids):
    if family in R6_BUILD:
        return r6.risk_of(R6_BUILD[family][0], legs, mids)
    return r5.risk_of(family, legs, mids)


def execute(m, ev, family, p):
    entry_chain = m.chain(ev['secid'], p['entry_day'])
    quotes = [leg_quote(entry_chain, leg) for leg in p['legs']]
    if any(q is None for q in quotes):
        return None, 'missing_entry_quote'
    entry_row = m.stock(ev['secid'], p['entry_day'])
    if entry_row is None or not entry_row[0] or entry_row[0] < 10:
        return None, 'spot_below_10_or_missing'
    tiers = [t for t in ('standard', 'tight') if liquidity(quotes, p['legs'], t)]
    if not tiers:
        return None, 'illiquid'
    mids = [mid(b, a) for b, a, _ in quotes]
    risk, why = risk_of(family, p['legs'], mids)
    if risk is None:
        return None, why
    exit_row = m.stock(ev['secid'], p['exit_day'])
    if exit_row is None or entry_row[2] != exit_row[2]:
        return None, 'split_or_missing_stock_in_window'
    trade = {'tiers': tiers, 'risk': risk, 'legs': len(p['legs'])}
    exit_chain = m.chain(ev['secid'], p['exit_day'])
    exit_iso = p['exit_day'].isoformat()
    vals, half_exit, settled = [], [], 0
    for leg in p['legs']:
        if leg[0] == exit_iso:
            k, s = leg[1], exit_row[0]
            vals.append(max(s - k, 0.0) if leg[2] == 'C' else max(k - s, 0.0))
            half_exit.append(0.0)
            settled += 1
            continue
        q = leg_quote(exit_chain, leg)
        if q is None:
            trade['status'] = 'unresolved'
            return trade, None
        vals.append(mid(q[0], q[1]))
        half_exit.append((q[1] - q[0]) / 2)
    gross = sum(leg[3] * (x - e) for leg, e, x in zip(p['legs'], mids, vals)) * MULT
    half = sum(abs(leg[3]) * ((a - b) / 2 + h) for leg, (b, a, _), h in zip(p['legs'], quotes, half_exit)) * MULT
    fees = FEE * sum(abs(leg[3]) for leg in p['legs']) * 2 - FEE * settled
    trade.update(status='closed', fees=fees, half_spreads=half, settled_legs=settled,
                 pnl_mid=gross - fees, pnl_c25=gross - fees - 0.25 * half, pnl_c50=gross - fees - 0.5 * half)
    for c in ('mid', 'c25', 'c50'):
        trade['ret_' + c] = trade['pnl_' + c] / risk
    trade['exit_stock_move'] = math.log(exit_row[0] / entry_row[0]) if entry_row[0] > 0 and exit_row[0] > 0 else None
    return trade, None


def simulate_event(m, ev, lag=0):
    out = []
    for phase, family, entry_label, exit_label in base_trades():
        rec = {'secid': ev['secid'], 'issuer': ev['issuer'], 'ticker': ev['ticker'], 'E': ev['E'], 'Q': ev['Q'],
               'timing': ev['timing'], 'phase': phase, 'family': f'{phase}:{family}', 'entry': entry_label,
               'exit': exit_label}
        p, why = plan(m, ev, phase, family, entry_label, exit_label, lag)
        if p is None:
            rec['status'] = 'skip:' + why
            out.append(rec)
            continue
        trade, why = execute(m, ev, family, p)
        if trade is None:
            rec['status'] = 'skip:' + why
            out.append(rec)
            continue
        rec.update(trade)
        rec.update({'entry_day': p['entry_day'], 'exit_day': p['exit_day'], 'front': p['front'], 'back': p['back'],
                    'spot': p['spot']})
        rec.update({'f_' + k: v for k, v in p['features'].items()})
        out.append(rec)
    return out
