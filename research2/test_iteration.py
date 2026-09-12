import unittest
import numpy as np
import pandas as pd
from research2.iterate_strategies import score,position

class ExecutionTests(unittest.TestCase):
    def test_entry_and_exit_fractions_apply_to_their_own_spread(self):
        p=pd.DataFrame(dict(weight=[1.],option_pnl=[2.],hedge_pnl=[1.],commission=[.013],stock_cost=[.02],entry_halfspread=[.1],exit_halfspread=[.4]))
        midpoint=score(p,0,0).iloc[0]
        self.assertAlmostEqual(midpoint-score(p,0,1).iloc[0],.4)
        self.assertAlmostEqual(midpoint-score(p,1,0).iloc[0],.1)
        self.assertAlmostEqual(score(p,.5,.5).iloc[0],(midpoint+score(p,1,1).iloc[0])/2)

    def test_pair_nets_identical_stock_hedges(self):
        row=dict(sid=1,name='TEST',event=pd.Timestamp('2020-01-01'),year=2020,ids='1',status='scored',legs=1,
                 option_move=1.,hedge_move=2.,delta=.4,stock_cost=.08,commission=.013,entry_relative_spread=.1,
                 entry_mid=2.,spread_cost=.3,signal_mid=2.,signal_spot=100.,signal_relative_spread=.1,edge=.2,history_tail=.1)
        other=dict(row,ids='2',edge=-.2)
        result=position(pd.DataFrame([row,other]),[1,-1],'pair','test')
        self.assertAlmostEqual(result['stock_cost'],0.)
        self.assertAlmostEqual(result['hedge_pnl'],0.)
        self.assertAlmostEqual(result['entry_halfspread'],.2)
        self.assertAlmostEqual(result['commission'],.026)
        self.assertAlmostEqual(result['notional'],200.)

if __name__=='__main__':unittest.main()
