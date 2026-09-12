# Option strategy lab

This implements the seven research ideas discussed with the user. It is a
calibration research harness, not a broker or a live trading system.

## What counts as an unseen answer?

There are three different questions:

1. **Fit:** reproduce the options whose prices were supplied to calibration.
   This is a diagnostic of fit, not an accuracy test.
2. **Withheld-contract pricing:** use designated reference option prices to
   estimate the market state, then price different strikes. The withheld calls
   and their matching puts are excluded together, across all maturities and
   dates. This measures interpolation/generalization conditional on observable
   market inputs. A test mutates every withheld price and checks that the fitted
   parameters and inferred forwards do not change.
3. **Future evaluation:** freeze the research choices before observing later
   outcomes. The lab additionally reports next-close parameter transport with
   parameters fixed at the prior close and the new stock price supplied at
   scoring time. That is conditional repricing, not a forecast of stock prices.
   A reference-IV benchmark gets that same new spot input for a fair comparison.

Using some current quotes as inputs is legitimate for a market-implied pricing
model. Using the exact quote being scored to fit its own implied volatility is
circular. Reporting same-time withheld-strike accuracy as future trading skill
would also be misleading. None of these experiments can supply a uniquely
identified risk-neutral distribution without assumptions or market information.

## Fixed research protocol

The default research window is 2020-01-21 through 2020-12-10, within the existing
calibration period. Earlier 2020 observations provide past-only clock inputs.
2021 onward is not loaded into the runner. Earlier conversations already inspected
2021–2024, so those dates cannot become a prospectively untouched final test again.

The protocol file fixes thresholds, costs, holding periods and fit complexity.
There is no profitability-driven parameter search. Running seven strategies is
still exploratory multiple-model selection; a later final evaluation needs fresh
data and frozen choices. The generated manifest records source and protocol hashes.

Reference partition: SHA256(secid, strike_price) modulo 3; approximately one third
of strikes are targets and two thirds are reference strikes. Target quote prices
do not enter forward extraction, initialization, calibration weights, expiration
selection or parameter estimation. Trading signals may compare independently
computed target fair values with target bid/ask prices, as a trader would.

## Model specification

The pricer uses Heston background variance and a compensated scheduled Gaussian
mixture jump, with the new session/closure variance clock. To keep daily fitting
bounded and reproducible, kappa=2 and theta=v0; sigma, xi, rho and (when separately
identified) earnings scale are fitted. The jump is a fixed 85% core / 15% wider
downside-tail shape. These restrictions are hypotheses, not findings.

Clock ratios use strictly earlier underlying open/close intervals, excluding
earnings windows and split-factor transitions. They are physical relative-variance
priors. Their equivalence to risk-neutral clock ratios is NOT assumed to have been
validated. A separately refitted all-calendar-time Heston model and reference-only
IV interpolation are included as benchmarks. Do not interpret a price difference
created by an arbitrary clock change as mispricing.

Daily equity options use a European approximation. Six non-dividend names in the
calibration window are included to reduce dividend-related confounding; OTM
references are preferred. American puts can still have early-exercise value.
Earnings dates are retrospective and their historical availability is unverified.
Announcement-day fits are excluded because announcement times are unavailable.

## Strategies

| Rule | Signal | Position | Exit |
|---|---|---|---|
| Individual convergence | Target theory-versus-market gap exceeds costs and buffer | Long/short target option, initial stock delta hedge | Convergence decision then next close; otherwise three-session limit |
| Same-event calendar | Relative gap between maturities containing the same earnings | Opposing expirations, small integer ratios matching event sensitivity | Convergence or time limit, always before release |
| Weekend/holiday calendar | Relative gap ahead of an extended closure | Opposing expirations, approximate diffusion-sensitivity matching | First session close after closure |
| Butterfly shape | Package theory differs from executable package prices | Equal-spaced target-strike call butterfly or reverse | Convergence or holding limit; event-spanning deadlines extend past release |
| Post-earnings | Gap after the release is removed from the model | Target option plus initial stock hedge | Convergence or three-session limit |
| Session rotation | Prior physical interval variance versus option-implied interval variance | Initially delta-hedged option held during day or overnight | Actual open/close snapshots required |
| Pre-earnings | Target residual during the pre-release window | Target option plus initial stock hedge | Convergence or limit, before the release |

All proposals are selected using their signal-time information. Contract IDs,
quantities and initial stock hedge shares are fixed before entry. The daily
engine fills at the next session's closing bid/ask, with additional costs. A
convergence observation similarly schedules liquidation at the following close,
not the already-observed close. Deadlines are fixed independently of outcomes.

Convergence is monitored at package level against executable liquidation quotes.
It can result from the theoretical price moving toward the market and therefore
does not ensure profit. The initial stock hedge is not dynamically rebalanced.
Calendar matching neutralizes one modeled sensitivity approximately, not all risk.

Each strategy is its own research book. There is at most one live position per
name in each book. Overlapping books are never summed into an alleged portfolio.
Missing exits and contract changes are unresolved rather than silently discarded.
An unresolved book is not allowed to resume as though its position vanished.

## Data and execution limits

The WRDS downloader is outside this repository at
`/Users/nick/stock/wrds_studies/pull_strategy_lab.py`. It fetches standard-sized
2020 option contracts with no delta filter, underlying opens/closes and historical
rates. Licensed raw and result files stay outside this Git repository.

Opening stock prices do not substitute for opening option quotes. The seventh
data capability (separate session trading) is explicitly blocked without actual
timestamped option open/close observations. The signal generator and execution
adapter are implemented and tested with synthetic quotes; synthetic tests are
not presented as empirical returns.

Quote scenarios are not verified live fills. Commissions and explicit option/stock
slippage are modeled; financing, borrow, margin, market impact beyond the chosen
slippage, and American exercise/assignment are not. Returns are normalized by
gross option contract spot notional, not invested capital or required margin.

## Run

From the repository directory:

```sh
python -m unittest -v test_variance_clock strategy_lab.test_lab
python -m strategy_lab.run \
  --data /Users/nick/stock/wrds_studies/strategy_lab_data \
  --output /Users/nick/stock/wrds_studies/strategy_lab_results
```

Optional `--sids` and `--max-dates` are for smoke tests, not searching profitable
subsamples. `--intraday-quotes` accepts a CSV with UTC-aware timestamp, secid,
optionid, strike, exdate, cp_flag, best_bid, best_offer, spot and cfadj columns.

Outputs include the report, fit metadata, reference/target split audits, contract
predictions, conditional future repricing scores, trade identities and statuses,
cost/P&L decomposition, and model-versus-residual P&L attribution where available.

## Component and strategy follow-up

`ablation` runs all eight flat/Heston × jump/no-jump × calendar/physical-clock
combinations on the original identical reference snapshots and target contracts.
It also tests two reference-residual IV hybrids, recording numerical convergence,
optimizer limits and necessary within-expiry strike consistency checks.
`replay` uses the original daily strategy rules with four alternative marking
methods, and tests frozen-information next-day conditional repricing.

```sh
python -m unittest test_variance_clock strategy_lab.test_lab strategy_lab.test_ablation
python -m strategy_lab.ablation --data ../wrds_studies/strategy_lab_data --old ../wrds_studies/strategy_lab_results --output ../wrds_studies/ablation_results
python -m strategy_lab.replay --data ../wrds_studies/strategy_lab_data --results ../wrds_studies/ablation_results
python -m strategy_lab.boundary_audit --data ../wrds_studies/strategy_lab_data --results ../wrds_studies/ablation_results
python -m strategy_lab.followup_report --results ../wrds_studies/ablation_results --old ../wrds_studies/strategy_lab_results
python -m strategy_lab.verify_followup --results ../wrds_studies/ablation_results --old ../wrds_studies/strategy_lab_results --data ../wrds_studies/strategy_lab_data
python -m strategy_lab.freeze --results ../wrds_studies/ablation_results
```

Use a separate output directory for new experiments. The boundary audit is an
explicitly post-ablation diagnostic of wider parameter limits and optimization
effort, not a new candidate selected for trading. The report includes same-trade
spread costs, option/stock attribution, side breakdowns, concentration stress,
weekly cluster intervals and pre-recorded qualification rules.

The follow-up retained interpolation as a pricing benchmark: hybrid same-date
accuracy improved modestly but necessary strike checks worsened, and next-day
conditional repricing did not improve. Parameter limits explain part of the
structural model's error. No tested trading book met the qualification rule.
Neither the interpolation nor the hybrid is a validated arbitrage-free quoting
surface. Structural event sensitivities also remain unvalidated risk proxies.

`followup_protocol.json` reserves October 2026–March 2027 for future paper
evaluation. `freeze` writes an exclusive timestamped source archive and hashes
outside the repository, and refuses to reserve a period that has already begun.
This reserves research choices; it does not implement a prospective data feed,
schedule a job, or produce future results. Point-in-time event data and genuine
intraday quote/trade data remain prerequisites for the corresponding studies.
