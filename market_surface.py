"""Reference-calibrated European option prices with convex strike interpolation.

MarketSlice prices one expiry. It is not a full arbitrage-free term structure,
an American exercise engine, or an estimate of an option's physical fair value.
Inputs and outputs are prices per underlying share, not contract totals.
"""
from dataclasses import dataclass
from typing import Callable
import numpy as np
from research2.smiles import ConvexSmile, call_prior
from strategy_lab.model import bsm, invert_iv


@dataclass
class MarketSlice:
    spot: float
    maturity: float
    rate: float
    dividend_yield: float
    curve: ConvexSmile
    mode: str
    reference_strikes: np.ndarray
    reference_rmse: float

    @classmethod
    def fit(cls, spot: float, maturity: float, strikes, midpoints, is_call,
            half_spreads=None, *, rate=0., dividend_yield=0.,
            structural_call_price: Callable | None=None, prior_weight=10.):
        """Fit reference quotes only; target quotes are not an input.

        Supply one reference option per strike (OTM quotes are customary).
        For a structural hybrid, supply a callable mapping strikes to current
        structural call prices for this same spot, expiry and carry. The engine
        adds reference-IV residuals and projects onto a convex call curve.
        Without that callable it uses a PCHIP reference-IV prior.
        """
        if not np.isfinite([spot,maturity,rate,dividend_yield,prior_weight]).all():
            raise ValueError('Spot, maturity, carry and prior weight must be finite')
        if spot<=0 or maturity<=0 or prior_weight<=0:
            raise ValueError('Spot, maturity and prior weight must be positive')
        K=np.atleast_1d(np.asarray(strikes,dtype=float));mid=np.atleast_1d(np.asarray(midpoints,dtype=float))
        calls=np.atleast_1d(np.asarray(is_call,dtype=bool))
        spread=np.zeros_like(K) if half_spreads is None else np.atleast_1d(np.asarray(half_spreads,dtype=float))
        if any(x.ndim!=1 or len(x)!=len(K) for x in [mid,calls,spread]) or len(K)<4:
            raise ValueError('At least four aligned one-dimensional reference quotes are required')
        if not np.isfinite(np.r_[K,mid,spread]).all() or np.any(K<=0) or np.any(mid<0) or np.any(spread<0):
            raise ValueError('Reference strikes must be positive; prices and half-spreads nonnegative and finite')
        order=np.argsort(K);K,mid,calls,spread=(a[order] for a in [K,mid,calls,spread])
        if np.any(np.diff(K)<=0):raise ValueError('Use one reference quote per distinct strike')
        F=spot*np.exp((rate-dividend_yield)*maturity);D=np.exp(-rate*maturity)
        x=K/F;normalized_calls=mid/(D*F)+np.where(calls,0.,1-x)
        if np.any(normalized_calls>1+1e-8):raise ValueError('Reference price exceeds the European call upper bound after parity conversion')
        iv=invert_iv(F,K,maturity,rate,mid,calls);logm=np.log(x)
        if structural_call_price is None:
            prior=call_prior(logm,iv,maturity);mode='market_pchip'
        else:
            def structural_iv(strikes):
                price=np.asarray(structural_call_price(np.asarray(strikes)),dtype=float)
                if price.shape!=np.asarray(strikes).shape or not np.isfinite(price).all():
                    raise ValueError('Structural callback must return one finite call price per strike')
                return invert_iv(F,np.asarray(strikes),maturity,rate,price,np.ones(len(strikes),dtype=bool))
            residual=iv-structural_iv(K)
            def prior(xx):
                vol=np.maximum(.001,structural_iv(xx*F)+np.interp(np.log(xx),logm,residual))
                return bsm(1.,xx,maturity,0.,vol,True)
            mode='structural_hybrid'
        curve=ConvexSmile(x,normalized_calls,np.maximum(spread/(D*F),.00005),prior,prior_weight)
        if not curve.ok:raise RuntimeError('Strike-constrained calibration failed: '+curve.message)
        fitted=D*F*(curve(x)-np.where(calls,0.,1-x))
        return cls(float(spot),float(maturity),float(rate),float(dividend_yield),curve,mode,K.copy(),
                   float(np.sqrt(np.mean((fitted-mid)**2))))

    def price(self,strike,call=True):
        """Price supplied strikes using this fitted expiry; no target quotes needed."""
        K=np.asarray(strike,dtype=float)
        if not np.isfinite(K).all() or np.any(K<=0):raise ValueError('Strikes must be positive and finite')
        F=self.spot*np.exp((self.rate-self.dividend_yield)*self.maturity)
        D=np.exp(-self.rate*self.maturity);value=D*F*(self.curve(K/F)-np.where(call,0.,1-K/F))
        return float(value) if np.ndim(value)==0 else value
