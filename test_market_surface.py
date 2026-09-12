import unittest
import numpy as np
from market_surface import MarketSlice
from strategy_lab.model import bsm


class MarketSurfaceTests(unittest.TestCase):
    def fit(self,hybrid=False):
        K=np.array([75.,85.,92.,98.,103.,110.,120.,135.]);T=.15;r=.03;F=100*np.exp(r*T)
        cp=K>=F;mid=bsm(F,K,T,r,.3,cp)
        callback=(lambda k:bsm(F,k,T,r,.35,True)) if hybrid else None
        return MarketSlice.fit(100,T,K,mid,cp,np.full(len(K),.02),rate=r,structural_call_price=callback)

    def test_both_modes_price_heldout_contracts(self):
        K=np.array([90.,95.,100.,105.,115.]);T=.15;r=.03;truth=bsm(100*np.exp(r*T),K,T,r,.3,True)
        for hybrid in [False,True]:
            s=self.fit(hybrid);np.testing.assert_allclose(s.price(K),truth,atol=.04)
            self.assertIsInstance(s.price(100),float)

    def test_put_call_parity_and_strike_consistency(self):
        s=self.fit(True);K=np.linspace(10.,300.,2001);c=s.price(K);p=s.price(K,False)
        np.testing.assert_allclose(c-p,100-K*np.exp(-.03*.15),atol=1e-10)
        slope=np.diff(c)/np.diff(K)
        self.assertLessEqual(slope.max(),1e-8);self.assertGreaterEqual(slope.min(),-np.exp(-.03*.15)-1e-8)
        self.assertGreaterEqual(np.diff(slope).min(),-1e-7)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):MarketSlice.fit(100,.1,[90,90,100,110],[10,10,4,1],[True]*4)
        with self.assertRaises(ValueError):self.fit().price(-1)
        with self.assertRaises(ValueError):MarketSlice.fit(100,.1,[90,95,100,110],[10,7,4,1],[True]*4,
            structural_call_price=lambda k:np.array([1.]))


if __name__=='__main__':unittest.main()
