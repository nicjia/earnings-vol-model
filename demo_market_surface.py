"""Offline illustration of structural and market-anchored option prices."""
import numpy as np
from cos_pricer import price_heston_jump
from earnings_mixture import EarningsMixtureJump,MixtureComponent
from market_surface import MarketSlice


def main():
    spot=100.;T=45/365;rate=.03
    event=EarningsMixtureJump([MixtureComponent(.85,0,.045),MixtureComponent(.15,-.035,.12)])
    truth=dict(v0=.28**2,theta=.28**2,kappa=2.,xi=.7,rho=-.55)
    structural=dict(v0=.32**2,theta=.32**2,kappa=2.,xi=.5,rho=-.4)
    def structural_calls(K):
        return np.array([price_heston_jump(spot,float(k),T,rate,0.,structural,event,True,N=512) for k in K])
    references=np.array([75.,85.,92.,98.,103.,110.,120.,135.]);calls=references>=spot*np.exp(rate*T)
    mid=np.array([price_heston_jump(spot,k,T,rate,0.,truth,event,bool(c),N=512) for k,c in zip(references,calls)])
    market=MarketSlice.fit(spot,T,references,mid,calls,np.full(len(references),.02),rate=rate)
    hybrid=MarketSlice.fit(spot,T,references,mid,calls,np.full(len(references),.02),rate=rate,
                           structural_call_price=structural_calls)
    targets=np.array([90.,95.,100.,105.,115.])
    print('Synthetic illustration — not a historical performance result.')
    print('Eight reference quotes; the five target strikes below were not fitted.')
    print('All prices are dollars per option share. Standard 100-share contracts cost 100 times these values.\n')
    print('Strike   Synthetic truth   Structural   Market prior   Structural hybrid')
    for k,raw,plain,combined in zip(targets,structural_calls(targets),market.price(targets),hybrid.price(targets)):
        actual=price_heston_jump(spot,k,T,rate,0.,truth,event,True,N=512)
        print(f'{k:6.1f}   {actual:15.4f}   {raw:10.4f}   {plain:12.4f}   {combined:17.4f}')


if __name__=='__main__':main()
