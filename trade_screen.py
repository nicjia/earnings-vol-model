"""Conservative current-quote screening; not a forecast or order interface."""
from dataclasses import dataclass
import numpy as np
from market_surface import MarketSlice

@dataclass(frozen=True)
class QuoteAssessment:
    value: float
    eligible: bool
    reasons: tuple[str, ...]
    signed_mid_edge: float


def assess_quote(surface: MarketSlice, strike: float, call: bool, bid: float,
                 ask: float, direction: int, *, minimum_edge=.20,
                 minimum_premium=1., maximum_relative_spread=.10,
                 roundtrip_commission=.013) -> QuoteAssessment:
    """Screen a fresh snapshot before retaining a previously selected direction.

    Surface and bid/ask must be contemporaneous (caller responsibility). Prices
    and commissions are per share. No fill, physical-return, or exit-cost promise
    is implied. Reference RMSE is a heuristic buffer, not a confidence interval.
    """
    if direction not in (-1,1):raise ValueError('Direction must be +1 or -1')
    values=[strike,bid,ask,minimum_edge,minimum_premium,maximum_relative_spread,roundtrip_commission]
    if not np.isfinite(values).all() or strike<=0 or bid<0 or ask<bid or min(values[3:])<0:
        raise ValueError('Require valid finite quotes, strike and nonnegative screening settings')
    value=float(surface.price(strike,call));mid=(bid+ask)/2;edge=direction*(value-mid);reasons=[]
    if not surface.reference_strikes.min()<=strike<=surface.reference_strikes.max():reasons.append('outside_reference_strikes')
    if mid<minimum_premium or mid<=0:reasons.append('small_premium')
    if mid<=0 or (ask-bid)>maximum_relative_spread*mid:reasons.append('wide_spread')
    if edge<=minimum_edge*mid:reasons.append('insufficient_directional_edge')
    if edge<=ask-bid+roundtrip_commission+2*surface.reference_rmse:reasons.append('insufficient_cost_buffer')
    return QuoteAssessment(value,not reasons,tuple(reasons),edge)
