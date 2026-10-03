# Research8: standalone stock-only models

The user's thesis: value options from stock behaviour alone (past and predicted stock movement), never from today's
option quotes. The market price is only what is paid; fair value is judged by realized payoffs and after-cost P&L.

| Step | Pre-registration | Code | Status |
|---|---|---|---|
| Phase 1: stock return distributions (31 models) | [protocol_phase1.json](protocol_phase1.json), [clarifications](phase1_clarifications.md) | `panel.py`, `features.py`, `dist.py`, `phase1.py`, `report1.py` | dev running |
| Phase 2 (A0): stock-only values vs market, 320 rules | [protocol_phase2.json](protocol_phase2.json) | `options2.py`, `value2.py`, `rules2.py` | records built |
| Approach R (ruler): strangle vs straddle anchor, 60 rules | [protocol_ruler.json](protocol_ruler.json) | `ruler.py` | waiting on phase 1 freeze |
| Approach T (direct trader), 8 rules | [protocol_trader.json](protocol_trader.json) | `trader.py` | waiting on phase 1 freeze |

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
