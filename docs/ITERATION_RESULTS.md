# Trading iterations: results and diagnosis

This round tested seven strategy families, partial execution costs, hedge timing, liquidity and model-agreement gates, tail sizing, market regimes, entry limits, protective wings and an exit before earnings. It also expanded the pre-earnings test to different companies under a frozen rule. No robust after-cost trading edge was established. The clearest positive result was lower observed tail risk from protective wings, with a cost to average returns.

## Reassessing the original 20% signal

The original +25.99% was an event-average return divided by option premium, including a stock hedge. It was not an account or margin return. Two events with very large returns on small option premiums strongly influenced the mean. Removing those two events changes it to approximately -14.4%; that removal is a diagnosis, not a trading rule.

The same book was negative at midpoint under equal signal-stock-notional normalization. Keeping exactly the same 156 option trades and refreshing the same reference-IV delta method at entry instead of retaining the signal-date delta changes the premium-normalized midpoint mean from +25.99% to -4.67%. This is a different hedge rule, not a retroactive correction to the recorded original option P&L.

### Partial-spread sensitivity on the unchanged original book

| Fraction of adverse half-spread paid at both entry and exit | Premium-normalized mean |
|---|---:|
| 0%: midpoint at both ends | +25.99% |
| 25% | +10.75% |
| 50% | -4.48% |
| 75% | -19.72% |
| 100%: buy at ask, sell at bid | -34.96% |

The arithmetic break-even is approximately 42.6% of full modeled crossing cost. Midpoint entry/full-cross exit returns -1.14%; full-cross entry/midpoint exit returns -7.83%. Commissions and stock costs remain in these numbers. With an unchanged spread, buying at ask and later selling at bid costs one full quoted width relative to midpoint marks, not two full widths. Midpoint at both ends removes all modeled crossing cost. These are price scenarios, not observed passive fills or fill probabilities.

## Strategy, diagnosis, adjustment and retest

| Family | Where it lost or proved fragile | Adjustment tested | Retest finding |
|---|---|---|---|
| Single-option residual | Wide markets, small premium denominators, stock-hedge sensitivity | Signal spread/premium gates, model agreement, estimated cost coverage, refreshed entry deltas | Fewer trades and lower costs; no robust later-period gain |
| Vertical relative value | Opposite residuals did not cover two-leg costs reliably | Both legs liquid, agreement, gap covers estimated costs | Only four adjusted trades in the earlier period and none later; no confirmed opportunity |
| Calendar relative value | Little gross advantage and substantial spreads | Both-leg liquidity and cost coverage | Only one adjusted later trade, negative after full crossing |
| Historical versus implied variance | Long-side losses and unstable short performance across periods | Short-only rule, prior-tail sizing, entry hedge, recent-volatility and drawdown gates | Early-period positives did not survive the later comparison |
| Marketable entry limits | Signal-date valuation could be stale by entry | Require actual entry ask/bid to preserve the 20% gap; add liquidity/minimum premium gate | Positive later subset had only three trades across two events; stronger liquidity gate left no later trades |
| Protected short earnings volatility | Large earnings outliers on naked short straddles | Add nearest eligible 5%/10% put and call wings; test a signal cost budget | Substantial risk reduction, but no better average after costs; cost gate did not change the later sample |
| Pre-earnings convergence | Holding through the announcement mixed valuation signals with jump outcomes | Enter nine sessions before earnings, exit six before; liquidity/cost gates, entry limits, then reference-support guard | A small positive original-name subset did not transfer to additional companies |

## Protective wings: matched risk comparison

For 38 matched later-period events, the nearer-wing option book was compared with one naked short straddle at the same core-straddle stock-notional exposure, without a stock hedge. Adding wings was not allowed to mechanically halve exposure by doubling the denominator.

- Worst observed loss: approximately halved.
- Standard deviation of event returns: approximately 62% lower.
- Average net return: slightly worse, from -19.34 to -21.66 basis points of core-straddle stock notional.
- The farther-wing version also reduced dispersion but had a worse average.

This is a historical risk/cost comparison, not proof of optimal sizing. Wing strikes are the nearest eligible listed strikes to the specified distances, not always exactly 5% or 10%. The structures bound European expiry payoffs; daily liquidation prices, assignment, financing and account margin are not claimed to be bounded or fully modeled.

## Pre-earnings candidate and additional-company check

The initial pre-earnings panel used 2021–2024. The same fixed rules were expanded to 2016–2020 and 2025, producing 19,542 candidate contracts across 171 original-name earnings events. The 5% liquidity/cost rule produced nine later-period trades across seven events, with a positive crossed-quote mean. Its full original-name sample was negative, including the earlier years.

The rule was frozen before adding ADSK, BIIB, VRTX, NOW and ISRG. Their 2022–2025 panel contained 3,780 candidates across 62 usable events; distribution records showed no positive cash-distribution records over the tested period. The fixed primary rule produced four trades across three events. All four lost after costs. This additional-company check did not validate the apparent original-name opportunity.

Two VRTX trades were extrapolations: target strikes 395 and 405 against actual fitted reference strikes 450–510. A no-extrapolation guard was added and retested. It removed these two trades; the two remaining additional-company trades still lost. This adjustment used inspected data and is exploratory, not a second untouched validation.

The pre-earnings work therefore covers 233 company-earnings events across eleven names in two separate panels. Many events produce no qualifying trades. Neither the number of candidate options nor multiple strikes on one event should be counted as independent evidence.

## Detailed artifacts

- [Main strategy and execution tables](STRATEGY_ITERATION.md)
- [Expanded original-name pre-earnings test](PRE_EARNINGS_CONVERGENCE.md)
- [Frozen additional-company check](PRE_EARNINGS_NEW_NAMES.md)
- [Reference-support diagnosis and retest](REFERENCE_SUPPORT_RETEST.md)
- [Initial pre-earnings panel](PRE_EARNINGS_INITIAL.md)

Licensed quote data and trade ledgers remain under `wrds_studies`. Main outputs are in `strategy_iteration`, `pre_event_combined`, and `pre_event_new_names_combined`. Frozen rules and experiment scripts are in `research2`.

All results are historical quote-based scenarios. Actual announcement schedules as known beforehand, passive fill probabilities, depth, adverse selection, financing, borrow, margin and assignment are incomplete or unmodeled. Most panels have been inspected repeatedly; the additional-company rule was frozen before its results were pulled, but that is still historical research rather than prospective trading. No live orders were sent.
