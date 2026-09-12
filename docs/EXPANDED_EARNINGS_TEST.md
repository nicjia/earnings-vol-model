# Expanded earnings testing and option-surface coverage

Added automated I/B/E/S earnings windows for 2016–2019, retaining the original five names and historical forecast/threshold rules. Earlier years have warmup and reference-expiry exclusions; the added usable events are not every reported event. Older and newer panels remain retrospective historical research, with actual announcement dates rather than a verified as-of schedule. 2025 quote coverage ends in August.

The prior six-trade result came from nearest-three held-out strikes per option type at one expiry, one pre-earnings signal date, not the entire surface or every trading day. The separate broader screen now evaluates every held-out strike within 80–120% of spot, across all expiries selected by the existing reference pipeline (up to five) with 8–90 DTE. The same signal bid > 0 and midpoint >= $0.25 screen applies. Reference/calibration strikes remain excluded from targets. No additional relative-spread restriction is imposed on target contracts. It is still not the entire listed surface: far wings, other maturities, reference strikes, and other daily timestamps are outside this experiment.

Both runs keep signal three sessions before earnings, next-close entry, first close after earnings exit, exact option IDs and the same target trades for midpoint versus crossed fills. These are valuation-gap trades through earnings, not trades held to expiry or an automatically capital-constrained portfolio. Adding many contracts creates correlated exposures; contracts are averaged within company-earnings events for the reported mean.

**Returns below are relative to entry option midpoint premium, not account capital or short-option margin. Mid net includes $0.65/contract/side and 2 bp/side of stock costs. Bid–ask net additionally crosses the quoted option spread. Hedged results hold the initial stock delta fixed; unhedged results are also retained. No guaranteed fill, financing, borrow, assignment or margin model is implied.**

The expanded original screen has 168 usable earnings events (56 more than before). At the 10% threshold, direct historical-jump straddles average +2.05% of option premium after crossed quotes over 104 trades; the descriptive interval still includes losses. The broader current-market screen has 170 events and 25,420 single-option candidates. At 5%, 10%, and 20% thresholds it closes 853, 369, and 156 trades respectively. All three lose on average after crossed quotes, with or without the fixed stock hedge. Both long and short sides lose after crossing.

The large discrepancies concentrate in wide quoted markets. Mean full entry spread is 37.2%, 57.7%, and 81.2% of entry midpoint for those three selected groups. These are not representative liquid ATM spreads. At 20%, fixed-hedge midpoint net is +25.99%, but crossed net is -34.96%, and the midpoint interval spans losses. The one unresolved candidate never passes these trading thresholds; every selected trade has a scored outcome. Entry quotes can be cheaper than the $0.25 signal-date filter because execution is delayed one session.

## Coverage

| screen | events | single_candidates | straddle_candidates | unresolved |
|---|---|---|---|---|
| Original candidate rules, expanded years | 168 | 991 | 168 | 0 |
| Broader surface screen | 170 | 25420 | 168 | 1 |

## Original candidate rules, enlarged event sample: historical jump at 10%

| model | kind | fill | closed | events | equal_event_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|---|---|---|---|
| historical_final_anchored | single | bidask_net | 457 | 106 | -0.85 | -16.21 | 13.91 |
| historical_final_anchored | single | mid_net | 457 | 106 | 2.59 | -12.94 | 17.01 |
| historical_final_anchored | straddle | bidask_net | 79 | 79 | -4.88 | -17.25 | 6.74 |
| historical_final_anchored | straddle | mid_net | 79 | 79 | -1.83 | -14.01 | 9.38 |
| historical_structural | single | bidask_net | 594 | 123 | 0.25 | -15.84 | 14.67 |
| historical_structural | single | mid_net | 594 | 123 | 3.52 | -13.09 | 18.23 |
| historical_structural | straddle | bidask_net | 104 | 104 | 2.05 | -8.17 | 11.34 |
| historical_structural | straddle | mid_net | 104 | 104 | 5.04 | -5.09 | 14.89 |

## Current market hybrid under the original candidate rules

| threshold | kind | fill | closed | events | equal_event_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|---|---|---|---|
| 0.00 | single | bidask_net | 991 | 168 | 0.18 | -8.15 | 7.58 |
| 0.00 | single | mid_net | 991 | 168 | 3.28 | -4.95 | 10.97 |
| 0.00 | straddle | bidask_net | 168 | 168 | 2.52 | -6.15 | 10.50 |
| 0.00 | straddle | mid_net | 168 | 168 | 5.34 | -3.12 | 13.67 |
| 0.05 | single | bidask_net | 7 | 5 | -8.55 | -54.98 | 60.76 |
| 0.05 | single | mid_net | 7 | 5 | 3.23 | -38.71 | 66.93 |

## Broader screen: current market hybrid with fixed initial stock hedge

| threshold | kind | fill | selected | closed | unresolved | events | equal_event_pct | ci_low_pct | ci_high_pct | mean_entry_spread_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | single | bidask_net | 853 | 853 | 0 | 105 | -46.66 | -71.88 | -21.07 | 37.21 |
| 0.05 | single | mid_net | 853 | 853 | 0 | 105 | -22.65 | -46.25 | 0.98 | 37.21 |
| 0.10 | single | bidask_net | 369 | 369 | 0 | 67 | -39.81 | -85.61 | 19.25 | 57.73 |
| 0.10 | single | mid_net | 369 | 369 | 0 | 67 | -1.49 | -46.78 | 56.40 | 57.73 |
| 0.20 | single | bidask_net | 156 | 156 | 0 | 37 | -34.96 | -92.74 | 29.16 | 81.23 |
| 0.20 | single | mid_net | 156 | 156 | 0 | 37 | 25.99 | -31.28 | 95.63 | 81.23 |

## Broader screen: long versus short, crossed quotes, fixed stock hedge

| threshold | kind | side | closed | events | equal_event_pct |
|---|---|---|---|---|---|
| 0.05 | single | all | 853 | 105 | -46.66 |
| 0.05 | single | long | 517 | 91 | -46.48 |
| 0.05 | single | short | 336 | 66 | -43.59 |
| 0.10 | single | all | 369 | 67 | -39.81 |
| 0.10 | single | long | 193 | 56 | -40.91 |
| 0.10 | single | short | 176 | 38 | -31.27 |
| 0.20 | single | all | 156 | 37 | -34.96 |
| 0.20 | single | long | 57 | 22 | -33.21 |
| 0.20 | single | short | 99 | 24 | -57.42 |

## Broader screen without stock hedge

| threshold | kind | fill | closed | events | equal_event_pct | ci_low_pct | ci_high_pct |
|---|---|---|---|---|---|---|---|
| 0.05 | single | bidask_net | 853 | 105 | -55.44 | -79.25 | -35.71 |
| 0.05 | single | mid_net | 853 | 105 | -31.44 | -53.06 | -12.37 |
| 0.10 | single | bidask_net | 369 | 67 | -72.60 | -101.96 | -44.63 |
| 0.10 | single | mid_net | 369 | 67 | -34.28 | -65.52 | -6.41 |
| 0.20 | single | bidask_net | 156 | 37 | -82.14 | -115.19 | -52.50 |
| 0.20 | single | mid_net | 156 | 37 | -21.19 | -43.19 | 0.43 |

Intervals are descriptive company-event bootstrap intervals, not corrected for trying multiple specifications and thresholds. Sparse subgroups cannot support precise inference. Missing outcomes are counted and not converted to wins or zero P&L. Summary rows are absent when no trades qualify; absence is not a measured zero return. All candidate predictions and quotes are stored in the ledger, along with spread measures and unresolved status.

Pricing inputs, manual mixture controls, and the distinction between a variance clock and explicit overnight jumps are documented in [MODEL_INPUTS.md](MODEL_INPUTS.md). In particular, the latest trading experiments use calendar-time structural parameters with closure weights equal to one; no automatic nightly jump-mixture calibration is being tested.

Local result directories: wrds_studies/historical_jump_expanded and wrds_studies/historical_jump_wide_combined. Each has candidates.pkl, trades.pkl and summary.csv. Annual subdirectories preserve the original and broader runs separately. Source is research2/historical_jump.py; expansion rules are in research2/expanded_jump_plan.json. Original 112-event results remain in HISTORICAL_JUMP_TRADING.md.
