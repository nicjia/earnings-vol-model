# Research5: autonomous earnings-options strategy study

Frozen 2026-10-02T19:49:31.564704+00:00 on sample A; evaluated 2026-10-02T19:52:19.244320+00:00. Protocol sha256 `ee89673b6c02f7a5`, grid sha256 `a48a1535e065f2f9`.

Returns are equal-risk event returns on max-loss risk (debit for long premium and calendars), closing midpoint fills unless stated, $0.65/contract/side fees. Samples: A = 2018-2021 name half A (selection), B = 2018-2021 name half B, C = 2022-2023, D = 2024-2025 (quotes end 2025-08-26).

## Verdict

0 of 5 frozen policies qualified under the pre-registered gates (55 of 1224 candidates were eligible on sample A).

## Frozen policies

### `long_straddle|E-2->E-1|R<=0.9|tight`

Stage-A max-t adjusted p = 0.110. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 228 | 72 | +2.6% | [+0.9%, +4.9%] | +1.4% | +0.2% | +1.2% | 51% | -17.6% |
| B | 198 | 65 | -0.4% | [-1.6%, +0.8%] | -1.6% | -2.9% | -1.0% | 42% | -58.3% |
| C | 212 | 92 | +2.1% | [+0.3%, +3.7%] | +1.0% | -0.1% | +1.3% | 51% | -28.8% |
| D | 170 | 87 | +1.3% | [-0.1%, +2.5%] | +0.1% | -1.0% | +0.5% | 51% | -20.9% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not available: no option quotes at E-3 | | | | | | | | |
| C | not available: no option quotes at E-3 | | | | | | | | |
| D | not available: no option quotes at E-3 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 228 | +12.6% | +2.3% | +6.7% | +4.5% |
| B | 198 | -1.4% | +2.9% | -6.2% | +6.8% |
| C | 212 | +9.3% | +3.1% | +4.3% | +4.2% |
| D | 172 | +4.4% | +1.2% | +0.5% | +1.5% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; A: max-t adjusted p not < 0.05

### `long_strangle|E-2->E-1|R<=0.9|tight`

Stage-A max-t adjusted p = 0.234. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 202 | 64 | +4.7% | [+1.1%, +9.1%] | +3.4% | +2.1% | +1.5% | 50% | -28.0% |
| B | 161 | 52 | -0.1% | [-2.1%, +2.2%] | -1.4% | -2.8% | -1.4% | 40% | -30.7% |
| C | 165 | 75 | +3.6% | [+0.8%, +6.2%] | +2.4% | +1.2% | +2.0% | 52% | -30.5% |
| D | 143 | 77 | +2.3% | [-0.3%, +4.5%] | +0.9% | -0.5% | +0.9% | 52% | -30.7% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | not available: no option quotes at E-3 | | | | | | | | |
| C | not available: no option quotes at E-3 | | | | | | | | |
| D | not available: no option quotes at E-3 | | | | | | | | |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 202 | +20.6% | +4.0% | +14.4% | +6.0% |
| B | 161 | -0.3% | +3.5% | -4.5% | +5.2% |
| C | 165 | +12.5% | +3.4% | +8.1% | +4.1% |
| D | 145 | +6.7% | +1.4% | +2.6% | +2.0% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; A: max-t adjusted p not < 0.05

### `short_iron_condor_wide|E-1->after_release|R>=1.0|standard`

Stage-A max-t adjusted p = 0.454. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 482 | 106 | +2.1% | [-0.4%, +4.5%] | +0.9% | -0.4% | +1.8% | 69% | -163.9% |
| B | 319 | 84 | +0.4% | [-2.6%, +3.3%] | -1.1% | -2.6% | -0.1% | 66% | -100.5% |
| C | 515 | 157 | -2.9% | [-5.7%, -0.3%] | -4.1% | -5.3% | -3.2% | 63% | -104.0% |
| D | 347 | 137 | -1.3% | [-5.7%, +2.4%] | -2.8% | -4.2% | -1.8% | 65% | -105.0% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 264 | 76 | +0.4% | [-3.3%, +3.9%] | -0.9% | -2.2% | -0.4% | 66% | -100.3% |
| C | 445 | 150 | -2.8% | [-6.6%, +0.9%] | -3.9% | -5.0% | -3.4% | 63% | -101.5% |
| D | 301 | 127 | +0.5% | [-4.3%, +4.7%] | -0.8% | -2.2% | -0.2% | 68% | -106.8% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 484 | +19.7% | +9.7% | +6.2% | +11.2% |
| B | 319 | +2.0% | +7.5% | -7.4% | +9.8% |
| C | 520 | -27.7% | +33.7% | -36.0% | +40.4% |
| D | 350 | -9.2% | +19.4% | -17.8% | +25.5% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05

### `short_iron_fly_2x|E-1->after_release|R>=1.0|tight`

Stage-A max-t adjusted p = 0.394. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 283 | 71 | +4.2% | [-0.2%, +8.7%] | +3.1% | +1.9% | +3.2% | 62% | -129.4% |
| B | 164 | 56 | -0.5% | [-7.0%, +6.1%] | -1.7% | -3.0% | -2.4% | 59% | -100.0% |
| C | 357 | 118 | -2.5% | [-6.9%, +1.8%] | -3.6% | -4.6% | -3.3% | 58% | -101.7% |
| D | 181 | 81 | +4.1% | [-1.6%, +9.5%] | +2.9% | +1.6% | +2.5% | 59% | -99.5% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 141 | 50 | -1.8% | [-8.5%, +5.1%] | -3.0% | -4.3% | -4.2% | 56% | -99.4% |
| C | 313 | 112 | -3.7% | [-9.4%, +1.4%] | -4.8% | -5.8% | -4.9% | 54% | -100.6% |
| D | 153 | 70 | +3.2% | [-3.8%, +9.9%] | +2.0% | +0.8% | +1.2% | 59% | -99.5% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 285 | +25.4% | +12.4% | +17.6% | +13.2% |
| B | 164 | -2.0% | +7.6% | -6.0% | +8.0% |
| C | 360 | -17.9% | +19.7% | -24.1% | +25.2% |
| D | 183 | +16.4% | +8.7% | +11.3% | +9.1% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; A: max-t adjusted p not < 0.05

### `short_iron_condor|E-1->after_release|R>=1.4|tight`

Stage-A max-t adjusted p = 0.632. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 218 | 70 | +4.1% | [-1.1%, +9.4%] | +2.2% | +0.3% | +2.7% | 63% | -100.4% |
| B | 130 | 54 | +1.9% | [-4.2%, +7.8%] | -0.3% | -2.6% | -0.7% | 58% | -100.6% |
| C | 236 | 102 | -2.3% | [-7.6%, +2.6%] | -4.2% | -6.0% | -3.8% | 57% | -102.8% |
| D | 132 | 65 | -2.3% | [-10.9%, +6.6%] | -4.6% | -6.8% | -4.9% | 58% | -104.0% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 119 | 49 | +3.6% | [-3.1%, +10.0%] | +1.5% | -0.7% | +0.7% | 56% | -96.2% |
| C | 216 | 99 | -2.5% | [-8.1%, +2.9%] | -4.2% | -6.0% | -4.4% | 55% | -104.1% |
| D | 124 | 68 | -2.1% | [-11.7%, +7.0%] | -4.4% | -6.7% | -5.0% | 59% | -104.1% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 219 | +18.6% | +7.9% | +9.2% | +8.7% |
| B | 130 | +4.7% | +4.6% | -1.2% | +6.2% |
| C | 237 | -11.2% | +25.6% | -18.7% | +28.9% |
| D | 132 | -6.6% | +13.4% | -12.0% | +16.7% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05

## Autonomous walk-forward selector

Each year the same eligibility rule and objective pick one candidate from all earlier years; it then trades that year untouched.

| Year | Policy chosen from earlier years | Train lower bound | OOS events | OOS mean (mid) | OOS mean 25% cost | OOS win rate |
|---|---|---|---|---|---|---|
| 2020 | `long_strangle|E-2->E-1|R<=0.9|tight` | +1.4% | 68 | -0.9% | -2.2% | 31% |
| 2021 | `long_straddle|E-2->E-1|TS<=1.1|standard` | +1.6% | 69 | -4.0% | -6.0% | 28% |
| 2022 | `long_strangle|E-1->E+3|R<=0.9|tight` | +2.0% | 10 | -21.3% | -22.6% | 40% |
| 2023 | `long_strangle|E-2->E-1|HR>=1.2|tight` | +0.7% | 60 | -0.1% | -1.3% | 47% |
| 2024 | `long_strangle|E-1->E+1|R<=0.75|tight` | +4.7% | 30 | -1.3% | -2.5% | 37% |
| 2025 | `long_strangle|E-1->E+2|R<=0.75|tight` | +4.9% | 3 | -5.7% | -7.2% | 33% |

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| 2020-2025 OOS | 240 | 102 | -2.5% | [-7.7%, +2.6%] | -4.0% | -5.5% | -6.8% | 35% | -97.7% |
| 2022-2025 OOS | 103 | 46 | -2.7% | [-14.9%, +9.5%] | -3.9% | -5.1% | -12.9% | 43% | -97.7% |

Illustrative account over the walk-forward trades: -12.2% at mid (max drawdown +14.6%), -18.3% at 25% cost.

## Post-freeze diagnostics (all 1,224 candidates; cannot change the frozen set)

| Sample | Candidates with >=100 events | Mean > 0 | Normal lower bound > 0 | Mean 25% cost > 0 |
|---|---|---|---|---|
| A | 1102 | 441 | 14 | 95 |
| B | 993 | 397 | 21 | 82 |
| C | 1101 | 290 | 15 | 130 |
| D | 1037 | 338 | 28 | 165 |

Candidates positive at 25% cost and excluding their best 5 events in all four samples (>=50 events each): 0. These are found after seeing B/C/D and are hypotheses for new data, not validated results.


### Unfiltered base strategies by sample (standard liquidity, midpoint mean / 25%-cost mean, events)

| Family | Timing | A | B | C | D |
|---|---|---|---|---|---|
| call_calendar | E-1->E+1 | -0.2% / -23.8% (910) | -1.0% / -31.5% (652) | -3.2% / -20.9% (809) | -4.0% / -32.5% (630) |
| call_calendar | E-1->E+2 | -4.0% / -28.3% (825) | +2.8% / -29.6% (576) | -1.0% / -19.5% (694) | -8.1% / -38.9% (546) |
| call_calendar | E-1->E+3 | -2.3% / -30.8% (727) | +2.0% / -32.3% (491) | -6.3% / -26.7% (595) | -7.5% / -40.7% (458) |
| call_calendar | E-1->E | +0.2% / -20.5% (1060) | +1.0% / -24.6% (774) | +0.0% / -15.8% (948) | -3.5% / -26.2% (742) |
| call_calendar | E-1->after_release | +2.0% / -20.0% (977) | -1.3% / -29.6% (713) | -1.1% / -18.2% (877) | -6.4% / -32.1% (679) |
| call_calendar | E-2->E+1 | -0.3% / -26.7% (872) | +2.3% / -30.2% (618) | -5.2% / -23.2% (716) | -1.1% / -30.1% (605) |
| call_calendar | E-2->E-1 | -2.5% / -22.6% (994) | -1.8% / -26.0% (741) | -4.0% / -19.2% (853) | -2.3% / -21.4% (705) |
| call_calendar | E-2->E | +3.0% / -20.3% (994) | +4.6% / -22.2% (741) | +0.1% / -17.1% (853) | -2.5% / -27.1% (705) |
| call_calendar | E-2->after_release | +2.5% / -23.1% (926) | +2.5% / -28.6% (680) | -0.6% / -18.0% (771) | -4.6% / -31.4% (641) |
| long_straddle | E-1->E+1 | -1.2% / -3.3% (1684) | -1.6% / -3.9% (1303) | +1.3% / -0.5% (1540) | +0.1% / -2.1% (1258) |
| long_straddle | E-1->E+2 | -1.2% / -3.2% (1565) | -1.6% / -3.8% (1189) | +2.5% / +0.7% (1411) | +0.3% / -2.0% (1191) |
| long_straddle | E-1->E+3 | -1.4% / -3.4% (1454) | -0.0% / -2.3% (1101) | +2.9% / +1.2% (1276) | +1.1% / -1.4% (1101) |
| long_straddle | E-1->E | -0.0% / -2.1% (1796) | -2.0% / -4.3% (1416) | +0.1% / -1.7% (1663) | +1.5% / -0.5% (1355) |
| long_straddle | E-1->after_release | -2.4% / -4.5% (1731) | -2.5% / -4.8% (1355) | -0.5% / -2.3% (1587) | -0.1% / -2.2% (1312) |
| long_straddle | E-2->E+1 | -0.4% / -2.4% (1657) | -1.5% / -3.7% (1285) | +2.2% / +0.4% (1485) | -1.0% / -3.3% (1248) |
| long_straddle | E-2->E-1 | +0.7% / -1.1% (1769) | +0.3% / -1.6% (1413) | +0.3% / -1.3% (1613) | +0.7% / -1.0% (1343) |
| long_straddle | E-2->E | +0.9% / -1.1% (1769) | -2.2% / -4.4% (1413) | +1.5% / -0.3% (1612) | +2.0% / -0.0% (1342) |
| long_straddle | E-2->after_release | -1.8% / -3.9% (1705) | -2.6% / -4.8% (1352) | +0.8% / -1.0% (1535) | -0.1% / -2.3% (1295) |
| long_strangle | E-1->E+1 | -0.5% / -2.9% (1566) | -0.1% / -2.7% (1221) | +3.7% / +1.6% (1455) | -0.6% / -3.3% (1207) |
| long_strangle | E-1->E+2 | +0.5% / -1.9% (1469) | -1.5% / -4.0% (1141) | +4.3% / +2.3% (1335) | -1.5% / -4.3% (1142) |
| long_strangle | E-1->E+3 | -1.7% / -4.1% (1368) | +0.1% / -2.3% (1043) | +3.6% / +1.6% (1236) | +0.6% / -2.2% (1054) |
| long_strangle | E-1->E | +0.4% / -2.0% (1675) | -3.0% / -5.4% (1285) | +1.7% / -0.4% (1570) | +2.9% / +0.4% (1288) |
| long_strangle | E-1->after_release | -2.3% / -4.7% (1605) | -1.9% / -4.5% (1259) | +1.2% / -1.0% (1500) | +0.4% / -2.3% (1248) |
| long_strangle | E-2->E+1 | -0.2% / -2.7% (1611) | -1.7% / -4.2% (1229) | +3.6% / +1.5% (1423) | -1.6% / -4.2% (1173) |
| long_strangle | E-2->E-1 | +1.0% / -1.1% (1707) | -0.0% / -2.3% (1311) | +0.0% / -1.9% (1544) | +1.4% / -0.7% (1262) |
| long_strangle | E-2->E | +2.2% / -0.1% (1708) | -3.7% / -6.2% (1311) | +2.4% / +0.2% (1541) | +1.7% / -0.7% (1255) |
| long_strangle | E-2->after_release | -2.7% / -5.2% (1651) | -3.2% / -5.8% (1267) | +1.4% / -0.8% (1466) | -1.0% / -3.6% (1205) |
| short_iron_condor_wide | E-1->E+1 | +0.5% / -0.7% (657) | -2.2% / -3.6% (438) | -3.5% / -4.7% (703) | -0.1% / -1.5% (466) |
| short_iron_condor_wide | E-1->E+2 | +0.2% / -1.1% (589) | -1.9% / -3.3% (391) | -3.8% / -4.9% (591) | -0.7% / -2.2% (398) |
| short_iron_condor_wide | E-1->E+3 | -0.6% / -1.9% (508) | -2.4% / -3.8% (324) | -4.5% / -5.6% (483) | -0.0% / -1.5% (313) |
| short_iron_condor_wide | E-1->E | +0.3% / -1.1% (744) | -1.0% / -2.6% (526) | -2.6% / -3.7% (817) | -2.7% / -4.1% (559) |
| short_iron_condor_wide | E-1->after_release | +1.4% / +0.2% (692) | -0.8% / -2.2% (481) | -2.8% / -4.0% (748) | -1.6% / -2.9% (507) |
| short_iron_condor_wide | E-2->E+1 | -1.5% / -2.8% (652) | +0.0% / -1.4% (416) | -2.8% / -3.9% (621) | -1.5% / -2.9% (435) |
| short_iron_condor_wide | E-2->E-1 | -2.5% / -3.8% (739) | -2.3% / -3.7% (509) | -2.1% / -3.3% (742) | -2.0% / -3.3% (496) |
| short_iron_condor_wide | E-2->E | -1.6% / -2.9% (738) | -0.0% / -1.5% (508) | -2.6% / -3.8% (738) | -3.2% / -4.6% (490) |
| short_iron_condor_wide | E-2->after_release | -1.0% / -2.3% (684) | +0.6% / -0.9% (455) | -1.8% / -3.0% (666) | -2.1% / -3.6% (458) |
| short_iron_condor | E-1->E+1 | -1.9% / -4.7% (1125) | -4.2% / -7.4% (800) | -4.4% / -7.1% (1066) | -2.6% / -5.9% (898) |
| short_iron_condor | E-1->E+2 | -2.4% / -5.1% (1017) | -2.2% / -5.2% (723) | -5.4% / -7.8% (936) | -1.3% / -4.7% (790) |
| short_iron_condor | E-1->E+3 | -1.3% / -4.2% (908) | -4.1% / -7.1% (633) | -6.8% / -9.2% (806) | -1.7% / -5.2% (680) |
| short_iron_condor | E-1->E | -2.6% / -5.5% (1254) | -1.9% / -5.1% (928) | -3.7% / -6.5% (1229) | -4.0% / -7.2% (1002) |
| short_iron_condor | E-1->after_release | +0.0% / -2.8% (1165) | -3.3% / -6.5% (862) | -3.9% / -6.6% (1134) | -2.9% / -6.2% (943) |
| short_iron_condor | E-2->E+1 | -1.6% / -4.4% (1112) | -3.5% / -6.7% (766) | -5.9% / -8.6% (997) | -2.6% / -6.0% (836) |
| short_iron_condor | E-2->E-1 | -4.0% / -6.5% (1242) | -3.2% / -6.2% (918) | -2.8% / -5.4% (1164) | -3.1% / -6.0% (963) |
| short_iron_condor | E-2->E | -4.4% / -7.2% (1241) | -2.2% / -5.4% (918) | -3.5% / -6.2% (1160) | -4.2% / -7.3% (946) |
| short_iron_condor | E-2->after_release | -1.0% / -3.7% (1147) | -2.3% / -5.5% (842) | -4.1% / -6.8% (1058) | -2.6% / -5.8% (886) |
| short_iron_fly_1x | E-1->E+1 | -3.0% / -12.5% (1429) | -5.0% / -15.3% (1054) | -5.6% / -14.4% (1322) | -2.2% / -12.8% (1071) |
| short_iron_fly_1x | E-1->E+2 | -3.3% / -12.6% (1279) | -5.3% / -15.3% (956) | -7.3% / -15.9% (1185) | -0.5% / -11.6% (995) |
| short_iron_fly_1x | E-1->E+3 | -1.9% / -11.1% (1162) | -7.2% / -17.0% (851) | -8.0% / -16.7% (1036) | -3.9% / -15.2% (884) |
| short_iron_fly_1x | E-1->E | -5.2% / -14.8% (1566) | -4.5% / -15.1% (1202) | -4.1% / -13.0% (1457) | -5.4% / -15.3% (1173) |
| short_iron_fly_1x | E-1->after_release | -2.0% / -11.7% (1480) | -4.3% / -15.0% (1122) | -3.5% / -12.5% (1371) | -2.0% / -12.4% (1122) |
| short_iron_fly_1x | E-2->E+1 | -4.5% / -13.8% (1388) | -4.7% / -15.2% (1045) | -6.2% / -14.7% (1238) | -1.6% / -12.7% (1052) |
| short_iron_fly_1x | E-2->E-1 | -6.1% / -14.5% (1539) | -6.2% / -15.7% (1188) | -4.7% / -12.7% (1394) | -5.0% / -13.5% (1157) |
| short_iron_fly_1x | E-2->E | -6.8% / -16.4% (1539) | -3.9% / -14.1% (1188) | -4.3% / -13.1% (1388) | -6.3% / -16.3% (1144) |
| short_iron_fly_1x | E-2->after_release | -3.9% / -13.6% (1447) | -3.6% / -14.0% (1112) | -4.8% / -13.6% (1298) | -2.0% / -12.5% (1086) |
| short_iron_fly_2x | E-1->E+1 | +0.3% / -1.3% (671) | -2.1% / -3.9% (466) | -2.4% / -3.8% (720) | -0.2% / -2.1% (501) |
| short_iron_fly_2x | E-1->E+2 | -0.2% / -1.8% (600) | -2.1% / -3.9% (414) | -2.9% / -4.3% (616) | -1.4% / -3.5% (436) |
| short_iron_fly_2x | E-1->E+3 | +1.5% / -0.2% (510) | -2.7% / -4.5% (352) | -4.7% / -6.0% (507) | -2.9% / -5.0% (344) |
| short_iron_fly_2x | E-1->E | +0.4% / -1.3% (759) | -0.2% / -2.0% (550) | -1.7% / -3.1% (835) | -2.5% / -4.3% (587) |
| short_iron_fly_2x | E-1->after_release | +1.3% / -0.4% (711) | +0.0% / -1.8% (510) | -1.5% / -2.9% (767) | -1.8% / -3.7% (542) |
| short_iron_fly_2x | E-2->E+1 | -1.6% / -3.2% (664) | -0.6% / -2.5% (441) | -2.3% / -3.7% (635) | -1.1% / -3.1% (432) |
| short_iron_fly_2x | E-2->E-1 | -2.4% / -3.8% (749) | -1.8% / -3.5% (530) | -1.7% / -2.9% (745) | -1.6% / -3.1% (514) |
| short_iron_fly_2x | E-2->E | -1.2% / -2.8% (747) | +0.7% / -1.1% (529) | -1.7% / -3.1% (741) | -3.7% / -5.5% (509) |
| short_iron_fly_2x | E-2->after_release | +0.1% / -1.5% (698) | +1.2% / -0.7% (477) | -1.3% / -2.7% (678) | -1.5% / -3.5% (473) |
| straddle_calendar | E-1->E+1 | -0.8% / -24.1% (877) | -2.4% / -29.1% (585) | -3.5% / -21.5% (735) | -5.4% / -36.3% (597) |
| straddle_calendar | E-1->E+2 | -5.0% / -30.1% (768) | +4.5% / -25.0% (508) | -0.5% / -20.2% (624) | -2.7% / -38.1% (511) |
| straddle_calendar | E-1->E+3 | -3.5% / -30.8% (681) | -1.3% / -33.4% (427) | -2.8% / -24.1% (532) | -1.3% / -42.6% (427) |
| straddle_calendar | E-1->E | -0.4% / -20.4% (1023) | -1.3% / -24.5% (720) | -1.9% / -18.0% (881) | -6.9% / -32.7% (717) |
| straddle_calendar | E-1->after_release | +0.7% / -21.1% (943) | -3.8% / -29.1% (650) | -3.6% / -21.2% (806) | -9.0% / -38.0% (645) |
| straddle_calendar | E-2->E+1 | -1.5% / -25.8% (814) | +1.3% / -24.8% (571) | -4.2% / -21.8% (657) | -7.2% / -39.6% (564) |
| straddle_calendar | E-2->E-1 | -5.7% / -24.3% (973) | -5.9% / -27.2% (700) | -5.1% / -20.8% (805) | -5.5% / -25.4% (665) |
| straddle_calendar | E-2->E | -0.6% / -23.3% (973) | +0.8% / -22.5% (700) | +0.3% / -17.2% (805) | -8.6% / -35.3% (664) |
| straddle_calendar | E-2->after_release | -0.6% / -24.7% (891) | +0.9% / -24.0% (633) | -1.0% / -19.0% (722) | -9.6% / -39.5% (604) |
