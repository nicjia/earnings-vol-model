import datetime as dt
import unittest

import numpy as np
from scipy import stats

from . import dist
from . import features as F
from . import panel


class TestScores(unittest.TestCase):
    def test_normal_closed_forms(self):
        y = np.array([-1.2, 0.0, 0.7, 2.5])
        Q = np.tile(stats.norm.ppf(dist.LEVELS), (len(y), 1))
        s = dist.score(Q, y)
        exact = y * (2 * stats.norm.cdf(y) - 1) + 2 * stats.norm.pdf(y) - 1 / np.sqrt(np.pi)
        np.testing.assert_allclose(s['crps'], exact, atol=2e-3)
        np.testing.assert_allclose(s['pit'], stats.norm.cdf(y), atol=1e-3)
        np.testing.assert_allclose(s['log'][:3], stats.norm.logpdf(y[:3]), atol=1e-2)
        self.assertAlmostEqual(s['eabs'][0], np.sqrt(2 / np.pi), places=2)

    def test_table_matches_draws(self):
        shape = dist.Shape('Gauss', np.random.default_rng(1).standard_normal(20000))
        u = np.random.default_rng(2).standard_normal(20000)
        table = dist.jump_table(shape, u, seed=0)
        q = dist.table_lookup(table, np.array([1.0]))[0]
        np.testing.assert_allclose(q[[10, 52, 94]], stats.norm.ppf(dist.LEVELS[[10, 52, 94]]) * np.sqrt(2), atol=0.05)

    def test_normal_score_interp(self):
        lv = np.array([0.05, 0.5, 0.95])
        q = stats.norm.ppf(lv)[None, :] * 2
        np.testing.assert_allclose(dist.normal_score_interp(lv, q)[0], 2 * stats.norm.ppf(dist.LEVELS), atol=1e-9)


class TestFeatures(unittest.TestCase):
    def test_forward_sum_and_count(self):
        x = np.array([[1.0], [2.0], [np.nan], [4.0], [5.0]])
        np.testing.assert_array_equal(F.forward_sum(x, 1)[:, 0], [2, np.nan, 4, 5, np.nan])
        np.testing.assert_array_equal(F.forward_count(x, 2)[:, 0], [1, 1, 2, 0, 0])

    def test_ewma_seed_and_skip(self):
        r = np.full((25, 1), 0.01)
        r[22] = np.nan
        v = F.ewma(r)
        self.assertTrue(np.isnan(v[18, 0]))
        self.assertAlmostEqual(v[19, 0], 1e-4)
        self.assertAlmostEqual(v[22, 0], v[21, 0])

    def test_garch_horizon_limits(self):
        th = [0.05, 0.0, 0.9, 6.0]
        self.assertAlmostEqual(float(F.garch_horizon(2.0, 2.0, th, 10, 1.0)), 20.0)
        self.assertAlmostEqual(float(F.garch_horizon(3.0, 2.0, th, 1, 1.0)), 3.0)

    def test_release_session(self):
        d = [dt.date(2024, 1, 2), dt.date(2024, 1, 3), dt.date(2024, 1, 5)]
        dates = np.array(d)
        self.assertEqual(panel.release_session(d[1], '07:00:00', dates), 1)
        self.assertEqual(panel.release_session(d[1], '16:05:00', dates), 2)
        self.assertEqual(panel.release_session(dt.date(2024, 1, 4), '07:00:00', dates), 2)


if __name__ == '__main__':
    unittest.main()
