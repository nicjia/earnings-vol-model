"""Timestamp-aware entry point for session/closure variance and scheduled jumps."""
from dataclasses import dataclass
from datetime import datetime

from variance_clock import clock_exposure, utc
from earnings_mixture import EarningsMixtureJump, price_option
from cos_pricer import price_diffusion_jumps, price_heston_jump


@dataclass(frozen=True)
class ScheduledJump:
    at: datetime
    distribution: EarningsMixtureJump


def price_clocked_option(S0, K, start, expiry, r, q, sigma_diff, sessions,
                         weights, events=(), call=True, *, heston=None,
                         exchange_timezone="America/New_York", **cos_options):
    """Price a European option and return (price, ClockExposure).

    Uses actual timestamps: jumps at/before valuation are already realized;
    jumps after expiry are excluded. A jump exactly at expiry is included.
    Reopening jumps are optional explicit events, not automatically inferred.
    """
    exposure = clock_exposure(start, expiry, sessions, exchange_timezone)
    jumps = tuple(e.distribution for e in events if utc(start) < utc(e.at) <= utc(expiry))
    T, tv = exposure.calendar_time, exposure.variance_time(weights)
    if heston is not None:
        value = price_heston_jump(S0, K, T, r, q, heston, call=call,
                                  variance_time=tv, jumps=jumps, **cos_options)
    elif len(jumps) <= 1:
        value = price_option(S0, K, T, r, q, sigma_diff,
                             jumps[0] if jumps else None, call, variance_time=tv)
    else:
        value = price_diffusion_jumps(S0, K, T, r, q, sigma_diff, jumps,
                                      call, variance_time=tv, **cos_options)
    return value, exposure
