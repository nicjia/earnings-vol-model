# Pre-earnings convergence test

This experiment avoids holding through the announcement. Signal ten sessions before earnings, enter at the next close, exit six sessions before earnings. Options still expire after the announcement, so earnings remains priced throughout the holding period. The 5% liquidity/cost rule was frozen before pulling additional-company results for ADSK, BIIB, VRTX, NOW and ISRG in 2022–2025. These companies did not supply the rule-development trades. Other thresholds remain sensitivity checks, not candidates to select using this panel. Historical dates are retrospective, and closing quotes do not establish actual fills.

The same current hybrid prices held-out strikes. Thresholds are 5%, 10%, 20%. The fixed adjustment requires signal midpoint >= $1, full signal spread <=10%, model-only and hybrid directional agreement, and the gap to cover the signal-estimated full round-trip spread plus fees. A separate entry-limit variant requires the actual entry ask/bid to preserve the signal-price threshold under the frozen dollar valuation; it uses entry quotes, never exit outcomes. Agreement between two interpolators is not independent information.

Three hedge choices are reported: none, fixed signal-date reference delta, and vendor entry-date delta. Missing vendor deltas are counted as unavailable; no P&L is inferred for them. Entry/exit fractions of 0, .25, .5, 1 span midpoint to fully adverse quoted fills. Reported all_event_bp averages P&L/stock-notional across all eligible events, with unselected allocations idle. Premium-normalized returns are supplementary, not account returns. This is a separate-company historical check of a fixed rule, not a prospective live test. No retuning on these companies is included in this run.

Candidates: 3780 individual contracts across 62 company-earnings events.

| threshold | version | fraction | period | closed | unresolved | events | all_event_bp | ci_low_bp | ci_high_bp | premium_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | baseline | 0.00 | later | 517 | 71 | 54 | 1.11 | -3.31 | 4.85 | -1.54 |
| 0.05 | baseline | 0.00 | all | 517 | 71 | 54 | 1.11 | -3.31 | 4.85 | -1.54 |
| 0.05 | baseline | 1.00 | later | 517 | 71 | 54 | -53.82 | -65.12 | -42.99 | -70.93 |
| 0.05 | baseline | 1.00 | all | 517 | 71 | 54 | -53.82 | -65.12 | -42.99 | -70.93 |
| 0.05 | liquid_cost | 0.00 | later | 4 | 0 | 3 | -1.26 | -3.10 | 0.00 | -18.72 |
| 0.05 | liquid_cost | 0.00 | all | 4 | 0 | 3 | -1.26 | -3.10 | 0.00 | -18.72 |
| 0.05 | liquid_cost | 1.00 | later | 4 | 0 | 3 | -4.03 | -10.81 | 0.00 | -26.96 |
| 0.05 | liquid_cost | 1.00 | all | 4 | 0 | 3 | -4.03 | -10.81 | 0.00 | -26.96 |
| 0.05 | entry_limit | 0.00 | later | 100 | 3 | 34 | 1.85 | -2.33 | 5.88 | -1.46 |
| 0.05 | entry_limit | 0.00 | all | 100 | 3 | 34 | 1.85 | -2.33 | 5.88 | -1.46 |
| 0.05 | entry_limit | 1.00 | later | 100 | 3 | 34 | -29.03 | -40.93 | -18.39 | -48.82 |
| 0.05 | entry_limit | 1.00 | all | 100 | 3 | 34 | -29.03 | -40.93 | -18.39 | -48.82 |
| 0.10 | baseline | 0.00 | later | 330 | 63 | 48 | 1.36 | -3.16 | 5.68 | -7.43 |
| 0.10 | baseline | 0.00 | all | 330 | 63 | 48 | 1.36 | -3.16 | 5.68 | -7.43 |
| 0.10 | baseline | 1.00 | later | 330 | 63 | 48 | -46.84 | -57.42 | -36.93 | -94.29 |
| 0.10 | baseline | 1.00 | all | 330 | 63 | 48 | -46.84 | -57.42 | -36.93 | -94.29 |
| 0.10 | liquid_cost | 0.00 | later | 1 | 0 | 1 | -0.70 | -2.26 | 0.00 | -35.14 |
| 0.10 | liquid_cost | 0.00 | all | 1 | 0 | 1 | -0.70 | -2.26 | 0.00 | -35.14 |
| 0.10 | liquid_cost | 1.00 | later | 1 | 0 | 1 | -0.87 | -2.81 | 0.00 | -43.68 |
| 0.10 | liquid_cost | 1.00 | all | 1 | 0 | 1 | -0.87 | -2.81 | 0.00 | -43.68 |
| 0.10 | entry_limit | 0.00 | later | 50 | 3 | 24 | 3.38 | -1.07 | 7.56 | 0.79 |
| 0.10 | entry_limit | 0.00 | all | 50 | 3 | 24 | 3.38 | -1.07 | 7.56 | 0.79 |
| 0.10 | entry_limit | 1.00 | later | 50 | 3 | 24 | -16.11 | -24.77 | -8.11 | -61.37 |
| 0.10 | entry_limit | 1.00 | all | 50 | 3 | 24 | -16.11 | -24.77 | -8.11 | -61.37 |
| 0.20 | baseline | 0.00 | later | 201 | 60 | 36 | 3.28 | -1.01 | 7.71 | -3.25 |
| 0.20 | baseline | 0.00 | all | 201 | 60 | 36 | 3.28 | -1.01 | 7.71 | -3.25 |
| 0.20 | baseline | 1.00 | later | 201 | 60 | 36 | -34.02 | -44.03 | -23.89 | -113.24 |
| 0.20 | baseline | 1.00 | all | 201 | 60 | 36 | -34.02 | -44.03 | -23.89 | -113.24 |
| 0.20 | entry_limit | 0.00 | later | 22 | 3 | 15 | 1.27 | -1.37 | 4.05 | 4.89 |
| 0.20 | entry_limit | 0.00 | all | 22 | 3 | 15 | 1.27 | -1.37 | 4.05 | 4.89 |
| 0.20 | entry_limit | 1.00 | later | 22 | 3 | 15 | -9.72 | -17.19 | -3.62 | -81.39 |
| 0.20 | entry_limit | 1.00 | all | 22 | 3 | 15 | -9.72 | -17.19 | -3.62 | -81.39 |

## Side and cost diagnosis

| threshold | version | period | side | trades | option_bp | stock_bp | cost_bp | net_bp |
|---|---|---|---|---|---|---|---|---|
| 0.05 | baseline | later | short | 329 | -0.84 | -0.04 | 68.18 | -69.06 |
| 0.05 | baseline | later | long | 188 | 6.79 | -0.40 | 74.39 | -68.00 |
| 0.05 | baseline | all | short | 329 | -0.84 | -0.04 | 68.18 | -69.06 |
| 0.05 | baseline | all | long | 188 | 6.79 | -0.40 | 74.39 | -68.00 |
| 0.05 | liquid_cost | later | short | 1 | -174.17 | 132.02 | 12.10 | -54.24 |
| 0.05 | liquid_cost | later | long | 3 | 31.61 | -46.09 | 108.36 | -122.84 |
| 0.05 | liquid_cost | all | short | 1 | -174.17 | 132.02 | 12.10 | -54.24 |
| 0.05 | liquid_cost | all | long | 3 | 31.61 | -46.09 | 108.36 | -122.84 |
| 0.05 | entry_limit | later | short | 58 | 17.22 | -17.88 | 58.92 | -59.58 |
| 0.05 | entry_limit | later | long | 42 | 35.71 | -30.38 | 54.81 | -49.49 |
| 0.05 | entry_limit | all | short | 58 | 17.22 | -17.88 | 58.92 | -59.58 |
| 0.05 | entry_limit | all | long | 42 | 35.71 | -30.38 | 54.81 | -49.49 |
| 0.10 | baseline | later | short | 234 | 2.14 | -2.01 | 67.92 | -67.79 |
| 0.10 | baseline | later | long | 96 | 6.09 | 0.91 | 72.99 | -65.99 |
| 0.10 | baseline | all | short | 234 | 2.14 | -2.01 | 67.92 | -67.79 |
| 0.10 | baseline | all | long | 96 | 6.09 | 0.91 | 72.99 | -65.99 |
| 0.10 | liquid_cost | later | short | 1 | -174.17 | 132.02 | 12.10 | -54.24 |
| 0.10 | liquid_cost | all | short | 1 | -174.17 | 132.02 | 12.10 | -54.24 |
| 0.10 | entry_limit | later | short | 35 | 3.91 | -4.42 | 51.78 | -52.29 |
| 0.10 | entry_limit | later | long | 15 | 45.92 | -35.44 | 44.69 | -34.21 |
| 0.10 | entry_limit | all | short | 35 | 3.91 | -4.42 | 51.78 | -52.29 |
| 0.10 | entry_limit | all | long | 15 | 45.92 | -35.44 | 44.69 | -34.21 |
| 0.20 | baseline | later | short | 156 | 3.24 | -3.23 | 67.44 | -67.43 |
| 0.20 | baseline | later | long | 45 | -3.90 | 13.46 | 72.82 | -63.25 |
| 0.20 | baseline | all | short | 156 | 3.24 | -3.23 | 67.44 | -67.43 |
| 0.20 | baseline | all | long | 45 | -3.90 | 13.46 | 72.82 | -63.25 |
| 0.20 | entry_limit | later | short | 15 | 7.81 | -6.60 | 49.14 | -47.92 |
| 0.20 | entry_limit | later | long | 7 | 28.04 | -16.11 | 51.87 | -39.94 |
| 0.20 | entry_limit | all | short | 15 | 7.81 | -6.60 | 49.14 | -47.92 |
| 0.20 | entry_limit | all | long | 7 | 28.04 | -16.11 | 51.87 | -39.94 |

All hedge/fill comparisons are retained in wrds_studies/pre_event_new_names_combined/summary.csv; candidate and trade ledgers are saved alongside it. The original holding-through-earnings experiments are unchanged.
