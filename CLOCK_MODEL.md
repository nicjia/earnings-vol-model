# Overnight and weekend option pricing

The new `price_clocked_option` entry point prices individual European calls and
puts using separate elapsed-time buckets: regular session, weekday overnight,
weekend closure and weekday holiday closure. It supports flat diffusion or a
deterministically time-changed Heston process, plus timestamped independent jumps.

This is pricing infrastructure. No overnight/weekend coefficients have been
estimated, no existing empirical applications have been recalibrated, and no
new trading edge is claimed. Existing calls retain their calendar-time behavior.

## Two clocks

Interest and continuous dividend carry use actual calendar seconds / (365 days).
Background variance uses

    variance_time = (session_seconds + overnight_weight * overnight_seconds
                     + weekend_weight * weekend_seconds
                     + holiday_weight * holiday_seconds) / seconds_per_year
    integrated_variance = sigma_diff**2 * variance_time

Session weight is fixed at one to set the scale. All three closure weights equal
to one reproduce calendar time. Weights are variance multipliers, not volatility
multipliers. `sigma_diff` must be fitted consistently with this normalization;
do not reuse a previously fitted calendar-time volatility with new weights and
interpret the resulting price change as corrected fair value.

In Heston mode, both variance dynamics and return diffusion evolve in variance
time. Carry and discounting remain in calendar time. This is a deterministic
time-change specification, not a general session-switching Heston model. Its
parameters must also be refitted in that time unit.

## Exchange schedule and timestamps

Supply a complete ordered list of `Session(open, close)` with timezone-aware
timestamps. Sessions must bracket the entire valuation-to-expiry horizon. Use
actual exchange opens/closes, including early closes and holidays. The code does
not download an exchange calendar and cannot infer a missing session row versus
a real holiday. It does reject missing horizon coverage and overlapping sessions.

Durations are calculated in UTC; local exchange dates determine closure type.
A Friday-close to Monday-open gap is one weekend closure. A weekday closure
spanning a holiday is one holiday closure. Weekend classification takes
precedence for holiday weekends. This classification applies to the full gap,
including its Friday evening and Monday morning. Partial gaps are prorated by
actual elapsed seconds. A DST weekend therefore contains one fewer/more hour.

Jumps apply only when `valuation < event_timestamp <= expiry`. Pass the actual
expiration timestamp; do not substitute midnight on the expiration date. Events
already realized are excluded. A reopening jump is represented at the chosen
reopening timestamp, which is a modeling convention for accumulated closed-market
risk, not a forecast that all news arrives at that moment.

## Multiple jumps without exponential expansion

With K components per event and n independent events, explicit mixture expansion
has K**n paths. The COS characteristic function instead uses

    phi_total(u) = phi_background(u) * product(phi_event_j(u))

At N Fourier frequencies this costs O(N * sum(K_j)) per evaluation, not K**n.
Identically distributed independent events can equivalently use phi_event(u)**n.
Monte Carlo samples one component per event on each path, also without building
the full tree. COS accuracy still depends on truncation and frequency resolution;
extreme or nearly discrete distributions require convergence checks.

One mixture component is a distributional component, not a forecast of a specific
news story. Weekend jumps are not inherently inappropriate. A flexible core/tail
mixture may be useful if supported by calibration. A beat/miss interpretation is
unnecessary. Dependence between jumps, or jump distributions conditional on past
outcomes/volatility, is not captured by the independent product.

Do not estimate background closure variance from the entire close-to-open return
and then add another jump calibrated to that same entire return. Either allocate
closure risk to a variance clock, to reopening jumps, or fit their combined
contribution jointly. Earnings-containing closures must separate scheduled-event
risk from ordinary closure risk. Physical return distributions are not directly
risk-neutral option-pricing distributions.

## Run

    python demo_clock.py
    python -m unittest -v test_variance_clock

The demo deliberately labels its arbitrary coefficients as illustrative. Tests
cover calendar equivalence, carry/parity, actual-hour DST changes, holidays,
partial closures, event timestamps, and COS versus exact/Monte Carlo pricing.

## Calibration and trading diagnosis

Session and closure coefficients need identifiable calibration data: suitable
option prices across timestamps/expirations and/or session/close-to-open return
observations. A term structure where session and closure exposures are nearly
collinear cannot reliably identify all weights. Separate ordinary closures from
earnings, use only the designated calibration period, and freeze all parameters
before testing later observations. Historical returns can constrain a model but
do not by themselves identify its risk-neutral jump distribution.

The existing executable straddle experiment uses a standardized history-versus-
premium rule and a fixed post-announcement exit. It neither computes model fair
values nor exits on convergence. Long/short P&L alone therefore does not identify
overpricing/underpricing by this pricing engine.

For model calibration diagnostics, record theoretical price, bid/ask, timestamp,
contract and calibration provenance. Report signed theoretical-minus-mid errors
by side, strike, expiry and clock exposure, with leave-out contracts where
possible. Fitted-point residuals measure fit, not independent predictive accuracy.

A future convergence exit would monitor the executable liquidation quote against
an updated theoretical value with a defined tolerance, plus maximum holding time
and event/expiry rules. Exact equality is not a practical trigger. Convergence
can happen because the model value moves toward the market rather than the market
moving favorably, so it does not guarantee profit. This change does not install a
convergence trading rule or claim that closing snapshots suffice for intraday fills.
