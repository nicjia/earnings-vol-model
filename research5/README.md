# Research5: autonomous earnings-options strategy study

A pre-registered search for an earnings-options trading rule that uses only
historical information at the decision close, closing-midpoint fills, the full
300-name 2018–2025 event cache, and many structures, timings and filters.
Candidates are frozen on one sample and validated on samples they never saw.

**Result: none of the five frozen policies qualified, and the autonomous
walk-forward selector lost money out of sample.** The full numbers, including
every failed candidate, are in [docs/research5](../docs/research5/).

## Design

The [protocol](protocol.json) was committed before any trading result was
computed (`cd2fe3b`). Its main choices:

- **Data.** 300 securities fixed at a 2017 formation date (later delistings
  kept), 8,500+ I/B/E/S earnings events with closing option quotes from E-2 to
  E+3, and daily stock prices from 2015.
- **Families (8).** Long straddle, long strangle, short iron fly with 1× and
  2× straddle wings, short iron condor (0.5×/1.5× and 1×/2× implied move),
  call calendar and straddle calendar.
- **Timings (9).** A pre-event hold (E-2→E-1), through-event holds from E-2 or
  E-1 to E, E+1, E+2 or E+3, and an "after release" exit. That exit leaves at
  E or E+1 according to the name's release timing, inferred only from its
  earlier events' stock moves.
- **Historical-only signals.** R = implied move ÷ historical fair move (the
  last 8 earnings moves plus background EWMA volatility); TS = front ÷ back
  ATM implied vol; HR = the name's past realized-to-implied move ratio. Each
  family gets 7–9 filters, and each candidate uses standard or tight liquidity.
  That makes 1,224 candidates in total.
- **Execution.** Closing midpoint fills at entry and exit, $0.65 per contract
  per side, with 25% and 50% half-spread cost sensitivities. Returns are on
  maximum-loss risk; for debit packages that is the debit.
- **Samples.** A = 2018–2021 with half of the names, chosen by hash (selection
  only). B = 2018–2021 with the other half. C = 2022–2023. D = 2024–2025.
  B, C and D cannot be simulated until the frozen file exists. Evaluation
  refuses to run if any source file, the grid or the selection records changed
  after freezing.
- **Selection and gates.** The objective is the cluster-robust lower 95%
  bound of mean midpoint return. A candidate is eligible only if it has at
  least 150 events and 40 issuers, a positive mean at 25% cost, and a positive
  mean excluding its best 5 events. At most one policy per family is frozen,
  up to five in total. To qualify, a frozen policy needs a positive
  weekly-bootstrap lower bound in B, C and D, a positive mean at 25% cost in
  each, and a max-t adjusted selection p < 0.05.
- **Autonomous walk-forward.** Each year from 2020 to 2025, the same rule picks
  one candidate from all earlier years and trades that year untouched.

## Findings (aggregate)

| Frozen policy | A (selection) | B | C | D | B+C+D pooled |
|---|---|---|---|---|---|
| Long straddle E-2→E-1, R≤0.9, tight | +2.6% | −0.4% | +2.1%* | +1.3% | +1.0%* (−0.1% at 25% cost) |
| Long strangle E-2→E-1, R≤0.9, tight | +4.7% | −0.1% | +3.6%* | +2.3% | +1.9%* (+0.6% at 25% cost) |
| Short wide iron condor E-1→after release, R≥1.0 | +2.1% | +0.4% | −2.9% | −1.3% | −1.6% |
| Short iron fly 2× E-1→after release, R≥1.0, tight | +4.2% | −0.5% | −2.5% | +4.1% | −0.3% |
| Short iron condor E-1→after release, R≥1.4, tight | +4.1% | +1.9% | −2.3% | −2.3% | −1.2% |

Mean equal-risk event return at closing midpoints. \* marks a weekly-cluster
bootstrap 95% lower bound above zero. The pooled column is a post-freeze
diagnostic, not a pre-registered gate.

- **The only positive out-of-selection results** are the pre-event
  long-premium trades: buy at the E-2 close, sell at the E-1 close, before the
  announcement. They are positive in C and in pooled B+C+D at midpoint, but
  flat in B. The edge is about one percent of the debit per event and mostly
  disappears at 25%–50% of the quoted half-spread. The gain comes from the
  roughly 10% of trades where the stock already moved at least half the
  implied earnings move during that pre-announcement day; the rest lose
  slightly. That fits releases that came before their I/B/E/S date, so it is
  not established as a pre-event volatility premium.
- **Short-premium rules** win 57–69% of the time but lose on average out of
  selection. Losses in the ~30% of events whose stock moves exceed the implied
  move outweigh the gains. Unfiltered iron flies, condors and calendars are
  negative in nearly every sample, and calendars lose 20%–40% of the debit
  once even a quarter of the spread is paid.
- **The walk-forward selector** picked a different long-premium rule almost
  every year. It averaged −2.5% per event out of sample at midpoint
  (2020–2025, 240 events), −12% on the illustrative 2%-risk account.
- **Post-freeze diagnostics:** no candidate out of all 1,224 was positive at
  25% cost and excluding its best 5 events in all four samples.

## Limitations

The I/B/E/S dates are retrospective and carry no release time. Midpoint fills
are assumed, not demonstrated. American exercise is ignored apart from a
dividend exclusion. The universe is a static 2017 formation. Margin is not
modelled beyond max-loss risk. A previous study (research4) and earlier
repository experiments inspected parts of these names and years, so no sample
is a pristine holdout. The one-session signal-lag check is unavailable for
E-2 entries, because there are no E-3 quotes.

## Data that would sharpen this

1. **Announcement times** (I/B/E/S `anntims` or a point-in-time calendar).
   These would show whether the pre-event long-premium gains come from
   releases that preceded their recorded date.
2. **A fresh cross-section:** the same quote windows for names outside the
   300-name universe (e.g. the next 300–600 by 2017 dollar volume, and
   post-2017 listings). This is the only way to get an untouched holdout for
   the pre-event rule now that every year has been used.
3. **Longer pre-event windows** (quotes from E-10 to E-3) to test the
   implied-vol run-up across more entry dates. This would also allow the
   signal-lag check for E-2 entries.

## Run

The engine uses only the Python standard library, including a reader for the
cache's pandas pickles, so it runs where numpy/pandas cannot be installed.

```sh
python -m unittest research5.test_research5
python -m research5.data --source ../wrds_studies/earnings_vol --output ../wrds_studies/research5_cache
python -m research5.run select   --cache ../wrds_studies/research5_cache --results ../wrds_studies/research5_results
python -m research5.run evaluate --cache ../wrds_studies/research5_cache --results ../wrds_studies/research5_results
python -m research5.report      --results ../wrds_studies/research5_results
python -m research5.diagnostics --results ../wrds_studies/research5_results
```

Outputs are created exclusively and never overwritten. Licensed quotes and
trade-level records stay outside this repository.
