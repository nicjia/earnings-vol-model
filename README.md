# Earnings volatility model

European option pricing with Heston stochastic volatility, scheduled earnings jumps, and a constrained surface fitted to reference quotes. The strongest result is pricing held-out strikes accurately; the trading experiments did not establish a robust after-cost edge.

## Results

| Experiment | Result | Definition and evidence |
|---|---|---|
| Held-out pricing, 2020 | **4.07 spot-bp MAE; 95.5% inside bid–ask** | 118,117 target quotes; [pricing report](docs/PROJECT.md#pricing-results) and [metrics](docs/final_metrics.json) |
| Historical confirmation, 2025 | **87.0% inside bid–ask; 4.85 spot-bp MAE** | 23,650 target quotes; same reference-quote protocol; [pricing report](docs/PROJECT.md#pricing-results) |
| Scheduled-jump ablation | **27% lower MAE than jump-free Heston** | 21.54 → 15.80 spot bp on the 2020 sample; [eight-way ablation](docs/structural_ablation.json) |
| Conditional earnings repricing | **69% lower MAE than unchanged strike IV** | 72.24 → 22.10 spot bp across 14 later-year events, supplying observed later stock prices; [comparison](docs/PROJECT.md#repricing-through-earnings) |
| Protective wings | **62% lower P&L dispersion; roughly half the worst observed loss** | 38 matched events at equal core-straddle stock-notional exposure; [risk comparison](docs/ITERATION_RESULTS.md#protective-wings-matched-risk-comparison) |

Target strikes and their put/call parity twins are withheld from calibration. The pricing tests cover **141,767 quotes** across the two years, with 2020 used for development. The hybrid is competitive with market interpolation, not consistently better: the market-only surface put 96.5% and 89.7% inside bid–ask in the respective samples. A simpler two-expiry estimate also beat the structural conditional-repricing adjustment.

### Trading attribution

The 156-position, 37-event experiment produced a +25.99% event-average premium-normalized return under simulated midpoint fills, including a stock hedge. Removing two events changes it to −14.4%; refreshing the entry hedge changes it to −4.67%; full quoted crossing gives −34.96%. These are separate sensitivity checks on the original experiment, not account returns.

A broader pre-registered search ([research5](research5/README.md)) covered 1,224 rules: eight structures, nine entry/exit timings and historical-only filters on 300 names over 2018–2025. None of its five frozen policies passed out-of-selection validation. The only positive out-of-sample result is a small pre-announcement long-premium trade that fades at 25%–50% of the quoted half-spread.

The arithmetic break-even is 42.6% of full modeled crossing cost. It is not evidence that those fills are attainable. The contribution is the option/hedge/cost attribution and risk analysis, rather than a demonstrated profitable strategy. See [trading results](docs/ITERATION_RESULTS.md) and [experiment definitions](docs/RESULTS.md).

## Run

```bash
python -m pip install -r requirements.txt
python demo_market_surface.py  # offline constrained-surface example
python demo_price.py           # closed-form pricing vs Monte Carlo
python demo_clock.py           # session/closure variance clock
```

Run the correctness tests with:

```bash
python -m pip install -r requirements-test.txt
python -m unittest test_trade_screen test_market_surface test_variance_clock research2.test_research research2.test_historical_jump research2.test_iteration strategy_lab.test_lab strategy_lab.test_ablation
```

Historical studies require licensed quote data that are not distributed here. The offline demos and tests use generated inputs; they do not reproduce the historical panel.

## Model

- Flat diffusion with a scheduled Gaussian-mixture jump has a weighted Black-76 price. Jumps apply only to expiries that contain the earnings date.
- Heston diffusion and independent scheduled jumps combine through characteristic functions and Fourier-cosine pricing, without enumerating jump-outcome combinations.
- An optional variance clock separates exchange sessions, overnight closures, weekends and holidays. Physical-return clock weights did not improve risk-neutral pricing: the wider calibration gave 14.91 versus 14.06 spot bp for calendar time.
- Reference quotes correct the structural smile; a constrained call-price curve enforces decreasing, convex prices within each expiry. This does not eliminate cross-expiry arbitrage.

The [project report](docs/PROJECT.md) gives samples, baselines and limitations. The [methods PDF](docs/methods.pdf) covers the pricing mathematics. Core implementations are in `earnings_mixture.py`, `cos_pricer.py`, `variance_clock.py` and `market_surface.py`.
