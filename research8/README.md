# Research8: standalone stock-only models

The user's thesis: value options from stock behaviour alone (past and predicted stock movement), never from today's
option quotes. The market price is only what is paid; fair value is judged by realized payoffs and after-cost P&L.

| Step | Pre-registration | Code | Status |
|---|---|---|---|
| Phase 1: stock return distributions (31 models) | [protocol_phase1.json](protocol_phase1.json), [clarifications](phase1_clarifications.md) | `panel.py`, `features.py`, `dist.py`, `phase1.py`, `report1.py` | **passed untouched test**: HAR_FHS_shrunk CRPS +2.2% [+1.7, +2.7], log +0.147 nats, all gates; HAR_T_shrunk passes tail gate; release-day pick fails gate 2 |
| Phase 2 (A0): stock-only values vs market, 320 rules | [protocol_phase2.json](protocol_phase2.json) | `options2.py`, `value2.py`, `rules2.py` | frozen 2 rules, **failed test** (-4.8%, -9.3% at 25% cost) |
| Approach R (ruler): strangle vs straddle anchor, 60 rules | [protocol_ruler.json](protocol_ruler.json) | `ruler.py` | no dev-eligible rule |
| Approach T (direct trader), 8 rules | [protocol_trader.json](protocol_trader.json) | `trader.py` | no dev-eligible rule |
| Cross-sectional long-short book, 80 rules | [protocol_xsec.json](protocol_xsec.json) | `xsec.py` | no dev-eligible rule |
| Pre-release long premium + model filter, 56 rules | [protocol_prerel.json](protocol_prerel.json) | `prerel.py` | no dev-eligible rule |
| Skew relative value, 30 rules | [protocol_skew.json](protocol_skew.json) | `skew.py` | no dev-eligible rule |
| Stock trades around releases, 63 rules | [protocol_stockev.json](protocol_stockev.json) | `stockev.py` | no dev-eligible rule |
| Weekly stock long-short factors, 12 rules | [protocol_factors.json](protocol_factors.json) | `factors.py` | no dev-eligible rule |
| Daily-panel model-timed vol premium, 96 rules | [protocol_daily.json](protocol_daily.json) | `daily.py` | pre-registered before the data exists; waiting for the pull |
| Model-timed index put-writing (public CBOE data), 11 rules | [protocol_putwrite.json](protocol_putwrite.json) | `putwrite.py` | **HAR >= 1.5 passed every strong gate on the untouched 2016-2026 test** (Sharpe 1.07, t 2.70) but held only 14 of 129 months; EWMA >= 1.0 failed |

Generated summary of every round: [docs/research8/SUMMARY.md](../docs/research8/SUMMARY.md).

Splits (user decision): develop on the original 300 names through 2022; untouched test on the 500 expanded names
from 2023. The expanded names' option outcomes were seen once before for six research7 hypotheses (disclosed in each
protocol). Results are summarised by code only (aggregates in `docs/research8/`); trade-level files stay private.

## Reproduce

```sh
python3 -m research8.panel   --data ../wrds_studies --output ../wrds_studies/research8_phase1/panel.npz
python3 -m research8.phase1  dev --panel ../wrds_studies/research8_phase1/panel.npz --out ../wrds_studies/research8_phase1/scores
python3 -m research8.report1 dev --scores ../wrds_studies/research8_phase1/scores --docs docs/research8/phase1
python3 -m research8.options2 --cache ../wrds_studies/research7_cache --cache-e ../wrds_studies/research7_cache_e
python3 -m research8.value2  --models <frozen models>
python3 -m research8.rules2  dev --model <phase 1 best_crps>
python3 -m unittest research8.test_research8
```
