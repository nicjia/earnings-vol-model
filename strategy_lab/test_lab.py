import unittest
from types import SimpleNamespace
from dataclasses import replace
import numpy as np
import pandas as pd
from variance_clock import ClockWeights, ClockExposure
from cos_pricer import price_heston_jump
from .protocol import Protocol, STRATEGIES, is_target
from .model import cos_batch, jump, fit_surface
from .strategies import Leg, Plan, package, hedge_ratio
from .execution import extract, settle, simulate, simulate_session


class FakeMarket:
    def __init__(self):
        self.dates=pd.bdate_range('2020-01-02','2020-06-30')
        self.events={1:[]}
        self.stock=pd.DataFrame([dict(secid=1,date=d,close=100.,cfadj=1.) for d in self.dates]).set_index(['secid','date'])
    def shift(self,date,n): return self.dates[self.dates.get_loc(pd.Timestamp(date))+n]
    def close_time(self,date): return pd.Timestamp(date).tz_localize('UTC')+pd.Timedelta(hours=21)
    def expiry_time(self,date): return self.close_time(date)
    def exposure(self,date,exp): return ClockExposure(session=(pd.Timestamp(exp)-pd.Timestamp(date)).days*86400)
    def rate(self,date,T): return .01


def quote(optionid=1,bid=4.,ask=4.2):
    return dict(optionid=optionid,strike=100.,exdate=pd.Timestamp('2020-02-21'),cp_flag='C',
                best_bid=bid,best_offer=ask,mid=(bid+ask)/2,halfspread=(ask-bid)/2)


def plan(qty=1):
    leg=Leg(1,100.,pd.Timestamp('2020-02-21'),'C',qty,4.1,4.5)
    return Plan('single_convergence',1,pd.Timestamp('2020-01-02'),pd.Timestamp('2020-01-03'),
                pd.Timestamp('2020-01-08'),(leg,),0,.4,.2)


class LabTests(unittest.TestCase):
    def test_all_seven_registered(self):
        self.assertEqual(len(STRATEGIES),7)

    def test_contract_partition_stable_across_parity_twins(self):
        choices=[is_target(1,k) for k in range(80000,120001,1000)]
        self.assertTrue(any(choices)); self.assertFalse(all(choices))
        self.assertEqual(is_target(1,100000),is_target(1,100000.0))

    def test_vectorized_engine_matches_existing_engine(self):
        K=np.array([80.,95.,100.,105.,130.]); cp=np.array([False,True,False,True,True])
        par=np.array([.3,.4,-.5,.04]); T=.1; tv=.06
        actual=cos_batch(100,K,cp,T,tv,.02,0,par,1,1024)
        hp=dict(v0=.09,theta=.09,kappa=2,xi=.4,rho=-.5)
        expected=np.array([price_heston_jump(100,k,T,.02,0,hp,jump(.04),bool(c),variance_time=tv,N=2048)
                           for k,c in zip(K,cp)])
        np.testing.assert_allclose(actual,expected,atol=1e-6)

    def test_target_price_mutation_cannot_change_fit(self):
        m=FakeMarket(); d=pd.Timestamp('2020-01-02'); rows=[]; oid=1
        for e in pd.to_datetime(['2020-02-07','2020-02-21','2020-03-20']):
            T=(e-d).days/365
            ks=np.arange(80.,121.,2.)
            for cp in ['C','P']:
                px=cos_batch(100,ks,np.full(len(ks),cp=='C'),T,T,.01,0,[.3,.4,-.5,0],0,512)
                for k,v in zip(ks,px):
                    rows.append(dict(optionid=oid,strike_price=int(k*1000),strike=k,exdate=e,cp_flag=cp,
                        best_bid=max(v-.02,.001),best_offer=v+.02,mid=v,halfspread=.02)); oid+=1
        raw=pd.DataFrame(rows); protocol=replace(Protocol(),cos_terms=256,max_fit_evaluations=15)
        a=fit_surface(raw,1,d,m,protocol,ClockWeights(1,1,1))
        changed=raw.copy(); mask=changed.strike_price.map(lambda k:is_target(1,k))
        changed.loc[mask,['best_bid','best_offer','mid','halfspread']]=[1000,2000,1500,500]
        b=fit_surface(changed,1,d,m,protocol,ClockWeights(1,1,1))
        np.testing.assert_array_equal(a.parameters,b.parameters)
        self.assertEqual(a.carry,b.carry)
        self.assertTrue(set(changed.loc[mask,'strike_price']).isdisjoint(a.reference_strikes))

    def test_exact_cost_accounting_both_sides(self):
        en=pd.DataFrame([quote(bid=4,ask=4.2)]); ex=pd.DataFrame([quote(bid=4,ask=4.2)])
        for side in [1,-1]:
            r=settle(plan(side),en,ex,100,100,Protocol())
            self.assertAlmostEqual(r['option_mid_pnl'],0)
            self.assertAlmostEqual(r['spread_cost'],20)
            self.assertAlmostEqual(r['net_pnl'],-23.3)

    def test_missing_exit_preserved(self):
        m=FakeMarket(); p=plan()
        r=simulate(p,{p.entry_date:pd.DataFrame([quote()])},{},m,Protocol())
        self.assertEqual(r['status'],'unresolved')
        self.assertNotIn('net_pnl',r)

    def test_convergence_fills_next_close_not_signal_close(self):
        m=FakeMarket(); p=plan()
        frames={d:pd.DataFrame([quote(bid=v,ask=v+.2)]) for d,v in
                [(p.entry_date,4.),(pd.Timestamp('2020-01-06'),6.),(pd.Timestamp('2020-01-07'),3.)]}
        surface=SimpleNamespace(prices=lambda r:pd.Series(5.,index=r.index))
        r=simulate(p,frames,{pd.Timestamp('2020-01-06'):surface},m,Protocol())
        self.assertEqual(r['exit_date'],'2020-01-07 00:00:00')
        self.assertLess(r['net_pnl'],0) # Convergence on Monday does not guarantee Tuesday profit.

    def test_changed_contract_is_not_silently_substituted(self):
        x=pd.DataFrame([quote()]); x.loc[0,'strike']=50
        rows,reason=extract(x,plan())
        self.assertIsNone(rows); self.assertEqual(reason,'contract_terms_changed')

    def test_horizon_guard(self):
        p=replace(plan(),deadline=pd.Timestamp('2021-01-05'))
        r=simulate(p,{p.entry_date:pd.DataFrame([quote()])},{},FakeMarket(),Protocol())
        self.assertEqual(r['status'],'censored')

    def test_open_quotes_not_synthesized_from_closes(self):
        r=simulate_session(plan(),None,Protocol())
        self.assertEqual(r['status'],'blocked')

    def test_intraday_actual_quotes_accounting(self):
        p=replace(plan(),strategy='session_rotation',interval='daytime',
            entry_date=pd.Timestamp('2020-01-03T14:30Z'),deadline=pd.Timestamp('2020-01-03T21:00Z'))
        a=quote(); a.update(timestamp=p.entry_date,secid=1,spot=100,cfadj=1)
        b=quote(bid=5,ask=5.2); b.update(timestamp=p.deadline,secid=1,spot=100,cfadj=1)
        r=simulate_session(p,pd.DataFrame([a,b]),Protocol())
        self.assertEqual(r['status'],'closed'); self.assertAlmostEqual(r['net_pnl'],76.7)

    def test_integer_hedging(self):
        i,j,err=hedge_ratio(3,2)
        self.assertEqual(i*3,j*2); self.assertEqual(err,0)


if __name__=='__main__': unittest.main()
