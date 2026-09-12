# Historical earnings-jump trading experiments

## Findings

The 112-event comparison did not establish a profitable historical-jump replacement. At the specified 10% threshold with a fixed stock hedge, direct historical replacement earned +4.47% at midpoint fills after modeled costs and +1.54% crossing quotes for 77 straddles, versus -2.07% / -5.35% for 439 single options. The straddle event-bootstrap interval after crossing quotes spans roughly -10% to +12%. Anchoring the replacement to the delivered market curve returned -2.82% / -5.90% for 63 straddles and -6.27% / -9.72% for 346 singles. Both long and short sides of that anchored strategy lost on average.

The delivered market hybrid itself generated no 10% or 20% signals in the selected candidate set. At 5%, it generated six individual-option trades across four events: +11.45% at midpoint fills after costs, -1.57% crossing quotes. This tiny sample does not establish midpoint profitability. The older uncorrected structural model gave positive 10% averages, but its intervals included losses. Unhedged outcomes differ and are reported below; a positive unhedged result should not be labeled an isolated volatility edge.

Results vary materially by year. The direct historical straddle strategy's crossed means were +23.12%, -10.34%, -20.18%, +1.13%, +20.31%, and -2.21% for 2020 through 2025 respectively. Its worst individual result was a short NFLX straddle around January 2022, losing approximately 206% of entry option premium, including its fixed stock hedge and modeled costs. None of the paired comparisons with always-short exposure established an improvement using the calendar-week intervals.

## What was tested

Five recurring names (ADBE, AMD, AMZN, NFLX, TSLA), plus GOOGL in 2020, across 2020–2025. The expanded 2021–2024 panels were requested before their results were inspected. No winning threshold was selected afterward. 2020 and 2025 had been examined in earlier project work; this is historical research, not a prospective live result.

Historical jump variance uses the own-name last eight completed earnings events, minimum six. Each historical outcome is the compounded stock return from the close before the reported announcement to the close after it. Subtract the estimate of two ordinary sessions' variance (last 60 non-event observations), average the excess squares, and floor the final variance at zero. Map that variance into the existing compensated mixture, keeping its shape and zero risk-neutral multiplicative drift. This is a physical-history-informed valuation hypothesis, not a known true price or a fully historical distribution fit.

The latest identifiable reference-only Heston/jump calibration, at most 30 days old and referring to the same upcoming announcement, supplies frozen structural parameters. The signal-date spot, carry, and reference quotes are observed at the signal. The implied jump is replaced without refitting diffusion, stochastic-volatility parameters, or the replacement jump to the option target. Expansion years use anchor snapshots 15 and 10 sessions before earnings; earlier panels use their existing eligible anchors.

Methods: frozen_market_structural is the original frozen structural fit; historical_structural changes only its jump scale. historical_reference_anchored begins at linear reference-IV pricing and adds the change in implied total variance caused by replacing the structural jump. current_market_hybrid and current_market_only call the delivered constrained MarketSlice API, with and without the structural prior. historical_final_anchored applies the same jump-variance change to the delivered hybrid. Reference correction is computed before replacement, never refitted to erase the historical signal. The adjusted historical forecast curves are not claimed to retain every strike constraint of the market curve.

Signal three sessions before the reported earnings date; entry at the following close (two sessions before); exit at the first close after the date. This fixed exit captures both morning and evening releases without choosing the largest return day. Thresholds are 0%, 5%, 10%, 20% of the signal midpoint, with 10% the designated main comparison. Long if prediction exceeds midpoint by the threshold, short for the symmetric shortfall. The signal is not recomputed using next-close execution quotes.

At the earliest eligible 8–45 day expiry, choose the nearest three held-out strikes per call/put, and separately one nearest held-out ATM call/put straddle. Target signal bids must be positive, each leg midpoint at least $0.25; target relative spreads are not screened away. Identical contracts are followed at entry and exit, with no exit-delta filtering. Current-market reference filters are unchanged from the existing pricing pipeline.

Both unhedged and fixed initial reference-IV delta-hedged positions are evaluated. No hedge rebalancing occurs. Mid gross assumes midpoint fills with no costs. Mid net adds $0.65 per contract per side and 2 bp per side of stock traded. Crossed net buys at ask and sells at bid, adding the same costs. There is no extra option slippage on top of the requested fill scenarios.

**All percentage performance tables below divide P&L by entry option midpoint premium. They are not account returns, annual returns, or returns on short-option margin. Individual contracts are averaged within each company-earnings event, then events equally weighted. Positive short returns do not measure capital efficiency.** Different strategy rows overlap and must not be added as a portfolio.

## Coverage and checks

{
  "eligible_events": 112,
  "single_candidates": 668,
  "straddle_candidates": 112,
  "unresolved": 0,
  "past_only_history": true,
  "delayed_execution": true,
  "midpoint_and_crossed_same_trades": true,
  "mirrored_pnl_check": true,
  "candidate_entry_relative_spread_median_pct": 1.6927661647348762,
  "candidate_entry_relative_spread_p90_pct": 4.893178158982212,
  "historical_anchor_variance_floor_positions": 7
}

| year | status | events |
|---|---|---|
| 2020 | eligible | 18 |
| 2020 | missing_date | 1 |
| 2020 | no_identifiable_anchor | 5 |
| 2021 | eligible | 20 |
| 2022 | eligible | 20 |
| 2023 | eligible | 20 |
| 2024 | eligible | 20 |
| 2025 | eligible | 14 |
| 2025 | missing_date | 6 |

## Main 10% threshold, fixed stock hedge

| model | kind | fill | closed | events | equal_event_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|---|---|---|---|
| frozen_market_structural | single | bidask_net | 264 | 59 | 6.61 | -15.48 | 28.80 |
| frozen_market_structural | single | mid_net | 264 | 59 | 9.45 | -11.76 | 33.19 |
| frozen_market_structural | straddle | bidask_net | 46 | 46 | 7.77 | -6.91 | 23.14 |
| frozen_market_structural | straddle | mid_net | 46 | 46 | 10.12 | -4.49 | 24.84 |
| historical_final_anchored | single | bidask_net | 346 | 77 | -9.72 | -28.32 | 6.69 |
| historical_final_anchored | single | mid_net | 346 | 77 | -6.27 | -24.27 | 10.29 |
| historical_final_anchored | straddle | bidask_net | 63 | 63 | -5.90 | -18.32 | 6.12 |
| historical_final_anchored | straddle | mid_net | 63 | 63 | -2.82 | -15.21 | 8.93 |
| historical_reference_anchored | single | bidask_net | 337 | 76 | -10.39 | -29.46 | 6.48 |
| historical_reference_anchored | single | mid_net | 337 | 76 | -7.00 | -25.71 | 9.75 |
| historical_reference_anchored | straddle | bidask_net | 63 | 63 | -5.90 | -18.95 | 6.34 |
| historical_reference_anchored | straddle | mid_net | 63 | 63 | -2.82 | -14.89 | 9.14 |
| historical_structural | single | bidask_net | 439 | 85 | -5.35 | -28.10 | 11.71 |
| historical_structural | single | mid_net | 439 | 85 | -2.07 | -24.33 | 15.08 |
| historical_structural | straddle | bidask_net | 77 | 77 | 1.54 | -9.95 | 12.30 |
| historical_structural | straddle | mid_net | 77 | 77 | 4.47 | -6.59 | 15.21 |

Intervals above resample company-earnings events and are descriptive, not multiple-testing-adjusted. A separate paired calendar-week resampling against always-short appears below. Sparse subgroups do not support precise inference.

## Long versus short, 10%, crossed quotes, stock hedge

| model | kind | side | closed | events | equal_event_pct |
|---|---|---|---|---|---|
| frozen_market_structural | single | all | 264 | 59 | 6.61 |
| frozen_market_structural | single | long | 92 | 19 | 2.56 |
| frozen_market_structural | single | short | 172 | 40 | 8.53 |
| frozen_market_structural | straddle | all | 46 | 46 | 7.77 |
| frozen_market_structural | straddle | long | 16 | 16 | -3.80 |
| frozen_market_structural | straddle | short | 30 | 30 | 13.94 |
| historical_final_anchored | single | all | 346 | 77 | -9.72 |
| historical_final_anchored | single | long | 75 | 14 | -10.99 |
| historical_final_anchored | single | short | 271 | 63 | -9.43 |
| historical_final_anchored | straddle | all | 63 | 63 | -5.90 |
| historical_final_anchored | straddle | long | 14 | 14 | -9.38 |
| historical_final_anchored | straddle | short | 49 | 49 | -4.91 |
| historical_reference_anchored | single | all | 337 | 76 | -10.39 |
| historical_reference_anchored | single | long | 75 | 14 | -10.99 |
| historical_reference_anchored | single | short | 262 | 62 | -10.25 |
| historical_reference_anchored | straddle | all | 63 | 63 | -5.90 |
| historical_reference_anchored | straddle | long | 14 | 14 | -9.38 |
| historical_reference_anchored | straddle | short | 49 | 49 | -4.91 |
| historical_structural | single | all | 439 | 85 | -5.35 |
| historical_structural | single | long | 91 | 18 | 3.63 |
| historical_structural | single | short | 348 | 67 | -7.77 |
| historical_structural | straddle | all | 77 | 77 | 1.54 |
| historical_structural | straddle | long | 15 | 15 | 1.25 |
| historical_structural | straddle | short | 62 | 62 | 1.60 |

## Threshold sensitivity, stock hedge, crossed quotes

| model | threshold | kind | closed | events | equal_event_pct |
|---|---|---|---|---|---|
| always_long | 0.00 | single | 668 | 112 | -1.60 |
| always_long | 0.00 | straddle | 112 | 112 | -4.87 |
| always_short | 0.00 | single | 668 | 112 | -6.06 |
| always_short | 0.00 | straddle | 112 | 112 | -1.03 |
| current_market_hybrid | 0.00 | single | 668 | 112 | -5.62 |
| current_market_hybrid | 0.00 | straddle | 112 | 112 | -4.60 |
| current_market_hybrid | 0.05 | single | 6 | 4 | -1.57 |
| current_market_only | 0.00 | single | 668 | 112 | -3.08 |
| current_market_only | 0.00 | straddle | 112 | 112 | -2.59 |
| current_market_only | 0.05 | single | 6 | 4 | -1.57 |
| frozen_market_structural | 0.00 | single | 668 | 112 | 2.01 |
| frozen_market_structural | 0.00 | straddle | 112 | 112 | -1.02 |
| frozen_market_structural | 0.05 | single | 428 | 87 | 5.31 |
| frozen_market_structural | 0.05 | straddle | 72 | 72 | 2.43 |
| frozen_market_structural | 0.10 | single | 264 | 59 | 6.61 |
| frozen_market_structural | 0.10 | straddle | 46 | 46 | 7.77 |
| frozen_market_structural | 0.20 | single | 88 | 28 | -0.50 |
| frozen_market_structural | 0.20 | straddle | 11 | 11 | 4.70 |
| historical_final_anchored | 0.00 | single | 668 | 112 | 0.93 |
| historical_final_anchored | 0.00 | straddle | 112 | 112 | 3.53 |
| historical_final_anchored | 0.05 | single | 486 | 89 | -5.04 |
| historical_final_anchored | 0.05 | straddle | 84 | 84 | -0.85 |
| historical_final_anchored | 0.10 | single | 346 | 77 | -9.72 |
| historical_final_anchored | 0.10 | straddle | 63 | 63 | -5.90 |
| historical_final_anchored | 0.20 | single | 158 | 41 | -15.28 |
| historical_final_anchored | 0.20 | straddle | 23 | 23 | -12.87 |
| historical_reference_anchored | 0.00 | single | 668 | 112 | 0.42 |
| historical_reference_anchored | 0.00 | straddle | 112 | 112 | 2.31 |
| historical_reference_anchored | 0.05 | single | 485 | 89 | -3.18 |
| historical_reference_anchored | 0.05 | straddle | 82 | 82 | -1.43 |
| historical_reference_anchored | 0.10 | single | 337 | 76 | -10.39 |
| historical_reference_anchored | 0.10 | straddle | 63 | 63 | -5.90 |
| historical_reference_anchored | 0.20 | single | 156 | 41 | -16.94 |
| historical_reference_anchored | 0.20 | straddle | 21 | 21 | -12.23 |
| historical_structural | 0.00 | single | 668 | 112 | -2.27 |
| historical_structural | 0.00 | straddle | 112 | 112 | -0.15 |
| historical_structural | 0.05 | single | 565 | 102 | 2.08 |
| historical_structural | 0.05 | straddle | 95 | 95 | 3.12 |
| historical_structural | 0.10 | single | 439 | 85 | -5.35 |
| historical_structural | 0.10 | straddle | 77 | 77 | 1.54 |
| historical_structural | 0.20 | single | 251 | 60 | 10.22 |
| historical_structural | 0.20 | straddle | 42 | 42 | -0.20 |
| reference_only | 0.00 | single | 668 | 112 | 0.53 |
| reference_only | 0.00 | straddle | 112 | 112 | 6.62 |
| reference_only | 0.05 | single | 5 | 4 | -5.23 |

## Without the stock hedge, 10%

| model | kind | fill | closed | events | equal_event_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|---|---|---|---|
| frozen_market_structural | single | bidask_net | 264 | 59 | -7.95 | -28.85 | 11.06 |
| frozen_market_structural | single | mid_net | 264 | 59 | -5.11 | -25.26 | 13.90 |
| frozen_market_structural | straddle | bidask_net | 46 | 46 | 9.22 | -5.21 | 24.46 |
| frozen_market_structural | straddle | mid_net | 46 | 46 | 11.57 | -3.22 | 25.80 |
| historical_final_anchored | single | bidask_net | 346 | 77 | 2.92 | -13.14 | 17.75 |
| historical_final_anchored | single | mid_net | 346 | 77 | 6.36 | -8.97 | 21.47 |
| historical_final_anchored | straddle | bidask_net | 63 | 63 | -3.36 | -15.57 | 8.16 |
| historical_final_anchored | straddle | mid_net | 63 | 63 | -0.27 | -12.00 | 11.28 |
| historical_reference_anchored | single | bidask_net | 337 | 76 | 3.56 | -13.79 | 18.75 |
| historical_reference_anchored | single | mid_net | 337 | 76 | 6.95 | -9.45 | 21.37 |
| historical_reference_anchored | straddle | bidask_net | 63 | 63 | -3.36 | -15.09 | 8.40 |
| historical_reference_anchored | straddle | mid_net | 63 | 63 | -0.27 | -12.41 | 10.98 |
| historical_structural | single | bidask_net | 439 | 85 | 8.50 | -4.92 | 21.57 |
| historical_structural | single | mid_net | 439 | 85 | 11.78 | -1.54 | 24.58 |
| historical_structural | straddle | bidask_net | 77 | 77 | 3.15 | -8.21 | 13.87 |
| historical_structural | straddle | mid_net | 77 | 77 | 6.09 | -5.11 | 16.57 |

## Per-year 10% results, stock hedge, crossed quotes

| year | model | kind | closed | events | equal_event_pct |
|---|---|---|---|---|---|
| 2020 | frozen_market_structural | single | 59 | 11 | -9.21 |
| 2020 | frozen_market_structural | straddle | 10 | 10 | -10.78 |
| 2020 | historical_final_anchored | single | 64 | 14 | 28.61 |
| 2020 | historical_final_anchored | straddle | 12 | 12 | 28.98 |
| 2020 | historical_reference_anchored | single | 63 | 13 | 28.14 |
| 2020 | historical_reference_anchored | straddle | 12 | 12 | 28.98 |
| 2020 | historical_structural | single | 64 | 12 | 26.40 |
| 2020 | historical_structural | straddle | 11 | 11 | 23.12 |
| 2021 | frozen_market_structural | single | 41 | 9 | 19.40 |
| 2021 | frozen_market_structural | straddle | 7 | 7 | 7.62 |
| 2021 | historical_final_anchored | single | 77 | 16 | -6.77 |
| 2021 | historical_final_anchored | straddle | 13 | 13 | -14.97 |
| 2021 | historical_reference_anchored | single | 76 | 16 | -6.28 |
| 2021 | historical_reference_anchored | straddle | 13 | 13 | -14.97 |
| 2021 | historical_structural | single | 87 | 15 | -15.08 |
| 2021 | historical_structural | straddle | 15 | 15 | -10.34 |
| 2022 | frozen_market_structural | single | 50 | 12 | 11.87 |
| 2022 | frozen_market_structural | straddle | 10 | 10 | 13.00 |
| 2022 | historical_final_anchored | single | 45 | 11 | -61.50 |
| 2022 | historical_final_anchored | straddle | 9 | 9 | -40.15 |
| 2022 | historical_reference_anchored | single | 41 | 11 | -62.23 |
| 2022 | historical_reference_anchored | straddle | 9 | 9 | -40.15 |
| 2022 | historical_structural | single | 70 | 16 | -62.47 |
| 2022 | historical_structural | straddle | 13 | 13 | -20.18 |
| 2023 | frozen_market_structural | single | 43 | 11 | -5.94 |
| 2023 | frozen_market_structural | straddle | 7 | 7 | 5.46 |
| 2023 | historical_final_anchored | single | 77 | 18 | -21.73 |
| 2023 | historical_final_anchored | straddle | 14 | 14 | -15.45 |
| 2023 | historical_reference_anchored | single | 76 | 18 | -23.11 |
| 2023 | historical_reference_anchored | straddle | 14 | 14 | -15.45 |
| 2023 | historical_structural | single | 81 | 16 | 7.77 |
| 2023 | historical_structural | straddle | 15 | 15 | 1.13 |
| 2024 | frozen_market_structural | single | 48 | 10 | 17.24 |
| 2024 | frozen_market_structural | straddle | 7 | 7 | 34.02 |
| 2024 | historical_final_anchored | single | 52 | 10 | -1.31 |
| 2024 | historical_final_anchored | straddle | 9 | 9 | 8.55 |
| 2024 | historical_reference_anchored | single | 51 | 10 | -0.01 |
| 2024 | historical_reference_anchored | straddle | 9 | 9 | 8.55 |
| 2024 | historical_structural | single | 85 | 16 | 22.92 |
| 2024 | historical_structural | straddle | 14 | 14 | 20.31 |
| 2025 | frozen_market_structural | single | 23 | 6 | 11.17 |
| 2025 | frozen_market_structural | straddle | 5 | 5 | 1.09 |
| 2025 | historical_final_anchored | single | 31 | 8 | 5.05 |
| 2025 | historical_final_anchored | straddle | 6 | 6 | -4.05 |
| 2025 | historical_reference_anchored | single | 30 | 8 | 5.74 |
| 2025 | historical_reference_anchored | straddle | 6 | 6 | -4.05 |
| 2025 | historical_structural | single | 52 | 10 | -3.71 |
| 2025 | historical_structural | straddle | 9 | 9 | -2.21 |

## Comparison with unconditional short exposure

Each candidate receives equal option-premium allocation within an event; unselected allocations remain idle. This makes participation comparable on all eligible events. The paired intervals resample calendar weeks, keeping names with announcements in the same week together. These allocations remain research normalization, not a funded margin portfolio.

| kind | model | opportunities | trading_events | allocated_premium_pct | always_short_pct | difference_pct | weekly_ci_low_pct | weekly_ci_high_pct |
|---|---|---|---|---|---|---|---|---|
| single | frozen_market_structural | 112 | 59 | 2.45 | -6.06 | 8.51 | -6.07 | 26.86 |
| single | historical_structural | 112 | 85 | -2.08 | -6.06 | 3.98 | -6.19 | 15.57 |
| single | historical_final_anchored | 112 | 77 | -6.02 | -6.06 | 0.04 | -9.63 | 11.34 |
| single | current_market_hybrid | 112 | 0 | 0.00 | -6.06 | 6.06 | -6.92 | 21.23 |
| straddle | frozen_market_structural | 112 | 46 | 3.19 | -1.03 | 4.22 | -7.86 | 17.35 |
| straddle | historical_structural | 112 | 77 | 1.06 | -1.03 | 2.08 | -6.90 | 12.33 |
| straddle | historical_final_anchored | 112 | 63 | -3.32 | -1.03 | -2.29 | -11.57 | 7.88 |
| straddle | current_market_hybrid | 112 | 0 | 0.00 | -1.03 | 1.03 | -9.61 | 12.02 |

## Earnings data and limitations

Historical earnings dates are queried and cached from I/B/E/S via the existing WRDS connection; stock returns and option quotes use OptionMetrics. No manual parsing of release dates is required. Actual historical announcement dates do not establish when the schedule became known to a trader. A live implementation requires an as-of scheduled calendar, revisions, and release timestamps. The 2025 quote sample ends in August, so later 2025 dates are unavailable.

Midpoints and crossed daily quotes are fill scenarios, not evidence of attainable fills or sufficient size. Borrow, financing, margin, assignment, American early exercise, and intraday execution are not modeled. Multiple strikes per event are not independent observations. Historical earnings variance includes estimation error, changing company risk, and incomplete separation from ordinary variance. Inserting it into a risk-neutral model does not remove risk premia or prove market mispricing. The historical-adjustment variance floor was recorded rather than silently dropping those positions.

## Files

Source: research2/historical_jump.py. Fixed rules: research2/historical_jump_plan.json. Local licensed-data outputs: wrds_studies/historical_jump_combined/{candidates.pkl,trades.pkl,summary.csv,year_summary.csv,benchmark_comparison.csv,coverage.csv,validation.json}. The candidate/trade ledger preserves dates, contract IDs, history cutoff, fitted anchor, implied/historical variance, signal discrepancies, quoted spreads, stock hedge, costs, and both execution scenarios.
