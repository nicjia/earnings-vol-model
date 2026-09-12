# Pricing, hedging and event-repricing experiments

The final conclusions are in [PROJECT.md](../docs/PROJECT.md). These modules retain the development work and comparisons that produced the final market-pricing interface.

| Module | Purpose |
|---|---|
| `smiles.py` | Strike-constrained cubic projection and SSVI benchmark |
| `develop.py` | Common-reference pricing comparisons and daily hedge panel |
| `hedging.py` | Past-only empirical delta regression comparisons |
| `event_hedges.py` | Transport an earlier identifiable event fit into option-plus-stock hedges |
| `confirmation_states.py` | Prepare historical reference calibrations for later-period comparisons |
| `transport.py` | Conditional event-preserving repricing, with fixed announcement brackets |
| `round_report.py` | Record pricing/hedging attempts, including failed confirmation |
| `verify_market_api.py` | Reproduce the historical pricing results through the public interface |
| `final_results.py` | Generate aggregate project metrics and figures |

The public entry point is `market_surface.MarketSlice`. The baseline is a PCHIP IV prior projected onto a decreasing convex call-price curve. The hybrid adds reference-IV residuals to a structural call-price callback before the same projection. The default prior weight is 10, as evaluated historically.

## Reproduction

Run from the repository root, using an environment with `requirements.txt` installed. Licensed inputs and individual results belong outside this repository. The paths below refer to the local research workspace, not bundled public datasets.

```sh
python -m research2.develop --data ../wrds_studies/strategy_lab_data --previous ../wrds_studies/ablation_results --output ../wrds_studies/new_pricing_development
python -m research2.hedging --output ../wrds_studies/new_pricing_development
python -m research2.event_hedges --data ../wrds_studies/strategy_lab_data --previous ../wrds_studies/ablation_results --output ../wrds_studies/new_event_hedges
python -m research2.transport --data ../wrds_studies/strategy_lab_data --states ../wrds_studies/ablation_results --output ../wrds_studies/new_transport
python -m research2.verify_market_api
python -m research2.final_results
```

Use new output directories when changing an experiment. `plan.json` describes round 1. Timestamped hypothesis records and later-period selection records are stored with private results. The 2025 database returned quotes only through August 29. It was used first for the frozen round-1 pricing/hedging comparisons and later for a descriptive transport comparison; the latter is not a new untouched test.

## Result locations in the local workspace

- `wrds_studies/research2_development_v2`: final numerical implementation of the 2020 constrained pricing comparisons.
- `wrds_studies/research2_pricing_confirmation`: 2025 pricing predictions.
- `wrds_studies/research2_confirmation`: frozen risk/pricing records and 2025 event hedges.
- `wrds_studies/research2_round1/REPORT.md`: round-1 findings and public-API verification.
- `wrds_studies/transport_development_v4`: completed 2020 event-transport comparison.
- `wrds_studies/transport_external_2025`: later-year descriptive transport results.

Earlier transport versions are retained as development history. In particular, the first `transport_development` run did not use the final announcement bracket and is not a valid final event-repricing result. The final tables use version 4.

## Limitations

Projection constrains strikes within each expiry, not cross-expiry calendar arbitrage. Retrospective event dates are not verified point-in-time schedules. Conditional repricing supplies the later stock price equally to the methods; it is not a stock forecast. Hedge-error comparisons are not trading returns. A structural event component is model-dependent and has not been shown to outperform simpler event estimates or gamma hedges consistently.
