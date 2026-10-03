import copy
import datetime as dt
import unittest

from research5.engine import bs_price
from research7 import candidates, data, engine


def synthetic(n_events=10, spot=100.0, move=0.05):
    sessions, d = [], dt.date(2018, 1, 1)
    while len(sessions) < 900:
        if d.weekday() < 5:
            sessions.append(d)
        d += dt.timedelta(days=1)
    stocks = {1: {day: (spot, 0.002 if i % 2 else -0.002, 1.0, 1e6) for i, day in enumerate(sessions)}}
    events = []
    for k in range(n_events):
        q = 70 + 63 * k
        while sessions[q].weekday() != 3:  # Thursday reaction day, Friday weekly expiry
            q += 1
        sign = 1 if k % 2 else -1
        stocks[1][sessions[q]] = (spot, sign * move, 1.0, 1e6)
        for j in range(q, q + 8):
            stocks[1][sessions[j]] = (spot * (1 + sign * move), stocks[1][sessions[j]][1] if j == q else 0.0, 1.0, 1e6)
        events.append({'secid': 1, 'ticker': 'TST', 'issuer': 'TEST INC', 'ibes_ticker': 'TST', 'announce': sessions[q],
                       'anntims': '07:00:00', 'timing': 'before_open', 'E': sessions[q], 'P_index': q - 1, 'Q_index': q,
                       'P': sessions[q - 1], 'Q': sessions[q], 'eps': 1.10 if sign > 0 else 0.90,
                       'consensus': {'statpers': sessions[q - 5], 'mean': 1.0, 'stdev': 0.05, 'numest': 10}})
    quotes = {}
    for ev in events:
        expiries = [ev['Q'] + dt.timedelta(days=n) for n in (1, 8, 15, 29)]
        for off in range(-11, 6):
            idx = ev['Q_index'] + off
            day = sessions[idx]
            s = stocks[1][day][0]
            chain = {}
            for j, ex in enumerate(expiries):
                if ex < day:
                    continue
                strikes = {}
                for k2 in range(75, 126):
                    k = float(k2)
                    iv = [0.9, 0.6, 0.5, 0.45][j] if off < 0 else [0.3, 0.32, 0.33, 0.34][j]
                    t = max((ex - day).days, 0.5) / 365
                    c, p = bs_price(s, k, iv, t, True), bs_price(s, k, iv, t, False)
                    strikes[k] = [round(c * 0.99, 2), round(c * 1.01 + 0.02, 2), 500.0,
                                  round(p * 0.99, 2), round(p * 1.01 + 0.02, 2), 500.0]
                chain[ex.isoformat()] = strikes
            quotes[(1, day.isoformat())] = chain
    base = {'sessions': sessions, 'stocks': stocks, 'events': events, 'dividends': {}, 'issuer_of': {1: 'TEST INC'}}
    return base, quotes


def market(base, quotes):
    m = engine.Market(base, quotes)
    m.implied = {(ev['secid'], ev['Q']): m.implied_move_at_P(ev) for ev in base['events']}
    return m


class Research7Tests(unittest.TestCase):
    def test_release_timing_rule(self):
        sessions = [dt.date(2024, 1, d) for d in (2, 3, 4, 5, 8)]
        index = {d: i for i, d in enumerate(sessions)}
        self.assertEqual(data.release_timing(dt.date(2024, 1, 4), '07:30:00', sessions, index), (1, 2, 'before_open'))
        self.assertEqual(data.release_timing(dt.date(2024, 1, 4), '16:05:00', sessions, index), (2, 3, 'after_close'))
        self.assertEqual(data.release_timing(dt.date(2024, 1, 6), '16:05:00', sessions, index), (3, 4, 'non_session_date'))
        self.assertEqual(data.release_timing(dt.date(2024, 1, 4), '12:00:00', sessions, index)[2], 'during_session')
        self.assertEqual(data.release_timing(dt.date(2024, 1, 4), '', sessions, index)[2], 'missing_time')

    def test_pre_release_trade_exits_before_release_and_holds_event_expiry(self):
        base, quotes = synthetic()
        m = market(base, quotes)
        ev = base['events'][-1]
        p, why = engine.plan(m, ev, 'pre', 'long_straddle', 'P-4', 'P')
        self.assertIsNone(why)
        self.assertEqual(p['exit_day'], ev['P'])
        self.assertGreaterEqual(dt.date.fromisoformat(p['front']), ev['Q'])
        trade, why = engine.execute(m, ev, 'long_straddle', p)
        self.assertIsNone(why)
        self.assertEqual(trade['status'], 'closed')

    def test_calendar_hold_front_settles_on_expiry(self):
        base, quotes = synthetic()
        m = market(base, quotes)
        ev = base['events'][-1]
        p, why = engine.plan(m, ev, 'through', 'atm_straddle_calendar_1w', 'P', 'hold_front')
        self.assertIsNone(why)
        self.assertEqual(p['exit_day'].isoformat(), p['front'])
        trade, _ = engine.execute(m, ev, 'atm_straddle_calendar_1w', p)
        self.assertEqual(trade['settled_legs'], 2)

    def test_post_surprise_direction_and_jm(self):
        base, quotes = synthetic()
        m = market(base, quotes)
        up = base['events'][-1] if base['events'][-1]['eps'] > 1 else base['events'][-2]
        p, why = engine.plan(m, up, 'post', 'post_surprise_vertical', 'Q', 'Q+2')
        self.assertIsNone(why)
        self.assertGreater(p['features']['SUE'], 0)
        self.assertEqual({leg[2] for leg in p['legs']}, {'C'})
        self.assertIsNotNone(p['features']['JM'])

    def test_no_lookahead_any_base_trade_with_and_without_lag(self):
        base, quotes = synthetic()
        ev = base['events'][-2]
        m1 = market(base, quotes)
        for lag in (0, 1):
            for phase, family, entry, exit_ in engine.base_trades():
                p, why = engine.plan(m1, ev, phase, family, entry, exit_, lag)
                decision = m1.session(engine.rel_index(ev, entry) - lag)
                base2, quotes2 = copy.deepcopy(base), copy.deepcopy(quotes)
                for day in list(base2['stocks'][1]):
                    if day > decision:
                        base2['stocks'][1][day] = (1.0, 0.5, 3.0, 1.0)
                for key in list(quotes2):
                    if dt.date.fromisoformat(key[1]) > decision:
                        for chain in quotes2[key].values():
                            for leg in chain.values():
                                leg[:] = [0.01, 50.0, 1.0, 0.01, 50.0, 1.0]
                m2 = engine.Market(base2, quotes2, m1.implied)
                self.assertEqual(engine.plan(m2, ev, phase, family, entry, exit_, lag), (p, why),
                                 (phase, family, entry, exit_, lag))

    def test_lag_decides_one_session_earlier(self):
        base, quotes = synthetic()
        m = market(base, quotes)
        ev = base['events'][-1]
        p, _ = engine.plan(m, ev, 'through', 'short_iron_fly_2x', 'P', 'Q', lag=1)
        self.assertEqual(p['decision_day'], m.session(ev['P_index'] - 1))
        self.assertEqual(p['entry_day'], ev['P'])

    def test_grid(self):
        self.assertEqual(len(candidates.grid()), 1944)
        self.assertTrue(set(candidates.REPLICATIONS.values()) <= set(candidates.by_id()))


if __name__ == '__main__':
    unittest.main()
