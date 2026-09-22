# Results and experiment definitions

These results come from different experiments and normalizations. They should not be combined into a single portfolio return or a single validation sample.

| Result | Sample and definition | Source |
|---|---|---|
| 141,767 withheld option quotes | 118,117 in 2020 and 23,650 in 2025; target strikes and parity twins excluded from fitting | [Pricing metrics](final_metrics.json), [project report](PROJECT.md) |
| 27% lower structural pricing error | Calendar Heston MAE falls from 21.5433 to 15.8016 spot bp with scheduled jumps: 26.65%, rounded; 2020 development sample only | [Structural ablation](structural_ablation.json), `strategy_lab/ablation.py` |
| 69% lower conditional repricing error | 2025 equal-event MAE falls from 72.236 to 22.099 spot bp against unchanged strike IV; 14 events, observed later stock price supplied | [Pricing metrics](final_metrics.json), [project report](PROJECT.md#repricing-through-earnings) |
| 25.99% event-average premium-normalized return | 156 positions, 37 earnings events; original signal-date stock hedge, simulated midpoint fills, commissions and stock costs | [Trading iterations](ITERATION_RESULTS.md) |
| Lower observed risk with wings | 38 matched events at equal core-straddle stock-notional exposure; roughly half the worst observed loss and 62% lower return standard deviation | [Matched comparison](ITERATION_RESULTS.md#protective-wings-matched-risk-comparison) |

## Interpreting the trading result

The 25.99% statistic averages position returns within events, then weights the 37 events equally. It is not a compounded account or margin return. Full quoted crossing changes it to −34.96%; refreshing the reference-based hedge at entry changes the midpoint mean to −4.67%. Removing the two largest premium-return events changes the original mean to about −14.4%. Protective wings reduce observed risk but slightly worsen mean net return.

The hybrid prices neighboring contracts competitively but does not consistently beat the market-only smoother. Neither the trading experiment nor the pricing comparison establishes an executable forecasting edge.

## Current-quote screening

`trade_screen.assess_quote` checks reference-strike support, premium size, relative spread, directional model gap, and a cost buffer. Inputs must be from the same snapshot. It is a screening function, not a return forecast or execution model. `test_trade_screen.py` covers both trade directions, extrapolation, invalid quotes, and liquidity gates.

Raw quote histories and contract-level ledgers remain outside this repository. The numerical ablation artifact above contains only method-level aggregates.
