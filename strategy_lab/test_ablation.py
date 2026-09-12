import unittest
from dataclasses import replace
import numpy as np
import pandas as pd
from earnings_mixture import price_option
from variance_clock import ClockWeights
from .model import cos_batch, jump, prepare_surface, fit_surface
from .ablation import fit_variant, OverlaySurface
from .protocol import Protocol, is_target
from .test_lab import FakeMarket
from .followup_report import block_interval


class AblationTests(unittest.TestCase):
    def test_flat_event_cf_matches_closed_form(self):
        K=np.array([70.,90.,100.,110.,140.]); cp=np.array([False,True,False,True,True])
        for n in [0,1]:
            actual=cos_batch(100,K,cp,.2,.08,.03,.01,[.35,.5,-.4,.06],n,1024,True)
            expected=[price_option(100,k,.2,.03,.01,.35,jump(.06) if n else None,
                                  bool(c),variance_time=.08) for k,c in zip(K,cp)]
            np.testing.assert_allclose(actual,expected,atol=1e-7)

    def fixture(self):
        m=FakeMarket(); d=pd.Timestamp('2020-01-02'); rows=[]
        for e in pd.to_datetime(['2020-02-07','2020-02-21','2020-03-20']):
            T=m.exposure(d,e).calendar_time; K=np.arange(80.,121.,2.)
            for cp in ['C','P']:
                px=cos_batch(100,K,np.full(len(K),cp=='C'),T,T,.01,0,[.3,.4,-.5,0],0,512)
                for k,v in zip(K,px):
                    rows.append(dict(optionid=len(rows)+1,strike_price=int(k*1000),strike=k,exdate=e,cp_flag=cp,
                        best_bid=max(v-.02,.001),best_offer=v+.02,mid=v,halfspread=.02))
        return m,d,pd.DataFrame(rows),replace(Protocol(),cos_terms=256,max_fit_evaluations=35)

    def test_fast_fit_agrees_with_original(self):
        m,d,raw,p=self.fixture(); w=ClockWeights(1,1,1)
        old=fit_surface(raw,1,d,m,p,w); base,chosen,event=prepare_surface(raw,1,d,m,p,w)
        new,_=fit_variant(base,chosen,event,False,True,w,p)
        np.testing.assert_allclose(new.prices(raw),old.prices(raw),atol=1e-5)

    def test_overlay_targets_cannot_change_calibration(self):
        m,d,raw,p=self.fixture(); w=ClockWeights(1,1,1)
        base,chosen,event=prepare_surface(raw,1,d,m,p,w)
        base,_=fit_variant(base,chosen,event,False,True,w,p)
        a=OverlaySurface(base,chosen)
        targets=raw[raw.strike_price.map(lambda k:is_target(1,k))].copy()
        before=a.prices(targets).copy()
        targets[['mid','best_bid','best_offer']]=1000
        np.testing.assert_array_equal(a.prices(targets),before)
        np.testing.assert_allclose(a.prices(chosen),chosen.mid,atol=1e-6)

    def test_week_cluster_preserves_perfect_dependence(self):
        d=pd.to_datetime(['2020-01-06','2020-01-13','2020-01-20','2020-01-27'])
        a=block_interval([1,2,3,4],d)
        b=block_interval(np.repeat([1,2,3,4],20),np.repeat(d,20))
        np.testing.assert_allclose(a,b)


if __name__=='__main__': unittest.main()
