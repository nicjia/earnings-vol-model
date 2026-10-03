# Research7: release-timed earnings options

This round uses a new WRDS pull (`research7-data-2026-10` in `nicjia/options-data`) with I/B/E/S
announcement times. Every trade is placed relative to **P**, the last close before the release, and
**Q**, the first close after it. The pull also widens the quote window to E-10..E+5 and the expiries
to 45 days. The [protocol](protocol.json) was committed before any result (`a3bc7d4`). Full tables
are in [docs/research7](../docs/research7/).

**Status: no rule has qualified yet, by design.** Samples A–D (the 300 original names, 2018–2025)
were all used by earlier rounds. The final test is the expanded universe (sample E): about 500 names
that have never been downloaded. Every rule it will test is fixed in
[e_hypotheses.json](e_hypotheses.json), committed before that data exists.

## Data checks

- **Announcement times:** 8,112 releases before the open, 5,155 after the close and 12 on
  non-trading dates. 125 releases during market hours are excluded. The bigger daily move falls on
  the expected day in 71% of before-open and 80% of after-close releases.
- **Quotes:** every event has quotes for all 16 sessions; 58.8 million rows in total.

## What was tested (1,944 candidates)

- **Pre-release** (exit at P): long straddle and strangle, a one-week straddle calendar and a 2×
  iron fly, entered 9, 4 or 1 sessions before P.
- **Through the release** (enter at P, P-1 or P-4): straddles, strangles, iron flies and condors
  exiting at Q, Q+2 or Q+4. Weekly, two-week and monthly calendars, double calendars and a double
  diagonal, exiting at Q or held to the short weekly's expiry.
- **Post-release** (enter at Q): iron fly, and debit verticals that follow the move, fade it, or
  follow the consensus EPS surprise.
- **Checks:** a signal-lag check that decides one session earlier for every frozen rule, and
  replications of the research5/6 leads with correct timing.

## Findings (samples A–D; midpoint mean return per event unless noted)

**Earlier leads, re-run with exact timing (pre-registered):**

| Rule | A | B | C | D | B+C+D pooled | 25% / 50% cost |
|---|---|---|---|---|---|---|
| Long straddle P-1→P, R≤0.9 | +1.4%* | +2.1%* | +4.0%* | +3.1%* | +3.1%* | +1.9% / +0.8% |
| Long strangle P-1→P, R≤0.9 | +1.9% | +2.9% | +6.7%* | +7.9%* | +5.8%* | +4.5% / +3.2% |

\* marks a weekly-bootstrap 95% lower bound above zero.

- The pre-release long-premium edge holds in every sample, for before-open and after-close releases
  alike, and with the decision taken one session earlier.
- Unlike in research5, it does not depend on a few large pre-release stock moves. The 91% of trades
  where the stock moved less than half the implied move still average +1.5% (straddle) and +2.9%
  (strangle). That points to a real but small rise in option prices before earnings, close to the
  size of trading costs.
- The two research6 calendar leads were positive at midpoint pooled (+3.1% and +5.2%) and about zero
  or negative at 25% cost.

**Frozen policies.** All five are calendars held to the short weekly's expiry. On B+C+D pooled:

- **Double calendar at ±1 straddle, one-week back, entered at P-4, front/back vol ratio ≥ 1.15:**
  +14.3% (95% interval +7.1% to +21.9%), +1.7% at 25% cost.
- **Double calendar at the ATM-put edges, same timing:** +12.0% (+4.7% to +19.7%), +1.1% at 25% cost.
- **Unfiltered two-week double calendar entered at P-4:** +9.7% (+5.2% to +14.3%), +2.9% at 25% cost.
- **ATM put calendar:** +4.7% at midpoint, negative at 25% cost.
- **Double diagonal:** about zero.

Every frozen policy failed at least one gate in B, C or D: usually D's bootstrap bound or its
25%-cost mean, and for the two-week calendar, C. Every one is negative at 50% cost. The one-week
double calendars were weaker in C and D when decided one session earlier. The double calendars at
the straddle edges lose when the stock barely moves and win when it moves 0.5–1× or more of the
implied move.

**Walk-forward selector.** It picked double and put calendars every year and averaged +8.2% per
event out of sample (2020–2025, 887 events, 95% interval +1.9% to +15.6%). That is the first positive
lower bound across the three rounds. At 25% cost it is −6.5%.

**After the release.** Iron flies and the momentum, fade and surprise verticals did not hold up.

**Post-freeze diagnostics.** 14 candidates were positive at 25% cost and excluding their best 5
events in all four samples. They are pre-release long straddles and strangles, two-week double
calendars entered at P-4 or P-1, and wide iron flies and condors. The strongest is the two-week
double calendar entered at P-4 with front/back vol ratio ≥ 1.15: +18.5% / +28.2% / +12.3% / +12.2%,
with a positive lower bound in every sample. All 14 are hypotheses for sample E.

## Bottom line so far

Calendars held to the weekly's expiry, and pre-release long premium, show consistent midpoint
edges with release-correct timing. Their size is comparable to a quarter to half of the quoted
spread. Whether this is tradable depends on (1) sample E, the untouched names, and (2) real fill
quality on multi-leg orders.

## Run

```sh
python -m unittest research7.test_research7
python data_pulls/fetch_release.py --manifest ../options-data/manifests/research7-data-2026-10.json --output ..
python -m research7.data --source ../wrds_studies/research7_data --output ../wrds_studies/research7_cache
python -m research7.run select   --cache ../wrds_studies/research7_cache --results ../wrds_studies/research7_results
python -m research7.run evaluate --cache ../wrds_studies/research7_cache --results ../wrds_studies/research7_results
python -m research7.report --results ../wrds_studies/research7_results
python -m research5.diagnostics --results ../wrds_studies/research7_results --title "Research7 post-freeze diagnostics"
```
