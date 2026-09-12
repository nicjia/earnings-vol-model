# Strategy iteration: execution, losses and targeted adjustments

All work is historical simulation. Development is 2016–2021; later comparison is 2022–2025. Both periods have appeared in prior analyses, so later results are not an untouched confirmation. No threshold or configuration was selected by maximizing later-period profit. Four baseline/adjustment families are defined in iteration_plan.json.

## The 20% midpoint result

A midpoint fill pays zero modeled half-spread cost. A fraction of 1 pays the full adverse quoted half-spread at that leg. Fraction 0.5 is halfway from midpoint to the adverse bid/ask, not midpoint itself. Entry and exit fractions can differ. Commissions and stock execution costs remain. Fractions are hypothetical execution assumptions, not fill-rate estimates.

| entry_fraction | exit_fraction | events | premium_pct | spot_bp |
|---|---|---|---|---|
| 0.00 | 0.00 | 37 | 25.99 | -7.28 |
| 0.25 | 0.25 | 37 | 10.75 | -11.82 |
| 0.50 | 0.50 | 37 | -4.48 | -16.36 |
| 0.75 | 0.75 | 37 | -19.72 | -20.90 |
| 1.00 | 1.00 | 37 | -34.96 | -25.44 |
| 0.00 | 1.00 | 37 | -1.14 | -14.22 |
| 1.00 | 0.00 | 37 | -7.83 | -18.49 |
| 0.25 | 0.75 | 37 | -2.81 | -15.29 |
| 0.75 | 0.25 | 37 | -6.16 | -17.43 |

Removing top events is diagnostic only:

| remove_best | remaining | premium_pct |
|---|---|---|
| 0 | 37 | 25.99 |
| 1 | 36 | 5.88 |
| 2 | 35 | -14.39 |
| 3 | 34 | -20.68 |
| 5 | 32 | -30.47 |

The previous +26% number is a mean of premium-normalized event returns, not account profit. Small option premiums and gains on the associated stock hedge can make this number extreme. The primary metric here is P&L per gross stock notional, allocated equally across selected positions within an event. Untraded event allocations remain idle. It is still not a funded portfolio or a margin return. Pairs net their stock hedge and have two option contracts' gross spot notional. Protective-wing comparisons instead preserve the original core straddle's two stock-notional units and use no stock hedge as primary; adding wings does not mechanically dilute their exposure denominator. The original signal, next-close entry and post-earnings exit remain unchanged.

## Strategies and diagnosis-driven adjustments

1. **Single residual:** baseline requires a 20% hybrid/midpoint discrepancy. Large discrepancies occurred in wide markets and tiny premiums; the initial stock hedge produced major winners/losses. Adjustment permits a 5% discrepancy but requires signal premium >= $1, full spread <= 10%, agreement with market-only pricing, and an edge greater than the estimated full round-trip spread plus commissions. Costs are estimated from signal quotes, not realized exit quotes.
2. **Vertical relative value:** buy an option with positive residual and sell one with negative residual, same expiry and type, different strikes. Select one pair/event by signal gap divided by gross premium, above 5%. Opposite residuals do not guarantee realizable relative value; wide leg spreads can consume the gap. Adjustment requires both legs to pass the same liquidity/agreement screen and the gap to cover signal-estimated crossing costs. The option legs form a vertical but the associated stock hedge means the full portfolio is not claimed to have bounded loss.
3. **Calendar relative value:** equivalent opposite-residual pairing at the same strike and type across expiries. Baseline buys the cheap residual and sells the rich one, with one selected pair/event. Adjustment adds both-leg liquidity/agreement and estimated-cost coverage. Both expiries span the announcement; this compares relative pricing rather than claiming to remove all event exposure.
4. **Historical variance:** buy ATM straddle when forecast variance exceeds implied by 25%, sell for the reverse. Earnings outliers and stale physical variance estimates can dominate. Adjustment requires signal liquidity, historical-adjusted option valuation to agree and cover estimated costs, and caps exposure using the largest absolute completed earnings move in the prior eight events. Scaling reduces both gains and losses; it does not by itself demonstrate forecasting improvement.

The broad diagnosis motivating liquidity adjustments uses previously inspected data. Date separation limits reuse in comparisons but cannot undo prior knowledge of this panel. The earlier known failure of short earnings-volatility positions motivates the tail-aware sizing adjustment.

## Before/after and later-period comparisons

Returns are basis points of allocated gross stock notional; all_event_bp includes zero for untraded events. Weekly bootstrap intervals preserve same-week clustering. They are descriptive and not adjusted for multiple strategies.

| family | version | period | entry_fraction | closed | events | all_event_bp | ci_low_bp | ci_high_bp | premium_pct |
|---|---|---|---|---|---|---|---|---|---|
| calendar_relative_value | adjusted | development | 0.00 | 4 | 4 | -0.14 | -0.57 | 0.24 | -16.02 |
| calendar_relative_value | adjusted | development | 0.50 | 4 | 4 | -0.17 | -0.61 | 0.19 | -17.94 |
| calendar_relative_value | adjusted | development | 1.00 | 4 | 4 | -0.21 | -0.66 | 0.14 | -19.85 |
| calendar_relative_value | adjusted | later | 0.00 | 1 | 1 | 0.11 | 0.00 | 0.33 | 1.45 |
| calendar_relative_value | adjusted | later | 0.50 | 1 | 1 | 0.01 | 0.00 | 0.05 | 0.20 |
| calendar_relative_value | adjusted | later | 1.00 | 1 | 1 | -0.08 | -0.24 | 0.00 | -1.06 |
| calendar_relative_value | adjusted | all | 0.00 | 5 | 5 | -0.03 | -0.28 | 0.21 | -12.53 |
| calendar_relative_value | adjusted | all | 0.50 | 5 | 5 | -0.09 | -0.33 | 0.13 | -14.31 |
| calendar_relative_value | adjusted | all | 1.00 | 5 | 5 | -0.15 | -0.41 | 0.07 | -16.09 |
| calendar_relative_value | adjusted_entry_hedge | development | 0.00 | 4 | 4 | -0.12 | -0.53 | 0.26 | -14.30 |
| calendar_relative_value | adjusted_entry_hedge | development | 0.50 | 4 | 4 | -0.16 | -0.57 | 0.21 | -16.22 |
| calendar_relative_value | adjusted_entry_hedge | development | 1.00 | 4 | 4 | -0.19 | -0.62 | 0.16 | -18.13 |
| calendar_relative_value | adjusted_entry_hedge | later | 0.00 | 1 | 1 | 0.02 | 0.00 | 0.05 | 0.22 |
| calendar_relative_value | adjusted_entry_hedge | later | 0.50 | 1 | 1 | -0.08 | -0.24 | 0.00 | -1.03 |
| calendar_relative_value | adjusted_entry_hedge | later | 1.00 | 1 | 1 | -0.17 | -0.52 | 0.00 | -2.29 |
| calendar_relative_value | adjusted_entry_hedge | all | 0.00 | 5 | 5 | -0.06 | -0.29 | 0.15 | -11.40 |
| calendar_relative_value | adjusted_entry_hedge | all | 0.50 | 5 | 5 | -0.12 | -0.36 | 0.09 | -13.18 |
| calendar_relative_value | adjusted_entry_hedge | all | 1.00 | 5 | 5 | -0.18 | -0.46 | 0.06 | -14.96 |
| calendar_relative_value | adjusted_reference_hedge | development | 0.00 | 4 | 4 | -0.10 | -0.50 | 0.26 | -14.00 |
| calendar_relative_value | adjusted_reference_hedge | development | 0.50 | 4 | 4 | -0.14 | -0.54 | 0.21 | -15.91 |
| calendar_relative_value | adjusted_reference_hedge | development | 1.00 | 4 | 4 | -0.17 | -0.58 | 0.16 | -17.83 |
| calendar_relative_value | adjusted_reference_hedge | later | 0.00 | 1 | 1 | 0.02 | 0.00 | 0.06 | 0.27 |
| calendar_relative_value | adjusted_reference_hedge | later | 0.50 | 1 | 1 | -0.07 | -0.23 | 0.00 | -0.99 |
| calendar_relative_value | adjusted_reference_hedge | later | 1.00 | 1 | 1 | -0.17 | -0.51 | 0.00 | -2.24 |
| calendar_relative_value | adjusted_reference_hedge | all | 0.00 | 5 | 5 | -0.05 | -0.26 | 0.15 | -11.14 |
| calendar_relative_value | adjusted_reference_hedge | all | 0.50 | 5 | 5 | -0.11 | -0.34 | 0.09 | -12.93 |
| calendar_relative_value | adjusted_reference_hedge | all | 1.00 | 5 | 5 | -0.17 | -0.44 | 0.06 | -14.71 |
| calendar_relative_value | baseline | development | 0.00 | 43 | 43 | -0.86 | -2.42 | 0.44 | -1.12 |
| calendar_relative_value | baseline | development | 0.50 | 43 | 43 | -4.04 | -6.55 | -1.97 | -19.30 |
| calendar_relative_value | baseline | development | 1.00 | 43 | 43 | -7.21 | -11.42 | -3.87 | -37.49 |
| calendar_relative_value | baseline | later | 0.00 | 20 | 20 | -0.08 | -1.72 | 1.31 | -1.47 |
| calendar_relative_value | baseline | later | 0.50 | 20 | 20 | -2.09 | -4.19 | -0.38 | -20.33 |
| calendar_relative_value | baseline | later | 1.00 | 20 | 20 | -4.10 | -7.01 | -1.73 | -39.18 |
| calendar_relative_value | baseline | all | 0.00 | 63 | 63 | -0.52 | -1.68 | 0.48 | -1.23 |
| calendar_relative_value | baseline | all | 0.50 | 63 | 63 | -3.19 | -4.89 | -1.67 | -19.63 |
| calendar_relative_value | baseline | all | 1.00 | 63 | 63 | -5.86 | -8.54 | -3.55 | -38.02 |
| calendar_relative_value | baseline_entry_hedge | development | 0.00 | 41 | 41 | -0.83 | -2.15 | 0.22 | -3.72 |
| calendar_relative_value | baseline_entry_hedge | development | 0.50 | 41 | 41 | -3.53 | -5.76 | -1.70 | -19.66 |
| calendar_relative_value | baseline_entry_hedge | development | 1.00 | 41 | 41 | -6.23 | -10.08 | -3.19 | -35.61 |
| calendar_relative_value | baseline_entry_hedge | later | 0.00 | 20 | 20 | -0.04 | -1.72 | 1.43 | 1.41 |
| calendar_relative_value | baseline_entry_hedge | later | 0.50 | 20 | 20 | -2.05 | -4.17 | -0.33 | -17.44 |
| calendar_relative_value | baseline_entry_hedge | later | 1.00 | 20 | 20 | -4.05 | -6.93 | -1.73 | -36.29 |
| calendar_relative_value | baseline_entry_hedge | all | 0.00 | 61 | 61 | -0.49 | -1.58 | 0.46 | -2.03 |
| calendar_relative_value | baseline_entry_hedge | all | 0.50 | 61 | 61 | -2.88 | -4.48 | -1.53 | -18.93 |
| calendar_relative_value | baseline_entry_hedge | all | 1.00 | 61 | 61 | -5.28 | -7.83 | -3.19 | -35.83 |
| calendar_relative_value | baseline_reference_hedge | development | 0.00 | 43 | 43 | -0.93 | -2.26 | 0.17 | -4.33 |
| calendar_relative_value | baseline_reference_hedge | development | 0.50 | 43 | 43 | -4.11 | -6.48 | -2.15 | -22.51 |
| calendar_relative_value | baseline_reference_hedge | development | 1.00 | 43 | 43 | -7.29 | -11.36 | -3.99 | -40.70 |
| calendar_relative_value | baseline_reference_hedge | later | 0.00 | 20 | 20 | -0.35 | -2.06 | 1.13 | -3.42 |
| calendar_relative_value | baseline_reference_hedge | later | 0.50 | 20 | 20 | -2.36 | -4.57 | -0.55 | -22.27 |
| calendar_relative_value | baseline_reference_hedge | later | 1.00 | 20 | 20 | -4.37 | -7.42 | -1.92 | -41.12 |
| calendar_relative_value | baseline_reference_hedge | all | 0.00 | 63 | 63 | -0.68 | -1.77 | 0.28 | -4.04 |
| calendar_relative_value | baseline_reference_hedge | all | 0.50 | 63 | 63 | -3.35 | -4.98 | -1.88 | -22.44 |
| calendar_relative_value | baseline_reference_hedge | all | 1.00 | 63 | 63 | -6.02 | -8.62 | -3.73 | -40.83 |
| entry_limits | baseline | development | 0.00 | 139 | 28 | -2.93 | -8.35 | 1.52 | 3.76 |
| entry_limits | baseline | development | 0.50 | 139 | 28 | -5.66 | -12.08 | -0.55 | -29.58 |
| entry_limits | baseline | development | 1.00 | 139 | 28 | -8.38 | -16.14 | -2.30 | -62.91 |
| entry_limits | baseline | later | 0.00 | 17 | 9 | -1.99 | -5.96 | 1.62 | -30.87 |
| entry_limits | baseline | later | 0.50 | 17 | 9 | -3.00 | -7.65 | 0.94 | -52.43 |
| entry_limits | baseline | later | 1.00 | 17 | 9 | -4.00 | -9.35 | 0.28 | -73.99 |
| entry_limits | baseline | all | 0.00 | 156 | 37 | -2.52 | -5.87 | 0.55 | -4.67 |
| entry_limits | baseline | all | 0.50 | 156 | 37 | -4.50 | -8.51 | -0.91 | -35.14 |
| entry_limits | baseline | all | 1.00 | 156 | 37 | -6.48 | -11.30 | -2.23 | -65.61 |
| entry_limits | limit_liquid | development | 0.00 | 7 | 2 | 0.17 | -0.49 | 0.99 | 24.89 |
| entry_limits | limit_liquid | development | 0.50 | 7 | 2 | 0.16 | -0.51 | 0.96 | 20.60 |
| entry_limits | limit_liquid | development | 1.00 | 7 | 2 | 0.14 | -0.54 | 0.94 | 16.31 |
| entry_limits | limit_liquid | all | 0.00 | 7 | 2 | 0.10 | -0.27 | 0.57 | 24.89 |
| entry_limits | limit_liquid | all | 0.50 | 7 | 2 | 0.09 | -0.29 | 0.56 | 20.60 |
| entry_limits | limit_liquid | all | 1.00 | 7 | 2 | 0.08 | -0.30 | 0.54 | 16.31 |
| entry_limits | limit_only | development | 0.00 | 32 | 9 | 0.24 | -0.92 | 1.62 | -52.47 |
| entry_limits | limit_only | development | 0.50 | 32 | 9 | -0.22 | -1.40 | 1.01 | -76.41 |
| entry_limits | limit_only | development | 1.00 | 32 | 9 | -0.68 | -2.19 | 0.61 | -100.34 |
| entry_limits | limit_only | later | 0.00 | 3 | 2 | 2.01 | 0.00 | 5.21 | 284.91 |
| entry_limits | limit_only | later | 0.50 | 3 | 2 | 1.87 | 0.00 | 4.86 | 271.70 |
| entry_limits | limit_only | later | 1.00 | 3 | 2 | 1.73 | 0.00 | 4.52 | 258.50 |
| entry_limits | limit_only | all | 0.00 | 35 | 11 | 1.01 | -0.20 | 2.53 | 8.87 |
| entry_limits | limit_only | all | 0.50 | 35 | 11 | 0.69 | -0.48 | 2.12 | -13.12 |
| entry_limits | limit_only | all | 1.00 | 35 | 11 | 0.37 | -0.85 | 1.77 | -35.10 |
| historical_variance | adjusted | development | 0.00 | 59 | 59 | 15.35 | -0.89 | 29.31 | 5.49 |
| historical_variance | adjusted | development | 0.50 | 59 | 59 | 13.68 | -2.69 | 27.61 | 4.73 |
| historical_variance | adjusted | development | 1.00 | 59 | 59 | 12.01 | -4.23 | 25.97 | 3.96 |
| historical_variance | adjusted | later | 0.00 | 52 | 52 | -3.70 | -22.36 | 13.29 | -0.88 |
| historical_variance | adjusted | later | 0.50 | 52 | 52 | -5.01 | -23.93 | 12.06 | -1.29 |
| historical_variance | adjusted | later | 1.00 | 52 | 52 | -6.31 | -25.41 | 10.84 | -1.71 |
| historical_variance | adjusted | all | 0.00 | 111 | 111 | 7.06 | -4.88 | 18.23 | 2.51 |
| historical_variance | adjusted | all | 0.50 | 111 | 111 | 5.55 | -6.44 | 16.74 | 1.91 |
| historical_variance | adjusted | all | 1.00 | 111 | 111 | 4.04 | -8.09 | 15.29 | 1.30 |
| historical_variance | adjusted_entry_hedge | development | 0.00 | 59 | 59 | 14.84 | 1.16 | 27.43 | 5.59 |
| historical_variance | adjusted_entry_hedge | development | 0.50 | 59 | 59 | 13.17 | -0.62 | 25.60 | 4.82 |
| historical_variance | adjusted_entry_hedge | development | 1.00 | 59 | 59 | 11.50 | -2.33 | 23.80 | 4.05 |
| historical_variance | adjusted_entry_hedge | later | 0.00 | 52 | 52 | -1.02 | -15.17 | 12.33 | 0.02 |
| historical_variance | adjusted_entry_hedge | later | 0.50 | 52 | 52 | -2.33 | -16.69 | 11.15 | -0.39 |
| historical_variance | adjusted_entry_hedge | later | 1.00 | 52 | 52 | -3.63 | -18.09 | 9.95 | -0.81 |
| historical_variance | adjusted_entry_hedge | all | 0.00 | 111 | 111 | 7.94 | -1.91 | 17.43 | 2.98 |
| historical_variance | adjusted_entry_hedge | all | 0.50 | 111 | 111 | 6.43 | -3.43 | 15.95 | 2.38 |
| historical_variance | adjusted_entry_hedge | all | 1.00 | 111 | 111 | 4.91 | -4.96 | 14.53 | 1.78 |
| historical_variance | adjusted_entry_hedge_short_only | development | 0.00 | 49 | 49 | 18.52 | 5.24 | 30.26 | 8.38 |
| historical_variance | adjusted_entry_hedge_short_only | development | 0.50 | 49 | 49 | 17.00 | 3.67 | 28.73 | 7.53 |
| historical_variance | adjusted_entry_hedge_short_only | development | 1.00 | 49 | 49 | 15.47 | 2.14 | 27.17 | 6.67 |
| historical_variance | adjusted_entry_hedge_short_only | later | 0.00 | 38 | 38 | -2.58 | -15.47 | 9.92 | -0.73 |
| historical_variance | adjusted_entry_hedge_short_only | later | 0.50 | 38 | 38 | -3.67 | -16.60 | 8.87 | -1.19 |
| historical_variance | adjusted_entry_hedge_short_only | later | 1.00 | 38 | 38 | -4.75 | -17.86 | 7.86 | -1.65 |
| historical_variance | adjusted_entry_hedge_short_only | all | 0.00 | 87 | 87 | 9.34 | 0.00 | 18.30 | 4.40 |
| historical_variance | adjusted_entry_hedge_short_only | all | 0.50 | 87 | 87 | 8.00 | -1.36 | 16.99 | 3.72 |
| historical_variance | adjusted_entry_hedge_short_only | all | 1.00 | 87 | 87 | 6.67 | -2.73 | 15.75 | 3.03 |
| historical_variance | adjusted_reference_hedge | development | 0.00 | 59 | 59 | 14.87 | 1.16 | 27.45 | 5.62 |
| historical_variance | adjusted_reference_hedge | development | 0.50 | 59 | 59 | 13.20 | -0.69 | 25.55 | 4.86 |
| historical_variance | adjusted_reference_hedge | development | 1.00 | 59 | 59 | 11.54 | -2.33 | 23.86 | 4.09 |
| historical_variance | adjusted_reference_hedge | later | 0.00 | 52 | 52 | -1.03 | -15.24 | 12.41 | 0.02 |
| historical_variance | adjusted_reference_hedge | later | 0.50 | 52 | 52 | -2.34 | -16.63 | 11.24 | -0.39 |
| historical_variance | adjusted_reference_hedge | later | 1.00 | 52 | 52 | -3.64 | -18.03 | 10.00 | -0.81 |
| historical_variance | adjusted_reference_hedge | all | 0.00 | 111 | 111 | 7.95 | -1.96 | 17.46 | 3.00 |
| historical_variance | adjusted_reference_hedge | all | 0.50 | 111 | 111 | 6.44 | -3.46 | 15.97 | 2.40 |
| historical_variance | adjusted_reference_hedge | all | 1.00 | 111 | 111 | 4.93 | -4.99 | 14.54 | 1.80 |
| historical_variance | adjusted_reference_hedge_short_only | development | 0.00 | 49 | 49 | 18.54 | 5.31 | 30.34 | 8.42 |
| historical_variance | adjusted_reference_hedge_short_only | development | 0.50 | 49 | 49 | 17.02 | 3.68 | 28.74 | 7.56 |
| historical_variance | adjusted_reference_hedge_short_only | development | 1.00 | 49 | 49 | 15.49 | 2.11 | 27.19 | 6.70 |
| historical_variance | adjusted_reference_hedge_short_only | later | 0.00 | 38 | 38 | -2.68 | -15.60 | 9.83 | -0.76 |
| historical_variance | adjusted_reference_hedge_short_only | later | 0.50 | 38 | 38 | -3.76 | -16.80 | 8.83 | -1.23 |
| historical_variance | adjusted_reference_hedge_short_only | later | 1.00 | 38 | 38 | -4.85 | -18.02 | 7.79 | -1.69 |
| historical_variance | adjusted_reference_hedge_short_only | all | 0.00 | 87 | 87 | 9.30 | -0.10 | 18.29 | 4.41 |
| historical_variance | adjusted_reference_hedge_short_only | all | 0.50 | 87 | 87 | 7.97 | -1.46 | 17.01 | 3.72 |
| historical_variance | adjusted_reference_hedge_short_only | all | 1.00 | 87 | 87 | 6.64 | -2.84 | 15.76 | 3.04 |
| historical_variance | adjusted_short_only | development | 0.00 | 49 | 49 | 18.54 | 3.19 | 32.34 | 8.06 |
| historical_variance | adjusted_short_only | development | 0.50 | 49 | 49 | 17.01 | 1.61 | 30.77 | 7.20 |
| historical_variance | adjusted_short_only | development | 1.00 | 49 | 49 | 15.49 | -0.09 | 29.27 | 6.34 |
| historical_variance | adjusted_short_only | later | 0.00 | 38 | 38 | -4.96 | -22.82 | 10.73 | -1.82 |
| historical_variance | adjusted_short_only | later | 0.50 | 38 | 38 | -6.04 | -23.99 | 9.70 | -2.28 |
| historical_variance | adjusted_short_only | later | 1.00 | 38 | 38 | -7.13 | -25.19 | 8.76 | -2.74 |
| historical_variance | adjusted_short_only | all | 0.00 | 87 | 87 | 8.31 | -2.97 | 19.13 | 3.75 |
| historical_variance | adjusted_short_only | all | 0.50 | 87 | 87 | 6.98 | -4.38 | 17.77 | 3.06 |
| historical_variance | adjusted_short_only | all | 1.00 | 87 | 87 | 5.64 | -5.83 | 16.48 | 2.37 |
| historical_variance | baseline | development | 0.00 | 65 | 65 | 25.63 | -10.66 | 58.32 | 7.27 |
| historical_variance | baseline | development | 0.50 | 65 | 65 | 21.28 | -15.22 | 54.29 | 5.61 |
| historical_variance | baseline | development | 1.00 | 65 | 65 | 16.93 | -19.78 | 49.99 | 3.94 |
| historical_variance | baseline | later | 0.00 | 54 | 54 | -12.49 | -59.90 | 31.36 | -2.88 |
| historical_variance | baseline | later | 0.50 | 54 | 54 | -16.35 | -64.04 | 27.62 | -4.07 |
| historical_variance | baseline | later | 1.00 | 54 | 54 | -20.20 | -67.93 | 23.78 | -5.25 |
| historical_variance | baseline | all | 0.00 | 119 | 119 | 9.04 | -19.85 | 36.17 | 2.66 |
| historical_variance | baseline | all | 0.50 | 119 | 119 | 4.90 | -24.03 | 32.06 | 1.22 |
| historical_variance | baseline | all | 1.00 | 119 | 119 | 0.77 | -28.23 | 28.26 | -0.23 |
| historical_variance | baseline_entry_hedge | development | 0.00 | 65 | 65 | 23.34 | -9.86 | 53.89 | 7.33 |
| historical_variance | baseline_entry_hedge | development | 0.50 | 65 | 65 | 18.99 | -14.44 | 49.49 | 5.67 |
| historical_variance | baseline_entry_hedge | development | 1.00 | 65 | 65 | 14.64 | -19.05 | 45.35 | 4.00 |
| historical_variance | baseline_entry_hedge | later | 0.00 | 54 | 54 | -4.97 | -41.51 | 32.38 | -0.67 |
| historical_variance | baseline_entry_hedge | later | 0.50 | 54 | 54 | -8.83 | -45.71 | 28.65 | -1.86 |
| historical_variance | baseline_entry_hedge | later | 1.00 | 54 | 54 | -12.68 | -49.67 | 24.79 | -3.04 |
| historical_variance | baseline_entry_hedge | all | 0.00 | 119 | 119 | 11.01 | -13.48 | 34.84 | 3.70 |
| historical_variance | baseline_entry_hedge | all | 0.50 | 119 | 119 | 6.88 | -17.60 | 30.84 | 2.25 |
| historical_variance | baseline_entry_hedge | all | 1.00 | 119 | 119 | 2.75 | -21.94 | 26.81 | 0.81 |
| historical_variance | baseline_reference_hedge | development | 0.00 | 65 | 65 | 23.32 | -9.81 | 53.71 | 7.36 |
| historical_variance | baseline_reference_hedge | development | 0.50 | 65 | 65 | 18.97 | -14.37 | 49.42 | 5.70 |
| historical_variance | baseline_reference_hedge | development | 1.00 | 65 | 65 | 14.61 | -19.01 | 45.20 | 4.03 |
| historical_variance | baseline_reference_hedge | later | 0.00 | 54 | 54 | -4.73 | -41.52 | 32.82 | -0.58 |
| historical_variance | baseline_reference_hedge | later | 0.50 | 54 | 54 | -8.59 | -45.44 | 28.95 | -1.76 |
| historical_variance | baseline_reference_hedge | later | 1.00 | 54 | 54 | -12.44 | -49.41 | 25.22 | -2.95 |
| historical_variance | baseline_reference_hedge | all | 0.00 | 119 | 119 | 11.11 | -13.44 | 34.87 | 3.76 |
| historical_variance | baseline_reference_hedge | all | 0.50 | 119 | 119 | 6.97 | -17.69 | 30.96 | 2.31 |
| historical_variance | baseline_reference_hedge | all | 1.00 | 119 | 119 | 2.84 | -22.06 | 26.98 | 0.86 |
| historical_variance | regime_both | development | 0.00 | 38 | 38 | 11.89 | 0.32 | 22.87 | 7.60 |
| historical_variance | regime_both | development | 0.50 | 38 | 38 | 10.79 | -0.74 | 21.76 | 6.74 |
| historical_variance | regime_both | development | 1.00 | 38 | 38 | 9.69 | -1.91 | 20.47 | 5.89 |
| historical_variance | regime_both | later | 0.00 | 26 | 26 | -4.16 | -14.95 | 6.37 | -2.16 |
| historical_variance | regime_both | later | 0.50 | 26 | 26 | -4.89 | -15.79 | 5.66 | -2.64 |
| historical_variance | regime_both | later | 1.00 | 26 | 26 | -5.63 | -16.64 | 4.99 | -3.11 |
| historical_variance | regime_both | all | 0.00 | 64 | 64 | 4.91 | -3.11 | 12.67 | 3.64 |
| historical_variance | regime_both | all | 0.50 | 64 | 64 | 3.96 | -4.15 | 11.72 | 2.93 |
| historical_variance | regime_both | all | 1.00 | 64 | 64 | 3.02 | -5.10 | 10.77 | 2.23 |
| historical_variance | regime_drawdown | development | 0.00 | 47 | 47 | 16.73 | 3.99 | 28.49 | 8.28 |
| historical_variance | regime_drawdown | development | 0.50 | 47 | 47 | 15.23 | 2.41 | 27.07 | 7.39 |
| historical_variance | regime_drawdown | development | 1.00 | 47 | 47 | 13.74 | 0.84 | 25.45 | 6.50 |
| historical_variance | regime_drawdown | later | 0.00 | 29 | 29 | -3.81 | -14.72 | 6.78 | -1.78 |
| historical_variance | regime_drawdown | later | 0.50 | 29 | 29 | -4.63 | -15.65 | 6.00 | -2.26 |
| historical_variance | regime_drawdown | later | 1.00 | 29 | 29 | -5.44 | -16.61 | 5.27 | -2.74 |
| historical_variance | regime_drawdown | all | 0.00 | 76 | 76 | 7.79 | -0.67 | 15.99 | 4.44 |
| historical_variance | regime_drawdown | all | 0.50 | 76 | 76 | 6.59 | -1.87 | 14.78 | 3.71 |
| historical_variance | regime_drawdown | all | 1.00 | 76 | 76 | 5.39 | -3.12 | 13.62 | 2.98 |
| historical_variance | regime_volatility | development | 0.00 | 40 | 40 | 13.71 | 1.70 | 24.70 | 7.81 |
| historical_variance | regime_volatility | development | 0.50 | 40 | 40 | 12.57 | 0.54 | 23.51 | 6.99 |
| historical_variance | regime_volatility | development | 1.00 | 40 | 40 | 11.44 | -0.62 | 22.31 | 6.16 |
| historical_variance | regime_volatility | later | 0.00 | 30 | 30 | -2.47 | -13.86 | 8.62 | -1.08 |
| historical_variance | regime_volatility | later | 0.50 | 30 | 30 | -3.30 | -14.84 | 7.78 | -1.54 |
| historical_variance | regime_volatility | later | 1.00 | 30 | 30 | -4.12 | -15.82 | 6.92 | -1.99 |
| historical_variance | regime_volatility | all | 0.00 | 70 | 70 | 6.66 | -1.65 | 14.71 | 4.00 |
| historical_variance | regime_volatility | all | 0.50 | 70 | 70 | 5.67 | -2.75 | 13.65 | 3.33 |
| historical_variance | regime_volatility | all | 1.00 | 70 | 70 | 4.67 | -3.80 | 12.61 | 2.67 |
| protected_earnings | ironfly_10 | development | 0.00 | 53 | 53 | 17.44 | 2.15 | 32.33 | 5.78 |
| protected_earnings | ironfly_10 | development | 0.50 | 53 | 53 | 11.88 | -3.88 | 27.10 | 3.59 |
| protected_earnings | ironfly_10 | development | 1.00 | 53 | 53 | 6.32 | -10.18 | 21.87 | 1.40 |
| protected_earnings | ironfly_10 | later | 0.00 | 38 | 38 | -8.72 | -27.46 | 8.76 | -3.11 |
| protected_earnings | ironfly_10 | later | 0.50 | 38 | 38 | -12.39 | -31.46 | 5.38 | -4.36 |
| protected_earnings | ironfly_10 | later | 1.00 | 38 | 38 | -16.07 | -35.79 | 2.16 | -5.60 |
| protected_earnings | ironfly_10 | all | 0.00 | 91 | 91 | 6.05 | -6.12 | 17.39 | 2.07 |
| protected_earnings | ironfly_10 | all | 0.50 | 91 | 91 | 1.31 | -11.09 | 13.10 | 0.27 |
| protected_earnings | ironfly_10 | all | 1.00 | 91 | 91 | -3.42 | -16.12 | 8.70 | -1.52 |
| protected_earnings | ironfly_10_cost_budget | development | 0.00 | 51 | 51 | 17.80 | 2.35 | 32.60 | 6.10 |
| protected_earnings | ironfly_10_cost_budget | development | 0.50 | 51 | 51 | 13.19 | -2.48 | 28.26 | 4.05 |
| protected_earnings | ironfly_10_cost_budget | development | 1.00 | 51 | 51 | 8.58 | -7.40 | 23.74 | 1.99 |
| protected_earnings | ironfly_10_cost_budget | later | 0.00 | 38 | 38 | -8.72 | -27.46 | 8.76 | -3.11 |
| protected_earnings | ironfly_10_cost_budget | later | 0.50 | 38 | 38 | -12.39 | -31.46 | 5.38 | -4.36 |
| protected_earnings | ironfly_10_cost_budget | later | 1.00 | 38 | 38 | -16.07 | -35.79 | 2.16 | -5.60 |
| protected_earnings | ironfly_10_cost_budget | all | 0.00 | 89 | 89 | 6.25 | -5.92 | 17.51 | 2.17 |
| protected_earnings | ironfly_10_cost_budget | all | 0.50 | 89 | 89 | 2.05 | -10.34 | 13.54 | 0.46 |
| protected_earnings | ironfly_10_cost_budget | all | 1.00 | 89 | 89 | -2.15 | -14.86 | 9.56 | -1.25 |
| protected_earnings | ironfly_5 | development | 0.00 | 53 | 53 | 10.16 | 2.01 | 19.35 | 3.47 |
| protected_earnings | ironfly_5 | development | 0.50 | 53 | 53 | 4.21 | -4.50 | 13.94 | 1.51 |
| protected_earnings | ironfly_5 | development | 1.00 | 53 | 53 | -1.74 | -11.20 | 8.31 | -0.45 |
| protected_earnings | ironfly_5 | later | 0.00 | 38 | 38 | -2.76 | -17.75 | 10.15 | -0.81 |
| protected_earnings | ironfly_5 | later | 0.50 | 38 | 38 | -6.94 | -21.90 | 5.97 | -2.02 |
| protected_earnings | ironfly_5 | later | 1.00 | 38 | 38 | -11.12 | -26.31 | 1.88 | -3.23 |
| protected_earnings | ironfly_5 | all | 0.00 | 91 | 91 | 4.53 | -3.43 | 12.00 | 1.68 |
| protected_earnings | ironfly_5 | all | 0.50 | 91 | 91 | -0.65 | -8.77 | 6.94 | 0.04 |
| protected_earnings | ironfly_5 | all | 1.00 | 91 | 91 | -5.83 | -14.34 | 2.27 | -1.61 |
| protected_earnings | ironfly_5_cost_budget | development | 0.00 | 50 | 50 | 11.09 | 3.15 | 20.04 | 4.16 |
| protected_earnings | ironfly_5_cost_budget | development | 0.50 | 50 | 50 | 6.43 | -1.67 | 15.29 | 2.45 |
| protected_earnings | ironfly_5_cost_budget | development | 1.00 | 50 | 50 | 1.77 | -6.55 | 10.78 | 0.74 |
| protected_earnings | ironfly_5_cost_budget | later | 0.00 | 38 | 38 | -2.76 | -17.75 | 10.15 | -0.81 |
| protected_earnings | ironfly_5_cost_budget | later | 0.50 | 38 | 38 | -6.94 | -21.90 | 5.97 | -2.02 |
| protected_earnings | ironfly_5_cost_budget | later | 1.00 | 38 | 38 | -11.12 | -26.31 | 1.88 | -3.23 |
| protected_earnings | ironfly_5_cost_budget | all | 0.00 | 88 | 88 | 5.06 | -2.74 | 12.33 | 2.01 |
| protected_earnings | ironfly_5_cost_budget | all | 0.50 | 88 | 88 | 0.61 | -7.24 | 7.83 | 0.52 |
| protected_earnings | ironfly_5_cost_budget | all | 1.00 | 88 | 88 | -3.84 | -11.91 | 3.66 | -0.98 |
| protected_earnings | naked_straddle | development | 0.00 | 54 | 54 | 43.02 | 9.08 | 75.54 | 15.24 |
| protected_earnings | naked_straddle | development | 0.50 | 54 | 54 | 39.30 | 5.20 | 71.64 | 13.48 |
| protected_earnings | naked_straddle | development | 1.00 | 54 | 54 | 35.59 | 1.29 | 68.40 | 11.73 |
| protected_earnings | naked_straddle | later | 0.00 | 40 | 40 | -1.80 | -40.87 | 34.29 | 0.25 |
| protected_earnings | naked_straddle | later | 0.50 | 40 | 40 | -4.56 | -43.96 | 31.83 | -0.88 |
| protected_earnings | naked_straddle | later | 1.00 | 40 | 40 | -7.33 | -47.16 | 29.08 | -2.02 |
| protected_earnings | naked_straddle | all | 0.00 | 94 | 94 | 23.51 | -1.77 | 47.65 | 8.86 |
| protected_earnings | naked_straddle | all | 0.50 | 94 | 94 | 20.21 | -5.44 | 44.71 | 7.37 |
| protected_earnings | naked_straddle | all | 1.00 | 94 | 94 | 16.90 | -9.11 | 41.65 | 5.88 |
| single_residual | adjusted | development | 0.00 | 49 | 17 | -6.95 | -13.89 | -1.54 | -22.35 |
| single_residual | adjusted | development | 0.50 | 49 | 17 | -7.28 | -14.28 | -1.74 | -25.56 |
| single_residual | adjusted | development | 1.00 | 49 | 17 | -7.61 | -14.79 | -1.95 | -28.77 |
| single_residual | adjusted | later | 0.00 | 7 | 5 | -0.45 | -4.30 | 3.24 | -103.61 |
| single_residual | adjusted | later | 0.50 | 7 | 5 | -0.64 | -4.41 | 2.76 | -105.59 |
| single_residual | adjusted | later | 1.00 | 7 | 5 | -0.84 | -4.57 | 2.29 | -107.56 |
| single_residual | adjusted | all | 0.00 | 56 | 22 | -4.12 | -8.18 | -0.62 | -40.82 |
| single_residual | adjusted | all | 0.50 | 56 | 22 | -4.39 | -8.49 | -0.85 | -43.75 |
| single_residual | adjusted | all | 1.00 | 56 | 22 | -4.66 | -8.79 | -1.09 | -46.67 |
| single_residual | adjusted_entry_hedge | development | 0.00 | 49 | 17 | -6.69 | -12.91 | -2.11 | -28.43 |
| single_residual | adjusted_entry_hedge | development | 0.50 | 49 | 17 | -7.02 | -13.38 | -2.32 | -31.64 |
| single_residual | adjusted_entry_hedge | development | 1.00 | 49 | 17 | -7.35 | -13.85 | -2.52 | -34.84 |
| single_residual | adjusted_entry_hedge | later | 0.00 | 7 | 5 | 0.15 | -3.23 | 3.82 | -76.20 |
| single_residual | adjusted_entry_hedge | later | 0.50 | 7 | 5 | -0.05 | -3.32 | 3.33 | -78.18 |
| single_residual | adjusted_entry_hedge | later | 1.00 | 7 | 5 | -0.25 | -3.43 | 2.86 | -80.15 |
| single_residual | adjusted_entry_hedge | all | 0.00 | 56 | 22 | -3.71 | -7.21 | -0.58 | -39.29 |
| single_residual | adjusted_entry_hedge | all | 0.50 | 56 | 22 | -3.99 | -7.52 | -0.84 | -42.21 |
| single_residual | adjusted_entry_hedge | all | 1.00 | 56 | 22 | -4.26 | -7.85 | -1.09 | -45.14 |
| single_residual | adjusted_reference_hedge | development | 0.00 | 49 | 17 | -6.65 | -12.92 | -2.02 | -26.95 |
| single_residual | adjusted_reference_hedge | development | 0.50 | 49 | 17 | -6.98 | -13.39 | -2.23 | -30.15 |
| single_residual | adjusted_reference_hedge | development | 1.00 | 49 | 17 | -7.31 | -13.88 | -2.44 | -33.36 |
| single_residual | adjusted_reference_hedge | later | 0.00 | 7 | 5 | 0.19 | -3.14 | 3.83 | -73.89 |
| single_residual | adjusted_reference_hedge | later | 0.50 | 7 | 5 | -0.00 | -3.25 | 3.34 | -75.87 |
| single_residual | adjusted_reference_hedge | later | 1.00 | 7 | 5 | -0.20 | -3.35 | 2.85 | -77.84 |
| single_residual | adjusted_reference_hedge | all | 0.00 | 56 | 22 | -3.67 | -7.21 | -0.54 | -37.62 |
| single_residual | adjusted_reference_hedge | all | 0.50 | 56 | 22 | -3.94 | -7.51 | -0.80 | -40.54 |
| single_residual | adjusted_reference_hedge | all | 1.00 | 56 | 22 | -4.22 | -7.81 | -1.05 | -43.47 |
| single_residual | baseline | development | 0.00 | 139 | 28 | -2.48 | -7.43 | 1.81 | 27.57 |
| single_residual | baseline | development | 0.50 | 139 | 28 | -5.20 | -11.46 | -0.13 | -5.76 |
| single_residual | baseline | development | 1.00 | 139 | 28 | -7.93 | -15.60 | -1.83 | -39.10 |
| single_residual | baseline | later | 0.00 | 17 | 9 | -0.43 | -4.73 | 4.51 | 21.05 |
| single_residual | baseline | later | 0.50 | 17 | 9 | -1.43 | -6.27 | 3.72 | -0.51 |
| single_residual | baseline | later | 1.00 | 17 | 9 | -2.44 | -7.92 | 2.89 | -22.07 |
| single_residual | baseline | all | 0.00 | 156 | 37 | -1.58 | -4.85 | 1.78 | 25.99 |
| single_residual | baseline | all | 0.50 | 156 | 37 | -3.56 | -7.52 | 0.23 | -4.48 |
| single_residual | baseline | all | 1.00 | 156 | 37 | -5.54 | -10.31 | -1.17 | -34.96 |
| single_residual | baseline_entry_hedge | development | 0.00 | 137 | 28 | -2.87 | -8.23 | 1.49 | 3.33 |
| single_residual | baseline_entry_hedge | development | 0.50 | 137 | 28 | -5.56 | -11.91 | -0.50 | -29.83 |
| single_residual | baseline_entry_hedge | development | 1.00 | 137 | 28 | -8.24 | -15.95 | -2.23 | -62.99 |
| single_residual | baseline_entry_hedge | later | 0.00 | 17 | 9 | -1.94 | -5.82 | 1.62 | -28.30 |
| single_residual | baseline_entry_hedge | later | 0.50 | 17 | 9 | -2.94 | -7.56 | 0.86 | -49.86 |
| single_residual | baseline_entry_hedge | later | 1.00 | 17 | 9 | -3.95 | -9.22 | 0.23 | -71.43 |
| single_residual | baseline_entry_hedge | all | 0.00 | 154 | 37 | -2.47 | -5.73 | 0.54 | -4.36 |
| single_residual | baseline_entry_hedge | all | 0.50 | 154 | 37 | -4.42 | -8.42 | -0.90 | -34.70 |
| single_residual | baseline_entry_hedge | all | 1.00 | 154 | 37 | -6.38 | -11.14 | -2.20 | -65.04 |
| single_residual | baseline_reference_hedge | development | 0.00 | 139 | 28 | -2.93 | -8.35 | 1.52 | 3.76 |
| single_residual | baseline_reference_hedge | development | 0.50 | 139 | 28 | -5.66 | -12.08 | -0.55 | -29.58 |
| single_residual | baseline_reference_hedge | development | 1.00 | 139 | 28 | -8.38 | -16.14 | -2.30 | -62.91 |
| single_residual | baseline_reference_hedge | later | 0.00 | 17 | 9 | -1.99 | -5.96 | 1.62 | -30.87 |
| single_residual | baseline_reference_hedge | later | 0.50 | 17 | 9 | -3.00 | -7.65 | 0.94 | -52.43 |
| single_residual | baseline_reference_hedge | later | 1.00 | 17 | 9 | -4.00 | -9.35 | 0.28 | -73.99 |
| single_residual | baseline_reference_hedge | all | 0.00 | 156 | 37 | -2.52 | -5.87 | 0.55 | -4.67 |
| single_residual | baseline_reference_hedge | all | 0.50 | 156 | 37 | -4.50 | -8.51 | -0.91 | -35.14 |
| single_residual | baseline_reference_hedge | all | 1.00 | 156 | 37 | -6.48 | -11.30 | -2.23 | -65.61 |
| vertical_relative_value | adjusted | development | 0.00 | 4 | 4 | -0.27 | -0.74 | 0.06 | -13.23 |
| vertical_relative_value | adjusted | development | 0.50 | 4 | 4 | -0.35 | -0.94 | 0.04 | -14.91 |
| vertical_relative_value | adjusted | development | 1.00 | 4 | 4 | -0.43 | -1.14 | 0.03 | -16.59 |
| vertical_relative_value | adjusted | all | 0.00 | 4 | 4 | -0.15 | -0.41 | 0.03 | -13.23 |
| vertical_relative_value | adjusted | all | 0.50 | 4 | 4 | -0.20 | -0.52 | 0.03 | -14.91 |
| vertical_relative_value | adjusted | all | 1.00 | 4 | 4 | -0.24 | -0.64 | 0.02 | -16.59 |
| vertical_relative_value | adjusted_entry_hedge | development | 0.00 | 4 | 4 | -0.32 | -0.71 | -0.03 | -14.48 |
| vertical_relative_value | adjusted_entry_hedge | development | 0.50 | 4 | 4 | -0.40 | -0.91 | -0.04 | -16.16 |
| vertical_relative_value | adjusted_entry_hedge | development | 1.00 | 4 | 4 | -0.47 | -1.12 | -0.05 | -17.84 |
| vertical_relative_value | adjusted_entry_hedge | all | 0.00 | 4 | 4 | -0.18 | -0.40 | -0.02 | -14.48 |
| vertical_relative_value | adjusted_entry_hedge | all | 0.50 | 4 | 4 | -0.22 | -0.51 | -0.02 | -16.16 |
| vertical_relative_value | adjusted_entry_hedge | all | 1.00 | 4 | 4 | -0.27 | -0.62 | -0.03 | -17.84 |
| vertical_relative_value | adjusted_reference_hedge | development | 0.00 | 4 | 4 | -0.31 | -0.69 | -0.04 | -14.02 |
| vertical_relative_value | adjusted_reference_hedge | development | 0.50 | 4 | 4 | -0.39 | -0.89 | -0.05 | -15.71 |
| vertical_relative_value | adjusted_reference_hedge | development | 1.00 | 4 | 4 | -0.47 | -1.10 | -0.06 | -17.39 |
| vertical_relative_value | adjusted_reference_hedge | all | 0.00 | 4 | 4 | -0.17 | -0.38 | -0.02 | -14.02 |
| vertical_relative_value | adjusted_reference_hedge | all | 0.50 | 4 | 4 | -0.22 | -0.49 | -0.03 | -15.71 |
| vertical_relative_value | adjusted_reference_hedge | all | 1.00 | 4 | 4 | -0.26 | -0.61 | -0.03 | -17.39 |
| vertical_relative_value | baseline | development | 0.00 | 39 | 39 | -2.51 | -6.65 | 1.32 | -11.16 |
| vertical_relative_value | baseline | development | 0.50 | 39 | 39 | -6.38 | -11.43 | -1.81 | -28.66 |
| vertical_relative_value | baseline | development | 1.00 | 39 | 39 | -10.25 | -16.61 | -4.45 | -46.15 |
| vertical_relative_value | baseline | later | 0.00 | 14 | 14 | 1.79 | -4.09 | 9.93 | -0.23 |
| vertical_relative_value | baseline | later | 0.50 | 14 | 14 | -0.08 | -5.94 | 7.60 | -12.35 |
| vertical_relative_value | baseline | later | 1.00 | 14 | 14 | -1.96 | -8.22 | 5.34 | -24.47 |
| vertical_relative_value | baseline | all | 0.00 | 53 | 53 | -0.64 | -4.15 | 3.56 | -8.27 |
| vertical_relative_value | baseline | all | 0.50 | 53 | 53 | -3.64 | -7.51 | 0.76 | -24.35 |
| vertical_relative_value | baseline | all | 1.00 | 53 | 53 | -6.64 | -11.16 | -1.94 | -40.43 |
| vertical_relative_value | baseline_entry_hedge | development | 0.00 | 39 | 39 | -1.96 | -5.25 | 1.40 | -9.99 |
| vertical_relative_value | baseline_entry_hedge | development | 0.50 | 39 | 39 | -5.83 | -10.10 | -1.76 | -27.49 |
| vertical_relative_value | baseline_entry_hedge | development | 1.00 | 39 | 39 | -9.70 | -15.35 | -4.39 | -44.98 |
| vertical_relative_value | baseline_entry_hedge | later | 0.00 | 14 | 14 | 1.29 | -2.67 | 6.29 | 1.91 |
| vertical_relative_value | baseline_entry_hedge | later | 0.50 | 14 | 14 | -0.58 | -4.64 | 4.06 | -10.21 |
| vertical_relative_value | baseline_entry_hedge | later | 1.00 | 14 | 14 | -2.46 | -6.97 | 2.02 | -22.33 |
| vertical_relative_value | baseline_entry_hedge | all | 0.00 | 53 | 53 | -0.54 | -3.06 | 2.34 | -6.85 |
| vertical_relative_value | baseline_entry_hedge | all | 0.50 | 53 | 53 | -3.54 | -6.50 | -0.44 | -22.92 |
| vertical_relative_value | baseline_entry_hedge | all | 1.00 | 53 | 53 | -6.55 | -10.37 | -2.90 | -39.00 |
| vertical_relative_value | baseline_reference_hedge | development | 0.00 | 39 | 39 | -2.15 | -5.60 | 1.29 | -10.43 |
| vertical_relative_value | baseline_reference_hedge | development | 0.50 | 39 | 39 | -6.02 | -10.53 | -1.83 | -27.93 |
| vertical_relative_value | baseline_reference_hedge | development | 1.00 | 39 | 39 | -9.89 | -15.82 | -4.42 | -45.42 |
| vertical_relative_value | baseline_reference_hedge | later | 0.00 | 14 | 14 | 1.24 | -2.64 | 6.27 | 1.00 |
| vertical_relative_value | baseline_reference_hedge | later | 0.50 | 14 | 14 | -0.63 | -4.61 | 3.98 | -11.12 |
| vertical_relative_value | baseline_reference_hedge | later | 1.00 | 14 | 14 | -2.51 | -6.95 | 2.00 | -23.23 |
| vertical_relative_value | baseline_reference_hedge | all | 0.00 | 53 | 53 | -0.67 | -3.22 | 2.28 | -7.41 |
| vertical_relative_value | baseline_reference_hedge | all | 0.50 | 53 | 53 | -3.68 | -6.74 | -0.51 | -23.49 |
| vertical_relative_value | baseline_reference_hedge | all | 1.00 | 53 | 53 | -6.68 | -10.58 | -3.01 | -39.56 |

## Long/short, stock versus option contributions, full bid–ask crossing

| family | version | period | fill | dimension | label | trades | events | option_bp | hedge_bp | fees_bp | spread_bp | net_bp |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| calendar_relative_value | adjusted | all | 1 | side | pair | 5 | 5 | 4.08 | -4.91 | 0.28 | 4.05 | -5.17 |
| calendar_relative_value | adjusted_entry_hedge | all | 1 | side | pair | 5 | 5 | 4.08 | -5.89 | 0.29 | 4.05 | -6.16 |
| calendar_relative_value | adjusted_reference_hedge | all | 1 | side | pair | 5 | 5 | 4.08 | -5.48 | 0.29 | 4.05 | -5.75 |
| calendar_relative_value | baseline | all | 1 | side | pair | 63 | 63 | 0.58 | -1.53 | 0.46 | 14.40 | -15.81 |
| calendar_relative_value | baseline_entry_hedge | all | 1 | side | pair | 61 | 61 | 0.62 | -1.52 | 0.46 | 13.36 | -14.72 |
| calendar_relative_value | baseline_reference_hedge | all | 1 | side | pair | 63 | 63 | 0.58 | -1.96 | 0.46 | 14.40 | -16.24 |
| entry_limits | baseline | all | 1 | side | long | 57 | 22 | -30.57 | 21.85 | 0.61 | 24.47 | -33.80 |
| entry_limits | baseline | all | 1 | side | short | 99 | 24 | 4.75 | 0.83 | 0.48 | 24.40 | -19.29 |
| entry_limits | limit_liquid | all | 1 | side | long | 7 | 2 | -15.28 | 41.03 | 0.26 | 1.32 | 24.17 |
| entry_limits | limit_only | all | 1 | side | long | 23 | 9 | -11.64 | 26.31 | 0.37 | 16.84 | -2.54 |
| entry_limits | limit_only | all | 1 | side | short | 12 | 4 | -4.21 | 19.01 | 0.41 | 18.88 | -4.49 |
| historical_variance | adjusted | all | 1 | side | long | 24 | 24 | -9.34 | 0.82 | 0.37 | 2.49 | -11.38 |
| historical_variance | adjusted | all | 1 | side | short | 87 | 87 | 24.30 | -7.69 | 0.37 | 5.22 | 11.02 |
| historical_variance | adjusted_entry_hedge | all | 1 | side | long | 24 | 24 | -9.34 | -0.18 | 0.40 | 2.49 | -12.41 |
| historical_variance | adjusted_entry_hedge | all | 1 | side | short | 87 | 87 | 24.30 | -5.59 | 0.47 | 5.22 | 13.03 |
| historical_variance | adjusted_entry_hedge_short_only | all | 1 | side | short | 87 | 87 | 24.30 | -5.59 | 0.47 | 5.22 | 13.03 |
| historical_variance | adjusted_reference_hedge | all | 1 | side | long | 24 | 24 | -9.34 | 0.14 | 0.40 | 2.49 | -12.09 |
| historical_variance | adjusted_reference_hedge | all | 1 | side | short | 87 | 87 | 24.30 | -5.65 | 0.47 | 5.22 | 12.97 |
| historical_variance | adjusted_reference_hedge_short_only | all | 1 | side | short | 87 | 87 | 24.30 | -5.65 | 0.47 | 5.22 | 12.97 |
| historical_variance | adjusted_short_only | all | 1 | side | short | 87 | 87 | 24.30 | -7.69 | 0.37 | 5.22 | 11.02 |
| historical_variance | baseline | all | 1 | side | long | 25 | 25 | -33.62 | -11.51 | 2.14 | 11.30 | -58.56 |
| historical_variance | baseline | all | 1 | side | short | 94 | 94 | 43.05 | -13.42 | 0.73 | 11.95 | 16.96 |
| historical_variance | baseline_entry_hedge | all | 1 | side | long | 25 | 25 | -33.62 | -13.20 | 2.28 | 11.30 | -60.40 |
| historical_variance | baseline_entry_hedge | all | 1 | side | short | 94 | 94 | 43.05 | -9.13 | 0.95 | 11.95 | 21.03 |
| historical_variance | baseline_reference_hedge | all | 1 | side | long | 25 | 25 | -33.62 | -12.48 | 2.28 | 11.30 | -59.68 |
| historical_variance | baseline_reference_hedge | all | 1 | side | short | 94 | 94 | 43.05 | -9.15 | 0.95 | 11.95 | 21.00 |
| historical_variance | regime_both | all | 1 | side | short | 64 | 64 | 18.97 | -5.50 | 0.44 | 5.00 | 8.03 |
| historical_variance | regime_drawdown | all | 1 | side | short | 76 | 76 | 21.91 | -4.05 | 0.44 | 5.37 | 12.05 |
| historical_variance | regime_volatility | all | 1 | side | short | 70 | 70 | 25.41 | -8.76 | 0.46 | 4.85 | 11.34 |
| protected_earnings | ironfly_10 | all | 1 | side | pair | 91 | 91 | 12.33 | -4.98 | 1.19 | 17.70 | -11.53 |
| protected_earnings | ironfly_10_cost_budget | all | 1 | side | pair | 89 | 89 | 12.98 | -4.11 | 1.19 | 16.06 | -8.38 |
| protected_earnings | ironfly_5 | all | 1 | side | pair | 91 | 91 | 9.50 | -5.34 | 1.19 | 19.36 | -16.39 |
| protected_earnings | ironfly_5_cost_budget | all | 1 | side | pair | 88 | 88 | 10.82 | -5.17 | 1.20 | 17.20 | -12.75 |
| protected_earnings | naked_straddle | all | 1 | side | short | 94 | 94 | 43.05 | -13.42 | 0.73 | 11.95 | 16.96 |
| single_residual | adjusted | all | 1 | side | long | 40 | 18 | -25.68 | -13.20 | 0.66 | 2.80 | -42.34 |
| single_residual | adjusted | all | 1 | side | short | 16 | 6 | 57.61 | -32.95 | 0.61 | 4.40 | 19.64 |
| single_residual | adjusted_entry_hedge | all | 1 | side | long | 40 | 18 | -25.68 | -14.49 | 0.70 | 2.80 | -43.67 |
| single_residual | adjusted_entry_hedge | all | 1 | side | short | 16 | 6 | 57.61 | -29.20 | 0.62 | 4.40 | 23.38 |
| single_residual | adjusted_reference_hedge | all | 1 | side | long | 40 | 18 | -25.68 | -14.31 | 0.72 | 2.80 | -43.50 |
| single_residual | adjusted_reference_hedge | all | 1 | side | short | 16 | 6 | 57.61 | -28.99 | 0.62 | 4.40 | 23.60 |
| single_residual | baseline | all | 1 | side | long | 57 | 22 | -30.57 | 27.14 | 0.59 | 24.47 | -28.49 |
| single_residual | baseline | all | 1 | side | short | 99 | 24 | 4.75 | -0.25 | 0.46 | 24.40 | -20.35 |
| single_residual | baseline_entry_hedge | all | 1 | side | long | 57 | 22 | -30.57 | 21.95 | 0.62 | 24.47 | -33.71 |
| single_residual | baseline_entry_hedge | all | 1 | side | short | 97 | 24 | 4.72 | 0.25 | 0.50 | 22.94 | -18.46 |
| single_residual | baseline_reference_hedge | all | 1 | side | long | 57 | 22 | -30.57 | 21.85 | 0.61 | 24.47 | -33.80 |
| single_residual | baseline_reference_hedge | all | 1 | side | short | 99 | 24 | 4.75 | 0.83 | 0.48 | 24.40 | -19.29 |
| vertical_relative_value | adjusted | all | 1 | side | pair | 4 | 4 | -11.96 | 5.84 | 0.38 | 3.77 | -10.27 |
| vertical_relative_value | adjusted_entry_hedge | all | 1 | side | pair | 4 | 4 | -11.96 | 4.77 | 0.43 | 3.77 | -11.39 |
| vertical_relative_value | adjusted_reference_hedge | all | 1 | side | pair | 4 | 4 | -11.96 | 4.98 | 0.44 | 3.77 | -11.18 |
| vertical_relative_value | baseline | all | 1 | side | pair | 53 | 53 | -0.57 | -0.72 | 0.74 | 19.26 | -21.30 |
| vertical_relative_value | baseline_entry_hedge | all | 1 | side | pair | 53 | 53 | -0.57 | -0.41 | 0.75 | 19.26 | -21.00 |
| vertical_relative_value | baseline_reference_hedge | all | 1 | side | pair | 53 | 53 | -0.57 | -0.83 | 0.76 | 19.26 | -21.43 |

## Per-year full-crossing diagnosis

| family | version | label | trades | option_bp | hedge_bp | fees_bp | spread_bp | net_bp |
|---|---|---|---|---|---|---|---|---|
| calendar_relative_value | adjusted | 2019 | 1 | -1.22 | -3.55 | 0.12 | 0.77 | -5.66 |
| calendar_relative_value | adjusted | 2021 | 3 | 4.10 | -6.79 | 0.18 | 1.93 | -4.79 |
| calendar_relative_value | adjusted | 2024 | 1 | 9.29 | -0.62 | 0.73 | 13.72 | -5.78 |
| calendar_relative_value | adjusted_entry_hedge | 2019 | 1 | -1.22 | -2.97 | 0.11 | 0.77 | -5.07 |
| calendar_relative_value | adjusted_entry_hedge | 2021 | 3 | 4.10 | -6.39 | 0.18 | 1.93 | -4.40 |
| calendar_relative_value | adjusted_entry_hedge | 2024 | 1 | 9.29 | -7.31 | 0.77 | 13.72 | -12.52 |
| calendar_relative_value | adjusted_reference_hedge | 2019 | 1 | -1.22 | -3.33 | 0.12 | 0.77 | -5.44 |
| calendar_relative_value | adjusted_reference_hedge | 2021 | 3 | 4.10 | -5.67 | 0.18 | 1.93 | -3.67 |
| calendar_relative_value | adjusted_reference_hedge | 2024 | 1 | 9.29 | -7.06 | 0.77 | 13.72 | -12.27 |
| calendar_relative_value | baseline | 2016 | 1 | -1.22 | 5.44 | 0.18 | 1.82 | 2.21 |
| calendar_relative_value | baseline | 2017 | 6 | 2.44 | -0.87 | 0.32 | 7.25 | -6.00 |
| calendar_relative_value | baseline | 2018 | 6 | 5.20 | -3.29 | 0.36 | 4.78 | -3.23 |
| calendar_relative_value | baseline | 2019 | 9 | -0.95 | -1.16 | 0.33 | 4.54 | -6.97 |
| calendar_relative_value | baseline | 2020 | 8 | -8.09 | 0.16 | 0.76 | 44.61 | -53.30 |
| calendar_relative_value | baseline | 2021 | 13 | -0.19 | -0.20 | 0.52 | 10.64 | -11.54 |
| calendar_relative_value | baseline | 2022 | 3 | 4.83 | -22.94 | 0.35 | 16.98 | -35.45 |
| calendar_relative_value | baseline | 2024 | 11 | 1.66 | 0.04 | 0.52 | 13.80 | -12.62 |
| calendar_relative_value | baseline | 2025 | 6 | 5.85 | 0.52 | 0.35 | 15.74 | -9.72 |
| calendar_relative_value | baseline_entry_hedge | 2016 | 1 | -1.22 | 2.65 | 0.17 | 1.82 | -0.56 |
| calendar_relative_value | baseline_entry_hedge | 2017 | 6 | 2.44 | -0.58 | 0.32 | 7.25 | -5.71 |
| calendar_relative_value | baseline_entry_hedge | 2018 | 6 | 5.20 | -4.44 | 0.36 | 4.78 | -4.38 |
| calendar_relative_value | baseline_entry_hedge | 2019 | 9 | -0.95 | -0.77 | 0.32 | 4.54 | -6.58 |
| calendar_relative_value | baseline_entry_hedge | 2020 | 6 | -10.59 | 2.66 | 0.89 | 44.12 | -52.94 |
| calendar_relative_value | baseline_entry_hedge | 2021 | 13 | -0.19 | -0.97 | 0.51 | 10.64 | -12.31 |
| calendar_relative_value | baseline_entry_hedge | 2022 | 3 | 4.83 | -26.09 | 0.35 | 16.98 | -38.60 |
| calendar_relative_value | baseline_entry_hedge | 2024 | 11 | 1.66 | 1.26 | 0.53 | 13.80 | -11.41 |
| calendar_relative_value | baseline_entry_hedge | 2025 | 6 | 5.85 | 0.46 | 0.35 | 15.74 | -9.78 |
| calendar_relative_value | baseline_reference_hedge | 2016 | 1 | -1.22 | 3.63 | 0.17 | 1.82 | 0.41 |
| calendar_relative_value | baseline_reference_hedge | 2017 | 6 | 2.44 | -1.40 | 0.33 | 7.25 | -6.54 |
| calendar_relative_value | baseline_reference_hedge | 2018 | 6 | 5.20 | -5.05 | 0.37 | 4.78 | -5.00 |
| calendar_relative_value | baseline_reference_hedge | 2019 | 9 | -0.95 | -0.87 | 0.32 | 4.54 | -6.67 |
| calendar_relative_value | baseline_reference_hedge | 2020 | 8 | -8.09 | 1.22 | 0.76 | 44.61 | -52.25 |
| calendar_relative_value | baseline_reference_hedge | 2021 | 13 | -0.19 | -0.42 | 0.52 | 10.64 | -11.76 |
| calendar_relative_value | baseline_reference_hedge | 2022 | 3 | 4.83 | -27.16 | 0.35 | 16.98 | -39.66 |
| calendar_relative_value | baseline_reference_hedge | 2024 | 11 | 1.66 | -0.15 | 0.52 | 13.80 | -12.81 |
| calendar_relative_value | baseline_reference_hedge | 2025 | 6 | 5.85 | -0.35 | 0.35 | 15.74 | -10.59 |
| entry_limits | baseline | 2016 | 8 | -1.49 | -9.20 | 0.25 | 1.61 | -12.55 |
| entry_limits | baseline | 2017 | 25 | -1.06 | 2.40 | 0.26 | 5.29 | -4.21 |
| entry_limits | baseline | 2018 | 13 | 8.96 | 5.39 | 0.63 | 10.35 | 3.37 |
| entry_limits | baseline | 2019 | 6 | -1.32 | 2.86 | 0.29 | 6.08 | -4.84 |
| entry_limits | baseline | 2020 | 17 | -52.27 | 14.16 | 1.14 | 60.50 | -99.74 |
| entry_limits | baseline | 2021 | 70 | -4.15 | 13.77 | 0.49 | 30.19 | -21.05 |
| entry_limits | baseline | 2022 | 3 | 12.50 | -2.30 | 0.51 | 12.60 | -2.91 |
| entry_limits | baseline | 2024 | 2 | -79.12 | 31.59 | 1.01 | 13.07 | -61.61 |
| entry_limits | baseline | 2025 | 12 | -3.50 | -0.52 | 0.59 | 24.06 | -28.67 |
| entry_limits | limit_liquid | 2019 | 1 | -6.12 | -9.60 | 0.21 | 1.64 | -17.57 |
| entry_limits | limit_liquid | 2021 | 6 | -16.81 | 49.47 | 0.27 | 1.27 | 31.13 |
| entry_limits | limit_only | 2016 | 3 | -5.91 | -21.81 | 0.27 | 0.86 | -28.85 |
| entry_limits | limit_only | 2017 | 5 | 2.35 | 1.12 | 0.25 | 1.53 | 1.70 |
| entry_limits | limit_only | 2018 | 2 | -4.55 | -1.29 | 0.19 | 6.24 | -12.27 |
| entry_limits | limit_only | 2019 | 1 | -6.12 | -9.60 | 0.21 | 1.64 | -17.57 |
| entry_limits | limit_only | 2021 | 21 | -9.66 | 27.79 | 0.44 | 26.26 | -8.56 |
| entry_limits | limit_only | 2022 | 1 | -16.74 | 88.61 | 0.39 | 2.47 | 69.01 |
| entry_limits | limit_only | 2025 | 2 | -38.83 | 116.59 | 0.62 | 17.80 | 59.33 |
| historical_variance | adjusted | 2017 | 7 | -21.99 | -7.54 | 0.48 | 6.81 | -36.82 |
| historical_variance | adjusted | 2018 | 11 | 16.99 | -4.31 | 0.38 | 5.59 | 6.71 |
| historical_variance | adjusted | 2019 | 14 | 50.98 | -12.69 | 0.62 | 3.20 | 34.46 |
| historical_variance | adjusted | 2020 | 12 | 91.35 | -2.31 | 0.16 | 5.74 | 83.15 |
| historical_variance | adjusted | 2021 | 15 | -2.41 | -0.31 | 0.33 | 6.50 | -9.54 |
| historical_variance | adjusted | 2022 | 14 | -9.62 | -21.16 | 0.42 | 5.45 | -36.66 |
| historical_variance | adjusted | 2023 | 20 | -2.36 | 1.95 | 0.34 | 2.91 | -3.66 |
| historical_variance | adjusted | 2024 | 9 | 17.09 | -4.04 | 0.19 | 3.58 | 9.27 |
| historical_variance | adjusted | 2025 | 9 | 12.34 | -5.05 | 0.37 | 2.95 | 3.97 |
| historical_variance | adjusted_entry_hedge | 2017 | 7 | -21.99 | -1.89 | 0.53 | 6.81 | -31.22 |
| historical_variance | adjusted_entry_hedge | 2018 | 11 | 16.99 | -13.95 | 0.44 | 5.59 | -2.99 |
| historical_variance | adjusted_entry_hedge | 2019 | 14 | 50.98 | -19.64 | 0.72 | 3.20 | 27.42 |
| historical_variance | adjusted_entry_hedge | 2020 | 12 | 91.35 | -9.71 | 0.24 | 5.74 | 75.66 |
| historical_variance | adjusted_entry_hedge | 2021 | 15 | -2.41 | 13.57 | 0.40 | 6.50 | 4.27 |
| historical_variance | adjusted_entry_hedge | 2022 | 14 | -9.62 | -17.89 | 0.60 | 5.45 | -33.56 |
| historical_variance | adjusted_entry_hedge | 2023 | 20 | -2.36 | 5.50 | 0.43 | 2.91 | -0.20 |
| historical_variance | adjusted_entry_hedge | 2024 | 9 | 17.09 | -0.96 | 0.22 | 3.58 | 12.32 |
| historical_variance | adjusted_entry_hedge | 2025 | 9 | 12.34 | 1.47 | 0.41 | 2.95 | 10.45 |
| historical_variance | adjusted_entry_hedge_short_only | 2017 | 4 | -11.34 | 1.29 | 0.53 | 10.66 | -21.24 |
| historical_variance | adjusted_entry_hedge_short_only | 2018 | 9 | 18.09 | -12.84 | 0.31 | 5.29 | -0.35 |
| historical_variance | adjusted_entry_hedge_short_only | 2019 | 10 | 85.65 | -27.01 | 0.61 | 3.87 | 54.18 |
| historical_variance | adjusted_entry_hedge_short_only | 2020 | 12 | 91.35 | -9.71 | 0.24 | 5.74 | 75.66 |
| historical_variance | adjusted_entry_hedge_short_only | 2021 | 14 | 1.45 | 14.59 | 0.42 | 6.81 | 8.81 |
| historical_variance | adjusted_entry_hedge_short_only | 2022 | 13 | -14.43 | -17.28 | 0.63 | 5.76 | -38.10 |
| historical_variance | adjusted_entry_hedge_short_only | 2023 | 11 | 2.63 | 3.55 | 0.67 | 3.20 | 2.31 |
| historical_variance | adjusted_entry_hedge_short_only | 2024 | 6 | 7.78 | -1.43 | 0.27 | 4.13 | 1.95 |
| historical_variance | adjusted_entry_hedge_short_only | 2025 | 8 | 16.92 | 0.07 | 0.44 | 3.24 | 13.32 |
| historical_variance | adjusted_reference_hedge | 2017 | 7 | -21.99 | -1.50 | 0.53 | 6.81 | -30.83 |
| historical_variance | adjusted_reference_hedge | 2018 | 11 | 16.99 | -13.92 | 0.44 | 5.59 | -2.97 |
| historical_variance | adjusted_reference_hedge | 2019 | 14 | 50.98 | -19.51 | 0.72 | 3.20 | 27.55 |
| historical_variance | adjusted_reference_hedge | 2020 | 12 | 91.35 | -9.91 | 0.24 | 5.74 | 75.46 |
| historical_variance | adjusted_reference_hedge | 2021 | 15 | -2.41 | 13.62 | 0.40 | 6.50 | 4.31 |
| historical_variance | adjusted_reference_hedge | 2022 | 14 | -9.62 | -18.38 | 0.59 | 5.45 | -34.04 |
| historical_variance | adjusted_reference_hedge | 2023 | 20 | -2.36 | 5.96 | 0.43 | 2.91 | 0.26 |
| historical_variance | adjusted_reference_hedge | 2024 | 9 | 17.09 | -1.30 | 0.22 | 3.58 | 11.99 |
| historical_variance | adjusted_reference_hedge | 2025 | 9 | 12.34 | 1.46 | 0.41 | 2.95 | 10.44 |
| historical_variance | adjusted_reference_hedge_short_only | 2017 | 4 | -11.34 | 2.00 | 0.53 | 10.66 | -20.53 |
| historical_variance | adjusted_reference_hedge_short_only | 2018 | 9 | 18.09 | -12.95 | 0.31 | 5.29 | -0.47 |
| historical_variance | adjusted_reference_hedge_short_only | 2019 | 10 | 85.65 | -26.82 | 0.61 | 3.87 | 54.36 |
| historical_variance | adjusted_reference_hedge_short_only | 2020 | 12 | 91.35 | -9.91 | 0.24 | 5.74 | 75.46 |
| historical_variance | adjusted_reference_hedge_short_only | 2021 | 14 | 1.45 | 14.64 | 0.42 | 6.81 | 8.87 |
| historical_variance | adjusted_reference_hedge_short_only | 2022 | 13 | -14.43 | -17.88 | 0.63 | 5.76 | -38.70 |
| historical_variance | adjusted_reference_hedge_short_only | 2023 | 11 | 2.63 | 4.06 | 0.67 | 3.20 | 2.82 |
| historical_variance | adjusted_reference_hedge_short_only | 2024 | 6 | 7.78 | -2.12 | 0.27 | 4.13 | 1.27 |
| historical_variance | adjusted_reference_hedge_short_only | 2025 | 8 | 16.92 | -0.06 | 0.44 | 3.24 | 13.19 |
| historical_variance | adjusted_short_only | 2017 | 4 | -11.34 | -10.49 | 0.45 | 10.66 | -32.94 |
| historical_variance | adjusted_short_only | 2018 | 9 | 18.09 | -4.48 | 0.23 | 5.29 | 8.08 |
| historical_variance | adjusted_short_only | 2019 | 10 | 85.65 | -18.03 | 0.50 | 3.87 | 63.26 |
| historical_variance | adjusted_short_only | 2020 | 12 | 91.35 | -2.31 | 0.16 | 5.74 | 83.15 |
| historical_variance | adjusted_short_only | 2021 | 14 | 1.45 | -0.34 | 0.34 | 6.81 | -6.04 |
| historical_variance | adjusted_short_only | 2022 | 13 | -14.43 | -20.41 | 0.45 | 5.76 | -41.05 |
| historical_variance | adjusted_short_only | 2023 | 11 | 2.63 | 0.25 | 0.54 | 3.20 | -0.86 |
| historical_variance | adjusted_short_only | 2024 | 6 | 7.78 | -8.55 | 0.24 | 4.13 | -5.13 |
| historical_variance | adjusted_short_only | 2025 | 8 | 16.92 | -7.52 | 0.40 | 3.24 | 5.77 |
| historical_variance | baseline | 2017 | 8 | -38.26 | -17.65 | 1.75 | 14.21 | -71.89 |
| historical_variance | baseline | 2018 | 13 | 7.03 | -25.11 | 1.54 | 15.50 | -35.12 |
| historical_variance | baseline | 2019 | 14 | 73.33 | -15.60 | 1.96 | 7.15 | 48.62 |
| historical_variance | baseline | 2020 | 14 | 172.94 | -2.99 | 0.34 | 15.12 | 154.49 |
| historical_variance | baseline | 2021 | 16 | 2.09 | -0.13 | 0.61 | 13.04 | -11.68 |
| historical_variance | baseline | 2022 | 16 | -7.34 | -48.55 | 0.85 | 12.92 | -69.66 |
| historical_variance | baseline | 2023 | 20 | -29.13 | 6.43 | 0.92 | 9.54 | -33.17 |
| historical_variance | baseline | 2024 | 9 | 56.15 | -10.22 | 0.59 | 11.46 | 33.89 |
| historical_variance | baseline | 2025 | 9 | 14.99 | -8.78 | 0.92 | 7.74 | -2.45 |
| historical_variance | baseline_entry_hedge | 2017 | 8 | -38.26 | -12.41 | 1.84 | 14.21 | -66.73 |
| historical_variance | baseline_entry_hedge | 2018 | 13 | 7.03 | -36.08 | 1.68 | 15.50 | -46.23 |
| historical_variance | baseline_entry_hedge | 2019 | 14 | 73.33 | -30.60 | 2.23 | 7.15 | 33.35 |
| historical_variance | baseline_entry_hedge | 2020 | 14 | 172.94 | -14.89 | 0.57 | 15.12 | 142.36 |
| historical_variance | baseline_entry_hedge | 2021 | 16 | 2.09 | 16.72 | 0.77 | 13.04 | 5.00 |
| historical_variance | baseline_entry_hedge | 2022 | 16 | -7.34 | -41.08 | 1.18 | 12.92 | -62.52 |
| historical_variance | baseline_entry_hedge | 2023 | 20 | -29.13 | 13.72 | 1.19 | 9.54 | -26.13 |
| historical_variance | baseline_entry_hedge | 2024 | 9 | 56.15 | 4.33 | 0.69 | 11.46 | 48.34 |
| historical_variance | baseline_entry_hedge | 2025 | 9 | 14.99 | 10.41 | 1.03 | 7.74 | 16.63 |
| historical_variance | baseline_reference_hedge | 2017 | 8 | -38.26 | -12.13 | 1.84 | 14.21 | -66.44 |
| historical_variance | baseline_reference_hedge | 2018 | 13 | 7.03 | -35.77 | 1.69 | 15.50 | -45.93 |
| historical_variance | baseline_reference_hedge | 2019 | 14 | 73.33 | -30.40 | 2.23 | 7.15 | 33.54 |
| historical_variance | baseline_reference_hedge | 2020 | 14 | 172.94 | -15.74 | 0.57 | 15.12 | 141.51 |
| historical_variance | baseline_reference_hedge | 2021 | 16 | 2.09 | 16.77 | 0.78 | 13.04 | 5.04 |
| historical_variance | baseline_reference_hedge | 2022 | 16 | -7.34 | -40.58 | 1.17 | 12.92 | -62.01 |
| historical_variance | baseline_reference_hedge | 2023 | 20 | -29.13 | 14.42 | 1.19 | 9.54 | -25.44 |
| historical_variance | baseline_reference_hedge | 2024 | 9 | 56.15 | 3.79 | 0.69 | 11.46 | 47.80 |
| historical_variance | baseline_reference_hedge | 2025 | 9 | 14.99 | 10.45 | 1.03 | 7.74 | 16.67 |
| historical_variance | regime_both | 2017 | 3 | -57.83 | 19.46 | 0.31 | 9.14 | -47.82 |
| historical_variance | regime_both | 2018 | 6 | 6.88 | -4.77 | 0.28 | 4.88 | -3.04 |
| historical_variance | regime_both | 2019 | 8 | 80.06 | -28.71 | 0.68 | 4.14 | 46.53 |
| historical_variance | regime_both | 2020 | 8 | 80.23 | -11.23 | 0.26 | 6.42 | 62.32 |
| historical_variance | regime_both | 2021 | 13 | 19.61 | 3.19 | 0.39 | 5.39 | 17.02 |
| historical_variance | regime_both | 2022 | 6 | -79.82 | 11.45 | 0.60 | 6.68 | -75.65 |
| historical_variance | regime_both | 2023 | 10 | 18.75 | -8.96 | 0.64 | 2.86 | 6.30 |
| historical_variance | regime_both | 2024 | 5 | 21.44 | -10.16 | 0.26 | 4.50 | 6.52 |
| historical_variance | regime_both | 2025 | 5 | -1.39 | -6.39 | 0.32 | 3.56 | -11.65 |
| historical_variance | regime_drawdown | 2017 | 4 | -11.34 | 2.00 | 0.53 | 10.66 | -20.53 |
| historical_variance | regime_drawdown | 2018 | 9 | 18.09 | -12.95 | 0.31 | 5.29 | -0.47 |
| historical_variance | regime_drawdown | 2019 | 9 | 85.44 | -29.81 | 0.66 | 4.06 | 50.91 |
| historical_variance | regime_drawdown | 2020 | 11 | 90.37 | -9.42 | 0.23 | 5.92 | 74.79 |
| historical_variance | regime_drawdown | 2021 | 14 | 1.45 | 14.64 | 0.42 | 6.81 | 8.87 |
| historical_variance | regime_drawdown | 2022 | 7 | -70.59 | 12.04 | 0.54 | 6.56 | -65.64 |
| historical_variance | regime_drawdown | 2023 | 10 | 18.75 | -8.96 | 0.64 | 2.86 | 6.30 |
| historical_variance | regime_drawdown | 2024 | 6 | 7.78 | -2.12 | 0.27 | 4.13 | 1.27 |
| historical_variance | regime_drawdown | 2025 | 6 | 4.05 | -2.38 | 0.44 | 3.58 | -2.34 |
| historical_variance | regime_volatility | 2017 | 3 | -57.83 | 19.46 | 0.31 | 9.14 | -47.82 |
| historical_variance | regime_volatility | 2018 | 6 | 6.88 | -4.77 | 0.28 | 4.88 | -3.04 |
| historical_variance | regime_volatility | 2019 | 9 | 80.90 | -25.51 | 0.62 | 3.91 | 50.85 |
| historical_variance | regime_volatility | 2020 | 9 | 82.67 | -11.68 | 0.27 | 6.13 | 64.60 |
| historical_variance | regime_volatility | 2021 | 13 | 19.61 | 3.19 | 0.39 | 5.39 | 17.02 |
| historical_variance | regime_volatility | 2022 | 9 | -14.02 | -21.46 | 0.77 | 5.72 | -41.97 |
| historical_variance | regime_volatility | 2023 | 10 | 18.75 | -8.96 | 0.64 | 2.86 | 6.30 |
| historical_variance | regime_volatility | 2024 | 5 | 21.44 | -10.16 | 0.26 | 4.50 | 6.52 |
| historical_variance | regime_volatility | 2025 | 6 | 2.51 | -2.68 | 0.35 | 3.29 | -3.82 |
| protected_earnings | ironfly_10 | 2017 | 5 | -15.10 | 16.06 | 1.23 | 27.60 | -27.87 |
| protected_earnings | ironfly_10 | 2018 | 10 | 16.47 | -12.34 | 0.70 | 21.67 | -18.24 |
| protected_earnings | ironfly_10 | 2019 | 9 | 91.91 | -19.27 | 1.12 | 8.85 | 62.67 |
| protected_earnings | ironfly_10 | 2020 | 14 | 48.52 | 4.28 | 0.42 | 24.09 | 28.30 |
| protected_earnings | ironfly_10 | 2021 | 15 | 7.67 | -7.31 | 1.14 | 19.70 | -20.49 |
| protected_earnings | ironfly_10 | 2022 | 13 | -20.05 | -16.65 | 1.28 | 19.50 | -57.47 |
| protected_earnings | ironfly_10 | 2023 | 11 | -14.27 | 6.98 | 2.46 | 9.98 | -19.73 |
| protected_earnings | ironfly_10 | 2024 | 6 | -16.59 | -1.31 | 0.98 | 14.36 | -33.25 |
| protected_earnings | ironfly_10 | 2025 | 8 | -8.94 | -4.88 | 1.54 | 11.80 | -27.16 |
| protected_earnings | ironfly_10_cost_budget | 2017 | 5 | -15.10 | 16.06 | 1.23 | 27.60 | -27.87 |
| protected_earnings | ironfly_10_cost_budget | 2018 | 9 | 23.87 | -4.14 | 0.65 | 15.13 | 3.94 |
| protected_earnings | ironfly_10_cost_budget | 2019 | 9 | 91.91 | -19.27 | 1.12 | 8.85 | 62.67 |
| protected_earnings | ironfly_10_cost_budget | 2020 | 13 | 50.92 | 4.69 | 0.38 | 18.15 | 37.08 |
| protected_earnings | ironfly_10_cost_budget | 2021 | 15 | 7.67 | -7.31 | 1.14 | 19.70 | -20.49 |
| protected_earnings | ironfly_10_cost_budget | 2022 | 13 | -20.05 | -16.65 | 1.28 | 19.50 | -57.47 |
| protected_earnings | ironfly_10_cost_budget | 2023 | 11 | -14.27 | 6.98 | 2.46 | 9.98 | -19.73 |
| protected_earnings | ironfly_10_cost_budget | 2024 | 6 | -16.59 | -1.31 | 0.98 | 14.36 | -33.25 |
| protected_earnings | ironfly_10_cost_budget | 2025 | 8 | -8.94 | -4.88 | 1.54 | 11.80 | -27.16 |
| protected_earnings | ironfly_5 | 2017 | 5 | 13.03 | -2.41 | 1.17 | 27.52 | -18.08 |
| protected_earnings | ironfly_5 | 2018 | 10 | 17.04 | -13.18 | 0.74 | 23.70 | -20.58 |
| protected_earnings | ironfly_5 | 2019 | 9 | 47.20 | -18.53 | 1.07 | 9.60 | 18.00 |
| protected_earnings | ironfly_5 | 2020 | 14 | 14.56 | 3.22 | 0.42 | 27.28 | -9.91 |
| protected_earnings | ironfly_5 | 2021 | 15 | 9.87 | -6.19 | 1.10 | 20.00 | -17.41 |
| protected_earnings | ironfly_5 | 2022 | 13 | 9.51 | -22.80 | 1.34 | 22.14 | -36.77 |
| protected_earnings | ironfly_5 | 2023 | 11 | -13.07 | 8.42 | 2.48 | 10.91 | -18.04 |
| protected_earnings | ironfly_5 | 2024 | 6 | -1.28 | -2.52 | 0.97 | 17.75 | -22.53 |
| protected_earnings | ironfly_5 | 2025 | 8 | -15.00 | 11.41 | 1.54 | 13.03 | -18.16 |
| protected_earnings | ironfly_5_cost_budget | 2017 | 5 | 13.03 | -2.41 | 1.17 | 27.52 | -18.08 |
| protected_earnings | ironfly_5_cost_budget | 2018 | 9 | 20.62 | -10.62 | 0.71 | 18.15 | -8.85 |
| protected_earnings | ironfly_5_cost_budget | 2019 | 9 | 47.20 | -18.53 | 1.07 | 9.60 | 18.00 |
| protected_earnings | ironfly_5_cost_budget | 2020 | 13 | 16.23 | 3.23 | 0.38 | 20.15 | -1.07 |
| protected_earnings | ironfly_5_cost_budget | 2021 | 14 | 15.22 | -6.74 | 1.15 | 17.56 | -10.23 |
| protected_earnings | ironfly_5_cost_budget | 2022 | 13 | 9.51 | -22.80 | 1.34 | 22.14 | -36.77 |
| protected_earnings | ironfly_5_cost_budget | 2023 | 11 | -13.07 | 8.42 | 2.48 | 10.91 | -18.04 |
| protected_earnings | ironfly_5_cost_budget | 2024 | 6 | -1.28 | -2.52 | 0.97 | 17.75 | -22.53 |
| protected_earnings | ironfly_5_cost_budget | 2025 | 8 | -15.00 | 11.41 | 1.54 | 13.03 | -18.16 |
| protected_earnings | naked_straddle | 2017 | 5 | -22.61 | -9.04 | 0.67 | 18.66 | -50.98 |
| protected_earnings | naked_straddle | 2018 | 10 | -15.29 | -13.50 | 0.44 | 13.94 | -43.18 |
| protected_earnings | naked_straddle | 2019 | 10 | 178.07 | -23.22 | 0.77 | 6.77 | 147.30 |
| protected_earnings | naked_straddle | 2020 | 14 | 172.94 | -2.99 | 0.34 | 15.12 | 154.49 |
| protected_earnings | naked_straddle | 2021 | 15 | 14.21 | -0.16 | 0.63 | 13.45 | -0.03 |
| protected_earnings | naked_straddle | 2022 | 15 | -36.15 | -35.25 | 0.84 | 12.98 | -85.22 |
| protected_earnings | naked_straddle | 2023 | 11 | 9.07 | 1.96 | 1.31 | 7.41 | 2.31 |
| protected_earnings | naked_straddle | 2024 | 6 | 19.85 | -27.70 | 0.65 | 10.99 | -19.49 |
| protected_earnings | naked_straddle | 2025 | 8 | 27.68 | -16.42 | 0.95 | 8.40 | 1.91 |
| single_residual | adjusted | 2018 | 2 | 9.64 | -23.05 | 0.31 | 4.60 | -18.32 |
| single_residual | adjusted | 2019 | 8 | 0.31 | -10.31 | 0.37 | 1.52 | -11.88 |
| single_residual | adjusted | 2020 | 4 | -26.40 | -91.05 | 1.27 | 8.29 | -127.01 |
| single_residual | adjusted | 2021 | 35 | -20.83 | 1.17 | 0.52 | 2.08 | -22.26 |
| single_residual | adjusted | 2022 | 1 | 23.21 | -68.98 | 0.29 | 0.96 | -47.01 |
| single_residual | adjusted | 2024 | 5 | 150.07 | -114.44 | 1.63 | 10.64 | 23.36 |
| single_residual | adjusted | 2025 | 1 | -66.03 | 37.61 | 0.93 | 1.03 | -30.39 |
| single_residual | adjusted_entry_hedge | 2018 | 2 | 9.64 | -26.87 | 0.31 | 4.60 | -22.14 |
| single_residual | adjusted_entry_hedge | 2019 | 8 | 0.31 | -11.85 | 0.40 | 1.52 | -13.45 |
| single_residual | adjusted_entry_hedge | 2020 | 4 | -26.40 | -85.33 | 1.20 | 8.29 | -121.21 |
| single_residual | adjusted_entry_hedge | 2021 | 35 | -20.83 | -0.21 | 0.57 | 2.08 | -23.70 |
| single_residual | adjusted_entry_hedge | 2022 | 1 | 23.21 | -53.61 | 0.23 | 0.96 | -31.59 |
| single_residual | adjusted_entry_hedge | 2024 | 5 | 150.07 | -106.10 | 1.61 | 10.64 | 31.72 |
| single_residual | adjusted_entry_hedge | 2025 | 1 | -66.03 | 34.55 | 0.90 | 1.03 | -33.42 |
| single_residual | adjusted_reference_hedge | 2018 | 2 | 9.64 | -27.76 | 0.32 | 4.60 | -23.04 |
| single_residual | adjusted_reference_hedge | 2019 | 8 | 0.31 | -12.17 | 0.40 | 1.52 | -13.78 |
| single_residual | adjusted_reference_hedge | 2020 | 4 | -26.40 | -85.75 | 1.21 | 8.29 | -121.64 |
| single_residual | adjusted_reference_hedge | 2021 | 35 | -20.83 | 0.19 | 0.59 | 2.08 | -23.31 |
| single_residual | adjusted_reference_hedge | 2022 | 1 | 23.21 | -50.66 | 0.22 | 0.96 | -28.64 |
| single_residual | adjusted_reference_hedge | 2024 | 5 | 150.07 | -106.48 | 1.61 | 10.64 | 31.34 |
| single_residual | adjusted_reference_hedge | 2025 | 1 | -66.03 | 36.08 | 0.92 | 1.03 | -31.91 |
| single_residual | baseline | 2016 | 8 | -1.49 | -8.34 | 0.25 | 1.61 | -11.70 |
| single_residual | baseline | 2017 | 25 | -1.06 | 2.08 | 0.25 | 5.29 | -4.52 |
| single_residual | baseline | 2018 | 13 | 8.96 | 4.45 | 0.59 | 10.35 | 2.46 |
| single_residual | baseline | 2019 | 6 | -1.32 | 3.24 | 0.31 | 6.08 | -4.48 |
| single_residual | baseline | 2020 | 17 | -52.27 | 15.68 | 1.02 | 60.50 | -98.11 |
| single_residual | baseline | 2021 | 70 | -4.15 | 14.02 | 0.48 | 30.19 | -20.79 |
| single_residual | baseline | 2022 | 3 | 12.50 | 28.24 | 0.48 | 12.60 | 27.66 |
| single_residual | baseline | 2024 | 2 | -79.12 | 36.08 | 1.05 | 13.07 | -57.16 |
| single_residual | baseline | 2025 | 12 | -3.50 | 4.57 | 0.55 | 24.06 | -23.54 |
| single_residual | baseline_entry_hedge | 2016 | 8 | -1.49 | -8.60 | 0.25 | 1.61 | -11.95 |
| single_residual | baseline_entry_hedge | 2017 | 25 | -1.06 | 3.32 | 0.28 | 5.29 | -3.30 |
| single_residual | baseline_entry_hedge | 2018 | 13 | 8.96 | 4.86 | 0.63 | 10.35 | 2.84 |
| single_residual | baseline_entry_hedge | 2019 | 6 | -1.32 | 2.28 | 0.30 | 6.08 | -5.42 |
| single_residual | baseline_entry_hedge | 2020 | 16 | -54.75 | 15.09 | 1.20 | 59.09 | -99.96 |
| single_residual | baseline_entry_hedge | 2021 | 69 | -4.57 | 12.84 | 0.51 | 29.06 | -21.31 |
| single_residual | baseline_entry_hedge | 2022 | 3 | 12.50 | -1.52 | 0.50 | 12.60 | -2.13 |
| single_residual | baseline_entry_hedge | 2024 | 2 | -79.12 | 33.17 | 1.01 | 13.07 | -60.03 |
| single_residual | baseline_entry_hedge | 2025 | 12 | -3.50 | -0.40 | 0.59 | 24.06 | -28.55 |
| single_residual | baseline_reference_hedge | 2016 | 8 | -1.49 | -9.20 | 0.25 | 1.61 | -12.55 |
| single_residual | baseline_reference_hedge | 2017 | 25 | -1.06 | 2.40 | 0.26 | 5.29 | -4.21 |
| single_residual | baseline_reference_hedge | 2018 | 13 | 8.96 | 5.39 | 0.63 | 10.35 | 3.37 |
| single_residual | baseline_reference_hedge | 2019 | 6 | -1.32 | 2.86 | 0.29 | 6.08 | -4.84 |
| single_residual | baseline_reference_hedge | 2020 | 17 | -52.27 | 14.16 | 1.14 | 60.50 | -99.74 |
| single_residual | baseline_reference_hedge | 2021 | 70 | -4.15 | 13.77 | 0.49 | 30.19 | -21.05 |
| single_residual | baseline_reference_hedge | 2022 | 3 | 12.50 | -2.30 | 0.51 | 12.60 | -2.91 |
| single_residual | baseline_reference_hedge | 2024 | 2 | -79.12 | 31.59 | 1.01 | 13.07 | -61.61 |
| single_residual | baseline_reference_hedge | 2025 | 12 | -3.50 | -0.52 | 0.59 | 24.06 | -28.67 |
| vertical_relative_value | adjusted | 2019 | 1 | -6.44 | -0.50 | 0.15 | 0.90 | -7.99 |
| vertical_relative_value | adjusted | 2020 | 1 | -41.48 | 26.95 | 0.79 | 10.68 | -26.01 |
| vertical_relative_value | adjusted | 2021 | 2 | 0.05 | -1.55 | 0.29 | 1.75 | -3.55 |
| vertical_relative_value | adjusted_entry_hedge | 2019 | 1 | -6.44 | -0.60 | 0.17 | 0.90 | -8.10 |
| vertical_relative_value | adjusted_entry_hedge | 2020 | 1 | -41.48 | 30.05 | 0.84 | 10.68 | -22.96 |
| vertical_relative_value | adjusted_entry_hedge | 2021 | 2 | 0.05 | -5.18 | 0.35 | 1.75 | -7.24 |
| vertical_relative_value | adjusted_reference_hedge | 2019 | 1 | -6.44 | -0.59 | 0.17 | 0.90 | -8.09 |
| vertical_relative_value | adjusted_reference_hedge | 2020 | 1 | -41.48 | 30.28 | 0.85 | 10.68 | -22.73 |
| vertical_relative_value | adjusted_reference_hedge | 2021 | 2 | 0.05 | -4.89 | 0.36 | 1.75 | -6.95 |
| vertical_relative_value | baseline | 2016 | 1 | 2.36 | 21.63 | 0.27 | 1.34 | 22.37 |
| vertical_relative_value | baseline | 2017 | 5 | 32.37 | -24.01 | 0.47 | 7.09 | 0.81 |
| vertical_relative_value | baseline | 2018 | 8 | -3.70 | 2.98 | 1.10 | 13.43 | -15.26 |
| vertical_relative_value | baseline | 2019 | 7 | -41.97 | 31.82 | 0.98 | 12.34 | -23.46 |
| vertical_relative_value | baseline | 2020 | 7 | -16.42 | 2.21 | 1.01 | 46.37 | -61.59 |
| vertical_relative_value | baseline | 2021 | 11 | -15.95 | 6.93 | 0.51 | 17.10 | -26.64 |
| vertical_relative_value | baseline | 2022 | 3 | 101.20 | -49.53 | 0.44 | 14.28 | 36.94 |
| vertical_relative_value | baseline | 2024 | 7 | 29.72 | -23.12 | 0.66 | 15.35 | -9.41 |
| vertical_relative_value | baseline | 2025 | 4 | -23.10 | 8.07 | 0.58 | 31.83 | -47.45 |
| vertical_relative_value | baseline_entry_hedge | 2016 | 1 | 2.36 | 25.13 | 0.29 | 1.34 | 25.85 |
| vertical_relative_value | baseline_entry_hedge | 2017 | 5 | 32.37 | -23.92 | 0.46 | 7.09 | 0.90 |
| vertical_relative_value | baseline_entry_hedge | 2018 | 8 | -3.70 | 3.20 | 1.10 | 13.43 | -15.04 |
| vertical_relative_value | baseline_entry_hedge | 2019 | 7 | -41.97 | 32.42 | 0.97 | 12.34 | -22.86 |
| vertical_relative_value | baseline_entry_hedge | 2020 | 7 | -16.42 | 5.21 | 1.07 | 46.37 | -58.65 |
| vertical_relative_value | baseline_entry_hedge | 2021 | 11 | -15.95 | 8.98 | 0.52 | 17.10 | -24.60 |
| vertical_relative_value | baseline_entry_hedge | 2022 | 3 | 101.20 | -70.91 | 0.50 | 14.28 | 15.50 |
| vertical_relative_value | baseline_entry_hedge | 2024 | 7 | 29.72 | -21.85 | 0.66 | 15.35 | -8.15 |
| vertical_relative_value | baseline_entry_hedge | 2025 | 4 | -23.10 | 12.65 | 0.59 | 31.83 | -42.88 |
| vertical_relative_value | baseline_reference_hedge | 2016 | 1 | 2.36 | 24.03 | 0.29 | 1.34 | 24.76 |
| vertical_relative_value | baseline_reference_hedge | 2017 | 5 | 32.37 | -24.62 | 0.47 | 7.09 | 0.20 |
| vertical_relative_value | baseline_reference_hedge | 2018 | 8 | -3.70 | 3.35 | 1.10 | 13.43 | -14.90 |
| vertical_relative_value | baseline_reference_hedge | 2019 | 7 | -41.97 | 31.97 | 0.97 | 12.34 | -23.31 |
| vertical_relative_value | baseline_reference_hedge | 2020 | 7 | -16.42 | 2.95 | 1.06 | 46.37 | -60.90 |
| vertical_relative_value | baseline_reference_hedge | 2021 | 11 | -15.95 | 9.32 | 0.53 | 17.10 | -24.27 |
| vertical_relative_value | baseline_reference_hedge | 2022 | 3 | 101.20 | -69.82 | 0.50 | 14.28 | 16.59 |
| vertical_relative_value | baseline_reference_hedge | 2024 | 7 | 29.72 | -23.02 | 0.66 | 15.35 | -9.31 |
| vertical_relative_value | baseline_reference_hedge | 2025 | 4 | -23.10 | 12.95 | 0.59 | 31.83 | -42.57 |

Full summaries include no-stock-hedge comparisons and asymmetric entry/exit fills. Trade selection never uses exit spreads or future P&L. One unresolved source candidate is retained; it has not qualified in these strategy selections. These fills do not model queues, adverse selection, latency, funding, borrow, American exercise or assignment. No live orders were sent. No mathematically independent information is created by agreement between two market-interpolation methods.

Outputs: wrds_studies/strategy_iteration/{positions.pkl,enriched_candidates.pkl,summary.csv,diagnosis.csv,fill_sweep.csv,concentration.csv}. Source: research2/iterate_strategies.py. The individual positions and signal-time conditions are reproducible from cached quote data.


## Second and third diagnostic rounds

A separate hedge sensitivity replaces the stock delta calculated on the signal date with the delta observed at entry. Vendor OptionMetrics deltas are the first alternative (four strategy positions lack a usable vendor delta). A second alternative refreshes the original reference-IV method at entry, holding contract selection and option P&L fixed; all 567 baseline/adjusted positions have that reference hedge. The entry reference builder includes 1–100 DTE so contracts do not become unavailable merely by aging through the signal filter. It retains the same reference-strike split, quote-quality filters, eight-reference-per-expiry method and interpolation; it does not use exit information. These simultaneous closing hedge fills remain modeled execution, not guaranteed attainable prices.

For the 156 original 20% trades, the same-reference entry hedge changes midpoint premium-normalized performance from +25.99% to -4.67%. This is a strategy sensitivity, not a retroactive correction to the original intentionally fixed signal-date hedge. Both versions are retained. The original book is negative under equal signal-stock-notional normalization even at midpoint fills. Its top two premium-return events account for more than its total average gain.

The historical-variance development diagnosis favored shorts over longs, so adjusted short-only variants were tested with each hedge rule. They remained negative in the later comparison. A further risk-regime round tests recent 20-session realized variance / 252-session variance <= 1.5, a 60-session drawdown no worse than -20%, and both filters together. These factors use split-adjusted returns available by the signal date. All three fixed filters are reported rather than choosing the best later outcome. None turned the later crossed-quote mean positive. Better early-period averages therefore have not survived the time-separated comparison.

Entry-hedge comparisons, short-only gates and regime variants appear in the tables above. Missing entry deltas are reported as unavailable, not silently filled. The paired vendor comparison is additionally saved in hedge_paired_comparison.csv; regime inputs are in regime_factors.pkl. Retest sources are entry_hedge_retest.py, reference_hedge_retest.py, short_only_retest.py and regime_retest.py.

## Decision from this round

No robust executable edge is established. Partial-spread fills can preserve the old premium-normalized headline only under favorable assumptions: its symmetric break-even is about 42.6% of the full modeled crossing cost, and its fixed-exposure normalization is already negative at midpoint. Refreshed hedges, more liquid residual trades, paired relative-value trades, short-only selection, tail sizing and regime gates have all been evaluated rather than treating a single favorable average as the objective. Any positive subgroup remains an exploratory candidate, not a selected live strategy.
