# Strategies

Rules that have passed an untouched out-of-sample test, specified exactly enough to implement.
This file is updated as new data and tests arrive. Last update: 2026-10-03 (research8: no new rule passed; see
`research8/README.md`).

**Status key**
- **Validated**: passed every pre-registered gate on data no rule was fitted to (research7 sample E: ~500 names never used
  before, 2018-2025).
- **Provisional**: passed sample E but with a warning sign; trade only on paper until forward data confirms it.
- Nothing here is validated for real money. All results assume closing **midpoint** fills unless a cost column says otherwise;
  whether real fills come close is untested. Next test: forward paper trading with recorded fills.

## Shared definitions (all strategies)

**Events.** Quarterly EPS announcements from I/B/E/S (`ibes.actu_epsus`, `pdicity='QTR'`, `measure='EPS'`), with
announcement date `d` and time `t` (US Eastern). One event per security and fiscal quarter (earliest announcement).

**Release timing (P and Q).**
- `d` a trading session and `t < 09:30`: **P** = session before `d`, **Q** = `d` (released before the open).
- `d` a trading session and `t >= 16:00`: **P** = `d`, **Q** = next session (released after the close).
- `d` not a trading session: **P** = last session before `d`, **Q** = first session after `d`.
- `09:30 <= t < 16:00` or `t` missing: **do not trade**.

P is the last close before the release; Q is the first close after it. `P-k` means k sessions before P.

**Prices and fills.** Decide and trade at the closing quote of the stated session (live analogue: about 15 minutes before
the close). Research fills are at the bid/ask midpoint of every leg, plus $0.65 per contract per side. "25% cost" means paying
an extra 25% of each leg's quoted half-spread at entry and at exit (50% likewise).

**Spot.** Stock closing price at the decision close. Skip if below $10.

**Front expiry for pre-release trades.** The first listed expiry with expiration date `>= Q` (it contains the release) and
`<= Q + 10 calendar days`, listed at the decision close. Skip if none.

**ATM strike.** The front-expiry strike, among those with both call and put bid and ask quoted, nearest the spot.

**Implied move M.** `(ATM call mid + ATM put mid) / spot` at the decision close.

**Strangle strikes.** Put: the quoted put strike strictly below spot nearest `spot x (1 - 0.5 M)`. Call: the quoted call
strike strictly above spot nearest `spot x (1 + 0.5 M)`.

**Liquidity (checked on every leg at entry).** bid > 0, mid >= $0.05, open interest >= 10, and
`(ask - bid) / mid <= 0.10` (**tight**) or `<= 0.25` (**standard**; long protective wings of short structures may go to 0.50).

**Exclusions.** Skip if a cash dividend ex-date falls after the entry date and on or before the expiry. Skip if the stock's
split adjustment factor changes between entry and exit.

**Historical signals (stock history only; earlier events are those whose Q is on or before the decision date).**
- `J_k = log(close at Q_k / close at P_k)` for an earlier event k, computed from total returns.
- Background vol `sigma`: daily log returns over the last 60 sessions up to the decision close, excluding the release
  returns (sessions after P_k up to Q_k) of earlier events; need at least 40. Seed the variance with the mean of the first 20
  squared returns, then `var = 0.94 x var + 0.06 x r^2` over the rest. `sigma = sqrt(var)`.
- `s = sigma x sqrt(max(n - 1, 0) / 252)`, where n = weekdays after the decision date up to and including the expiry date.
- **H** = average over the last 8 earlier events (need at least 6) of `E|J_k + s Z| = s sqrt(2/pi) exp(-J_k^2 / (2 s^2)) + J_k (1 - 2 Phi(-J_k / s))`.
- **R** = `M / H` (implied move relative to the stock's historical release move).
- **HR** = average over the last 8 earlier events with data (need at least 4) of `|J_k| / M_k`, where `M_k` is M measured at
  that event's P close with the pre-release front rule (how big releases were relative to what options implied).

**Returns.** P&L divided by the debit paid (long premium) or by `max wing width x 100 - credit` (short iron fly).
Results are averages per issuer-event; confidence intervals resample whole calendar weeks.

## Validated: pre-release long premium

All hold options **before** the release and sell at the **P close**, never through the release.

### S1. Strangle, P-1 to P, R <= 0.9, tight

- **Entry:** at the P-1 close, buy the strangle (strikes above) in the pre-release front expiry if `R <= 0.9`. Tight liquidity.
- **Exit:** sell both legs at the P close.
- **Results:**

  | Sample | Events | Mid | 95% CI | 25% cost | 50% cost |
  |---|---|---|---|---|---|
  | Sample E (untouched) | 252 | +4.0% | +2.0% to +6.0% | +2.5% | +1.0% |
  | Earlier samples B+C+D | 330 | +5.8% | +3.8% to +8.0% | +4.5% | +3.2% |

- Annual Sharpe on the earlier samples 1.44 (mid), 0.92 (25%). Holds when the signal is taken one session earlier.
- **Caution:** in sample E it worked for after-close releases (+4.5%) but not clearly for before-open ones (+1.6%, 43 events).

### S2. Straddle, P-9 to P, no filter, tight

- **Entry:** at the P-9 close, buy the ATM straddle in the pre-release front expiry. Tight liquidity.
- **Exit:** at the P close.
- **Results:**

  | Sample | Events | Mid | 95% CI | 25% cost | 50% cost |
  |---|---|---|---|---|---|
  | Sample E | 1,393 | +4.6% | +2.2% to +7.1% | +2.7% | +0.8% |
  | Earlier samples A / B / C / D | 934 / 693 / 815 / 700 | +2.1% / +2.8% / +2.5% / +4.7% | | | |

- Works for both release timings in E (+4.5% before open, +4.8% after close). This has the largest sample of the passing
  rules; the weekly front often is not listed yet at P-9, which limits how often it can trade.

### S3. Straddle, P-4 to P, HR >= 1.0 (standard or tight)

- **Entry:** at the P-4 close, buy the ATM straddle if `HR >= 1.0` (the stock has tended to move at least as much as options
  implied).
- **Exit:** at the P close.
- **Results:**

  | Sample | Events | Mid | 95% CI | 25% cost | 50% cost |
  |---|---|---|---|---|---|
  | Sample E, standard | 651 | +3.4% | +1.7% to +5.2% | +1.3% | -0.9% |
  | Sample E, tight | 473 | +3.0% | +1.4% to +4.6% | +1.5% | -0.1% |
  | Earlier samples, standard | | +2.8% / +3.9% / +3.0% / +2.8% (A/B/C/D) | | | |

### S4. Strangle, P-1 to P, HR >= 1.0, tight

- **Entry:** S1's structure and timing, with `HR >= 1.0` instead of the R filter.
- **Results:** sample E: 355 events, +2.8% (+1.0% to +4.6%), +1.2% at 25% cost, -0.3% at 50%. Earlier samples:
  +2.4% / +3.0% / +4.3% / +3.4%.

### S5. Straddle, P-1 to P, R <= 0.9, tight

- **Entry:** S1's timing and filter, with the ATM straddle.
- **Results:** sample E: 341 events, +2.0% (+0.7% to +3.2%), +0.6% at 25% cost, -0.8% at 50%.
- **Caution:** after-close releases only (+2.7%); before-open releases showed nothing (-0.2%). Weaker than S1.

**Why it may work.** Implied volatility tends to rise into earnings while the stock usually moves little before the release.
With exact release times, 91% of trades (those with small pre-release stock moves) were still profitable on average, so the
gain is not just from a few large pre-release moves.

## Portfolio of S1-S5 (descriptive, 2026-10-03)

Treating every S1-S5 trade as one unit of risk and averaging trades by entry week (research8/sportfolio.py;
docs/research8/sportfolio*): annual Sharpe at midpoint 0.9 / 1.9 / 2.2 / 1.3 in samples B / C / D / E, but only
0.2 / 1.5 / 1.2 / 0.5 at 25% cost and -0.6 / 1.1 / 0.2 / -0.4 at 50% cost. Adding P1 raises E to 0.65 at 25% cost.
The combination is positive at midpoint everywhere but not robust to realistic fills; this is not a test (every rule
had already passed E), and only forward paper trading with recorded fills can decide it.

## Passed an untouched test, thin evidence (research8, 2026-10-03)

### V1. Index put-writing only when VIX is far above a stock-only vol forecast (HAR >= 1.5)

- **Data/inputs (all public):** SPX daily closes, VIX close, the CBOE S&P 500 PutWrite index (PUT), 3-month T-bill (DTB3).
- **Model (stock-only):** HAR on SPX's own daily log returns: regress log(mean squared return over the next 21
  sessions) on logs of mean squared returns over the last 1, 5, 22 and 66 sessions (floors 1e-10), refitted each
  1 January on all pairs ending before it; forecast = exp(fit) x mean(exp(residual)); sigma_hat = sqrt(252 x forecast).
- **Decision:** at each monthly roll close (third Friday, or the previous session), if `VIX/100 / sigma_hat >= 1.5`,
  sell the one-month ATM SPX put (as the PUT index does, cash-secured in T-bills) and hold to the next roll; otherwise
  hold T-bills.
- **Results** (excess over T-bills, 15 bp of notional cost per held month; research8/putwrite.py, docs/research8/putwrite):

  | Sample | Months | Held | Sharpe | Block t | Max drawdown | "Always sell" Sharpe / max DD |
  |---|---|---|---|---|---|---|
  | Dev 2007-2015 | 107 | 5 | 0.71 | 2.09 | 0.0% | 0.30 / 37.5% |
  | Test 2016-2026 (untouched) | 129 | 14 | 1.07 | 2.70 | 0.2% | 0.46 / 30.1% |

  It passed every pre-registered strong gate (lower bound > 0, Sharpe >= 1.0, t >= 2.0, above "always", drawdown
  no larger).
- **Why it is thin:** only 19 active months in 19 years (7 of the 14 test months in 2021), so the average excess return
  on capital is small (+0.16% per month) even though it is +1.5% per held month with 93% winning months. Lower
  thresholds (1.1-1.3) were exposed to a -28% month that 1.5 avoided only because that month's ratio fell between 1.3
  and 1.5; a single crash month entered at ratio >= 1.5 would dominate the record. The PUT index is a benchmark: real
  fills, early assignment and margin are not modelled. The companion frozen rule (EWMA >= 1.0) failed the test.
- **Next step:** forward paper trading with recorded fills; size so that a -30% month on the put notional is tolerable.

## Provisional

### P1. Short 2x iron fly, P-4 to Q+4, standard (no filter, or R >= 1.0)

- **Expiry:** front = first listed expiry with expiration `>= max(Q+4 session date, Q)` and `<= Q + 30 days`.
- **Entry:** at the P-4 close, sell the ATM call and put; buy the put at the quoted strike strictly below the ATM strike
  nearest `K - 2 x straddle`, and the call strictly above nearest `K + 2 x straddle` (straddle = ATM call mid + put mid).
  Standard liquidity.
- **Exit:** at the Q+4 close (legs expiring that day settle at intrinsic from the stock close). Risk = largest wing width x 100 - credit.
- **Results:** sample E: 595 events, +8.3% (+5.0% to +11.5%), +5.3% at 25% cost, +2.2% at 50%. With `R >= 1.0`: +6.6%.
  Earlier samples: +2.3% / +6.5% / +3.6% / +4.4%.
- **Why provisional:** the gain is concentrated. It comes from the names added in 2020 (+18.4%) and after-close releases
  (+13.8%); the 2017-formation names (+3.3%) and before-open releases (+1.8%) are not significant. Losses can reach the full
  risk (worst -103%).

## Tested and rejected (do not trade)

- **Weekly calendars and double calendars held through earnings** (including short weekly / long next week at the
  expected-move edges, entered 1-4 sessions before the release and held to the short weekly's expiry): positive at midpoint
  (+3% to +14%) but negative at 25% of the half-spread on untouched names. All five frozen calendar policies failed sample E.
- **Post-release trades** (iron flies after the release, verticals following or fading the move or the EPS surprise).
- **Unfiltered long straddles/strangles held through the release**; most short iron condors and 1x iron flies.
- **Arbitrage-free ReLU curve and history-forecast payoff design**: no gain at executable prices (`docs/explorations/`).

## Implementation requirements

- A reliable announcement **time** (before the open or after the close) for every upcoming release; skip unknown or
  in-session times.
- Close-of-day execution with the legs filled together; record every fill against the quoted bid/ask to measure real cost.
- Equal risk per trade (research convention); the illustration used 2% of equity at risk per trade with overlapping positions.
- Never hold the pre-release strategies (S1-S5) through the release.

Sources: `research7/` (code and protocol), `docs/research7/` (A-D results), `docs/research7/E/REPORT_E.md` (sample E),
`docs/research7/sharpe_dsr.json` (Sharpe and deflated Sharpe).
