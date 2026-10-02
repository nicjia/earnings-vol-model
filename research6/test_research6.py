import copy
import datetime as dt
import unittest

from research5.engine import Market, bs_price, mid
from research6 import candidates, engine


def synthetic(n_events=9, spot=100.0, move=0.04):
    sessions, d = [], dt.date(2018, 1, 1)
    while len(sessions) < 800:
        if d.weekday() < 5:
            sessions.append(d)
        d += dt.timedelta(days=1)
    stocks = {1: {day: (spot, 0.001 if i % 2 else -0.001, 1.0, 1e6) for i, day in enumerate(sessions)}}
    events = []
    for k in range(n_events):
        idx = 60 + 63 * k
        while sessions[idx].weekday() != 2:  # Wednesday reports, Friday weekly expiry
            idx += 1
        events.append({'secid': 1, 'ticker': 'TST', 'issuer': 'TEST INC', 'announce': sessions[idx],
                       'E': sessions[idx], 'E_index': idx})
        sign = 1 if k % 2 else -1
        stocks[1][sessions[idx]] = (spot, sign * move, 1.0, 1e6)
        stocks[1][sessions[idx + 1]] = (spot * (1 + sign * move), 0.0, 1.0, 1e6)
        stocks[1][sessions[idx + 2]] = (spot * (1 + sign * move), 0.0, 1.0, 1e6)
    quotes = {}
    for ev in events:
        expiries = [ev['E'] + dt.timedelta(days=n) for n in (2, 9, 16)]
        for off in range(-2, 4):
            day = sessions[ev['E_index'] + off]
            s = stocks[1][day][0]
            chain = {}
            for j, ex in enumerate(expiries):
                if ex < day:
                    continue
                strikes = {}
                for k2 in range(80, 121):
                    k = k2 * 1.0
                    iv = [0.9, 0.6, 0.5][j] if off < 0 else [0.3, 0.32, 0.33][j]
                    t = max((ex - day).days, 0.5) / 365
                    c, p = bs_price(s, k, iv, t, True), bs_price(s, k, iv, t, False)
                    strikes[k] = [round(c * 0.99, 2), round(c * 1.01 + 0.02, 2), 500.0,
                                  round(p * 0.99, 2), round(p * 1.01 + 0.02, 2), 500.0]
                chain[ex.isoformat()] = strikes
            quotes[(1, day.isoformat())] = chain
    return {'sessions': sessions, 'stocks': stocks, 'events': events, 'dividends': {},
            'issuer_of': {1: 'TEST INC'}, 'ticker_of': {1: 'TST'}}, quotes


class Research6Tests(unittest.TestCase):
    def test_double_calendar_edges_and_expiry_settlement(self):
        base, quotes = synthetic()
        m = Market(base, quotes)
        ev = base['events'][-1]
        p, why = engine.plan(m, ev, 'double_calendar_straddle', 'E-1', 'hold_front')
        self.assertIsNone(why)
        chain = m.chain(1, p['entry_day'])
        spot = p['spot']
        M = p['features']['M']
        calls = [leg for leg in p['legs'] if leg[2] == 'C']
        puts = [leg for leg in p['legs'] if leg[2] == 'P']
        self.assertTrue(all(leg[1] >= spot * (1 + M) for leg in calls))
        self.assertTrue(all(leg[1] <= spot * (1 - M) for leg in puts))
        self.assertEqual({leg[0] for leg in p['legs'] if leg[3] < 0}, {p['front']})
        self.assertEqual({leg[0] for leg in p['legs'] if leg[3] > 0}, {p['back']})
        self.assertEqual(p['exit_day'].isoformat(), p['front'])  # weekly expires on E+2
        trade, why = engine.execute(m, ev, 'double_calendar_straddle', p)
        self.assertIsNone(why)
        self.assertEqual(trade['settled_legs'], 2)
        exit_chain = m.chain(1, p['exit_day'])
        s_exit = m.stock(1, p['exit_day'])[0]
        gross = 0.0
        for ex, k, cp, q, _ in p['legs']:
            b = 0 if cp == 'C' else 3
            entry = mid(chain[ex][k][b], chain[ex][k][b + 1])
            if ex == p['front']:
                out = max(s_exit - k, 0) if cp == 'C' else max(k - s_exit, 0)
            else:
                out = mid(exit_chain[ex][k][b], exit_chain[ex][k][b + 1])
            gross += q * (out - entry)
        self.assertAlmostEqual(trade['pnl_mid'], gross * 100 - 0.65 * (8 - 2), places=9)

    def test_put_sized_edges_are_inside_straddle_edges(self):
        base, quotes = synthetic()
        m = Market(base, quotes)
        ev = base['events'][-1]
        p1, _ = engine.plan(m, ev, 'double_calendar_put', 'E-1', 'E+1')
        p2, _ = engine.plan(m, ev, 'double_calendar_straddle', 'E-1', 'E+1')
        c1 = [leg[1] for leg in p1['legs'] if leg[2] == 'C'][0]
        c2 = [leg[1] for leg in p2['legs'] if leg[2] == 'C'][0]
        self.assertLess(c1, c2)

    def test_diagonal_risk_adds_strike_gap(self):
        legs = [('f', 110.0, 'C', -1, 'core'), ('f', 90.0, 'P', -1, 'core'),
                ('b', 112.0, 'C', 1, 'core'), ('b', 87.0, 'P', 1, 'core')]
        risk, _ = engine.risk_of('double_diagonal_straddle', legs, [1.0, 1.0, 1.5, 1.4])
        self.assertAlmostEqual(risk, (0.9) * 100 + 3 * 100)

    def test_post_event_direction(self):
        base, quotes = synthetic()
        m = Market(base, quotes)
        up = base['events'][-1]  # k=8 -> sign -1 ; use an up event
        up = base['events'][-2]
        p, _ = engine.plan(m, up, 'post_momentum_vertical', 'E+1', 'E+3')
        self.assertEqual({leg[2] for leg in p['legs']}, {'C'})
        p, _ = engine.plan(m, up, 'post_reversal_vertical', 'E+1', 'E+3')
        self.assertEqual({leg[2] for leg in p['legs']}, {'P'})

    def test_no_lookahead_in_any_family(self):
        base, quotes = synthetic()
        ev = base['events'][-2]
        m1 = Market(base, quotes)
        plans = {}
        for f in engine.FAMILIES:
            for entry, exit_ in engine.timings(f):
                plans[(f, entry, exit_)] = engine.plan(m1, ev, f, entry, exit_)
        for (f, entry, exit_), (p, why) in plans.items():
            decision = m1.session(ev, int(entry[1:]))
            base2, quotes2 = copy.deepcopy(base), copy.deepcopy(quotes)
            for day in list(base2['stocks'][1]):
                if day > decision:
                    base2['stocks'][1][day] = (1.0, 0.5, 3.0, 1.0)
            for key in list(quotes2):
                if dt.date.fromisoformat(key[1]) > decision:
                    for chain in quotes2[key].values():
                        for leg in chain.values():
                            leg[:] = [0.01, 50.0, 1.0, 0.01, 50.0, 1.0]
            self.assertEqual(engine.plan(Market(base2, quotes2), ev, f, entry, exit_), (p, why), (f, entry, exit_))

    def test_grid_size(self):
        n = (10 * 5 * 8 + 1 * 5 * 4 + 1 * 2 * 3 + 2 * 2 * 3 + 1 * 3 * 3) * 2
        self.assertEqual(len(candidates.grid()), n)


if __name__ == '__main__':
    unittest.main()
