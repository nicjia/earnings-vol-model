import unittest
from types import SimpleNamespace
import numpy as np
from trade_screen import assess_quote

class TradeScreenTests(unittest.TestCase):
 def surface(self,value):
  return SimpleNamespace(reference_strikes=np.array([90.,100.,110.,120.]),reference_rmse=.01,price=lambda strike,call:value)
 def test_reject_extrapolation_despite_large_gap(self):
  a=assess_quote(self.surface(3),130,True,1.95,2.05,1)
  self.assertFalse(a.eligible);self.assertIn('outside_reference_strikes',a.reasons)
 def test_reject_reversed_edge(self):
  self.assertFalse(assess_quote(self.surface(1),100,True,1.95,2.05,1).eligible)
 def test_long_short_symmetric(self):
  self.assertTrue(assess_quote(self.surface(3),100,True,1.95,2.05,1).eligible)
  self.assertTrue(assess_quote(self.surface(1),100,True,1.95,2.05,-1).eligible)
 def test_missing_quotes_not_zero(self):
  with self.assertRaises(ValueError):assess_quote(self.surface(3),100,True,float('nan'),2,1)
 def test_zero_and_wide_quotes(self):
  self.assertFalse(assess_quote(self.surface(3),100,True,0,0,1).eligible)
  self.assertFalse(assess_quote(self.surface(3),100,True,1,2,1).eligible)
if __name__=='__main__':unittest.main()
