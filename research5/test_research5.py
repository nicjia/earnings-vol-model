import copy
import datetime as dt
import json
import math
import os
import tempfile
import unittest
from unittest.mock import patch

from research5 import candidates, engine, run, stats


def synthetic(n_events=10, spot=100.0, move=0.05):
    """Weekday sessions, one security, quarterly events with a fixed ATM chain."""
    sessions, d = [], dt.date(2018, 1, 1)
    while len(sessions) < 800:
        if d.weekday() < 5:
            sessions.append(d)
        d += dt.timedelta(days=1)
    stocks = {1: {}}
    events = []
    for i, day in enumerate(sessions):
        stocks[1][day] = (spot, 0.001 if i % 2 else -0.001, 1.0, 1e6)
    for k in range(n_events):
        idx = 60 + 63 * k
        events.append({'secid': 1, 'ticker': 'TST', 'issuer': 'TEST INC', 'announce': sessions[idx],
                       'E': sessions[idx], 'E_index': idx})
        stocks[1][sessions[idx]] = (spot, move if k % 2 else -move, 1.0, 1e6)
    quotes = {}
    for ev in events:
        expiries = [ev['E'] + dt.timedelta(days=9), ev['E'] + dt.timedelta(days=30)]
        for off in range(-2, 4):
            day = sessions[ev['E_index'] + off]
            chain = {}
            for j, ex in enumerate(expiries):
                strikes = {}
                for k in range(80, 125, 5):
                    iv = (0.6 if j == 0 else 0.4) * (0.5 if off >= 0 else 1.0)
                    t = max((ex - day).days, 1) / 365
                    c = engine.bs_price(spot, k, iv, t, True)
                    p = engine.bs_price(spot, k, iv, t, False)
                    strikes[float(k)] = [round(c * 0.98, 2), round(c * 1.02 + 0.01, 2), 500.0,
                                         round(p * 0.98, 2), round(p * 1.02 + 0.01, 2), 500.0]
                chain[ex.isoformat()] = strikes
            quotes[(1, day.isoformat())] = chain
    base = {'sessions': sessions, 'stocks': stocks, 'events': events, 'dividends': {}, 'issuer_of': {1: 'TEST INC'},
            'ticker_of': {1: 'TST'}}
    return base, quotes


class EngineTests(unittest.TestCase):
    def test_expected_abs_matches_limits(self):
        self.assertAlmostEqual(engine.expected_abs(0.0, 1.0), math.sqrt(2 / math.pi), places=12)
        self.assertAlmostEqual(engine.expected_abs(5.0, 1e-9), 5.0, places=6)
        self.assertAlmostEqual(engine.expected_abs(-3.0, 0.0), 3.0)

    def test_implied_vol_round_trip(self):
        price = engine.bs_price(100, 105, 0.37, 0.1, True)
        self.assertAlmostEqual(engine.implied_vol(price, 100, 105, 0.1, True), 0.37, places=5)

    def test_iron_fly_pnl_and_risk(self):
        base, quotes = synthetic()
        market = engine.Market(base, quotes)
        ev = base['events'][-1]
        plan, why = engine.plan_trade(market, ev, 'short_iron_fly_1x', 'E-1', 'E+1')
        self.assertIsNone(why)
        trade, why = engine.execute(market, ev, 'short_iron_fly_1x', plan)
        self.assertIsNone(why)
        entry = market.chain(1, plan['entry_day'])
        exit_ = market.chain(1, plan['exit_day'])
        gross = 0.0
        for ex, k, cp, qty, _ in plan['legs']:
            b = 0 if cp == 'C' else 3
            gross += qty * (engine.mid(exit_[ex][k][b], exit_[ex][k][b + 1]) - engine.mid(entry[ex][k][b], entry[ex][k][b + 1]))
        self.assertAlmostEqual(trade['pnl_mid'], gross * 100 - 0.65 * 2 * 4, places=9)
        credit = -sum(q * engine.mid(entry[ex][k][0 if cp == 'C' else 3], entry[ex][k][1 if cp == 'C' else 4])
                      for ex, k, cp, q, _ in plan['legs']) * 100
        calls = sorted(k for _, k, cp, _, _ in plan['legs'] if cp == 'C')
        self.assertAlmostEqual(trade['risk'], (calls[1] - calls[0]) * 100 - credit, places=9)
        self.assertGreater(trade['pnl_mid'], trade['pnl_c25'])  # costs only reduce P&L
        self.assertGreater(trade['pnl_mid'], 0)  # synthetic vol halves after the event

    def test_missing_exit_is_unresolved_not_dropped(self):
        base, quotes = synthetic()
        market = engine.Market(base, quotes)
        ev = base['events'][-1]
        plan, _ = engine.plan_trade(market, ev, 'long_straddle', 'E-1', 'E+1')
        del quotes[(1, plan['exit_day'].isoformat())]
        trade, why = engine.execute(market, ev, 'long_straddle', plan)
        self.assertEqual(trade['status'], 'unresolved')

    def test_decisions_ignore_everything_after_decision_close(self):
        base, quotes = synthetic()
        ev = base['events'][-2]
        before = engine.Market(base, quotes)
        plans = {f: engine.plan_trade(before, ev, f, 'E-1', 'after_release')[0] for f in engine.FAMILIES}
        decision = before.session(ev, -1)
        base2, quotes2 = copy.deepcopy(base), copy.deepcopy(quotes)
        for day in list(base2['stocks'][1]):
            if day > decision:
                base2['stocks'][1][day] = (1.0, 0.9, 2.0, 1.0)
        for key in list(quotes2):
            if dt.date.fromisoformat(key[1]) > decision:
                for chain in quotes2[key].values():
                    for leg in chain.values():
                        leg[:] = [0.01, 99.0, 1.0, 0.01, 99.0, 1.0]
        after = engine.Market(base2, quotes2)
        for f in engine.FAMILIES:
            p2, _ = engine.plan_trade(after, ev, f, 'E-1', 'after_release')
            self.assertEqual(plans[f], p2, f)

    def test_release_timing_uses_earlier_events_only(self):
        base, quotes = synthetic(n_events=8)
        market = engine.Market(base, quotes)
        ev = base['events'][-1]
        self.assertEqual(market.release_timing(ev, market.session(ev, -1)), 'E')  # move lands on E
        for k in base['events'][:-1]:
            d0, d1 = market.session(k, 0), market.session(k, 1)
            base['stocks'][1][d0], base['stocks'][1][d1] = base['stocks'][1][d1], base['stocks'][1][d0]
        self.assertEqual(engine.Market(base, quotes).release_timing(ev, market.session(ev, -1)), 'E+1')


class StatsTests(unittest.TestCase):
    def test_cluster_se_and_duplicate_issuers(self):
        day = dt.date(2020, 1, 6)
        trades = [{'issuer': 'X', 'E': day, 'ret_mid': 1.0}, {'issuer': 'X', 'E': day, 'ret_mid': 3.0},
                  {'issuer': 'Y', 'E': day + dt.timedelta(days=7), 'ret_mid': 0.0}]
        points = stats.issuer_events(trades)
        self.assertEqual([v for _, v, _ in points], [2.0, 0.0])
        mean, se = stats.cluster_mean_se(points)
        self.assertAlmostEqual(mean, 1.0)
        self.assertAlmostEqual(se, math.sqrt(2 / 1 * (1 + 1) / 4))

    def test_bootstrap_is_deterministic(self):
        pts = [(f'2020-W{i:02d}', float(i % 3), None) for i in range(1, 30)]
        self.assertEqual(stats.bootstrap_interval(pts, draws=200), stats.bootstrap_interval(pts, draws=200))


class CandidateTests(unittest.TestCase):
    def test_grid_and_filters(self):
        self.assertEqual(len(candidates.grid()), (6 * 9 + 2 * 7) * 9 * 2)
        rec = {'f_R': 1.25, 'f_HR': 0.9, 'f_TS': None}
        self.assertTrue(candidates.passes('R>=1.2&HR<=1.0', rec))
        self.assertFalse(candidates.passes('R>=1.4', rec))
        self.assertFalse(candidates.passes('TS>=1.2', rec))
        self.assertTrue(candidates.passes('none', {}))


class FreezeTests(unittest.TestCase):
    def test_evaluation_refuses_changed_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            hashes = run.source_hashes()
            with open(os.path.join(tmp, 'frozen_policies.json'), 'w') as f:
                json.dump({'source_hashes': {**hashes, 'engine.py': '0' * 64}, 'grid_sha256': candidates.grid_hash()}, f)
            with self.assertRaises(SystemExit):
                run.verify_frozen(tmp)

    def test_later_samples_cannot_be_simulated_before_freezing(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('sys.argv', ['run', 'simulate', '--sample', 'D', '--results', tmp]):
                with self.assertRaises(SystemExit):
                    run.main()

    def test_portfolio_compounds_realized_pnl(self):
        d = dt.date(2020, 1, 1)
        t = {'entry_day': d, 'exit_day': d + dt.timedelta(days=2), 'risk': 100.0, 'pnl_mid': 50.0}
        p = run.portfolio([t])
        self.assertAlmostEqual(p['end'], 100000 * (1 + 0.02 * 0.5))


if __name__ == '__main__':
    unittest.main()
