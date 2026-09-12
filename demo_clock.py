"""Illustrative clock inputs only: these weights/jumps are NOT calibrated."""
from datetime import datetime
from zoneinfo import ZoneInfo
from variance_clock import Session, ClockWeights
from clocked_pricer import ScheduledJump, price_clocked_option
from earnings_mixture import EarningsMixtureJump, MixtureComponent


def timestamp(value):
    return datetime.fromisoformat(value).replace(tzinfo=ZoneInfo('America/New_York'))


def main():
    # Explicit regular exchange sessions; production callers supply a complete
    # exchange schedule, including early closes and holidays.
    sessions = [Session(timestamp(day+'T09:30'), timestamp(day+'T16:00'))
                for day in ['2026-09-11', '2026-09-14', '2026-09-15']]
    start, expiry = sessions[0].close, sessions[-1].close
    args = dict(S0=100, K=100, start=start, expiry=expiry, r=.04, q=0,
                sigma_diff=.30, sessions=sessions)
    calendar, _ = price_clocked_option(**args, weights=ClockWeights(1, 1, 1))
    clock, exposure = price_clocked_option(**args, weights=ClockWeights(.2, .1, .1))
    # Optional independent reopening risks; zero closed-session background
    # variance here illustrates assigning ALL closure risk to the jumps.
    closure_jump = EarningsMixtureJump([MixtureComponent(.9, 0, .005),
                                       MixtureComponent(.1, 0, .02)])
    events = [ScheduledJump(s.open, closure_jump) for s in sessions[1:]]
    jumped, _ = price_clocked_option(**args, weights=ClockWeights(0, 0, 0), events=events)
    print('ILLUSTRATION ONLY — coefficients are not estimated from data')
    print('Exposure (hours):', {k: v/3600 for k, v in vars(exposure).items()})
    print(f'Calendar clock call: ${calendar:.4f}')
    print(f'Weighted clock call: ${clock:.4f}')
    print(f'Session variance plus two reopening jumps call: ${jumped:.4f}')


if __name__ == '__main__':
    main()
