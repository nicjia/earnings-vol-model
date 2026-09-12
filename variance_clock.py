"""Deterministic variance clock from an explicit, complete exchange schedule.

Supply actual timezone-aware session opens/closes, including holidays and early
closes. No weekday-only calendar or fitted overnight/weekend weights are assumed.
All elapsed durations are measured in UTC (including across daylight saving).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from zoneinfo import ZoneInfo

YEAR_SECONDS = 365.0 * 24 * 60 * 60


def utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Use timezone-aware datetime timestamps")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class Session:
    open: datetime
    close: datetime


@dataclass(frozen=True)
class ClockWeights:
    """Relative variance per elapsed second; session scale is fixed at one.

    These are risk-neutral model inputs, not estimates provided by this module.
    All ones reproduce calendar time. A weekend weight applies to the entire
    Friday-close to Monday-open closure, not just Saturday and Sunday.
    """
    overnight: float
    weekend: float
    holiday: float

    def __post_init__(self):
        if any(not isfinite(x) or x < 0 for x in (self.overnight, self.weekend, self.holiday)):
            raise ValueError("Variance weights must be finite and nonnegative")


@dataclass(frozen=True)
class ClockExposure:
    session: float = 0.0
    overnight: float = 0.0
    weekend: float = 0.0
    holiday: float = 0.0

    @property
    def calendar_time(self):
        return (self.session + self.overnight + self.weekend + self.holiday) / YEAR_SECONDS

    def variance_time(self, weights):
        return (self.session + self.overnight * weights.overnight
                + self.weekend * weights.weekend + self.holiday * weights.holiday) / YEAR_SECONDS


def clock_exposure(start, expiry, sessions, exchange_timezone="America/New_York"):
    """Split [start, expiry] into disjoint session and exchange-closure seconds.

    Schedule must be chronological, complete and bracket the horizon, including
    adjacent sessions when the horizon starts/ends inside a closure. Missing
    session rows cannot be distinguished from holidays: completeness is the
    caller's responsibility. Weekend closures take precedence over holidays.
    """
    start, expiry = utc(start), utc(expiry)
    if expiry < start:
        raise ValueError("Expiry precedes valuation")
    if expiry == start:
        return ClockExposure()
    spans = [(utc(s.open), utc(s.close)) for s in sessions]
    if not spans or spans[0][0] > start or spans[-1][1] < expiry:
        raise ValueError("Exchange schedule must bracket the entire horizon")
    for i, (a, b) in enumerate(spans):
        if a >= b or (i and a <= spans[i-1][1]):
            raise ValueError("Sessions must be ordered, nonoverlapping and nonempty")
    zone = ZoneInfo(exchange_timezone)
    seconds = dict(session=0.0, overnight=0.0, weekend=0.0, holiday=0.0)

    def add(kind, a, b):
        seconds[kind] += max(0.0, (min(expiry, b) - max(start, a)).total_seconds())

    for i, (a, b) in enumerate(spans):
        add("session", a, b)
        if i + 1 == len(spans):
            continue
        nxt = spans[i+1][0]
        first, last = b.astimezone(zone).date(), nxt.astimezone(zone).date()
        days = (last - first).days
        weekend = any((first + timedelta(days=k)).weekday() >= 5 for k in range(days+1))
        kind = "weekend" if weekend else "holiday" if days > 1 else "overnight"
        add(kind, b, nxt)
    return ClockExposure(**seconds)
