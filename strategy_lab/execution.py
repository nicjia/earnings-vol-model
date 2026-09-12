"""Fixed contract identities, delayed decisions, explicit unresolved observations."""
import numpy as np
import pandas as pd


def extract(rows,plan):
    legs=[]
    for leg in plan.legs:
        x=rows[rows.optionid.eq(leg.optionid)]
        if len(x)!=1: return None,'missing_or_duplicate_contract'
        x=x.iloc[0]
        if x.strike!=leg.strike or x.exdate!=leg.exdate or x.cp_flag!=leg.cp_flag:
            return None,'contract_terms_changed'
        if not np.isfinite([x.best_bid,x.best_offer]).all() or x.best_bid<0 or x.best_offer<x.best_bid:
            return None,'invalid_quote'
        legs.append(x)
    return pd.DataFrame(legs),'ok'


def settle(plan,entry_rows,exit_rows,entry_spot,exit_spot,protocol):
    q=np.array([l.qty for l in plan.legs]); n=abs(q).sum(); h=plan.hedge_shares
    buy=np.where(q>0,entry_rows.best_offer,entry_rows.best_bid)
    sell=np.where(q>0,exit_rows.best_bid,exit_rows.best_offer)
    option_gross=100*float(q@(exit_rows.mid.to_numpy()-entry_rows.mid.to_numpy()))
    option_quoted=100*float(q@(sell-buy))
    stock_gross=h*(exit_spot-entry_spot)
    fees=2*n*protocol.commission_per_contract
    slippage=2*n*100*protocol.option_slippage_per_share
    stock_cost=abs(h)*(entry_spot+exit_spot)*protocol.stock_slippage_bps/10000
    net=option_quoted+stock_gross-fees-slippage-stock_cost
    return dict(option_mid_pnl=option_gross,stock_hedge_pnl=stock_gross,
        spread_cost=option_gross-option_quoted,commissions=fees,option_slippage=slippage,
        stock_cost=stock_cost,net_pnl=net,normalizer=100*entry_spot*max(abs(q).sum(),1),
        net_per_gross_option_notional=net/(100*entry_spot*max(abs(q).sum(),1)))


def simulate(plan,frames,surfaces,market,protocol):
    result=dict(strategy=plan.strategy,sid=plan.sid,signal_date=str(plan.signal_date),
        entry_date=str(plan.entry_date),deadline=str(plan.deadline),interval=plan.interval,
        legs=[dict(optionid=l.optionid,qty=l.qty,strike=l.strike,exdate=str(l.exdate),cp=l.cp_flag)
              for l in plan.legs],hedge_shares=plan.hedge_shares,signal_edge=plan.signal_edge,
        estimated_cost=plan.estimated_cost,exposure_mismatch=plan.exposure_mismatch,
        direction='long' if all(l.qty>0 for l in plan.legs) else
                  'short' if all(l.qty<0 for l in plan.legs) else 'spread')
    entry=frames.get(plan.entry_date,pd.DataFrame(columns=['optionid']))
    en,why=extract(entry,plan)
    if en is None: return dict(result,status='unfilled',reason=why)
    if plan.deadline>pd.Timestamp(protocol.end):
        return dict(result,status='censored',reason='horizon_outside_calibration')
    entry_stock=market.stock.loc[(plan.sid,plan.entry_date)]
    exit_date=plan.deadline; reason='maximum_holding_time'
    # Decision at a close -> liquidation at the FOLLOWING close. No fills at a
    # quote that was only just used to decide to liquidate.
    for date in market.dates[(market.dates>=plan.entry_date)&(market.dates<plan.deadline)]:
        if date not in frames or date not in surfaces: continue
        legs,_=extract(frames[date],plan)
        if legs is None: continue
        fair=surfaces[date].prices(legs)
        if fair.isna().any(): continue
        q=np.array([l.qty for l in plan.legs])
        cash=float(q@np.where(q>0,legs.best_bid,legs.best_offer))
        remaining=float(q@fair.to_numpy())-cash
        if remaining<=protocol.convergence_per_share*abs(q).sum():
            exit_date=market.shift(date,1); reason='convergence_signal_previous_close'; break
    ex,why=extract(frames.get(exit_date,pd.DataFrame(columns=['optionid'])),plan)
    if ex is None: return dict(result,status='unresolved',reason=why,exit_date=str(exit_date))
    exit_stock=market.stock.loc[(plan.sid,exit_date)]
    if entry_stock.cfadj!=exit_stock.cfadj:
        return dict(result,status='unresolved',reason='corporate_action_requires_contract_adjustment',exit_date=str(exit_date))
    values=settle(plan,en,ex,float(entry_stock.close),float(exit_stock.close),protocol)
    # Exact residual/model attribution where independent reference fits exist.
    if plan.entry_date in surfaces and exit_date in surfaces:
        a=surfaces[plan.entry_date].prices(en); b=surfaces[exit_date].prices(ex)
        if a.notna().all() and b.notna().all():
            q=np.array([l.qty for l in plan.legs]); model_change=100*float(q@(b.to_numpy()-a.to_numpy()))
            values['model_value_change']=model_change
            values['residual_convergence_pnl']=values['option_mid_pnl']-model_change
    return dict(result,status='closed',reason=reason,exit_date=str(exit_date),**values)


def simulate_session(plan,bars,protocol):
    """Real timestamped opening/closing option bars required. No synthetic opens.

    Required columns: timestamp (UTC aware), secid, optionid, strike, exdate,
    cp_flag, best_bid, best_offer, spot, cfadj. Additional depth/latency realism
    belongs in a later fill model; these remain quoted-price scenarios.
    """
    required={'timestamp','secid','optionid','strike','exdate','cp_flag','best_bid','best_offer','spot','cfadj'}
    if bars is None or not required.issubset(bars.columns):
        return dict(strategy='session_rotation',interval=plan.interval,status='blocked',
                    reason='timestamped_open_and_close_option_quotes_required')
    entry=bars[bars.timestamp.eq(plan.entry_date)&bars.secid.eq(plan.sid)].copy()
    exit=bars[bars.timestamp.eq(plan.deadline)&bars.secid.eq(plan.sid)].copy()
    for x in [entry,exit]: x['mid']=(x.best_bid+x.best_offer)/2
    en,why=extract(entry,plan)
    if en is None: return dict(strategy=plan.strategy,interval=plan.interval,status='unfilled',reason=why)
    ex,why=extract(exit,plan)
    if ex is None: return dict(strategy=plan.strategy,interval=plan.interval,status='unresolved',reason=why)
    if en.cfadj.iloc[0]!=ex.cfadj.iloc[0]:
        return dict(strategy=plan.strategy,interval=plan.interval,status='unresolved',reason='corporate_action')
    return dict(strategy=plan.strategy,interval=plan.interval,status='closed',
                **settle(plan,en,ex,float(en.spot.iloc[0]),float(ex.spot.iloc[0]),protocol))
