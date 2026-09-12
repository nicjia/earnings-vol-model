from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from .protocol import STRATEGIES


@dataclass(frozen=True)
class Leg:
    optionid: int
    strike: float
    exdate: pd.Timestamp
    cp_flag: str
    qty: int
    signal_price: float
    signal_theory: float


@dataclass(frozen=True)
class Plan:
    strategy: str
    sid: int
    signal_date: pd.Timestamp
    entry_date: pd.Timestamp
    deadline: pd.Timestamp
    legs: tuple
    hedge_shares: int
    signal_edge: float
    estimated_cost: float
    exposure_mismatch: float = 0.0
    interval: str = 'close_to_close'

    def record(self):
        return asdict(self)


def hedge_ratio(a,b):
    if not np.isfinite([a,b]).all() or min(a,b)<=1e-5: return None
    # Small integer contract positions; minimize relative exposure mismatch.
    choices=[(abs(i*a-j*b)/(i*a+j*b),i+j,i,j) for i in range(1,6) for j in range(1,6)]
    err,_,i,j=min(choices)
    return i,j,err


def package(name,rows,qty,surface,protocol,entry,deadline,mismatch=0.):
    if deadline<=entry or rows.theory.isna().any(): return None
    qty=np.asarray(qty,dtype=int)
    edge=float(qty@(rows.theory-rows.mid).to_numpy())
    cost=float(abs(qty)@(2*rows.halfspread+2*protocol.option_slippage_per_share
                           +2*protocol.commission_per_contract/100).to_numpy())
    buffer=abs(qty).sum()*max(.05,protocol.uncertainty_per_spot*surface.spot,surface.fit_rmse)
    if abs(edge)<=cost+buffer: return None
    qty=qty if edge>0 else -qty
    legs=tuple(Leg(int(r.optionid),float(r.strike),pd.Timestamp(r.exdate),r.cp_flag,int(q),
                   float(r.mid),float(r.theory)) for r,q in zip(rows.itertuples(),qty))
    hedge=int(round(-100*float(qty@rows.model_delta.to_numpy())))
    return Plan(name,surface.sid,surface.date,entry,deadline,legs,hedge,abs(edge),cost,mismatch)


def proposals(scored,surface,protocol):
    """All selections depend only on the signal snapshot and known-date schedule.

    Each strategy is a separate research book; overlapping books are not summed
    into a portfolio. Parameters/thresholds are not searched against returns.
    """
    market=surface.market; date=surface.date
    entry=market.shift(date,1); normal_end=market.shift(entry,protocol.maximum_holding_sessions)
    events=[pd.Timestamp(e) for e in market.events[surface.sid]]
    future=[e for e in events if e>date]; past=[e for e in events if e<date]
    next_event=min(future) if future else None
    if entry in events: return []
    rows=scored[(scored.best_bid>0)&(scored.best_offer>=scored.best_bid)&
                (scored.halfspread/scored.mid<.2)&scored.theory.notna()&scored.model_delta.notna()].copy()
    rows=rows[(rows.strike/surface.spot).between(.85,1.15)]
    if rows.empty: return []
    rows['abs_gap']=(rows.theory-rows.mid).abs()
    result=[]
    # Limit each strategy/name to one proposal per snapshot; best discrepancy is
    # selected before execution. The backtester rejects overlap within that book.
    def best(plans):
        p=[p for p in plans if p is not None]
        if p: result.append(max(p,key=lambda x:x.signal_edge-x.estimated_cost))
    otm=rows[((rows.cp_flag=='C')&(rows.strike>=surface.spot))|
             ((rows.cp_flag=='P')&(rows.strike<surface.spot))]
    singles=otm.sort_values('abs_gap',ascending=False).head(12)
    event_inside=next_event is not None and next_event<=normal_end
    if not event_inside:
        best(package('single_convergence',r.to_frame().T,[1],surface,protocol,entry,normal_end)
             for _,r in singles.iterrows())
    if past and 1<=(date-max(past)).days<=5:
        best(package('post_earnings',r.to_frame().T,[1],surface,protocol,entry,normal_end)
             for _,r in singles.iterrows())
    pre_window=next_event is not None and 4<=(next_event-date).days<=14
    if pre_window:
        deadline=min(normal_end,market.shift(next_event,-2))
        best(package('pre_earnings',r.to_frame().T,[1],surface,protocol,entry,deadline)
             for _,r in singles[singles.exdate>next_event].iterrows())

    # Same-event calendars and ordinary weekend calendars have distinct filters.
    calendar_plans=[]; weekend_plans=[]
    is_closure=(market.shift(entry,1)-entry).days>=3
    for (_,cp),g in rows.groupby(['strike','cp_flag']):
        g=g.sort_values('exdate')
        if len(g)<2: continue
        a,b=g.iloc[0],g.iloc[-1]
        pair=pd.DataFrame([a,b])
        if pre_window and a.exdate>next_event and b.exdate>next_event:
            # Both must contain exactly the same one event.
            if sum(date<e<=b.exdate for e in events)==1:
                h=hedge_ratio(a.event_sensitivity,b.event_sensitivity)
                if h and h[2]<.15:
                    calendar_plans.append(package('event_calendar',pair,[h[0],-h[1]],surface,
                        protocol,entry,min(normal_end,market.shift(next_event,-2)),h[2]))
        if is_closure and not event_inside:
            h=hedge_ratio(a.diffusion_sensitivity,b.diffusion_sensitivity)
            if h and h[2]<.15:
                weekend_plans.append(package('weekend_calendar',pair,[h[0],-h[1]],surface,
                    protocol,entry,market.shift(entry,1),h[2]))
    best(calendar_plans); best(weekend_plans)

    # Equal-spaced call butterflies: terminal exposure is bounded before any
    # stock hedge. Restrict to target strikes; reference strikes are never legs.
    flies=[]
    for exp,g in rows[rows.cp_flag=='C'].groupby('exdate'):
        g=g.sort_values('strike')
        if len(g)>15: g=g.iloc[np.argsort(abs(g.strike/surface.spot-1))[:15]].sort_values('strike')
        for i in range(len(g)-2):
            for k in range(i+2,len(g)):
                mid=(g.iloc[i].strike+g.iloc[k].strike)/2
                centers=g.iloc[i+1:k][np.isclose(g.iloc[i+1:k].strike,mid)]
                if centers.empty: continue
                triple=pd.DataFrame([g.iloc[i],centers.iloc[0],g.iloc[k]])
                deadline=normal_end
                if next_event is not None and entry<next_event<=deadline:
                    deadline=max(deadline,market.shift(next_event,2))
                flies.append(package('butterfly_shape',triple,[1,-2,1],surface,protocol,entry,deadline))
    best(flies)
    return result


def session_proposals(scored,surface,protocol,physical_session_rate):
    """Gamma/variance-premium signal for open/close bars, not closing substitutes.

    No earnings-containing intervals. The physical variance forecast is learned
    strictly from past underlying intervals; Q variance comes from fitted options.
    Exposure is initially delta-hedged, not continuously hedged. The approximation
    is a signal heuristic; actual marked P&L is required to validate it.
    """
    market=surface.market; day=market.shift(surface.date,1); following=market.shift(day,1)
    if any(day<=pd.Timestamp(e)<=following for e in market.events[surface.sid]): return []
    rows=scored[(scored.strike/surface.spot).between(.95,1.05)&(scored.best_bid>0)&
                (scored.halfspread/scored.mid<.15)&scored.theory.notna()].copy()
    if rows.empty: return []
    eps=surface.spot*.002
    gamma=(surface.prices(rows,spot=surface.spot+eps)-2*surface.prices(rows)
           +surface.prices(rows,spot=surface.spot-eps))/eps**2
    session_seconds=(market.schedule.loc[day,'close']-market.schedule.loc[day,'open']).total_seconds()
    gap_seconds=(market.schedule.loc[following,'open']-market.schedule.loc[day,'close']).total_seconds()
    gap_weight=surface.weights.weekend if (following-day).days>=3 else surface.weights.overnight
    output=[]
    for kind,seconds,weight in [('daytime',session_seconds,1.),('overnight',gap_seconds,gap_weight)]:
        physical=physical_session_rate*seconds*weight
        implied=surface.parameters[0]**2*seconds*weight/(365*24*3600)
        edges=.5*gamma*surface.spot**2*(physical-implied)
        costs=2*rows.halfspread+2*protocol.option_slippage_per_share+2*protocol.commission_per_contract/100
        good=(edges.abs()>costs+np.maximum(.05,protocol.uncertainty_per_spot*surface.spot))&gamma.gt(0)
        if not good.any(): continue
        idx=(edges.abs()-costs).where(good).idxmax(); r=rows.loc[idx]
        qty=1 if edges.loc[idx]>0 else -1
        leg=Leg(int(r.optionid),float(r.strike),r.exdate,r.cp_flag,qty,float(r.mid),float(r.theory))
        start=market.schedule.loc[day,'open' if kind=='daytime' else 'close']
        end=market.schedule.loc[day if kind=='daytime' else following,'close' if kind=='daytime' else 'open']
        output.append(Plan('session_rotation',surface.sid,surface.date,start,end,(leg,),
            int(round(-100*qty*r.model_delta)),float(abs(edges.loc[idx])),float(costs.loc[idx]),interval=kind))
    return output
