# Research6: weekly calendars, diagonals and post-event option trades

Frozen 2026-10-02T20:09:41.456331+00:00 on sample A; evaluated 2026-10-02T20:12:17.068498+00:00. Protocol sha256 `4cb88313dc11761b`, grid sha256 `b60d4baad434f3f6`.

Returns are equal-risk event returns on max-loss risk (debit for long premium and calendars), closing midpoint fills unless stated, $0.65/contract/side fees. Samples: A = 2018-2021 name half A (selection), B = 2018-2021 name half B, C = 2022-2023, D = 2024-2025 (quotes end 2025-08-26).

## Verdict

0 of 5 frozen policies qualified under the pre-registered gates (75 of 894 candidates were eligible on sample A).

## Frozen policies

### `atm_put_calendar|E-1->hold_front|R>=1.2|tight`

Stage-A max-t adjusted p = 0.062. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 317 | 80 | +18.4% | [+6.4%, +31.0%] | +7.1% | -4.2% | +11.7% | 50% | -228.5% |
| B | 179 | 56 | +11.1% | [-3.4%, +26.5%] | -3.3% | -17.6% | +1.2% | 47% | -205.8% |
| C | 280 | 110 | +2.5% | [-10.6%, +15.4%] | -9.5% | -21.4% | -2.7% | 43% | -434.8% |
| D | 180 | 88 | -6.4% | [-23.2%, +9.6%] | -27.1% | -47.8% | -15.5% | 39% | -383.8% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not run in research6 | | | | | | | | |
| C | not run in research6 | | | | | | | | |
| D | not run in research6 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 320 | +194.0% | +15.6% | +44.0% | +23.6% |
| B | 179 | +43.0% | +26.6% | -14.5% | +39.0% |
| C | 280 | +7.2% | +23.6% | -45.5% | +48.3% |
| D | 180 | -24.2% | +44.9% | -64.8% | +72.2% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05

### `atm_straddle_calendar|E-1->hold_front|R>=1.2|tight`

Stage-A max-t adjusted p = 0.062. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 339 | 84 | +16.9% | [+5.1%, +28.7%] | +5.3% | -6.4% | +11.7% | 47% | -117.8% |
| B | 191 | 54 | +7.3% | [-6.6%, +23.3%] | -5.3% | -18.0% | -1.8% | 45% | -156.2% |
| C | 299 | 113 | +3.8% | [-6.9%, +15.0%] | -6.3% | -16.4% | -1.2% | 42% | -121.7% |
| D | 212 | 97 | +8.1% | [-7.7%, +24.5%] | -11.9% | -31.8% | -1.8% | 42% | -271.6% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not run in research6 | | | | | | | | |
| C | not run in research6 | | | | | | | | |
| D | not run in research6 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 340 | +189.0% | +16.0% | +32.5% | +23.4% |
| B | 191 | +26.7% | +30.0% | -21.7% | +39.0% |
| C | 299 | +18.9% | +28.6% | -35.2% | +46.3% |
| D | 212 | +32.5% | +22.1% | -43.3% | +58.0% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05

### `double_diagonal_put|E-1->after_release|R>=1.2|tight`

Stage-A max-t adjusted p = 0.024. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 187 | 57 | +10.9% | [+4.7%, +17.6%] | +6.4% | +1.9% | +8.2% | 66% | -92.5% |
| B | 95 | 33 | -1.0% | [-11.5%, +9.4%] | -6.8% | -12.7% | -5.8% | 54% | -192.0% |
| C | 141 | 69 | -0.7% | [-7.8%, +7.3%] | -5.0% | -9.3% | -4.7% | 56% | -110.0% |
| D | 67 | 40 | -1.5% | [-11.2%, +8.4%] | -7.5% | -13.6% | -8.0% | 55% | -112.9% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not run in research6 | | | | | | | | |
| C | not run in research6 | | | | | | | | |
| D | not run in research6 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 187 | +49.2% | +5.4% | +26.3% | +6.3% |
| B | 95 | -2.3% | +9.9% | -12.7% | +14.7% |
| C | 141 | -2.6% | +14.3% | -13.7% | +20.8% |
| D | 67 | -2.1% | +7.7% | -9.9% | +11.1% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; D: fewer than 100 events or 40 issuers

### `atm_call_calendar|E-1->hold_front|R>=1.2|tight`

Stage-A max-t adjusted p = 0.068. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 352 | 85 | +14.6% | [+4.4%, +24.9%] | +3.1% | -8.4% | +9.9% | 47% | -267.0% |
| B | 198 | 63 | +3.7% | [-10.4%, +18.1%] | -10.6% | -24.8% | -4.5% | 41% | -216.8% |
| C | 309 | 118 | +1.1% | [-9.0%, +11.4%] | -9.1% | -19.3% | -3.0% | 42% | -168.0% |
| D | 222 | 102 | -4.9% | [-16.7%, +6.2%] | -23.7% | -42.5% | -13.5% | 36% | -182.2% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not run in research6 | | | | | | | | |
| C | not run in research6 | | | | | | | | |
| D | not run in research6 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 354 | +156.6% | +18.5% | +14.7% | +28.9% |
| B | 198 | +11.2% | +30.9% | -37.0% | +45.8% |
| C | 309 | +1.5% | +35.9% | -46.5% | +58.2% |
| D | 222 | -22.6% | +31.6% | -67.1% | +68.7% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05

### `double_calendar_straddle_2w|E-2->hold_front|TSw>=1.3|standard`

Stage-A max-t adjusted p = 0.062. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 360 | 83 | +10.5% | [+3.4%, +17.8%] | +4.1% | -2.2% | +7.5% | 51% | -101.3% |
| B | 238 | 56 | +6.5% | [-1.7%, +14.8%] | -0.6% | -7.7% | +2.0% | 49% | -90.2% |
| C | 263 | 97 | -0.9% | [-8.7%, +7.1%] | -6.8% | -12.7% | -3.8% | 43% | -254.7% |
| D | 244 | 99 | +3.2% | [-4.8%, +10.7%] | -6.2% | -15.6% | -1.1% | 43% | -118.8% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not run in research6 | | | | | | | | |
| C | not run in research6 | | | | | | | | |
| D | not run in research6 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 361 | +103.0% | +9.7% | +29.1% | +15.0% |
| B | 238 | +33.7% | +14.5% | -4.5% | +21.1% |
| C | 266 | -6.6% | +28.4% | -31.9% | +39.8% |
| D | 248 | +15.8% | +20.8% | -26.6% | +38.7% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05

## Autonomous walk-forward selector

Each year the same eligibility rule and objective pick one candidate from all earlier years; it then trades that year untouched.

| Year | Policy chosen from earlier years | Train lower bound | OOS events | OOS mean (mid) | OOS mean 25% cost | OOS win rate |
|---|---|---|---|---|---|---|
| 2020 | `atm_put_calendar|E-2->E+1|TSw>=1.3|standard` | +12.3% | 78 | +24.6% | +1.7% | 46% |
| 2021 | `atm_put_calendar|E-2->hold_front|TSw>=1.3|standard` | +13.8% | 138 | -3.7% | -28.5% | 41% |
| 2022 | `atm_put_calendar|E-1->hold_front|R>=1.2|tight` | +5.4% | 189 | +5.9% | -5.3% | 45% |
| 2023 | `atm_put_calendar|E-2->hold_front|TSw>=1.3|tight` | +5.2% | 138 | +11.5% | -2.3% | 38% |
| 2024 | `double_calendar_straddle_2w|E-2->hold_front|D<=1.0|standard` | +3.3% | 43 | +9.0% | -0.7% | 47% |
| 2025 | `double_calendar_straddle_2w|E-2->hold_front|D<=1.0|standard` | +3.4% | 71 | +2.0% | -6.9% | 39% |

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| 2020-2025 OOS | 657 | 159 | +7.1% | [-2.0%, +16.8%] | -8.6% | -24.3% | +3.5% | 42% | -434.8% |
| 2022-2025 OOS | 441 | 139 | +7.3% | [-2.7%, +16.9%] | -4.2% | -15.7% | +3.1% | 42% | -434.8% |

Illustrative account over the walk-forward trades: +104.5% at mid (max drawdown +36.7%), -75.0% at 25% cost.

## Post-freeze diagnostics (all 894 candidates; cannot change the frozen set)

| Sample | Candidates with >=100 events | Mean > 0 | Normal lower bound > 0 | Mean 25% cost > 0 |
|---|---|---|---|---|
| A | 854 | 592 | 150 | 91 |
| B | 756 | 416 | 66 | 43 |
| C | 838 | 308 | 10 | 12 |
| D | 758 | 175 | 2 | 10 |

Candidates positive at 25% cost and excluding their best 5 events in all four samples (>=50 events each): 2. These are found after seeing B/C/D and are hypotheses for new data, not validated results.

| Candidate | A mean / lower | B mean / lower | C mean / lower | D mean / lower |
|---|---|---|---|---|
| `double_diagonal_put|E-2->E+1|D<=1.0|tight` | +9.5% / +1.2% (n=172) | +5.8% / -2.3% (n=109) | +4.7% / -2.6% (n=145) | +11.1% / +0.6% (n=77) |
| `double_calendar_straddle_2w|E-1->hold_front|R>=1.2|standard` | +6.1% / -1.0% (n=239) | +9.2% / -0.2% (n=124) | +6.4% / +0.1% (n=183) | +10.0% / -4.0% (n=115) |

### Unfiltered base strategies by sample (standard liquidity, midpoint mean / 25%-cost mean, events)

| Family | Timing | A | B | C | D |
|---|---|---|---|---|---|
| atm_call_calendar | E-1->E+1 | +1.7% / -17.2% (1048) | -0.1% / -23.3% (761) | -1.5% / -16.3% (929) | -7.0% / -30.0% (730) |
| atm_call_calendar | E-1->after_release | +4.6% / -14.9% (1045) | -1.4% / -25.8% (761) | +1.1% / -14.4% (929) | -7.8% / -31.0% (729) |
| atm_call_calendar | E-1->hold_front | +2.1% / -14.7% (1048) | +2.8% / -17.5% (761) | -1.9% / -14.2% (929) | -5.2% / -25.6% (730) |
| atm_call_calendar | E-2->E+1 | +1.4% / -19.1% (981) | +3.9% / -20.6% (727) | -0.5% / -15.8% (835) | -2.9% / -26.5% (690) |
| atm_call_calendar | E-2->hold_front | -0.0% / -18.8% (981) | +9.8% / -10.9% (727) | +0.6% / -12.4% (835) | -2.0% / -21.5% (692) |
| atm_put_calendar | E-1->E+1 | +6.9% / -13.7% (879) | +4.4% / -18.6% (629) | -1.7% / -18.6% (830) | -13.4% / -42.7% (586) |
| atm_put_calendar | E-1->after_release | +5.2% / -15.9% (877) | +1.8% / -22.6% (629) | -0.3% / -18.4% (830) | -12.7% / -42.2% (587) |
| atm_put_calendar | E-1->hold_front | +9.7% / -8.1% (879) | +8.2% / -12.5% (629) | -0.7% / -15.2% (829) | -9.4% / -34.4% (587) |
| atm_put_calendar | E-2->E+1 | +5.0% / -15.2% (825) | +7.6% / -14.5% (619) | +1.0% / -16.1% (763) | -8.6% / -37.3% (567) |
| atm_put_calendar | E-2->hold_front | +5.1% / -13.4% (825) | +14.5% / -4.6% (619) | +4.2% / -11.1% (763) | -6.0% / -30.8% (567) |
| atm_straddle_calendar | E-1->E+1 | +2.8% / -16.0% (1013) | +0.0% / -20.9% (709) | -0.9% / -15.7% (865) | -9.3% / -35.4% (704) |
| atm_straddle_calendar | E-1->after_release | +3.2% / -16.2% (1010) | -3.3% / -25.7% (709) | -0.6% / -16.4% (865) | -10.6% / -36.9% (705) |
| atm_straddle_calendar | E-1->hold_front | +7.5% / -8.7% (1013) | +5.3% / -13.8% (709) | +0.8% / -12.0% (865) | -3.6% / -27.1% (704) |
| atm_straddle_calendar | E-2->E+1 | +0.5% / -19.1% (962) | +3.2% / -17.6% (687) | +1.5% / -13.8% (790) | -7.3% / -33.9% (653) |
| atm_straddle_calendar | E-2->hold_front | +1.9% / -16.1% (962) | +10.6% / -7.5% (687) | +4.4% / -9.0% (790) | -1.8% / -24.2% (654) |
| double_calendar_0.75 | E-1->E+1 | +1.8% / -9.7% (847) | -3.3% / -15.4% (544) | -2.9% / -12.8% (766) | -8.1% / -24.0% (550) |
| double_calendar_0.75 | E-1->after_release | +0.5% / -11.9% (847) | -4.0% / -16.6% (544) | -2.9% / -13.4% (766) | -10.0% / -26.5% (550) |
| double_calendar_0.75 | E-1->hold_front | +3.5% / -6.8% (847) | +1.9% / -8.7% (543) | -1.1% / -9.8% (766) | -4.8% / -18.8% (552) |
| double_calendar_0.75 | E-2->E+1 | -0.2% / -11.7% (810) | -0.7% / -13.6% (542) | -3.6% / -13.7% (675) | -5.7% / -22.5% (516) |
| double_calendar_0.75 | E-2->hold_front | +1.2% / -9.4% (809) | +2.4% / -8.6% (541) | -3.2% / -12.2% (675) | -1.7% / -17.3% (518) |
| double_calendar_1.25 | E-1->E+1 | -6.6% / -14.7% (543) | -8.5% / -18.6% (333) | -4.5% / -12.1% (537) | -3.9% / -16.1% (380) |
| double_calendar_1.25 | E-1->after_release | -7.8% / -16.2% (542) | -6.6% / -16.7% (333) | -4.4% / -12.4% (537) | -7.4% / -19.5% (379) |
| double_calendar_1.25 | E-1->hold_front | -2.3% / -9.6% (543) | -4.5% / -13.4% (333) | -2.8% / -9.6% (537) | +4.4% / -6.2% (383) |
| double_calendar_1.25 | E-2->E+1 | -2.1% / -11.4% (520) | +0.4% / -10.4% (315) | -3.5% / -12.1% (477) | -8.0% / -21.0% (379) |
| double_calendar_1.25 | E-2->hold_front | +1.1% / -7.3% (520) | +2.7% / -6.8% (315) | -4.1% / -11.7% (477) | -1.5% / -13.2% (379) |
| double_calendar_put | E-1->E+1 | +2.8% / -10.2% (908) | -3.1% / -17.8% (642) | -1.7% / -12.7% (826) | -6.5% / -24.3% (613) |
| double_calendar_put | E-1->after_release | +2.6% / -10.8% (905) | -3.7% / -18.9% (642) | -0.5% / -12.1% (826) | -8.3% / -26.8% (614) |
| double_calendar_put | E-1->hold_front | +5.1% / -6.2% (908) | +2.9% / -9.3% (641) | +1.3% / -8.3% (827) | -1.9% / -18.3% (619) |
| double_calendar_put | E-2->E+1 | +1.2% / -12.8% (923) | -0.0% / -15.1% (639) | -2.1% / -13.7% (751) | -4.6% / -23.0% (582) |
| double_calendar_put | E-2->hold_front | +3.6% / -9.0% (923) | +3.2% / -10.2% (638) | -0.2% / -10.4% (752) | -3.2% / -19.2% (583) |
| double_calendar_straddle_2w | E-1->E+1 | +1.5% / -5.0% (541) | +2.0% / -5.2% (319) | -0.6% / -6.4% (430) | +1.1% / -8.0% (315) |
| double_calendar_straddle_2w | E-1->after_release | +0.2% / -6.7% (540) | +1.0% / -6.1% (319) | -1.7% / -7.7% (429) | -4.3% / -13.3% (314) |
| double_calendar_straddle_2w | E-1->hold_front | +5.1% / -0.7% (541) | +6.4% / -0.0% (319) | +1.7% / -3.4% (430) | +5.2% / -3.7% (317) |
| double_calendar_straddle_2w | E-2->E+1 | +2.9% / -3.9% (533) | +2.8% / -4.7% (346) | -2.4% / -8.5% (381) | -1.2% / -10.4% (312) |
| double_calendar_straddle_2w | E-2->hold_front | +6.8% / +0.8% (533) | +4.9% / -1.7% (345) | -0.5% / -6.1% (381) | +2.5% / -6.4% (312) |
| double_calendar_straddle | E-1->E+1 | -4.2% / -13.1% (686) | -4.4% / -14.9% (435) | -3.8% / -12.4% (658) | -7.7% / -21.3% (465) |
| double_calendar_straddle | E-1->after_release | -6.3% / -15.9% (685) | -6.6% / -17.4% (435) | -3.3% / -12.9% (657) | -10.1% / -23.6% (465) |
| double_calendar_straddle | E-1->hold_front | -1.3% / -9.3% (686) | -0.2% / -9.7% (435) | -1.3% / -9.1% (658) | -2.3% / -14.4% (466) |
| double_calendar_straddle | E-2->E+1 | +1.7% / -8.1% (659) | -1.2% / -12.4% (428) | -3.0% / -12.1% (573) | -2.7% / -16.0% (441) |
| double_calendar_straddle | E-2->hold_front | +4.4% / -4.5% (659) | +1.7% / -8.1% (427) | -0.8% / -8.9% (573) | +1.5% / -10.9% (441) |
| double_diagonal_put | E-1->E+1 | +2.2% / -5.0% (643) | -6.7% / -15.5% (423) | -3.0% / -9.2% (555) | +0.3% / -6.8% (313) |
| double_diagonal_put | E-1->after_release | +3.0% / -4.9% (641) | -6.0% / -15.0% (423) | -1.4% / -7.9% (555) | -0.7% / -8.2% (313) |
| double_diagonal_put | E-1->hold_front | +2.2% / -4.2% (643) | -4.2% / -11.7% (422) | -3.0% / -8.4% (557) | -0.4% / -6.8% (314) |
| double_diagonal_put | E-2->E+1 | +3.0% / -4.0% (588) | -2.3% / -11.0% (419) | -2.8% / -8.8% (492) | -1.7% / -9.4% (296) |
| double_diagonal_put | E-2->hold_front | +3.7% / -2.8% (589) | -0.0% / -7.6% (418) | -2.5% / -7.7% (492) | -0.9% / -7.8% (298) |
| double_diagonal_straddle | E-1->E+1 | -3.6% / -7.6% (590) | -6.5% / -11.2% (372) | -4.5% / -8.1% (545) | -4.1% / -9.0% (376) |
| double_diagonal_straddle | E-1->after_release | -2.8% / -7.1% (589) | -5.1% / -10.0% (372) | -4.4% / -8.2% (545) | -5.1% / -10.1% (375) |
| double_diagonal_straddle | E-1->hold_front | -1.3% / -4.7% (590) | -3.8% / -8.0% (372) | -4.4% / -7.5% (545) | -3.0% / -7.2% (378) |
| double_diagonal_straddle | E-2->E+1 | -1.3% / -5.5% (589) | -1.7% / -6.8% (355) | -3.6% / -7.2% (515) | -6.2% / -11.1% (341) |
| double_diagonal_straddle | E-2->hold_front | -0.8% / -4.6% (589) | -1.9% / -6.1% (355) | -4.2% / -7.4% (516) | -4.8% / -9.3% (344) |
| hist_drift_vertical | E-1->E+1 | -0.6% / -4.5% (1388) | -2.3% / -6.7% (1004) | -2.6% / -6.0% (1250) | -0.8% / -5.2% (1041) |
| hist_drift_vertical | E-1->E+3 | -1.1% / -5.0% (1190) | -4.7% / -8.9% (843) | -1.1% / -4.4% (1052) | -1.7% / -6.4% (892) |
| hist_drift_vertical | E-1->after_release | -1.5% / -5.5% (1429) | -2.1% / -6.6% (1050) | -2.7% / -6.1% (1287) | -1.6% / -5.7% (1080) |
| post_iron_fly | E+1->E+2 | -8.4% / -18.7% (1134) | -8.9% / -20.1% (796) | -8.9% / -19.4% (1069) | -6.6% / -19.1% (835) |
| post_iron_fly | E+1->E+3 | -8.8% / -19.0% (1149) | -9.4% / -20.1% (808) | -9.9% / -19.9% (1059) | -6.1% / -17.9% (851) |
| post_momentum_vertical | E+1->E+2 | -4.3% / -8.6% (1102) | -4.0% / -8.6% (724) | -3.8% / -7.8% (1053) | -2.6% / -7.5% (834) |
| post_momentum_vertical | E+1->E+3 | -1.9% / -6.2% (1139) | -1.5% / -6.0% (757) | -3.4% / -7.4% (1063) | +0.8% / -3.9% (893) |
| post_reversal_vertical | E+1->E+2 | -2.2% / -6.6% (984) | -2.4% / -7.0% (679) | -0.4% / -4.5% (937) | -3.8% / -8.5% (720) |
| post_reversal_vertical | E+1->E+3 | -5.4% / -9.8% (1007) | -2.3% / -6.9% (699) | +0.5% / -3.3% (943) | -8.3% / -12.9% (757) |
| reverse_straddle_calendar | E-1->E+1 | -2.6% / -5.5% (1100) | -2.2% / -5.2% (764) | -1.6% / -3.9% (916) | -1.2% / -4.3% (777) |
| reverse_straddle_calendar | E-1->after_release | -2.7% / -5.7% (1097) | -1.8% / -5.0% (763) | -1.9% / -4.4% (916) | -1.1% / -4.2% (777) |
| reverse_straddle_calendar | E-1->hold_front | -3.0% / -5.4% (1100) | -2.6% / -5.3% (764) | -1.6% / -3.6% (916) | -1.6% / -4.3% (777) |
| reverse_straddle_calendar | E-2->E+1 | -1.9% / -4.7% (1044) | -2.5% / -5.4% (749) | -2.0% / -4.2% (844) | -1.1% / -4.3% (729) |
| reverse_straddle_calendar | E-2->hold_front | -2.0% / -4.4% (1044) | -3.1% / -5.6% (749) | -2.1% / -4.1% (844) | -1.5% / -4.1% (728) |
