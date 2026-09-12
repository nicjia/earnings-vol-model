# Pre-earnings convergence test

This experiment avoids holding through the announcement. Signal ten sessions before earnings, enter at the next close, exit six sessions before earnings. Options still expire after the announcement, so earnings remains priced throughout the holding period. The initial 2021–2024 test was expanded with fixed rules to 2016–2020 and 2025, reusing cached quotes and automatically downloading missing dates for the recurring names. GOOGL appears only in 2020. The initial result is preserved in PRE_EARNINGS_INITIAL.md and the corresponding private initial-result directory. Historical dates are retrospective, and closing quotes do not establish actual fills.

The same current hybrid prices held-out strikes. Thresholds are 5%, 10%, 20%. The fixed adjustment requires signal midpoint >= $1, full signal spread <=10%, model-only and hybrid directional agreement, and the gap to cover the signal-estimated full round-trip spread plus fees. A separate entry-limit variant requires the actual entry ask/bid to preserve the signal-price threshold under the frozen dollar valuation; it uses entry quotes, never exit outcomes. Agreement between two interpolators is not independent information.

Three hedge choices are reported: none, fixed signal-date reference delta, and vendor entry-date delta. Missing vendor deltas are counted as unavailable; no P&L is inferred for them. Entry/exit fractions of 0, .25, .5, 1 span midpoint to fully adverse quoted fills. Reported all_event_bp averages P&L/stock-notional across all eligible events, with unselected allocations idle. Premium-normalized returns are supplementary, not account returns. 2016–2021 is the development partition; 2022–2025 is a later historical comparison, not an untouched prospective test.

Candidates: 19542 individual contracts across 171 company-earnings events.

| threshold | version | fraction | period | closed | unresolved | events | all_event_bp | ci_low_bp | ci_high_bp | premium_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | baseline | 0.00 | development | 409 | 13 | 60 | -1.86 | -4.77 | 1.14 | -3.32 |
| 0.05 | baseline | 0.00 | later | 126 | 8 | 29 | 2.15 | -2.04 | 6.21 | -0.35 |
| 0.05 | baseline | 0.00 | all | 535 | 21 | 89 | -0.12 | -2.61 | 2.49 | -2.35 |
| 0.05 | baseline | 1.00 | development | 409 | 13 | 60 | -22.46 | -36.09 | -11.53 | -34.42 |
| 0.05 | baseline | 1.00 | later | 126 | 8 | 29 | -3.34 | -8.59 | 1.01 | -25.37 |
| 0.05 | baseline | 1.00 | all | 535 | 21 | 89 | -14.19 | -22.63 | -7.30 | -31.47 |
| 0.05 | liquid_cost | 0.00 | development | 22 | 0 | 10 | -1.03 | -1.98 | -0.19 | -8.82 |
| 0.05 | liquid_cost | 0.00 | later | 9 | 0 | 7 | 1.77 | 0.03 | 4.06 | 16.28 |
| 0.05 | liquid_cost | 0.00 | all | 31 | 0 | 17 | 0.18 | -0.80 | 1.44 | 1.52 |
| 0.05 | liquid_cost | 1.00 | development | 22 | 0 | 10 | -9.80 | -26.40 | -0.42 | -19.83 |
| 0.05 | liquid_cost | 1.00 | later | 9 | 0 | 7 | 1.55 | -0.05 | 3.74 | 13.10 |
| 0.05 | liquid_cost | 1.00 | all | 31 | 0 | 17 | -4.89 | -14.73 | 0.72 | -6.27 |
| 0.05 | entry_limit | 0.00 | development | 158 | 0 | 36 | -1.33 | -5.23 | 2.50 | -7.26 |
| 0.05 | entry_limit | 0.00 | later | 66 | 0 | 19 | 1.20 | -0.12 | 2.80 | 3.23 |
| 0.05 | entry_limit | 0.00 | all | 224 | 0 | 55 | -0.23 | -2.47 | 2.01 | -3.64 |
| 0.05 | entry_limit | 1.00 | development | 158 | 0 | 36 | -12.86 | -23.67 | -5.27 | -33.37 |
| 0.05 | entry_limit | 1.00 | later | 66 | 0 | 19 | -1.12 | -2.88 | 0.64 | -18.02 |
| 0.05 | entry_limit | 1.00 | all | 224 | 0 | 55 | -7.78 | -14.41 | -3.26 | -28.07 |
| 0.10 | baseline | 0.00 | development | 189 | 12 | 39 | 0.77 | -1.16 | 3.27 | 2.15 |
| 0.10 | baseline | 0.00 | later | 39 | 7 | 14 | 0.62 | -0.65 | 2.09 | 0.13 |
| 0.10 | baseline | 0.00 | all | 228 | 19 | 53 | 0.71 | -0.54 | 2.27 | 1.62 |
| 0.10 | baseline | 1.00 | development | 189 | 12 | 39 | -13.00 | -25.13 | -4.26 | -44.38 |
| 0.10 | baseline | 1.00 | later | 39 | 7 | 14 | -3.34 | -6.48 | -0.81 | -46.48 |
| 0.10 | baseline | 1.00 | all | 228 | 19 | 53 | -8.82 | -15.95 | -3.40 | -44.93 |
| 0.10 | liquid_cost | 0.00 | development | 10 | 0 | 4 | -0.39 | -0.93 | -0.02 | -11.32 |
| 0.10 | liquid_cost | 0.00 | all | 10 | 0 | 4 | -0.22 | -0.55 | -0.01 | -11.32 |
| 0.10 | liquid_cost | 1.00 | development | 10 | 0 | 4 | -7.73 | -23.74 | -0.04 | -26.10 |
| 0.10 | liquid_cost | 1.00 | all | 10 | 0 | 4 | -4.39 | -13.46 | -0.02 | -26.10 |
| 0.10 | entry_limit | 0.00 | development | 68 | 0 | 16 | 0.34 | -1.17 | 2.49 | 8.74 |
| 0.10 | entry_limit | 0.00 | later | 19 | 0 | 11 | 1.02 | -0.05 | 2.36 | 7.74 |
| 0.10 | entry_limit | 0.00 | all | 87 | 0 | 27 | 0.64 | -0.43 | 1.95 | 8.33 |
| 0.10 | entry_limit | 1.00 | development | 68 | 0 | 16 | -6.96 | -17.41 | -0.85 | -29.02 |
| 0.10 | entry_limit | 1.00 | later | 19 | 0 | 11 | -0.99 | -2.36 | 0.43 | -31.04 |
| 0.10 | entry_limit | 1.00 | all | 87 | 0 | 27 | -4.38 | -10.72 | -0.75 | -29.84 |
| 0.20 | baseline | 0.00 | development | 86 | 8 | 24 | 0.74 | -0.83 | 2.81 | 14.68 |
| 0.20 | baseline | 0.00 | later | 13 | 3 | 7 | 0.44 | -0.89 | 1.89 | -0.81 |
| 0.20 | baseline | 0.00 | all | 99 | 11 | 31 | 0.61 | -0.49 | 1.91 | 11.18 |
| 0.20 | baseline | 1.00 | development | 86 | 8 | 24 | -8.33 | -16.93 | -2.59 | -60.91 |
| 0.20 | baseline | 1.00 | later | 13 | 3 | 7 | -2.31 | -6.28 | 0.32 | -62.05 |
| 0.20 | baseline | 1.00 | all | 99 | 11 | 31 | -5.72 | -11.01 | -2.05 | -61.17 |
| 0.20 | entry_limit | 0.00 | development | 28 | 0 | 8 | 0.54 | -0.60 | 2.39 | 19.51 |
| 0.20 | entry_limit | 0.00 | later | 3 | 0 | 2 | 0.50 | -0.03 | 1.54 | 31.11 |
| 0.20 | entry_limit | 0.00 | all | 31 | 0 | 10 | 0.52 | -0.27 | 1.62 | 21.83 |
| 0.20 | entry_limit | 1.00 | development | 28 | 0 | 8 | -0.71 | -2.07 | 0.71 | -35.74 |
| 0.20 | entry_limit | 1.00 | later | 3 | 0 | 2 | 0.11 | -1.03 | 1.34 | -4.74 |
| 0.20 | entry_limit | 1.00 | all | 31 | 0 | 10 | -0.36 | -1.28 | 0.57 | -29.54 |

## Side and cost diagnosis

| threshold | version | period | side | trades | option_bp | stock_bp | cost_bp | net_bp |
|---|---|---|---|---|---|---|---|---|
| 0.05 | baseline | development | short | 167 | -20.86 | 16.45 | 53.70 | -58.12 |
| 0.05 | baseline | development | long | 242 | 6.61 | -2.37 | 28.56 | -24.32 |
| 0.05 | baseline | later | short | 40 | 7.50 | -1.64 | 18.56 | -12.70 |
| 0.05 | baseline | later | long | 86 | 14.91 | -10.34 | 16.66 | -12.10 |
| 0.05 | baseline | all | short | 207 | -15.38 | 12.95 | 46.91 | -49.34 |
| 0.05 | baseline | all | long | 328 | 8.79 | -4.46 | 25.44 | -21.11 |
| 0.05 | liquid_cost | development | short | 3 | -285.10 | 308.23 | 739.66 | -716.54 |
| 0.05 | liquid_cost | development | long | 19 | -33.76 | 18.51 | 7.22 | -22.47 |
| 0.05 | liquid_cost | later | short | 1 | 15.56 | -14.61 | 4.27 | -3.31 |
| 0.05 | liquid_cost | later | long | 8 | 78.19 | -46.60 | 4.15 | 27.44 |
| 0.05 | liquid_cost | all | short | 4 | -209.94 | 227.52 | 555.81 | -538.23 |
| 0.05 | liquid_cost | all | long | 27 | -0.59 | -0.78 | 6.31 | -7.68 |
| 0.05 | entry_limit | development | short | 46 | -52.35 | 44.59 | 84.51 | -92.27 |
| 0.05 | entry_limit | development | long | 112 | 6.54 | -4.39 | 19.33 | -17.18 |
| 0.05 | entry_limit | later | short | 9 | 14.94 | -0.07 | 15.42 | -0.54 |
| 0.05 | entry_limit | later | long | 57 | 27.35 | -21.26 | 9.93 | -3.84 |
| 0.05 | entry_limit | all | short | 55 | -41.34 | 37.29 | 73.20 | -77.26 |
| 0.05 | entry_limit | all | long | 169 | 13.56 | -10.08 | 16.16 | -12.68 |
| 0.10 | baseline | development | short | 91 | -14.69 | 12.97 | 53.65 | -55.37 |
| 0.10 | baseline | development | long | 98 | 5.81 | 5.67 | 36.68 | -25.20 |
| 0.10 | baseline | later | short | 9 | 0.28 | 4.05 | 25.17 | -20.84 |
| 0.10 | baseline | later | long | 30 | 26.86 | -21.26 | 24.51 | -18.91 |
| 0.10 | baseline | all | short | 100 | -13.34 | 12.17 | 51.08 | -52.26 |
| 0.10 | baseline | all | long | 128 | 10.74 | -0.64 | 33.83 | -23.73 |
| 0.10 | liquid_cost | development | short | 2 | -358.96 | 400.12 | 1048.04 | -1006.88 |
| 0.10 | liquid_cost | development | long | 8 | -46.68 | 28.77 | 10.90 | -28.81 |
| 0.10 | liquid_cost | all | short | 2 | -358.96 | 400.12 | 1048.04 | -1006.88 |
| 0.10 | liquid_cost | all | long | 8 | -46.68 | 28.77 | 10.90 | -28.81 |
| 0.10 | entry_limit | development | short | 24 | -53.68 | 53.74 | 112.92 | -112.86 |
| 0.10 | entry_limit | development | long | 44 | 2.24 | 5.96 | 19.94 | -11.74 |
| 0.10 | entry_limit | later | short | 2 | 15.03 | 12.38 | 20.93 | 6.48 |
| 0.10 | entry_limit | later | long | 17 | 36.01 | -25.54 | 13.79 | -3.32 |
| 0.10 | entry_limit | all | short | 26 | -48.40 | 50.56 | 105.85 | -103.68 |
| 0.10 | entry_limit | all | long | 61 | 11.65 | -2.82 | 18.23 | -9.40 |
| 0.20 | baseline | development | short | 45 | -10.40 | 4.74 | 37.36 | -43.02 |
| 0.20 | baseline | development | long | 41 | 5.00 | 10.05 | 55.32 | -40.27 |
| 0.20 | baseline | later | short | 2 | 6.00 | -3.39 | 21.49 | -18.88 |
| 0.20 | baseline | later | long | 11 | 39.63 | -31.60 | 33.22 | -25.19 |
| 0.20 | baseline | all | short | 47 | -9.70 | 4.39 | 36.68 | -41.99 |
| 0.20 | baseline | all | long | 52 | 12.33 | 1.24 | 50.65 | -37.08 |
| 0.20 | entry_limit | development | short | 10 | -12.39 | 3.26 | 21.92 | -31.04 |
| 0.20 | entry_limit | development | long | 18 | 28.88 | -10.26 | 17.73 | 0.89 |
| 0.20 | entry_limit | later | long | 3 | 85.39 | -58.94 | 12.47 | 13.98 |
| 0.20 | entry_limit | all | short | 10 | -12.39 | 3.26 | 21.92 | -31.04 |
| 0.20 | entry_limit | all | long | 21 | 36.95 | -17.21 | 16.98 | 2.76 |

All hedge/fill comparisons are retained in wrds_studies/pre_event_combined/summary.csv; candidate and trade ledgers are saved alongside it. The original holding-through-earnings experiments are unchanged.
