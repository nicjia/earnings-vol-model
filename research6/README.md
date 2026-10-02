# Research6: weekly calendars, diagonals and post-event trades

This round tests the idea of shorting the first post-earnings weekly and buying
the following weekly at strikes just outside the expected move, along with
variants and other structures. It uses the same cache, samples, selection rule
and gates as [research5](../research5/README.md). The
[protocol](protocol.json) was committed before any result (`179e5e3`).

**Result: none of the five frozen policies qualified.** Calendars do earn
money at closing midpoints: the first weekly loses more value after earnings
than the next one does. But that edge is about as large as paying a quarter of
the quoted spread on four legs. Full tables: [docs/research6](../docs/research6/).

## What was tested (894 candidates)

- **Double calendars:** sell the first post-earnings weekly call and put just
  outside an expected move, and buy the same strikes in the next weekly. The
  move is sized four ways: the ATM put alone (about half the straddle), 0.75×,
  1.0× and 1.25× the ATM straddle. A 1.0× version uses a two-week back expiry.
- **Double diagonals:** the same short legs, with the long legs one strike
  further out.
- **ATM calendars:** call, put and straddle calendars at the money.
- **Reverse straddle calendar:** buy the first weekly, sell the next one.
- **After the report:** an iron fly sold at the E+1 close, and debit verticals
  that follow or fade the earnings move.
- **History-driven verticals:** a debit vertical in the direction of the
  name's average past earnings move.
- **Timings:** enter at the E-1 or E-2 close. Exit at E+1, at the time inferred
  from the name's past release pattern, or by holding the short weekly to its
  expiry. A leg that expires on the exit day is settled at intrinsic value from
  the stock's closing price.
- **Filters:** implied ÷ historical move (R); front ÷ back implied vol (TSw);
  the implied volatility excluding the earnings event ÷ historical volatility
  (D); the name's past realized ÷ implied move (HR); for post-event trades,
  the size of the earnings move. Each with standard or tight liquidity.

## Findings

All figures are the mean return per event on risk; for calendars, risk is the
debit.

**The proposed trade:** E-1 entry, short weekly held to expiry (or E+3), long
next weekly.

| Strike distance | A (selection) | B | C | D | 25% half-spread cost |
|---|---|---|---|---|---|
| Outside ±ATM put (≈ ½ straddle) | +5.1% | +2.9% | +1.3% | −1.9% | −6% to −18% |
| Outside ±1.0 straddle | −1.3% | −0.2% | −1.3% | −2.3% | −9% to −14% |
| Outside ±1.0 straddle, 2-week back | +5.1% | +6.4% | +1.7% | +5.2% | −0.0% to −3.7% |

Exiting at E+1 instead of holding the short weekly to expiry was worse in every
version. Strikes closer to the money did better than the full-straddle edges.
The two-week back leg did better than the one-week leg.

**Frozen policies.** The five frozen policies were ATM put, straddle and call
calendars held to the weekly's expiry with R ≥ 1.2, a put-sized double
diagonal, and a two-week double calendar with TSw ≥ 1.3. They returned +10% to
+18% per event on sample A, and +2% to +8% pooled across B, C and D. Each one's
95% interval spanned zero, and each turned negative at 25% of the half-spread.
The ATM calendars win about +110% when the stock moves less than half the
implied move, and lose about −75% when it moves more than the implied move.

**Walk-forward selector.** It picked put calendars and then two-week double
calendars. Out of sample it averaged +7.1% per event (2020–2025, 657 events,
95% interval −2.0% to +16.8%) at midpoint, and −8.6% at 25% cost. On the
illustrative 2%-risk account that is +104% at midpoint but −75% at 25% cost:
nearly the whole result depends on fill quality.

**After the report and directional trades.** Post-event iron flies lost 6%–10%
in every sample. The momentum and fade verticals, the history-driven
verticals and the reverse calendars were negative or near zero.

**Post-freeze diagnostics.** Two of the 894 candidates were positive at 25%
cost and excluding their best 5 events in all four samples: a put-sized double
diagonal entered at E-2 with D ≤ 1.0 and tight liquidity, and the two-week
double calendar entered at E-1 with R ≥ 1.2. They were found after seeing
every sample, so they are hypotheses for fresh data, not results.

## Caveats

These carry over from research5: no announcement times, retrospective dates,
assumed midpoint fills, no American early exercise, and every sample already
seen by earlier work. Settling the short weekly at intrinsic from the closing
stock price ignores pin risk and after-hours moves on expiration day. About 6%
of ATM-calendar exits lose more than the debit because of inconsistent exit
midpoints; capping those losses changes the pooled means by 1–3 points. The
one-session signal-lag check from research5 was not run in this round.

## Run

```sh
python -m unittest research6.test_research6
python -m research6.run select   --cache ../wrds_studies/research5_cache --results ../wrds_studies/research6_results
python -m research6.run evaluate --cache ../wrds_studies/research5_cache --results ../wrds_studies/research6_results
python -m research5.report      --results ../wrds_studies/research6_results --title "Research6: weekly calendars, diagonals and post-event option trades"
python -m research5.diagnostics --results ../wrds_studies/research6_results --title "Research6 post-freeze diagnostics"
```
