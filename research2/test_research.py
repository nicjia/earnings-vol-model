import unittest
import numpy as np
import pandas as pd
from strategy_lab.model import bsm
from .smiles import ConvexSmile,ssvi_fit
from .hedging import fit_adjustment,features
from .transport import transport_variance


class ResearchTests(unittest.TestCase):
    def test_event_variance_survives_time_until_release(self):
        w=np.array([.02])
        before=transport_variance(w,.1,.09,.01,1,1)
        after=transport_variance(w,.1,.09,.01,1,0)
        np.testing.assert_allclose(before,[.019])
        np.testing.assert_allclose(before-after,[.01])

    def test_no_event_transport_matches_constant_iv(self):
        w=np.array([.01,.02,.03])
        np.testing.assert_allclose(transport_variance(w,.1,.08,.01,0,0),.8*w)

    def test_convex_projection_enforces_vertical_and_butterfly_bounds(self):
        x=np.linspace(.8,1.2,8);prior=lambda x:bsm(1.,x,.1,0,.3,True)
        observed=prior(x);observed[3]+=.004;observed[4]-=.003
        s=ConvexSmile(x,observed,np.full(8,.001),prior)
        self.assertTrue(s.ok)
        grid=np.linspace(.01,4,2001);c=s(grid);d=np.diff(c)/np.diff(grid)
        self.assertTrue(np.isfinite(c).all())
        self.assertGreaterEqual(d.min(),-1-1e-7);self.assertLessEqual(d.max(),1e-7)
        self.assertGreaterEqual(np.diff(d).min(),-1e-6)
        self.assertTrue((c>=np.maximum(1-grid,0)-1e-8).all())

    def test_projection_reproduces_smooth_reference_prices(self):
        x=np.linspace(.8,1.2,9);prior=lambda x:bsm(1.,x,.1,0,.3,True)
        s=ConvexSmile(x,prior(x),np.full(9,.0001),prior)
        np.testing.assert_allclose(s(x),prior(x),atol=1e-5)

    def test_ssvi_flat_case(self):
        k=np.linspace(-.2,.2,8);f,ok=ssvi_fit(k,np.full(8,.3),.1,np.full(8,.01))
        self.assertTrue(ok);np.testing.assert_allclose(f(k),.3,atol=.005)

    def test_empirical_hedge_learns_known_correction(self):
        rng=np.random.default_rng(8);n=1000
        rows=pd.DataFrame(dict(sid=1,date=np.repeat(pd.date_range('2020-01-01',periods=100),10),
            optionid=np.arange(n),delta_bs=rng.uniform(.1,.9,n),vega_scaled=rng.uniform(.1,.4,n),
            cp_flag='C',event_fraction=0.,days_to_event=100,delta_model=.5,stock_change=rng.normal(0,.02,n)))
        rows['actual_change']=(rows.delta_bs+.2*rows.vega_scaled)*rows.stock_change
        beta=fit_adjustment(rows,'hw');error=features(rows,'hw')@beta-.2*rows.vega_scaled
        self.assertLess(float(np.sqrt(np.mean(error**2))),.003)


if __name__=='__main__':unittest.main()
