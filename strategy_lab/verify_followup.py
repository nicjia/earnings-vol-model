"""Verify common samples, reference exclusion, timing and raw-quote P&L."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .data import MarketData
from .protocol import Protocol, is_target


def verify(results,old,data):
    out=Path(results); previous=Path(old); p=Protocol(); m=MarketData(data,p.end)
    pred=pd.concat([pd.read_pickle(f) for f in out.glob('predictions_*.pkl')])
    before=pd.read_pickle(previous/'predictions.pkl')
    keys=['secid','date','optionid']; a=pred.set_index(keys).sort_index(); b=before.set_index(keys).sort_index()
    assert a.index.equals(b.index) and len(a)==118117
    np.testing.assert_array_equal(a.mid,b.mid)
    np.testing.assert_allclose(a.interpolation,b.baseline,atol=1e-10)
    fits=pd.concat([pd.read_pickle(f) for f in out.glob('fits_*.pkl')])
    assert len(fits)==1068*8 and fits.converged.all()
    audits=json.loads((previous/'split_audits.json').read_text())
    for audit in audits:
        assert set(audit['reference_optionids']).isdisjoint(audit['target_optionids'])
        assert set(audit['reference_strikes']).isdisjoint(audit['target_strikes'])
        assert all(is_target(audit['sid'],k) for k in audit['target_strikes'])
    trades=json.loads((previous/'trades.json').read_text())
    for f in out.glob('replay_*.json'):
        if 'coverage' not in f.name: trades+=json.loads(f.read_text())
    frames={sid:m.quotes(sid).set_index(['date','optionid']) for sid in m.names}
    closed=0
    for t in trades:
        signal=pd.Timestamp(t['signal_date']); entry=pd.Timestamp(t['entry_date'])
        assert entry==m.shift(signal,1)
        if t['status']!='closed': continue
        sid=t['sid']; exit_date=pd.Timestamp(t['exit_date']); assert entry<exit_date<=pd.Timestamp(p.end)
        en=frames[sid].loc[[(entry,l['optionid']) for l in t['legs']]]
        ex=frames[sid].loc[[(exit_date,l['optionid']) for l in t['legs']]]
        for rows in [en,ex]:
            np.testing.assert_array_equal(rows.strike,[l['strike'] for l in t['legs']])
            np.testing.assert_array_equal(rows.cp_flag,[l['cp'] for l in t['legs']])
            assert all(rows.exdate.to_numpy()==pd.to_datetime([l['exdate'] for l in t['legs']]).to_numpy())
        qty=np.array([l['qty'] for l in t['legs']]); h=t['hedge_shares']; n=abs(qty).sum()
        s0=float(m.stock.loc[(sid,entry),'close']); s1=float(m.stock.loc[(sid,exit_date),'close'])
        quoted=100*np.sum(qty*(np.where(qty>0,ex.best_bid,ex.best_offer)-np.where(qty>0,en.best_offer,en.best_bid)))
        net=quoted+h*(s1-s0)-2*n*p.commission_per_contract-200*n*p.option_slippage_per_share
        net-=abs(h)*(s0+s1)*p.stock_slippage_bps/10000
        np.testing.assert_allclose(net,t['net_pnl'],atol=1e-7,rtol=1e-12)
        np.testing.assert_allclose(t['normalizer'],100*s0*n)
        closed+=1
    result=dict(passed=True,common_quotes=len(pred),reference_split_audits=len(audits),
        component_fits=len(fits),raw_quote_pnl_reconstructions=closed,all_entries_next_session=True,
        original_baseline_reproduced=True,
        limits='This verifies accounting and sample separation, not actual fills, point-in-time earnings schedule availability, or future profitability.')
    (out/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',required=True);p.add_argument('--old',required=True);p.add_argument('--data',required=True)
    a=p.parse_args();verify(a.results,a.old,a.data)
