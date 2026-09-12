# Pre-earnings convergence test

This experiment avoids holding through the announcement. Signal ten sessions before earnings, enter at the next close, exit six sessions before earnings. Options still expire after the announcement, so earnings remains priced throughout the holding period. Additional 2021–2024 entry/exit quotes were downloaded automatically for the five recurring names. Historical dates are retrospective, and closing quotes do not establish actual fills.

The same current hybrid prices held-out strikes. Thresholds are 5%, 10%, 20%. The fixed adjustment requires signal midpoint >= $1, full signal spread <=10%, model-only and hybrid directional agreement, and the gap to cover the signal-estimated full round-trip spread plus fees. A separate entry-limit variant requires the actual entry ask/bid to preserve the signal-price threshold under the frozen dollar valuation; it uses entry quotes, never exit outcomes. Agreement between two interpolators is not independent information.

Three hedge choices are reported: none, fixed signal-date reference delta, and vendor entry-date delta. Missing vendor deltas are counted as unavailable; no P&L is inferred for them. Entry/exit fractions of 0, .25, .5, 1 span midpoint to fully adverse quoted fills. Reported all_event_bp averages P&L/stock-notional across all eligible events, with unselected allocations idle. Premium-normalized returns are supplementary, not account returns. 2021 is the development partition; 2022–2024 is a later historical comparison, not an untouched prospective test.

Candidates: 9187 individual contracts across 80 company-earnings events.

| threshold | version | fraction | period | closed | unresolved | events | all_event_bp | ci_low_bp | ci_high_bp | premium_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | baseline | 0.00 | development | 168 | 8 | 13 | -3.24 | -6.49 | 0.24 | -12.74 |
| 0.05 | baseline | 0.00 | later | 70 | 0 | 21 | 3.22 | -0.09 | 7.84 | 3.47 |
| 0.05 | baseline | 0.00 | all | 238 | 8 | 34 | 1.61 | -1.12 | 5.07 | -2.73 |
| 0.05 | baseline | 1.00 | development | 168 | 8 | 13 | -20.11 | -34.86 | -8.75 | -41.16 |
| 0.05 | baseline | 1.00 | later | 70 | 0 | 21 | -1.06 | -4.52 | 2.73 | -19.38 |
| 0.05 | baseline | 1.00 | all | 238 | 8 | 34 | -5.82 | -10.66 | -1.48 | -27.71 |
| 0.05 | liquid_cost | 0.00 | development | 12 | 0 | 4 | -1.35 | -3.47 | 0.21 | -6.95 |
| 0.05 | liquid_cost | 0.00 | later | 7 | 0 | 5 | 1.15 | -0.01 | 3.14 | 11.13 |
| 0.05 | liquid_cost | 0.00 | all | 19 | 0 | 9 | 0.52 | -0.63 | 2.19 | 3.09 |
| 0.05 | liquid_cost | 1.00 | development | 12 | 0 | 4 | -7.78 | -25.24 | 0.00 | -17.24 |
| 0.05 | liquid_cost | 1.00 | later | 7 | 0 | 5 | 0.93 | -0.18 | 2.79 | 7.44 |
| 0.05 | liquid_cost | 1.00 | all | 19 | 0 | 9 | -1.25 | -5.42 | 1.52 | -3.53 |
| 0.05 | entry_limit | 0.00 | development | 69 | 0 | 8 | -2.40 | -4.02 | -0.84 | -14.03 |
| 0.05 | entry_limit | 0.00 | later | 38 | 0 | 13 | 1.35 | -0.25 | 3.43 | 5.17 |
| 0.05 | entry_limit | 0.00 | all | 107 | 0 | 21 | 0.41 | -0.92 | 2.17 | -2.14 |
| 0.05 | entry_limit | 1.00 | development | 69 | 0 | 8 | -14.38 | -28.23 | -4.46 | -47.85 |
| 0.05 | entry_limit | 1.00 | later | 38 | 0 | 13 | -0.55 | -2.47 | 1.62 | -13.63 |
| 0.05 | entry_limit | 1.00 | all | 107 | 0 | 21 | -4.01 | -7.92 | -0.72 | -26.67 |
| 0.10 | baseline | 0.00 | development | 77 | 7 | 9 | -0.51 | -3.48 | 1.81 | -13.72 |
| 0.10 | baseline | 0.00 | later | 21 | 0 | 9 | 1.18 | -0.09 | 2.83 | 10.70 |
| 0.10 | baseline | 0.00 | all | 98 | 7 | 18 | 0.76 | -0.51 | 2.19 | -1.51 |
| 0.10 | baseline | 1.00 | development | 77 | 7 | 9 | -11.01 | -24.27 | -2.45 | -60.44 |
| 0.10 | baseline | 1.00 | later | 21 | 0 | 9 | -1.38 | -3.46 | 0.62 | -25.94 |
| 0.10 | baseline | 1.00 | all | 98 | 7 | 18 | -3.79 | -7.09 | -1.08 | -43.19 |
| 0.10 | liquid_cost | 0.00 | development | 6 | 0 | 2 | -0.70 | -1.52 | 0.00 | -15.12 |
| 0.10 | liquid_cost | 0.00 | all | 6 | 0 | 2 | -0.18 | -0.45 | 0.00 | -15.12 |
| 0.10 | liquid_cost | 1.00 | development | 6 | 0 | 2 | -1.01 | -2.12 | 0.00 | -21.47 |
| 0.10 | liquid_cost | 1.00 | all | 6 | 0 | 2 | -0.25 | -0.61 | 0.00 | -21.47 |
| 0.10 | entry_limit | 0.00 | development | 31 | 0 | 4 | -0.03 | -0.81 | 0.86 | -5.94 |
| 0.10 | entry_limit | 0.00 | later | 11 | 0 | 7 | 1.12 | -0.03 | 2.78 | 13.85 |
| 0.10 | entry_limit | 0.00 | all | 42 | 0 | 11 | 0.83 | -0.10 | 2.13 | 6.65 |
| 0.10 | entry_limit | 1.00 | development | 31 | 0 | 4 | -6.31 | -15.11 | -0.74 | -59.65 |
| 0.10 | entry_limit | 1.00 | later | 11 | 0 | 7 | -0.41 | -1.84 | 1.20 | -19.18 |
| 0.10 | entry_limit | 1.00 | all | 42 | 0 | 11 | -1.89 | -4.22 | 0.02 | -33.90 |
| 0.20 | baseline | 0.00 | development | 41 | 5 | 5 | -0.88 | -2.11 | 0.04 | -17.82 |
| 0.20 | baseline | 0.00 | later | 8 | 0 | 4 | 1.01 | -0.01 | 2.55 | 24.53 |
| 0.20 | baseline | 0.00 | all | 49 | 5 | 9 | 0.53 | -0.33 | 1.78 | 1.00 |
| 0.20 | baseline | 1.00 | development | 41 | 5 | 5 | -9.88 | -23.18 | -0.71 | -107.62 |
| 0.20 | baseline | 1.00 | later | 8 | 0 | 4 | -0.32 | -1.82 | 1.26 | -15.42 |
| 0.20 | baseline | 1.00 | all | 49 | 5 | 9 | -2.71 | -5.96 | -0.25 | -66.64 |
| 0.20 | entry_limit | 0.00 | development | 15 | 0 | 2 | -0.39 | -0.94 | 0.00 | -22.42 |
| 0.20 | entry_limit | 0.00 | later | 3 | 0 | 2 | 0.61 | -0.04 | 1.94 | 31.11 |
| 0.20 | entry_limit | 0.00 | all | 18 | 0 | 4 | 0.36 | -0.22 | 1.43 | 4.34 |
| 0.20 | entry_limit | 1.00 | development | 15 | 0 | 2 | -1.88 | -5.99 | 0.00 | -116.11 |
| 0.20 | entry_limit | 1.00 | later | 3 | 0 | 2 | 0.13 | -1.29 | 1.65 | -4.74 |
| 0.20 | entry_limit | 1.00 | all | 18 | 0 | 4 | -0.37 | -1.73 | 0.91 | -60.43 |

## Side and cost diagnosis

| threshold | version | period | side | trades | option_bp | stock_bp | cost_bp | net_bp |
|---|---|---|---|---|---|---|---|---|
| 0.05 | baseline | development | short | 64 | -32.49 | 27.17 | 67.83 | -73.15 |
| 0.05 | baseline | development | long | 104 | 6.26 | -9.73 | 30.68 | -34.15 |
| 0.05 | baseline | later | short | 18 | 4.73 | 2.72 | 14.70 | -7.25 |
| 0.05 | baseline | later | long | 52 | 18.40 | -10.50 | 16.57 | -8.67 |
| 0.05 | baseline | all | short | 82 | -24.32 | 21.80 | 56.16 | -58.68 |
| 0.05 | baseline | all | long | 156 | 10.31 | -9.99 | 25.98 | -25.66 |
| 0.05 | liquid_cost | development | short | 1 | -137.38 | 124.44 | 122.90 | -135.84 |
| 0.05 | liquid_cost | development | long | 11 | -7.76 | 1.66 | 2.96 | -9.06 |
| 0.05 | liquid_cost | later | short | 1 | 15.56 | -14.61 | 4.27 | -3.31 |
| 0.05 | liquid_cost | later | long | 6 | 114.03 | -82.68 | 4.59 | 26.76 |
| 0.05 | liquid_cost | all | short | 2 | -60.91 | 54.92 | 63.59 | -69.58 |
| 0.05 | liquid_cost | all | long | 17 | 35.22 | -28.11 | 3.53 | 3.58 |
| 0.05 | entry_limit | development | short | 20 | -63.79 | 55.26 | 64.43 | -72.95 |
| 0.05 | entry_limit | development | long | 49 | 12.57 | -15.24 | 19.88 | -22.56 |
| 0.05 | entry_limit | later | short | 6 | 14.04 | 4.35 | 17.54 | 0.86 |
| 0.05 | entry_limit | later | long | 32 | 34.61 | -24.61 | 9.69 | 0.30 |
| 0.05 | entry_limit | all | short | 26 | -45.83 | 43.52 | 53.61 | -55.92 |
| 0.05 | entry_limit | all | long | 81 | 21.28 | -18.95 | 15.86 | -13.53 |
| 0.10 | baseline | development | short | 33 | -17.07 | 7.94 | 54.45 | -63.58 |
| 0.10 | baseline | development | long | 44 | 3.74 | -1.17 | 26.34 | -23.77 |
| 0.10 | baseline | later | short | 5 | 1.22 | 12.05 | 23.73 | -10.46 |
| 0.10 | baseline | later | long | 16 | 30.03 | -22.28 | 20.63 | -12.89 |
| 0.10 | baseline | all | short | 38 | -14.67 | 8.48 | 50.41 | -56.59 |
| 0.10 | baseline | all | long | 60 | 10.75 | -6.80 | 24.82 | -20.87 |
| 0.10 | liquid_cost | development | long | 6 | -4.69 | -2.41 | 3.15 | -10.26 |
| 0.10 | liquid_cost | all | long | 6 | -4.69 | -2.41 | 3.15 | -10.26 |
| 0.10 | entry_limit | development | short | 10 | -38.23 | 25.90 | 43.38 | -55.70 |
| 0.10 | entry_limit | development | long | 21 | -1.14 | 3.03 | 16.84 | -14.95 |
| 0.10 | entry_limit | later | short | 2 | 15.03 | 12.38 | 20.93 | 6.48 |
| 0.10 | entry_limit | later | long | 9 | 42.77 | -28.94 | 12.11 | 1.72 |
| 0.10 | entry_limit | all | short | 12 | -29.35 | 23.65 | 39.64 | -45.34 |
| 0.10 | entry_limit | all | long | 30 | 12.03 | -6.56 | 15.42 | -9.95 |
| 0.20 | baseline | development | short | 21 | -24.84 | 13.74 | 56.70 | -67.80 |
| 0.20 | baseline | development | long | 20 | -0.12 | 4.54 | 32.22 | -27.79 |
| 0.20 | baseline | later | short | 1 | 23.89 | -3.72 | 26.15 | -5.97 |
| 0.20 | baseline | later | long | 7 | 55.38 | -39.56 | 21.03 | -5.21 |
| 0.20 | baseline | all | short | 22 | -22.63 | 12.95 | 55.31 | -64.99 |
| 0.20 | baseline | all | long | 27 | 14.27 | -6.89 | 29.32 | -21.93 |
| 0.20 | entry_limit | development | short | 5 | -41.12 | 28.15 | 26.62 | -39.59 |
| 0.20 | entry_limit | development | long | 10 | -3.60 | 4.93 | 13.71 | -12.38 |
| 0.20 | entry_limit | later | long | 3 | 85.39 | -58.94 | 12.47 | 13.98 |
| 0.20 | entry_limit | all | short | 5 | -41.12 | 28.15 | 26.62 | -39.59 |
| 0.20 | entry_limit | all | long | 13 | 16.94 | -9.81 | 13.43 | -6.29 |

All hedge/fill comparisons are retained in wrds_studies/pre_event_combined/summary.csv; candidate and trade ledgers are saved alongside it. The original holding-through-earnings experiments are unchanged.
