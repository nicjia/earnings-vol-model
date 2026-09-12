import unittest
import numpy as np
import pandas as pd
from research2.historical_jump import forecast,MIXTURE_VARIANCE
from strategy_lab.model import jump

class HistoricalForecastTests(unittest.TestCase):
    def test_current_and_future_outcomes_cannot_change_forecast(self):
        signal=pd.Timestamp('2020-01-01')
        dates=pd.date_range('2017-01-01',periods=10,freq='90D')
        h=pd.DataFrame(dict(sid=1,available=dates,excess_square=np.arange(10)/10000,log_move=.03))
        expected=forecast(h,1,signal)
        poison=pd.DataFrame([dict(sid=1,available=signal,excess_square=100.,log_move=10.),dict(sid=1,available=signal+pd.Timedelta(days=1),excess_square=100.,log_move=10.)])
        self.assertEqual(expected,forecast(pd.concat([h,poison]),1,signal))
        self.assertEqual(expected['history_n'],8)
        self.assertLess(expected['history_last'],signal)

    def test_insufficient_history_does_not_invent_forecast(self):
        h=pd.DataFrame(dict(sid=[1]*5,available=pd.date_range('2018-01-01',periods=5),excess_square=.001,log_move=.03))
        self.assertIsNone(forecast(h,1,pd.Timestamp('2020-01-01')))

    def test_scale_matches_compensated_mixture_variance(self):
        desired=.0064;m=jump(np.sqrt(desired/MIXTURE_VARIANCE))
        mean=np.sum(m.w*m.mu)
        var=np.sum(m.w*(m.s*m.s+(m.mu-mean)**2))
        self.assertAlmostEqual(var,desired,places=12)
        self.assertAlmostEqual(np.sum(m.w*np.exp(m.mu+.5*m.s*m.s)),1.,places=12)

if __name__=='__main__':unittest.main()
