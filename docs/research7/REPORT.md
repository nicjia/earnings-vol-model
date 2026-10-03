# Research7: release-timed earnings options (I/B/E/S announcement times)

Frozen 2026-10-03T04:26:22.603387+00:00 on sample A; evaluated 2026-10-03T04:34:14.731970+00:00. Protocol sha256 `7c560c15ce00363f`, grid sha256 `1cfee7b5a50cc480`.

Returns are equal-risk event returns on max-loss risk (debit for long premium and calendars), closing midpoint fills unless stated, $0.65/contract/side fees. Samples: A = 2018-2021 name half A (selection), B = 2018-2021 name half B, C = 2022-2023, D = 2024-2025 (quotes end 2025-08-26).

## Verdict

0 of 5 frozen policies qualified under the pre-registered gates (171 of 1944 candidates were eligible on sample A).

## Frozen policies

### `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight`

Stage-A max-t adjusted p = 0.016. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 290 | 70 | +21.3% | [+10.7%, +32.2%] | +10.4% | -0.5% | +15.7% | 59% | -151.3% |
| B | 175 | 48 | +14.0% | [-2.2%, +32.2%] | +2.5% | -8.9% | +5.2% | 54% | -161.9% |
| C | 212 | 93 | +13.7% | [+2.8%, +24.6%] | +4.6% | -4.5% | +8.9% | 55% | -130.1% |
| D | 217 | 84 | +8.7% | [-4.0%, +21.0%] | -3.5% | -15.7% | +4.3% | 50% | -213.3% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 113 | 40 | +21.2% | [+3.8%, +39.9%] | +9.0% | -3.2% | +10.5% | 52% | -161.9% |
| C | 136 | 64 | +1.0% | [-11.5%, +13.1%] | -8.9% | -18.7% | -6.1% | 50% | -130.9% |
| D | 167 | 76 | -3.0% | [-15.8%, +10.6%] | -15.9% | -28.8% | -8.7% | 47% | -213.9% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 291 | +212.6% | +6.7% | +70.0% | +11.0% |
| B | 175 | +53.4% | +13.5% | +2.8% | +22.4% |
| C | 215 | +75.4% | +13.7% | +19.5% | +20.8% |
| D | 223 | +45.2% | +16.5% | -15.6% | +31.8% |

Failed gates: B: bootstrap lower bound not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; E: pending (expanded universe not yet evaluated)

### `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight`

Stage-A max-t adjusted p = 0.096. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 629 | 106 | +13.6% | [+5.3%, +21.7%] | +0.2% | -13.2% | +10.1% | 45% | -279.8% |
| B | 420 | 79 | +14.3% | [+1.1%, +28.0%] | -0.9% | -16.1% | +8.9% | 43% | -221.4% |
| C | 611 | 144 | +5.3% | [-5.3%, +16.7%] | -5.8% | -16.9% | +2.1% | 41% | -434.8% |
| D | 515 | 153 | -3.9% | [-14.4%, +7.7%] | -23.9% | -44.0% | -8.5% | 38% | -383.8% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 384 | 74 | +14.7% | [+1.2%, +28.4%] | -1.8% | -18.4% | +9.0% | 42% | -227.1% |
| C | 551 | 141 | +7.4% | [-4.5%, +20.6%] | -5.7% | -18.7% | +3.1% | 39% | -434.8% |
| D | 505 | 147 | -7.3% | [-17.5%, +2.8%] | -30.3% | -53.3% | -11.6% | 38% | -383.8% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 636 | +374.6% | +25.3% | -11.7% | +47.1% |
| B | 420 | +182.7% | +35.6% | -20.9% | +51.9% |
| C | 616 | +48.5% | +32.5% | -63.0% | +64.4% |
| D | 522 | -43.6% | +62.2% | -93.8% | +94.7% |

Failed gates: B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; D: mean excluding best 5 not > 0; A: max-t adjusted p not < 0.05; E: pending (expanded universe not yet evaluated)

### `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard`

Stage-A max-t adjusted p = 0.270. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 305 | 76 | +19.0% | [+6.0%, +33.3%] | +7.4% | -4.1% | +13.2% | 51% | -144.9% |
| B | 195 | 53 | +24.4% | [+10.0%, +40.3%] | +10.8% | -2.7% | +16.6% | 51% | -118.0% |
| C | 207 | 89 | +16.5% | [+2.5%, +31.2%] | +6.9% | -2.7% | +10.9% | 49% | -116.4% |
| D | 257 | 102 | +4.8% | [-5.9%, +15.4%] | -9.5% | -23.9% | +0.0% | 42% | -350.7% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 123 | 36 | +32.6% | [+5.9%, +61.6%] | +18.9% | +5.3% | +16.9% | 48% | -156.0% |
| C | 138 | 71 | +2.1% | [-12.6%, +17.6%] | -7.8% | -17.8% | -6.7% | 40% | -114.8% |
| D | 180 | 85 | +1.6% | [-11.7%, +16.5%] | -14.3% | -30.3% | -4.8% | 41% | -159.6% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 305 | +186.9% | +20.1% | +44.1% | +32.0% |
| B | 195 | +145.1% | +12.2% | +45.3% | +20.0% |
| C | 211 | +88.1% | +18.1% | +26.4% | +28.3% |
| D | 263 | +29.6% | +17.7% | -38.2% | +46.4% |

Failed gates: D: bootstrap lower bound not > 0; D: mean at 25% half-spread not > 0; A: max-t adjusted p not < 0.05; E: pending (expanded universe not yet evaluated)

### `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight`

Stage-A max-t adjusted p = 0.234. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 161 | 48 | +13.1% | [+4.2%, +22.9%] | +8.8% | +4.6% | +8.8% | 67% | -100.0% |
| B | 87 | 34 | -1.3% | [-11.6%, +10.1%] | -6.2% | -11.1% | -7.4% | 53% | -108.4% |
| C | 151 | 66 | -2.4% | [-11.5%, +6.3%] | -6.3% | -10.2% | -6.1% | 55% | -102.0% |
| D | 62 | 37 | +5.6% | [-8.7%, +18.4%] | +0.5% | -4.7% | -3.2% | 60% | -107.2% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 83 | 33 | +2.5% | [-9.1%, +14.2%] | -1.5% | -5.5% | -3.2% | 57% | -101.5% |
| C | 152 | 69 | -9.3% | [-18.6%, -0.1%] | -13.2% | -17.2% | -13.2% | 48% | -114.6% |
| D | 56 | 31 | +12.8% | [-3.8%, +30.4%] | +8.5% | +4.2% | +2.8% | 64% | -105.9% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 162 | +52.8% | +6.5% | +33.2% | +8.9% |
| B | 87 | -2.6% | +10.7% | -10.6% | +14.7% |
| C | 152 | -6.7% | +18.6% | -17.2% | +24.1% |
| D | 62 | +6.8% | +6.4% | +0.2% | +8.2% |

Failed gates: B: bootstrap lower bound not > 0; B: mean at 25% half-spread not > 0; C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; D: bootstrap lower bound not > 0; D: mean excluding best 5 not > 0; D: fewer than 100 events or 40 issuers; A: max-t adjusted p not < 0.05; E: pending (expanded universe not yet evaluated)

### `through:double_calendar_straddle_2w|P-4->hold_front|none|standard`

Stage-A max-t adjusted p = 0.162. Qualified: **no**.

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A (selection) | 475 | 88 | +11.5% | [+4.0%, +19.8%] | +4.9% | -1.6% | +8.7% | 50% | -131.1% |
| B | 242 | 56 | +15.4% | [+5.4%, +27.2%] | +8.7% | +2.0% | +10.4% | 54% | -122.5% |
| C | 314 | 116 | +4.1% | [-1.4%, +10.0%] | -1.3% | -6.7% | +1.8% | 48% | -95.7% |
| D | 265 | 109 | +11.0% | [+4.6%, +17.5%] | +2.5% | -6.0% | +7.5% | 51% | -94.9% |

Signal one session earlier (contracts fixed at decision, executed next close):

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| B | 241 | 58 | +14.4% | [+3.6%, +25.9%] | +7.8% | +1.3% | +10.2% | 50% | -103.7% |
| C | 313 | 112 | -1.6% | [-7.4%, +4.7%] | -7.1% | -12.5% | -3.9% | 45% | -109.4% |
| D | 256 | 105 | +8.7% | [+1.1%, +16.5%] | +0.2% | -8.4% | +5.1% | 49% | -88.7% |

Illustrative account (2% of equity at max-loss risk per trade, overlapping positions allowed):

| Sample | Trades | Total return mid | Max drawdown mid | Total return 25% cost | Max drawdown 25% cost |
|---|---|---|---|---|---|
| A | 476 | +168.1% | +14.8% | +45.4% | +23.8% |
| B | 242 | +102.2% | +10.8% | +47.3% | +14.6% |
| C | 319 | +26.7% | +11.4% | -9.9% | +17.8% |
| D | 269 | +77.1% | +12.5% | +14.2% | +22.0% |

Failed gates: C: bootstrap lower bound not > 0; C: mean at 25% half-spread not > 0; A: max-t adjusted p not < 0.05; E: pending (expanded universe not yet evaluated)

## Autonomous walk-forward selector

Each year the same eligibility rule and objective pick one candidate from all earlier years; it then trades that year untouched.

| Year | Policy chosen from earlier years | Train lower bound | OOS events | OOS mean (mid) | OOS mean 25% cost | OOS win rate |
|---|---|---|---|---|---|---|
| 2020 | `through:atm_put_calendar_1w|P-1->Q|HR<=1.0|standard` | +11.5% | 284 | +7.7% | -9.4% | 53% |
| 2021 | `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` | +11.2% | 96 | +5.8% | -7.8% | 49% |
| 2022 | `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` | +9.5% | 75 | +34.2% | +23.7% | 57% |
| 2023 | `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|standard` | +10.0% | 167 | +15.4% | +5.1% | 54% |
| 2024 | `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|standard` | +10.5% | 188 | -0.0% | -18.9% | 45% |
| 2025 | `through:double_calendar_straddle_1w|P-4->hold_front|D<=1.0|standard` | +5.9% | 77 | -7.3% | -18.6% | 34% |

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| 2020-2025 OOS | 887 | 183 | +8.2% | [+1.9%, +15.6%] | -6.5% | -21.3% | +6.3% | 50% | -375.4% |
| 2022-2025 OOS | 507 | 147 | +9.0% | [+1.4%, +17.1%] | -4.6% | -18.3% | +6.4% | 48% | -299.6% |

Illustrative account over the walk-forward trades: +279.7% at mid (max drawdown +24.4%), -73.9% at 25% cost.

## Post-freeze diagnostics (all 1,944 candidates; cannot change the frozen set)

| Sample | Candidates with >=100 events | Mean > 0 | Normal lower bound > 0 | Mean 25% cost > 0 |
|---|---|---|---|---|
| A | 1688 | 1001 | 184 | 377 |
| B | 1476 | 878 | 160 | 380 |
| C | 1683 | 648 | 39 | 178 |
| D | 1512 | 642 | 37 | 186 |

Candidates positive at 25% cost and excluding their best 5 events in all four samples (>=50 events each): 14. These are found after seeing B/C/D and are hypotheses for new data, not validated results.

| Candidate | A mean / lower | B mean / lower | C mean / lower | D mean / lower |
|---|---|---|---|---|
| `through:double_calendar_straddle_2w|P-4->hold_front|TSw>=1.15|standard` | +18.5% / +7.1% (n=252) | +28.2% / +11.0% (n=129) | +12.3% / +3.8% (n=152) | +12.2% / +3.3% (n=174) |
| `pre:long_straddle|P-1->P|R<=0.9|tight` | +1.4% / +0.0% (n=151) | +2.1% / +0.5% (n=136) | +4.0% / +1.9% (n=140) | +3.1% / +1.3% (n=108) |
| `through:double_calendar_straddle_2w|P-4->hold_front|D<=1.0|standard` | +11.2% / +0.4% (n=199) | +13.1% / +0.1% (n=106) | +8.9% / -0.1% (n=130) | +16.2% / +4.1% (n=104) |
| `pre:long_straddle|P-4->P|HR>=1.0|standard` | +2.8% / -0.2% (n=302) | +3.9% / -0.2% (n=224) | +3.0% / +0.1% (n=321) | +2.8% / +0.3% (n=379) |
| `pre:long_straddle|P-4->P|HR>=1.0|tight` | +3.0% / -0.2% (n=230) | +4.2% / -0.4% (n=180) | +3.0% / -0.4% (n=285) | +2.6% / +0.4% (n=331) |
| `pre:long_strangle|P-1->P|HR>=1.0|tight` | +2.4% / -0.7% (n=197) | +3.0% / -0.3% (n=150) | +4.3% / +0.8% (n=245) | +3.4% / +1.2% (n=300) |
| `pre:long_strangle|P-1->P|R<=0.9|tight` | +1.9% / -1.0% (n=124) | +2.9% / -0.2% (n=111) | +6.7% / +3.1% (n=118) | +7.9% / +4.0% (n=101) |
| `pre:long_straddle|P-9->P|none|tight` | +2.1% / -1.7% (n=934) | +2.8% / -0.8% (n=693) | +2.5% / -1.8% (n=815) | +4.7% / +0.5% (n=700) |
| `through:double_calendar_straddle_2w|P-1->hold_front|R>=1.2|standard` | +7.6% / -0.5% (n=294) | +5.8% / -1.9% (n=194) | +5.5% / -1.3% (n=238) | +10.6% / -0.3% (n=152) |
| `through:short_iron_fly_2x|P-4->Q+4|none|standard` | +2.3% / -2.2% (n=427) | +6.5% / +1.2% (n=268) | +3.6% / -0.5% (n=383) | +4.4% / -2.1% (n=290) |
| `through:short_iron_fly_2x|P-4->Q+4|R>=1.0|standard` | +2.4% / -2.3% (n=407) | +7.0% / +1.7% (n=245) | +4.1% / -0.2% (n=352) | +4.8% / -1.9% (n=266) |
| `through:short_iron_condor_wide|P-1->Q|R>=1.2|tight` | +1.8% / -2.8% (n=214) | +1.3% / -4.7% (n=126) | +1.6% / -2.9% (n=218) | +2.5% / -4.1% (n=104) |
| `through:short_iron_condor_wide|P-1->Q|R>=1.4|tight` | +1.8% / -2.9% (n=145) | +1.7% / -5.0% (n=83) | +1.5% / -3.3% (n=149) | +4.1% / -4.8% (n=61) |
| `through:short_iron_fly_2x|P-1->Q+4|D<=1.0|standard` | +2.3% / -3.5% (n=189) | +3.5% / -6.9% (n=104) | +4.7% / -2.3% (n=179) | +4.9% / -2.6% (n=115) |

### Unfiltered base strategies by sample (standard liquidity, midpoint mean / 25%-cost mean, events)

| Family | Timing | A | B | C | D |
|---|---|---|---|---|---|
| post:post_iron_fly_1x | Q->Q+2 | -10.3% / -20.8% (1023) | -9.2% / -19.9% (739) | -10.7% / -20.2% (927) | -8.1% / -20.1% (728) |
| post:post_iron_fly_1x | Q->Q+4 | -12.3% / -23.2% (1004) | -9.8% / -20.8% (714) | -9.5% / -18.9% (873) | -4.8% / -18.4% (714) |
| post:post_momentum_vertical | Q->Q+2 | -0.6% / -5.0% (1061) | -1.8% / -6.8% (780) | +1.6% / -2.4% (999) | -2.5% / -7.3% (863) |
| post:post_momentum_vertical | Q->Q+4 | +3.8% / -0.7% (1075) | +1.8% / -3.2% (749) | -0.9% / -4.8% (972) | -6.3% / -11.6% (866) |
| post:post_reversal_vertical | Q->Q+2 | -3.6% / -7.9% (923) | -3.6% / -8.0% (602) | -2.8% / -6.6% (838) | -3.0% / -7.7% (647) |
| post:post_reversal_vertical | Q->Q+4 | -4.4% / -8.9% (911) | -3.2% / -7.5% (605) | -1.7% / -5.5% (809) | -0.6% / -6.5% (634) |
| post:post_surprise_vertical | Q->Q+2 | +4.9% / +0.7% (974) | -8.7% / -12.8% (673) | -0.9% / -4.5% (914) | -1.2% / -6.0% (768) |
| post:post_surprise_vertical | Q->Q+4 | +8.5% / +4.2% (972) | -6.1% / -10.2% (659) | -1.4% / -5.0% (894) | -3.9% / -9.1% (764) |
| pre:long_straddle | P-1->P | +1.1% / -0.8% (1631) | +1.4% / -0.7% (1259) | +1.2% / -0.4% (1446) | +1.6% / -0.0% (1230) |
| pre:long_straddle | P-4->P | +2.1% / +0.0% (1526) | +1.7% / -0.5% (1174) | +1.4% / -0.2% (1316) | +2.1% / +0.4% (1113) |
| pre:long_straddle | P-9->P | +1.4% / -0.8% (1227) | +3.0% / +0.7% (973) | +1.8% / +0.3% (1004) | +5.1% / +3.1% (857) |
| pre:long_strangle | P-1->P | +1.5% / -0.7% (1557) | +2.0% / -0.4% (1158) | +2.0% / +0.1% (1370) | +2.4% / +0.3% (1183) |
| pre:long_strangle | P-4->P | +3.3% / +1.1% (1444) | +1.9% / -0.4% (1108) | +1.5% / -0.3% (1286) | +2.4% / +0.5% (1080) |
| pre:long_strangle | P-9->P | +2.3% / -0.0% (1211) | +3.2% / +0.6% (921) | +3.5% / +1.6% (1005) | +6.9% / +4.8% (839) |
| pre:short_iron_fly_2x | P-1->P | -2.1% / -3.6% (719) | -2.5% / -4.2% (499) | -2.2% / -3.5% (719) | -2.4% / -3.8% (518) |
| pre:short_iron_fly_2x | P-4->P | -2.3% / -3.8% (631) | -2.6% / -4.5% (410) | -2.6% / -3.8% (615) | -2.6% / -4.0% (438) |
| pre:short_iron_fly_2x | P-9->P | -0.8% / -2.4% (441) | -3.2% / -5.0% (301) | -2.9% / -4.1% (440) | -4.5% / -6.2% (324) |
| pre:straddle_calendar_1w | P-1->P | -2.4% / -22.1% (1021) | -2.7% / -26.3% (726) | -2.1% / -17.2% (861) | -1.4% / -22.2% (739) |
| pre:straddle_calendar_1w | P-4->P | +0.4% / -24.8% (871) | -0.2% / -27.2% (600) | -1.2% / -18.6% (635) | -1.2% / -26.4% (573) |
| pre:straddle_calendar_1w | P-9->P | +0.5% / -29.0% (606) | -3.6% / -38.7% (436) | -0.8% / -22.2% (485) | +8.4% / -25.9% (363) |
| through:atm_put_calendar_1w | P-1->Q | +7.8% / -12.8% (897) | +2.9% / -20.9% (649) | +2.2% / -15.2% (823) | -10.2% / -38.0% (617) |
| through:atm_put_calendar_1w | P-1->hold_front | +10.7% / -6.2% (897) | +12.9% / -6.2% (647) | +6.1% / -7.6% (824) | -7.4% / -28.9% (612) |
| through:atm_put_calendar_1w | P-4->Q | +6.2% / -20.3% (746) | -7.4% / -37.0% (513) | +4.8% / -14.0% (610) | -4.8% / -35.3% (498) |
| through:atm_put_calendar_1w | P-4->hold_front | +6.9% / -14.7% (746) | +10.6% / -14.0% (512) | +4.5% / -10.6% (609) | +2.4% / -23.3% (495) |
| through:atm_put_calendar_1w | P->Q | -2.4% / -23.1% (940) | -0.2% / -24.4% (683) | -3.5% / -19.9% (885) | -10.6% / -38.5% (648) |
| through:atm_put_calendar_1w | P->hold_front | +3.7% / -13.3% (940) | +5.0% / -15.1% (683) | -2.9% / -15.9% (884) | -4.7% / -26.9% (643) |
| through:atm_straddle_calendar_1w | P-1->Q | +2.5% / -17.1% (1021) | +1.2% / -21.1% (724) | +2.5% / -12.9% (857) | -10.6% / -36.4% (734) |
| through:atm_straddle_calendar_1w | P-1->hold_front | +7.9% / -7.5% (1021) | +12.0% / -6.1% (722) | +4.8% / -7.1% (859) | -0.9% / -21.9% (729) |
| through:atm_straddle_calendar_1w | P-4->Q | +4.1% / -19.6% (870) | -5.9% / -32.4% (598) | +5.6% / -11.4% (632) | -3.7% / -31.8% (568) |
| through:atm_straddle_calendar_1w | P-4->hold_front | +6.7% / -12.6% (870) | +7.9% / -12.7% (595) | +0.7% / -12.5% (632) | +3.3% / -19.5% (565) |
| through:atm_straddle_calendar_1w | P->Q | -1.9% / -20.4% (1062) | -2.6% / -24.6% (763) | -2.1% / -17.0% (937) | -11.2% / -35.1% (755) |
| through:atm_straddle_calendar_1w | P->hold_front | +2.7% / -12.3% (1062) | +4.1% / -13.5% (762) | -2.0% / -13.6% (938) | -3.3% / -22.8% (749) |
| through:atm_straddle_calendar_month | P-1->Q | +4.5% / -4.2% (637) | +5.2% / -4.0% (427) | -0.2% / -8.0% (488) | +0.7% / -10.3% (385) |
| through:atm_straddle_calendar_month | P-1->hold_front | +6.6% / -0.4% (637) | +9.3% / +1.8% (424) | +1.2% / -5.0% (490) | +7.6% / -1.5% (382) |
| through:atm_straddle_calendar_month | P-4->Q | +0.7% / -9.3% (508) | +5.1% / -5.5% (353) | -0.5% / -8.5% (365) | +3.8% / -7.4% (281) |
| through:atm_straddle_calendar_month | P-4->hold_front | +3.6% / -4.6% (508) | +10.7% / +2.5% (354) | +2.8% / -3.5% (365) | +7.2% / -1.8% (277) |
| through:atm_straddle_calendar_month | P->Q | +0.1% / -8.6% (657) | +3.9% / -5.9% (469) | -1.6% / -9.1% (514) | -1.1% / -13.1% (387) |
| through:atm_straddle_calendar_month | P->hold_front | +0.7% / -6.6% (657) | +7.8% / -0.4% (469) | -2.1% / -8.0% (515) | +2.4% / -7.6% (384) |
| through:double_calendar_put_1w | P-1->Q | +3.1% / -10.7% (973) | +1.3% / -14.3% (682) | +1.1% / -10.6% (813) | -4.8% / -22.0% (648) |
| through:double_calendar_put_1w | P-1->hold_front | +6.7% / -4.3% (973) | +6.2% / -6.4% (684) | +0.9% / -8.2% (812) | -1.4% / -15.3% (646) |
| through:double_calendar_put_1w | P-4->Q | +5.6% / -10.9% (804) | +2.6% / -15.9% (535) | +4.9% / -8.0% (600) | -1.9% / -20.9% (488) |
| through:double_calendar_put_1w | P-4->hold_front | +10.9% / -2.9% (804) | +7.0% / -8.1% (535) | +6.7% / -3.5% (597) | +4.7% / -11.6% (486) |
| through:double_calendar_put_1w | P->Q | -3.2% / -16.8% (946) | -5.7% / -20.7% (643) | -2.9% / -14.1% (899) | -10.1% / -27.8% (675) |
| through:double_calendar_put_1w | P->hold_front | +1.7% / -9.1% (946) | +0.5% / -11.6% (643) | -1.2% / -10.3% (897) | -4.1% / -18.4% (669) |
| through:double_calendar_straddle_1w | P-1->Q | -2.6% / -12.0% (718) | -1.7% / -12.6% (465) | -2.4% / -11.5% (640) | -3.7% / -17.3% (494) |
| through:double_calendar_straddle_1w | P-1->hold_front | +4.2% / -3.8% (716) | +2.7% / -6.5% (464) | +0.0% / -7.2% (638) | +3.3% / -8.3% (488) |
| through:double_calendar_straddle_1w | P-4->Q | +6.4% / -6.2% (578) | +9.9% / -4.4% (363) | +1.3% / -8.5% (461) | -1.2% / -16.5% (392) |
| through:double_calendar_straddle_1w | P-4->hold_front | +12.1% / +1.9% (579) | +11.1% / -0.1% (362) | +5.1% / -3.3% (462) | +3.8% / -9.3% (392) |
| through:double_calendar_straddle_1w | P->Q | -8.8% / -18.0% (701) | -8.8% / -18.4% (442) | -4.3% / -13.2% (719) | -11.1% / -23.8% (521) |
| through:double_calendar_straddle_1w | P->hold_front | -2.8% / -10.2% (700) | -0.7% / -8.8% (440) | -1.4% / -8.3% (717) | -6.2% / -17.0% (517) |
| through:double_calendar_straddle_2w | P-1->Q | +0.8% / -6.2% (558) | +1.3% / -6.0% (355) | -1.2% / -7.0% (437) | +1.2% / -8.2% (348) |
| through:double_calendar_straddle_2w | P-1->hold_front | +6.5% / +1.0% (555) | +6.5% / +0.0% (354) | +2.9% / -2.1% (434) | +6.7% / -1.8% (345) |
| through:double_calendar_straddle_2w | P-4->Q | +5.8% / -2.4% (474) | +13.2% / +4.9% (244) | +3.8% / -3.0% (315) | +4.4% / -4.9% (262) |
| through:double_calendar_straddle_2w | P-4->hold_front | +11.5% / +4.9% (475) | +15.4% / +8.7% (242) | +4.1% / -1.3% (314) | +11.0% / +2.5% (265) |
| through:double_calendar_straddle_2w | P->Q | -2.4% / -9.0% (511) | +0.5% / -6.3% (309) | -1.2% / -7.1% (461) | -6.9% / -15.1% (333) |
| through:double_calendar_straddle_2w | P->hold_front | +2.8% / -2.7% (510) | +4.5% / -1.6% (306) | +2.8% / -2.1% (458) | +0.8% / -7.0% (330) |
| through:double_diagonal_put_1w | P-1->Q | +1.8% / -5.6% (655) | -2.5% / -11.3% (447) | -0.7% / -6.9% (566) | -0.3% / -7.9% (352) |
| through:double_diagonal_put_1w | P-1->hold_front | +4.0% / -2.0% (655) | -1.1% / -8.1% (447) | -0.7% / -5.6% (565) | +2.3% / -3.8% (348) |
| through:double_diagonal_put_1w | P-4->Q | +6.3% / -2.5% (474) | -4.4% / -13.7% (294) | -0.4% / -6.9% (389) | +2.3% / -6.3% (221) |
| through:double_diagonal_put_1w | P-4->hold_front | +8.2% / +1.1% (475) | -0.3% / -8.2% (292) | +0.4% / -4.9% (386) | +3.6% / -3.3% (220) |
| through:double_diagonal_put_1w | P->Q | -2.5% / -10.3% (699) | -3.4% / -11.9% (445) | -0.6% / -6.6% (632) | -5.6% / -13.7% (386) |
| through:double_diagonal_put_1w | P->hold_front | -2.3% / -8.4% (699) | -1.2% / -8.6% (443) | -1.8% / -6.6% (630) | -6.2% / -12.6% (384) |
| through:long_straddle | P-1->Q+2 | -0.0% / -1.9% (1606) | -1.1% / -3.0% (1241) | +1.3% / -0.2% (1446) | +1.1% / -0.9% (1271) |
| through:long_straddle | P-1->Q+4 | -0.2% / -2.5% (1429) | -0.7% / -2.9% (1085) | +1.6% / -0.1% (1231) | +0.3% / -2.2% (1110) |
| through:long_straddle | P-1->Q | -4.1% / -6.0% (1826) | -2.9% / -4.9% (1435) | -1.5% / -3.2% (1641) | -0.4% / -2.4% (1398) |
| through:long_straddle | P-4->Q+2 | +0.6% / -1.4% (1475) | +2.2% / +0.4% (1129) | +1.2% / -0.2% (1247) | -1.7% / -3.7% (1111) |
| through:long_straddle | P-4->Q+4 | -0.9% / -3.2% (1309) | +2.0% / -0.2% (968) | +0.1% / -1.5% (1037) | -2.4% / -4.9% (952) |
| through:long_straddle | P-4->Q | -1.8% / -3.6% (1720) | +2.0% / +0.0% (1348) | -1.6% / -3.1% (1512) | -2.0% / -3.9% (1277) |
| through:long_straddle | P->Q+2 | -0.2% / -2.1% (1616) | -2.0% / -3.9% (1267) | +1.3% / -0.2% (1496) | -2.3% / -4.2% (1257) |
| through:long_straddle | P->Q+4 | -0.7% / -3.0% (1448) | -1.2% / -3.5% (1104) | +0.2% / -1.5% (1292) | -1.8% / -4.4% (1113) |
| through:long_straddle | P->Q | -3.5% / -5.4% (1788) | -3.0% / -5.2% (1433) | -2.5% / -4.2% (1677) | -3.2% / -5.1% (1411) |
| through:long_strangle | P-1->Q+2 | +2.2% / +0.0% (1540) | -2.9% / -5.0% (1200) | +2.8% / +1.0% (1359) | -0.8% / -3.1% (1203) |
| through:long_strangle | P-1->Q+4 | +0.7% / -1.7% (1382) | -3.0% / -5.5% (1062) | +1.8% / -0.3% (1197) | -0.9% / -4.1% (1043) |
| through:long_strangle | P-1->Q | -4.0% / -6.1% (1713) | -2.9% / -5.3% (1309) | -0.9% / -2.9% (1536) | -1.0% / -3.3% (1314) |
| through:long_strangle | P-4->Q+2 | -0.1% / -2.3% (1380) | +0.1% / -2.0% (1050) | -2.8% / -4.5% (1199) | -3.6% / -5.9% (1043) |
| through:long_strangle | P-4->Q+4 | -3.2% / -5.7% (1240) | -0.0% / -2.5% (929) | -3.0% / -5.1% (999) | -3.9% / -6.9% (861) |
| through:long_strangle | P-4->Q | -2.8% / -4.9% (1592) | -1.0% / -3.3% (1260) | -5.7% / -7.6% (1455) | -2.7% / -4.9% (1209) |
| through:long_strangle | P->Q+2 | -1.0% / -3.2% (1498) | -2.4% / -4.5% (1146) | +1.6% / -0.2% (1419) | -4.8% / -7.1% (1188) |
| through:long_strangle | P->Q+4 | -0.7% / -3.1% (1341) | -1.2% / -3.9% (996) | -1.1% / -3.2% (1242) | -3.3% / -6.4% (1034) |
| through:long_strangle | P->Q | -4.0% / -6.2% (1643) | -5.8% / -8.2% (1291) | -3.9% / -5.9% (1576) | -2.9% / -5.3% (1307) |
| through:short_iron_condor_wide | P-1->Q+2 | -0.9% / -2.0% (610) | +0.4% / -0.8% (412) | -1.7% / -2.7% (563) | -1.9% / -3.1% (424) |
| through:short_iron_condor_wide | P-1->Q+4 | +0.1% / -1.2% (478) | +3.3% / +1.9% (307) | -2.1% / -3.3% (429) | +0.7% / -1.1% (319) |
| through:short_iron_condor_wide | P-1->Q | +2.2% / +1.1% (742) | -1.2% / -2.5% (516) | -0.8% / -1.9% (754) | -2.5% / -3.8% (512) |
| through:short_iron_condor_wide | P-4->Q+2 | +0.6% / -0.4% (477) | -0.9% / -2.2% (329) | -0.1% / -1.0% (470) | -1.6% / -3.0% (360) |
| through:short_iron_condor_wide | P-4->Q+4 | +1.1% / -0.1% (402) | +5.1% / +3.7% (257) | +2.8% / +1.6% (353) | +4.1% / +2.5% (287) |
| through:short_iron_condor_wide | P-4->Q | +0.6% / -0.5% (640) | -1.5% / -2.8% (424) | +1.8% / +0.8% (624) | -2.8% / -3.9% (443) |
| through:short_iron_condor_wide | P->Q+2 | -0.6% / -1.8% (564) | -0.8% / -2.0% (395) | -2.7% / -3.7% (680) | -0.3% / -1.6% (490) |
| through:short_iron_condor_wide | P->Q+4 | -1.2% / -2.5% (447) | -0.6% / -2.0% (276) | -1.3% / -2.5% (471) | +1.9% / +0.2% (329) |
| through:short_iron_condor_wide | P->Q | +1.6% / +0.5% (724) | -1.1% / -2.4% (518) | -0.8% / -1.9% (875) | -1.6% / -2.8% (616) |
| through:short_iron_condor | P-1->Q+2 | -2.9% / -5.3% (1051) | -3.1% / -5.6% (742) | -4.7% / -6.9% (919) | -2.2% / -5.2% (826) |
| through:short_iron_condor | P-1->Q+4 | -1.8% / -4.6% (889) | -0.3% / -3.4% (605) | -5.7% / -8.3% (732) | +0.9% / -2.9% (643) |
| through:short_iron_condor | P-1->Q | -0.8% / -3.3% (1260) | -1.8% / -4.7% (936) | -1.2% / -3.7% (1178) | -3.1% / -6.0% (989) |
| through:short_iron_condor | P-4->Q+2 | -1.6% / -4.0% (862) | -5.6% / -8.2% (621) | -0.7% / -2.9% (767) | -2.2% / -5.2% (665) |
| through:short_iron_condor | P-4->Q+4 | -0.0% / -2.8% (745) | -0.4% / -3.6% (526) | -0.5% / -3.0% (605) | +0.3% / -3.2% (520) |
| through:short_iron_condor | P-4->Q | -1.5% / -3.9% (1114) | -5.8% / -8.5% (781) | +0.4% / -1.8% (1023) | -2.1% / -5.0% (820) |
| through:short_iron_condor | P->Q+2 | -2.1% / -4.6% (1046) | -1.1% / -3.7% (758) | -2.8% / -5.1% (1028) | +0.6% / -2.2% (870) |
| through:short_iron_condor | P->Q+4 | -1.9% / -4.8% (877) | +0.7% / -2.3% (594) | -3.7% / -6.3% (787) | +1.9% / -1.8% (661) |
| through:short_iron_condor | P->Q | -1.1% / -3.8% (1241) | -1.0% / -4.0% (939) | -1.3% / -3.9% (1283) | -1.4% / -4.4% (1054) |
| through:short_iron_fly_1x | P-1->Q+2 | -5.2% / -13.5% (1325) | -3.1% / -11.3% (1014) | -3.6% / -11.1% (1195) | -0.7% / -10.5% (1066) |
| through:short_iron_fly_1x | P-1->Q+4 | -4.8% / -14.8% (1137) | -4.6% / -14.6% (829) | -6.6% / -15.0% (971) | +1.1% / -11.3% (879) |
| through:short_iron_fly_1x | P-1->Q | -0.7% / -9.3% (1588) | -3.1% / -12.3% (1210) | -2.3% / -10.7% (1434) | -2.3% / -11.6% (1191) |
| through:short_iron_fly_1x | P-4->Q+2 | -3.5% / -11.7% (1166) | -7.3% / -15.8% (881) | -5.2% / -12.7% (997) | -1.9% / -11.6% (875) |
| through:short_iron_fly_1x | P-4->Q+4 | -2.2% / -11.5% (1021) | -6.9% / -17.3% (743) | -6.1% / -15.1% (779) | +0.6% / -11.4% (725) |
| through:short_iron_fly_1x | P-4->Q | -4.8% / -13.0% (1436) | -9.4% / -18.3% (1088) | -1.9% / -9.6% (1272) | -2.2% / -11.1% (1055) |
| through:short_iron_fly_1x | P->Q+2 | -4.0% / -12.8% (1343) | -4.2% / -13.0% (1032) | -5.1% / -12.7% (1275) | -0.2% / -9.5% (1053) |
| through:short_iron_fly_1x | P->Q+4 | -4.6% / -14.7% (1158) | -3.9% / -14.0% (845) | -5.6% / -14.3% (1035) | +0.8% / -11.3% (879) |
| through:short_iron_fly_1x | P->Q | -2.0% / -10.9% (1560) | -3.4% / -13.6% (1218) | -2.0% / -10.4% (1496) | +0.3% / -9.2% (1224) |
| through:short_iron_fly_2x | P-1->Q+2 | -2.6% / -3.9% (615) | +0.8% / -0.7% (436) | +0.1% / -1.0% (578) | -1.1% / -2.7% (433) |
| through:short_iron_fly_2x | P-1->Q+4 | +0.3% / -1.3% (486) | +3.4% / +1.5% (338) | -0.8% / -2.1% (451) | +0.6% / -1.5% (332) |
| through:short_iron_fly_2x | P-1->Q | +2.8% / +1.4% (750) | +0.6% / -1.1% (539) | +0.6% / -0.6% (753) | -3.9% / -5.6% (536) |
| through:short_iron_fly_2x | P-4->Q+2 | +0.8% / -0.5% (505) | +0.9% / -0.6% (347) | -1.7% / -2.9% (501) | -1.0% / -2.8% (372) |
| through:short_iron_fly_2x | P-4->Q+4 | +2.3% / +0.7% (427) | +6.5% / +4.7% (268) | +3.6% / +2.2% (383) | +4.4% / +2.3% (290) |
| through:short_iron_fly_2x | P-4->Q | +1.6% / +0.2% (662) | -1.3% / -2.9% (439) | +0.1% / -1.1% (655) | -1.9% / -3.5% (461) |
| through:short_iron_fly_2x | P->Q+2 | -0.5% / -1.9% (588) | -0.2% / -1.8% (425) | -1.1% / -2.3% (690) | +1.5% / -0.2% (512) |
| through:short_iron_fly_2x | P->Q+4 | +1.2% / -0.5% (455) | +1.3% / -0.6% (302) | +0.0% / -1.3% (488) | -0.0% / -2.3% (342) |
| through:short_iron_fly_2x | P->Q | +1.6% / +0.1% (755) | -1.1% / -3.0% (551) | -0.5% / -1.8% (893) | -1.0% / -2.7% (661) |

## Sample E (untouched expanded universe)

Reserved. The frozen policies above and the replications below are evaluated on the expanded names only after that data is downloaded; no policy can qualify before then.

## Frozen policies: pooled out-of-selection samples and release timing

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight` B+C+D | 604 | 127 | +12.0% | [+4.7%, +19.7%] | +1.1% | -9.8% | +9.4% | 53% | -213.3% |
| … before open | 260 | 67 | +16.4% | [+6.8%, +26.4%] | +4.8% | -6.9% | +12.6% | 54% | -176.1% |
| … after close | 344 | 68 | +8.7% | [-1.9%, +19.9%] | -1.7% | -12.0% | +4.1% | 52% | -213.3% |
| `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight` B+C+D | 1546 | 187 | +4.7% | [-1.6%, +12.0%] | -10.5% | -25.7% | +3.1% | 41% | -434.8% |
| … before open | 811 | 114 | +3.1% | [-5.4%, +12.0%] | -13.1% | -29.4% | +0.3% | 40% | -221.4% |
| … after close | 735 | 87 | +6.5% | [-3.3%, +16.2%] | -7.6% | -21.7% | +3.1% | 41% | -434.8% |
| `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` B+C+D | 659 | 139 | +14.3% | [+7.1%, +21.9%] | +1.7% | -11.0% | +11.9% | 47% | -350.7% |
| … before open | 296 | 80 | +16.4% | [+5.7%, +27.8%] | +1.7% | -13.1% | +12.1% | 48% | -350.7% |
| … after close | 363 | 67 | +12.5% | [+2.3%, +23.4%] | +1.6% | -9.3% | +8.3% | 46% | -148.2% |
| `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight` B+C+D | 300 | 96 | -0.4% | [-6.5%, +6.0%] | -4.9% | -9.3% | -2.7% | 55% | -108.4% |
| … before open | 175 | 57 | -1.0% | [-9.1%, +6.8%] | -5.7% | -10.3% | -4.0% | 55% | -108.4% |
| … after close | 125 | 44 | +0.4% | [-10.1%, +10.5%] | -3.8% | -8.0% | -4.8% | 55% | -97.0% |
| `through:double_calendar_straddle_2w|P-4->hold_front|none|standard` B+C+D | 821 | 153 | +9.7% | [+5.2%, +14.3%] | +2.9% | -3.9% | +8.0% | 51% | -122.5% |
| … before open | 499 | 93 | +7.2% | [+2.6%, +12.1%] | +0.3% | -6.6% | +5.3% | 50% | -122.5% |
| … after close | 321 | 72 | +13.4% | [+5.7%, +21.8%] | +6.8% | +0.2% | +9.4% | 51% | -94.9% |

## Replications of earlier leads with release-correct timing (pre-registered)

### research5_long_straddle: `pre:long_straddle|P-1->P|R<=0.9|tight`

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A | 151 | 56 | +1.4% | [+0.1%, +2.9%] | +0.2% | -1.1% | +0.5% | 54% | -15.3% |
| B | 136 | 47 | +2.1% | [+0.6%, +3.9%] | +0.7% | -0.6% | +1.1% | 55% | -19.7% |
| C | 140 | 63 | +4.0% | [+2.0%, +6.0%] | +3.0% | +1.9% | +2.3% | 64% | -16.4% |
| D | 108 | 68 | +3.1% | [+1.3%, +4.9%] | +2.1% | +1.1% | +2.1% | 60% | -20.9% |
| B+C+D pooled | 384 | 123 | +3.1% | [+2.0%, +4.2%] | +1.9% | +0.8% | +2.4% | 60% | -20.9% |
| B+C+D before open | 164 | 64 | +3.0% | [+1.5%, +4.3%] | +1.7% | +0.3% | +2.0% | 61% | -20.9% |
| B+C+D after close | 219 | 61 | +3.2% | [+1.7%, +4.7%] | +2.1% | +1.1% | +2.1% | 58% | -19.7% |
| B, decided one session earlier | 112 | 44 | +2.1% | [+0.0%, +4.4%] | +0.8% | -0.6% | +0.6% | 48% | -19.7% |
| C, decided one session earlier | 109 | 51 | +3.2% | [+1.6%, +4.9%] | +2.3% | +1.3% | +1.7% | 61% | -12.9% |
| D, decided one session earlier | 98 | 61 | +2.4% | [+0.3%, +4.3%] | +1.2% | +0.1% | +1.1% | 54% | -15.1% |

### research5_long_strangle: `pre:long_strangle|P-1->P|R<=0.9|tight`

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A | 124 | 45 | +1.9% | [-0.9%, +4.6%] | +0.5% | -0.9% | +0.0% | 51% | -25.0% |
| B | 111 | 40 | +2.9% | [-0.2%, +6.0%] | +1.5% | +0.0% | +0.9% | 53% | -29.2% |
| C | 118 | 54 | +6.7% | [+3.3%, +10.5%] | +5.6% | +4.5% | +3.7% | 64% | -22.9% |
| D | 101 | 62 | +7.9% | [+4.1%, +12.3%] | +6.5% | +5.2% | +4.7% | 64% | -17.4% |
| B+C+D pooled | 330 | 106 | +5.8% | [+3.8%, +8.0%] | +4.5% | +3.2% | +4.3% | 61% | -29.2% |
| B+C+D before open | 127 | 50 | +6.4% | [+3.2%, +10.4%] | +5.0% | +3.6% | +3.5% | 61% | -26.6% |
| B+C+D after close | 202 | 57 | +5.3% | [+2.8%, +7.9%] | +4.1% | +2.9% | +3.6% | 60% | -29.2% |
| B, decided one session earlier | 79 | 35 | +3.6% | [-0.3%, +7.6%] | +2.3% | +0.9% | +0.3% | 51% | -29.2% |
| C, decided one session earlier | 95 | 44 | +5.4% | [+2.3%, +8.7%] | +4.3% | +3.3% | +2.5% | 58% | -23.5% |
| D, decided one session earlier | 79 | 50 | +5.7% | [+1.4%, +10.7%] | +4.6% | +3.4% | +1.5% | 54% | -24.3% |

### research6_double_diagonal_put: `through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight`

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A | 182 | 68 | +7.9% | [+0.4%, +15.2%] | +2.1% | -3.6% | +4.8% | 67% | -230.0% |
| B | 118 | 43 | +2.8% | [-6.0%, +11.1%] | -2.8% | -8.3% | -0.5% | 61% | -179.4% |
| C | 161 | 79 | +2.2% | [-5.2%, +10.1%] | -2.7% | -7.6% | -1.4% | 58% | -103.4% |
| D | 88 | 50 | +5.3% | [-5.4%, +15.3%] | -0.0% | -5.3% | +0.8% | 62% | -121.6% |
| B+C+D pooled | 367 | 110 | +3.1% | [-1.9%, +8.3%] | -2.1% | -7.3% | +1.6% | 60% | -179.4% |
| B+C+D before open | 192 | 60 | +2.8% | [-3.1%, +8.5%] | -2.4% | -7.6% | +1.1% | 62% | -121.6% |
| B+C+D after close | 175 | 54 | +3.5% | [-4.4%, +11.9%] | -1.7% | -6.9% | +0.3% | 58% | -179.4% |
| B, decided one session earlier | 102 | 40 | +10.5% | [+2.7%, +18.3%] | +5.6% | +0.7% | +6.9% | 65% | -98.8% |
| C, decided one session earlier | 144 | 76 | +5.3% | [-1.3%, +12.0%] | +1.1% | -3.1% | +1.4% | 62% | -102.7% |
| D, decided one session earlier | 81 | 44 | +3.6% | [-8.3%, +14.1%] | -1.4% | -6.4% | -1.3% | 59% | -99.9% |

### research6_double_calendar_2w: `through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard`

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| A | 262 | 77 | +4.1% | [-1.5%, +9.3%] | -0.8% | -5.7% | +1.8% | 52% | -108.7% |
| B | 148 | 46 | +5.9% | [-2.1%, +14.3%] | +0.8% | -4.3% | +0.9% | 50% | -89.8% |
| C | 229 | 97 | +5.7% | [+0.9%, +10.6%] | +0.7% | -4.3% | +2.9% | 50% | -94.7% |
| D | 144 | 74 | +3.6% | [-6.3%, +14.8%] | -5.0% | -13.6% | -2.4% | 39% | -87.2% |
| B+C+D pooled | 521 | 136 | +5.2% | [+1.3%, +9.2%] | -0.8% | -6.8% | +3.2% | 47% | -94.7% |
| B+C+D before open | 353 | 85 | +4.8% | [+0.0%, +9.8%] | -1.1% | -6.9% | +2.9% | 47% | -89.8% |
| B+C+D after close | 168 | 56 | +6.0% | [-1.7%, +14.3%] | -0.3% | -6.6% | +0.1% | 46% | -94.7% |
| B, decided one session earlier | 148 | 44 | +0.7% | [-7.8%, +9.5%] | -4.2% | -9.2% | -4.2% | 47% | -87.6% |
| C, decided one session earlier | 235 | 99 | +0.9% | [-4.3%, +6.3%] | -3.5% | -7.9% | -1.9% | 49% | -110.4% |
| D, decided one session earlier | 135 | 71 | +9.2% | [+0.9%, +19.0%] | +0.8% | -7.5% | +2.9% | 47% | -87.3% |

