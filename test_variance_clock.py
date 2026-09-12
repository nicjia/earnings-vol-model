"""Run with: python -m unittest -v test_variance_clock"""
import unittest
from itertools import product
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np

from variance_clock import Session, ClockWeights, clock_exposure, YEAR_SECONDS
from clocked_pricer import ScheduledJump, price_clocked_option
from earnings_mixture import EarningsMixtureJump, MixtureComponent, price_option, price_option_mc, black76
from cos_pricer import (price_diffusion_jumps, independent_jumps_cf,
                        price_heston_jump, heston_cf, cos_price)


def dt(text):
    return datetime.fromisoformat(text).replace(tzinfo=ZoneInfo("America/New_York"))


def session(day, close="16:00"):
    return Session(dt(day + "T09:30"), dt(day + "T" + close))


class ClockTests(unittest.TestCase):
    def test_weekend_and_overnight(self):
        s = [session(d) for d in ["2026-09-11", "2026-09-14", "2026-09-15"]]
        x = clock_exposure(s[0].close, s[-1].close, s)
        self.assertEqual(x.weekend/3600, 65.5)
        self.assertEqual(x.overnight/3600, 17.5)
        self.assertEqual(x.session/3600, 13)
        self.assertAlmostEqual(x.variance_time(ClockWeights(1, 1, 1)), 4/365)

    def test_dst_actual_hours(self):
        s = [session("2026-03-06"), session("2026-03-09")]
        x = clock_exposure(s[0].close, s[1].open, s)
        self.assertEqual(x.weekend/3600, 64.5)

    def test_holiday_and_early_close(self):
        s = [session("2026-11-25"), session("2026-11-27", "13:00")]
        x = clock_exposure(s[0].close, s[1].close, s)
        self.assertEqual(x.holiday/3600, 41.5)
        self.assertEqual(x.session/3600, 3.5)

    def test_partial_closure_and_additivity(self):
        s = [session("2026-09-11"), session("2026-09-14")]
        a, b, c = s[0].close, dt("2026-09-12T12:00"), s[1].close
        full = clock_exposure(a, c, s)
        left, right = clock_exposure(a, b, s), clock_exposure(b, c, s)
        for key in ["session", "weekend", "overnight", "holiday"]:
            self.assertAlmostEqual(getattr(full, key), getattr(left, key)+getattr(right, key))

    def test_invalid_schedule_and_weights(self):
        s = [session("2026-09-11")]
        with self.assertRaises(ValueError):
            clock_exposure(s[0].close, dt("2026-09-14T10:00"), s)
        with self.assertRaises(ValueError):
            clock_exposure(datetime(2026, 9, 11), s[0].close, s)
        with self.assertRaises(ValueError):
            ClockWeights(1, -1, 1)


class PricingTests(unittest.TestCase):
    def setUp(self):
        self.jump = EarningsMixtureJump([MixtureComponent(.8, 0, .01),
                                        MixtureComponent(.2, -.02, .05)])

    def test_calendar_compatibility_and_discounting(self):
        T, tv = 10/365, 3/365
        for j in [None, self.jump]:
            legacy = price_option(100, 102, T, .05, .01, .3, j)
            self.assertAlmostEqual(legacy, price_option(100, 102, T, .05, .01, .3, j, variance_time=T))
            c = price_option(100, 102, T, .05, .01, .3, j, variance_time=tv)
            p = price_option(100, 102, T, .05, .01, .3, j, False, variance_time=tv)
            self.assertAlmostEqual(c-p, 100*np.exp(-.01*T)-102*np.exp(-.05*T))

    def test_single_jump_cos_matches_exact(self):
        for call in [True, False]:
            for k in [70, 90, 100, 110, 140]:
                exact = price_option(100, k, .1, .05, .01, .2, self.jump, call, variance_time=.03)
                cos = price_diffusion_jumps(100, k, .1, .05, .01, .2, [self.jump], call,
                                             variance_time=.03, N=1024)
                self.assertAlmostEqual(exact, cos, places=7)

    def test_multiple_jumps_vs_monte_carlo(self):
        jumps = [self.jump]*8
        px = price_diffusion_jumps(100, 102, .2, .05, .01, .2, jumps, variance_time=.07, N=1024)
        mc, se, ratio = price_option_mc(100, 102, .2, .05, .01, .2, None,
                                        n=400000, seed=72, variance_time=.07, jumps=jumps)
        self.assertLess(abs(px-mc), 5*se)
        self.assertLess(abs(ratio-1), .002)
        np.testing.assert_allclose(independent_jumps_cf([0, -1j], jumps), [1, 1], atol=1e-12)
        px2 = price_diffusion_jumps(100, 102, .2, .05, .01, .2, jumps, variance_time=.07, N=2048)
        self.assertAlmostEqual(px, px2, places=7)

    def test_heterogeneous_jumps_vs_small_exact_expansion(self):
        other = EarningsMixtureJump([MixtureComponent(.6, .01, .02),
                                     MixtureComponent(.4, -.03, .04)])
        events = [self.jump, other, self.jump]
        T, tv, sigma = .2, .06, .25
        exact = 0.0
        for branch in product(range(2), repeat=3):
            weight = np.prod([j.w[b] for j, b in zip(events, branch)])
            mu = sum(j.mu[b] for j, b in zip(events, branch))
            vj = sum(j.s[b]**2 for j, b in zip(events, branch))
            F = 100*np.exp(.04*T+mu+vj/2)
            exact += weight * black76(F, 105, np.sqrt((sigma**2*tv+vj)/T), T, .05)
        cos = price_diffusion_jumps(100, 105, T, .05, .01, sigma, events,
                                    variance_time=tv, N=2048)
        self.assertAlmostEqual(exact, cos, places=7)

    def test_rare_remote_component(self):
        rare = EarningsMixtureJump([MixtureComponent(.9999, 0, .001),
                                    MixtureComponent(.0001, .5, .01)])
        exact = price_option(100, 120, .1, .05, 0, .1, rare)
        cos = price_diffusion_jumps(100, 120, .1, .05, 0, .1, [rare], N=2048)
        self.assertAlmostEqual(exact, cos, places=7)

    def test_invalid_mixture(self):
        for components in [[], [MixtureComponent(-1, 0, .1)], [MixtureComponent(1, 0, -.1)]]:
            with self.assertRaises(ValueError):
                EarningsMixtureJump(components)

    def test_event_timestamp_boundaries(self):
        s = [session("2026-09-11"), session("2026-09-14")]
        start, end = s[0].close, s[1].close
        past = ScheduledJump(start, self.jump)
        future = ScheduledJump(dt("2026-09-14T16:01"), self.jump)
        at_expiry = ScheduledJump(end, self.jump)
        args = (100, 100, start, end, .05, 0, .3, s, ClockWeights(.2, .1, .1))
        no, x = price_clocked_option(*args)
        excluded, _ = price_clocked_option(*args, events=[past, future])
        included, _ = price_clocked_option(*args, events=[at_expiry])
        self.assertEqual(no, excluded)
        expected = price_option(100, 100, x.calendar_time, .05, 0, .3, self.jump,
                                variance_time=x.variance_time(args[-1]))
        self.assertAlmostEqual(included, expected)

    def test_heston_clock_preserves_carry(self):
        hp = dict(v0=.04, kappa=2, theta=.04, xi=.3, rho=-.6)
        T, tv = .1, .04
        actual = price_heston_jump(100, 105, T, .05, .01, hp, variance_time=tv)
        expected = cos_price(100, 105, T, .05, .01,
            lambda u: heston_cf(u, tv, 0, 0, **hp)*np.exp(1j*u*.04*T))
        self.assertAlmostEqual(actual, expected)
        p = price_heston_jump(100, 105, T, .05, .01, hp, call=False, variance_time=tv)
        self.assertAlmostEqual(actual-p, 100*np.exp(-.01*T)-105*np.exp(-.05*T))

    def test_zero_variance_and_expiry(self):
        self.assertAlmostEqual(price_option(100, 90, .1, .05, 0, .3, None, variance_time=0),
                               100-90*np.exp(-.005))
        self.assertEqual(price_option(100, 90, 0, .05, 0, .3, None), 10)


if __name__ == "__main__":
    unittest.main()
