# Reproducing the pricing checks

Use Python 3.10 or newer. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m unittest test_market_surface test_variance_clock research2.test_research research2.test_historical_jump research2.test_iteration strategy_lab.test_lab strategy_lab.test_ablation
python demo_market_surface.py
python demo_clock.py
```

These checks use synthetic inputs and require no data account. The market demo fits eight reference quotes and prices five withheld strikes. Prices are dollars per underlying share; multiply by 100 for a standard contract.

## Historical results

| Result | Record | Interpretation |
|---|---|---|
| 118,117 development quotes and 23,650 later-year quotes | [Aggregate metrics](final_metrics.json) | Target strikes are withheld; other quotes from the same snapshot remain inputs. |
| 2025 hybrid MAE of $0.228 and 87.0% inside bid–ask | [Project report](PROJECT.md) | Market-only interpolation reaches 89.7% inside bid–ask. |
| Conditional post-event repricing | [Project report](PROJECT.md) | Uses the observed later stock price. |
| 25.99% event-average premium-normalized midpoint result | [Strategy diagnostics](STRATEGY_ITERATION.md#second-and-third-diagnostic-rounds) | 156 trades, 37 events; entry-time reference hedging changes it to −4.67%. |
| Execution and concentration sensitivity | [Strategy diagnostics](STRATEGY_ITERATION.md#decision-from-this-round) | Two events contribute more than the original average gain; stock-notional normalization is negative even at midpoint. |

The historical pipelines require separately obtained licensed quote histories. The public tests verify numerical and accounting behavior; they do not reproduce the empirical tables. See [research commands](../research2/README.md) and [strategy commands](../strategy_lab/README.md) for those pipelines.
