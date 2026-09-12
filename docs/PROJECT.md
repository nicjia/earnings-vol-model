# Final project: event-aware market pricing

The project produces usable European option prices from a small set of reference quotes, together with a structural model for earnings and ordinary volatility. Its strongest demonstrated result is **market-conditioned pricing accuracy**. It has not established a profitable trading strategy or a new mathematical pricing method.

## What was built

The original engine models ordinary returns as diffusion and an earnings release as a jump at a specified time. The jump is a Gaussian mixture, compensated so its expected multiplicative return is one under the pricing measure. With flat diffusion, option prices are weighted Black-76 prices. With Heston stochastic volatility, the characteristic functions are multiplied and priced by the Fourier-cosine method.

An optional variance clock distinguishes exchange sessions, overnight closures, weekends and holidays. Carry and discounting still use elapsed calendar time. Independent scheduled jumps combine through their characteristic functions; pricing does not require enumerating every combination of jump outcomes. The mixture components are not identified as EPS beats or misses, and pricing probabilities are not physical outcome probabilities.

The final market-pricing layer corrects the structural smile using reference quotes and fits a constrained cubic call-price curve. A second mode uses only a PCHIP market-IV prior. Both yield decreasing, convex call prices within an expiry, with put prices obtained through parity. They are implemented in `market_surface.py`; `demo_market_surface.py` is an offline working example.

## Pricing results

The historical calculations use reference quotes to infer forwards and fit the curve; prices at other strikes are then evaluated. Both put and call at a target strike are withheld. Up to eight reference quotes per expiry and five expiries are used, with the same references for competing methods.

| Sample | Structural hybrid MAE, spot bp | Inside bid–ask | Market-only MAE, spot bp | Inside bid–ask |
|---|---:|---:|---:|---:|
| 2020 development | 4.074 | 95.5% | 4.095 | 96.5% |
| 2025 historical confirmation | 4.849 | 87.0% | 4.811 | 89.7% |

The 2020 sample has 118,117 target quotes, 1,068 snapshots and six names: ADBE, AMD, AMZN, GOOGL, NFLX and TSLA. The 2025 sample has 23,650 quotes and 251 eligible snapshots across the same names except GOOGL, excluded because the non-dividend assumption no longer applies. Available 2025 history ends on August 29. The snapshots require sufficient usable references and identifiable structural calibration, so these are not all listed contracts or a market-wide sample.

In 2025, the hybrid's average absolute error was **$0.228 per option share** and the median was **$0.062**. For a standard 100-share contract those correspond to $22.80 and $6.20. These are aggregate errors, not a guarantee for any particular contract. PCHIP IV interpolation scored 4.855 spot bp and 88.9% inside bid–ask; the tested SSVI slice scored 5.676 bp and 73.5%. The hybrid is competitive with interpolation, not consistently superior to it. All recorded constrained expiry slices passed the implemented strike checks, but cross-expiry arbitrage was not eliminated.

This is a legitimate market-pricing task: other contracts supply the calibration information, while the target contract's price is withheld. It is not a forecast made without market quotes, a claim that the target price must converge to the model, or an estimate of a unique physical “true value.”

## Why the original structural fit struggled

The eight-component comparison separately enabled or disabled Heston, earnings jumps and the physical-return variance clock on identical data. Calendar-time flat diffusion had 31.06 spot-bp error; adding an earnings jump reduced it to 26.34; Heston plus the jump reached 15.80. Thus both stochastic volatility and the event component contributed, but the restricted structural surface still underperformed market interpolation.

Physical-clock Heston/jump error was 18.64 bp. It hit a parameter boundary on about 89% of snapshots. Widening parameter bounds and allowing more optimizer iterations lowered it to 14.91 bp, versus 14.06 with calendar time under the same wider settings. Restrictive calibration explains part of the gap. These findings do not imply that weekends have no variance; historical return-based clock ratios are not automatically the right risk-neutral weights.

The market-residual hybrid largely removes the snapshot fitting gap. Its extra structural information, however, did not produce a material advantage over the equivalent smoother using only market IV. The earlier unconstrained hybrid also introduced more strike inconsistencies; the final projection addresses those within each expiry.

## Repricing through earnings

A second use of the engine is to update option values once earnings uncertainty has resolved. The experiments refresh the current reference smile, estimate an event component, and remove that component after the release. They compare structural event effects, simple ATM term-structure variance estimates, a nearest-two-expiry estimate, and a strike-dependent event estimate.

The table below uses a fixed bracket from the close before the reported announcement date to the close after it. **Every method is supplied the later observed stock price.** This tests conditional option repricing, not prediction of the stock's earnings move. Earnings dates are retrospective; the two-session bracket avoids choosing the larger observed return day.

| Repricing method | 2020 equal-event MAE, spot bp | 2025 equal-event MAE, spot bp |
|---|---:|---:|
| Keep the initial strike's IV unchanged | 90.54 | 72.24 |
| Structural event price-impact adjustment | 54.09 | 22.10 |
| ATM term-structure event estimate | 38.68 | 21.66 |
| Nearest-two-expiry event estimate | 38.18 | 18.91 |
| Strike-dependent term-structure estimate | 37.56 | 23.87 |

The structural event adjustment reduced 2025 conditional error about **69%** relative to unchanged IV. A simpler two-expiry estimate did better. That supports accounting for event resolution, not superiority of the Heston/mixture decomposition. There are 18 development events and 14 later-year events. The 2025 panel had already been examined in earlier experiments, so this is a descriptive external-year comparison, not another untouched confirmation test. Forecast curves were not established to be free of all static or dynamic arbitrage.

## Trading and risk-management results

The strategy work covered individual-option convergence, same-event calendars, weekend/holiday calendars, butterfly shape, pre-earnings convergence, post-earnings repricing and separate day/overnight variance positions. The separate-session rules require actual opening option quotes and could not be evaluated empirically with the daily dataset.

For the original 2020 individual-option book, 203 closed trades averaged **−0.126%** net per gross option spot notional. Longs averaged −0.011%; shorts −0.210%. Calendar-time structural pricing changed the whole-book mean to +0.031% over 215 closed trades, but the result was unstable and its interval included zero. These are not returns on premium or margin capital, and the books must not be added together as a portfolio.

The original weekend book's 71 closed trades averaged +0.114% at option midpoints including the stock hedge, +0.096% when option spreads were removed but other costs retained, and **−0.021%** at quoted costs. The option legs contributed −0.034% before costs; the stock hedge contributed +0.148%. Removing the five best net trades made even the zero-option-spread result negative. A midpoint result therefore did not establish a market-making opportunity.

Event-matched option-plus-stock hedges initially looked much better than delta–vega hedges. A delta–gamma comparison explained most of the gain. Event matching reduced development hedge MSE by about 10.6% versus gamma matching, but only 0.6% in the separate 2025 comparison, with uncertainty spanning no improvement. Scenario-covariance hedges did not establish an advantage either. Reference-trained empirical delta regressions with event and structural features failed to beat the practitioner Black–Scholes hedge in the daily development sample.

Thus **no robust after-cost trading edge or superior structural hedge is established**. Prices inferred from neighboring options can be useful without furnishing an executable signal. Price-model discrepancies, stock-hedge outcomes, timing and trading costs all affect P&L; losses on one side do not by themselves prove systematic market overpricing or underpricing.

## Earlier empirical work

The project also examined realized earnings moves, Gaussian-mixture distribution shapes, EPS and sales surprises, option-implied move forecasts, skew/tail rankings and straddle returns. Those studies motivated the separation of ordinary variance from event variance and did not support interpreting the jump as two clean beat/miss outcomes.

The earlier low explanatory power of EPS/revenue regressions does not prove that the unexplained reaction is caused by guidance or tone. Tail rankings are not calibrated tail probabilities. Earlier profitability and correlation claims that did not survive later revisions are not carried into the final conclusions. Prototype smile fits and plots are preserved in `PROTOTYPE_NOTES.md`, separately from the final historical comparisons.

## Boundaries and further ideas

The mathematical ingredients have prior literature; see [the prior-art map](../research2/PRIOR_ART.md). The contribution here is the implemented pricing/scenario system and the concrete empirical results above, not a claim that no one has combined these ideas before.

The current engine prices European payoffs. American exercise, dividends, contract adjustments, financing, borrow, inventory, assignment and executable intraday fills are incomplete or outside the relevant experiments. The live-market meaning of an inferred event component remains model-dependent. No market-efficiency theorem follows from unsuccessful strategies.

The most useful next extensions would be joint strike-and-maturity constraints, an American exercise/dividend layer, and direct comparison of scenario Greeks against realized hedging outcomes on a broader event sample. Genuine intraday quotes and trades are required before testing passive fills. Learning risk-neutral clock weights separately from physical-return weights is another modeling question. These are future work, not results claimed by the current project.

The final delivered scope is a runnable market-pricing engine with historical accuracy measurements and event-repricing scenarios. The October 2026–March 2027 prospective paper-evaluation window remains reserved; it has not been run or scheduled automatically.

## Subsequent historical-jump trading experiment

The requested historical-jump replacement and percentage-threshold strategies were subsequently tested across 112 eligible company-earnings events in 2020–2025, with midpoint and crossed-quote scenarios, both hedge choices, and long/short breakdowns. No robust historical-jump trading advantage was established. The full experiment is in [HISTORICAL_JUMP_TRADING.md](HISTORICAL_JUMP_TRADING.md).

A further automated expansion covers 168 events under the original candidate rules and a broader 25,420-option candidate screen across 170 events. See [EXPANDED_EARNINGS_TEST.md](EXPANDED_EARNINGS_TEST.md) and [MODEL_INPUTS.md](MODEL_INPUTS.md) for results and the precise model inputs/overnight treatment.

The subsequent iterative trading round evaluated seven strategy families, partial-spread execution, entry hedge changes, protective wings and pre-earnings convergence across additional companies. [ITERATION_RESULTS.md](ITERATION_RESULTS.md) summarizes the diagnoses and retests. It corrects the interpretation of the +26% midpoint statistic and records a matched protective-wing risk reduction without claiming trading alpha.
