# Handoff: continuing this research in a new session

Written 2026-10-03 so a fresh Claude Code session can pick up exactly where the previous one stopped.
Updated 2026-10-03 (second session, branch `claude/zealous-gates-y1a096`): see **Research8 status** at the end.
Read this file, then `STRATEGIES.md`, then the latest round README (`research7/README.md`).

## Goal

Build a fully functional self-trading algorithm for earnings and general options. It uses `rh_direct.py` (in the user's
`event-clock` folder) as its broker/quote API. `rh_direct` imitates MCP calls; the user confirms it is a paper/test interface,
not the real Robinhood API.

**Hard rules from the user:**
- Call `rh_direct` only from code, and filter its output in code. Never run it and read raw output yourself.
- Never read raw research results by eye; write code that summarises them.
- Pre-register rules before testing, preserve every failed result, and report honestly.
- Keep `STRATEGIES.md` updated with every rule that passes an untouched test, specified exactly enough to implement.

## Repositories and branch

- Code: `nicjia/earnings-vol-model` (public). Latest work is on branch `claude/zealous-gates-y1a096` (it contains all of
  `claude/blissful-goodall-7shzx0`); no PR unless asked.
- Data: `nicjia/options-data` (private). WRDS data lives in GitHub **releases**; manifests in `manifests/` on `main`.
- Never put licensed data or trade-level records in the public repo. Aggregates only (the `docs/` folders).

## Environment setup in a new session

Network access is now Full, so PyPI works. Suggested environment setup script (environment settings -> Setup script):

```sh
pip install numpy pandas scipy scikit-learn
```

Then, from `/home/user/earnings-vol-model` (attach `nicjia/options-data` to the session so it is cloned at
`/home/user/options-data`):

```sh
# Restore data (REST downloads; gh GraphQL is blocked in cloud sessions). Each verifies SHA-256 for every file.
python3 data_pulls/fetch_release.py --manifest /home/user/options-data/manifests/research7-data-2026-10.json --output /home/user
python3 data_pulls/fetch_release.py --manifest /home/user/options-data/manifests/research7-expanded-2026-10.json --output /home/user
(cd /home/user/options-data && python3 fetch_data.py --output ..)      # older earnings_vol cache (release cache-2026-10-02)

# Rebuild caches (minutes)
python3 -m research7.data --source /home/user/wrds_studies/research7_data --output /home/user/wrds_studies/research7_cache
python3 -m research7.sample_e build --source /home/user/wrds_studies/research7_expanded --cache /home/user/wrds_studies/research7_cache_e
python3 -m research5.data --source /home/user/wrds_studies/earnings_vol --output /home/user/wrds_studies/research5_cache

# Tests
python3 -m unittest research7.test_research7 research6.test_research6 research5.test_research5 data_pulls.test_data_pulls
```

Notes: WRDS (PostgreSQL, port 9737) is unreachable from cloud sessions. The user runs pulls on WRDS Cloud (`qrsh`, then
`python3 data_pulls/wrds_pull.py ...`), copies results to their Mac, and publishes with `data_pulls/publish_release.py`.
Private trade-level result files were never persisted (a push to options-data was blocked by the safety check). Their
SHA-256 values are in `docs/research*/private_outputs.sha256`, and they can be regenerated exactly by re-running the round
commands in each README. Frozen results directories are refused if any hashed source changes.

## Research so far (all at closing-midpoint fills unless noted)

| Round | Data | What was tested | Outcome |
|---|---|---|---|
| research4 (Codex) | earnings_vol cache | Long straddle rule | Failed validation and test |
| research5 | 300 names, E-2..E+3 quotes, 2018-25 | 1,224 rules: straddles, strangles, iron flies/condors, calendars | No frozen policy qualified; pre-event long premium a lead |
| research6 | same | 894 rules: weekly calendars/double calendars/diagonals (user's idea), post-event trades | Calendars positive at mid, negative at 25% cost |
| research7 | New WRDS pull with I/B/E/S release times, E-10..E+5, 45-day expiries | 1,944 release-timed rules; replications | Frozen calendars failed. **Sample E (500 untouched names): pre-release long straddle/strangle passed** (see STRATEGIES.md) |
| Sharpe/DSR | research7 A-D | Deflated Sharpe with 1,944 / 4,062 trials | Nothing clears DSR on A-D alone (noise max ~2.1-2.2 annual) |
| ReLU explorations | 12 names / all events | Butterflies, ReLU cleaning, payoff design | Mid-based relative value is quote noise; no edge at bid/ask |

Key lesson: when a signal is built from quoted mids and filled at mids, the edge is often spread capture. Always report
25% and 50% half-spread costs and prefer executable-price tests.

## Agreed next plan (user verified 2026-10-03)

User's thesis: a **standalone model** should value options from stock behaviour alone (past and predicted stock
movement), not from other current option quotes. The market price is only what you pay; fair value is judged by realized
payoffs and trading P&L, not by matching the market.

User decisions:
1. Yesterday's option prices may be used (lagged data = history). Today's quotes are never model inputs.
2. New data: continuous daily option panel (done in code; user to run, see below).
3. The four approaches below are accurate.
4. Success: forecast accuracy as a diagnostic; executable after-cost P&L, judged forward on paper, as the final test.
   Consider several fill levels.

Clarification on the "ruler" (approach R): when B is priced off anchor A and B looks expensive, the trade must include A
(thesis: if A is fair, B is mispriced). Express it as a position in both, e.g. B against A in the model's hedge ratio.

Approaches:
- **A0 stock-only true value:** distribution of stock moves to each expiry (diffusion with an overnight/intraday clock,
  earnings jumps, fat tails), then option value with a risk premium estimated only from history, American exercise and
  discrete dividends (binomial/LSM). Validate fair value against **realized payoffs** (calibration of expected payoff) and
  trading P&L, not market prices.
- **A1 market replicator:** predict today's implied vol surface from stock history, calendar/events and yesterday's surface.
  Must beat "today = yesterday".
- **T direct trader:** learn positions from features, trained on after-cost (and hedged) option P&L.
- **R ruler:** liquid anchor (ATM straddle) plus a history-modelled shape; trade anchor-versus-strike spreads.

Phases: 0 data -> 1 stock distribution model (log score/CRPS/PIT, walk-forward) -> 2 distribution to option value
(A0, American exercise) -> 3 replicator (A1) -> 4 traders -> 5 ruler -> 6 forward paper trading via `rh_direct`.

Open question the user raised: is the market price really "expected payoff + risk premium"? Evidence so far, all in our
data: realized release moves average 0.87x the implied move (`docs/explorations/relu_tools_output.txt`); long straddles held
through releases lose on average while short 2x iron flies through releases passed sample E; ATM butterflies are slightly
overpriced while upside tails were underpriced. So options are, on average, priced above expected payoff around earnings,
but not uniformly across strikes. A pure expected-payoff model will lean toward selling premium, which must be judged on tail
losses and drawdowns, not just averages.

## Pending user actions

1. **Daily panel pull** (code merged in `data_pulls/wrds_pull.py`, phase `daily`). On WRDS Cloud, in `qrsh`, after copying
   the updated `data_pulls/` folder:
   ```sh
   python3 data_pulls/wrds_pull.py daily --out ~/research8_daily --original-universe ~/universe.csv --wrds-user nic2637
   ```
   Defaults: 40 most liquid names of the 2017 universe plus SPY, every session 2016 to latest, expiries <= 120 days, strikes
   0.7-1.3 x close, 4 names per query (roughly 2 GB). Then copy to the Mac and publish:
   ```sh
   rsync -av nic2637@wrds-cloud.wharton.upenn.edu:~/research8_daily ~/stock/wrds_studies/
   python data_pulls/publish_release.py --data ~/stock/wrds_studies/research8_daily --root ~/stock --tag research8-daily-2026-10 --options-data ~/stock/options-data
   cd ~/stock/options-data && git add manifests/ && git commit -m "Add research8-daily-2026-10 manifest" && git push
   ```
2. Optional: real multi-leg fill records, to calibrate the fill-cost assumption.

## Immediate next steps for the new session

1. Restore data and caches (above), run the tests.
2. Phase 1 (does not need the daily panel): write and commit a protocol, then fit and compare stock-distribution models
   on the 800-name daily stock data already in `research7_data/stocks` and `research7_expanded/stocks` (OHLC, 2014-2025):
   EWMA/GARCH, HAR with overnight/intraday split, earnings-jump mixture (name history plus shrinkage), fat tails or bootstrap,
   gradient-boosted quantiles. Walk-forward, scored by log score/CRPS/PIT at 1-60 day horizons and on release days.
3. When the daily panel arrives: Phases 2-5, then wire the survivors and S1-S5 into a paper trader on `rh_direct`.

## Research8 status (second session, 2026-10-03)

Read `research8/README.md` and `docs/research8/SUMMARY.md` (generated by `python3 -m research8.summary`).

- **Phase 1 passed its untouched test.** Frozen `HAR_FHS_shrunk` (HAR variance with overnight/Garman-Klass inputs,
  empirical standardized shape, shrunk release-jump component) beats EWMA-Normal by +2.2% CRPS and +0.147 nats log score
  on the 500 expanded names in 2023-2025, in every horizon group, with calibrated 90% intervals.
- **No trading rule passed.** A0 (market price vs stock-only value) froze two rules that failed the test; the ruler,
  cross-sectional book, direct trader, model-filtered pre-release long premium, skew, stock-event and stock-factor rounds
  had no dev-eligible rule. All failures are committed with their protocols.
- Key finding: the stock-only model with release jumps values earnings straddles within about 4% of the market on
  average, and realized payoffs match it. There is no large average mispricing; relative signals did not survive.
- **Ready and waiting on the user:** (1) the daily panel pull (`research8/protocol_daily.json`, 96 rules
  pre-registered before the data exists; pipeline `python3 -m research8.daily build|records|value|dev`, tested on
  synthetic quotes); (2) `rh_direct.py`, needed for the paper trader (`live/strategies.py`, verified to match the
  backtest engine's selections on 400 historical events).
- Rebuild private caches: `python3 -m research8.panel`, `python3 -m research8.phase1 dev|final` (slow: about 1-2 hours
  each; set OMP_NUM_THREADS=1 for other sklearn jobs running at the same time), `python3 -m research8.options2`,
  `python3 -m research8.value2 --models ...`.
