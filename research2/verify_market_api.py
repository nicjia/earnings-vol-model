"""Check the public pricing interface against every historical confirmation quote."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from market_surface import MarketSlice
from variance_clock import ClockWeights
from strategy_lab.protocol import Protocol
from strategy_lab.data import MarketData
from strategy_lab.model import prepare_surface


def run(root):
    root=Path(root);market=MarketData(root/'research2_2025_data','2025-12-31')
    differences=[];count=0;slices=0
    for sid in market.names:
        states=pd.read_pickle(root/'research2_confirmation'/f'states_{sid}.pkl')
        expected=pd.read_pickle(root/'research2_pricing_confirmation'/f'pricing_{sid}.pkl')
        frames={d:g for d,g in market.quotes(sid).groupby('date')}
        for state in states:
            date=state['date'];base,ref,_=prepare_surface(frames[date],sid,date,market,Protocol(),ClockWeights(1,1,1))
            base.parameters,base.fit_rmse=state['variants']['calendar_heston_jump']
            for exp,g in ref.groupby('exdate'):
                target=expected[expected.date.eq(date)&expected.exdate.eq(exp)]
                r,q=base.carry[exp];T=market.exposure(date,exp).calendar_time
                def callback(K):return base.prices(pd.DataFrame(dict(strike=K,exdate=exp,cp_flag='C'))).to_numpy()
                for name,fn in [('convex_pchip_10',None),('convex_hybrid_10',callback)]:
                    model=MarketSlice.fit(base.spot,T,g.strike,g.mid,g.cp_flag.eq('C'),g.halfspread,
                        rate=r,dividend_yield=q,structural_call_price=fn)
                    actual=model.price(target.strike.to_numpy(),target.cp_flag.eq('C').to_numpy())
                    delta=np.abs(actual-target[name].to_numpy());differences.extend(delta.tolist())
                    np.testing.assert_allclose(actual,target[name],atol=1e-4,rtol=0.)
                count+=len(target);slices+=1
        print('verified public API',market.names[sid],flush=True)
    report=dict(quote_pairs=count,expiry_slices=slices,modes=2,
        maximum_price_difference=float(max(differences)),public_api_matches_historical_results=True)
    (root/'research2_round1'/'market_api_verification.json').write_text(json.dumps(report,indent=2));print(report)


if __name__=='__main__':run(Path(__file__).resolve().parents[2]/'wrds_studies')
