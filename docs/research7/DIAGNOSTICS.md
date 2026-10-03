# Research7 post-freeze diagnostics

Exploratory breakdowns of the five frozen policies after all stages were evaluated. None of these groupings was pre-registered as a gate, and none can change the frozen set or the verdict.

## `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 604 | +12.0% | [+4.7%, +19.7%] | +1.1% | +9.4% | 53% |
| 2018 selection | 89 | +29.4% | [+5.2%, +52.8%] | +15.4% | +15.4% | 58% |
| 2018 out-of-selection | 46 | +6.6% | [-17.9%, +31.4%] | -4.7% | -11.5% | 50% |
| 2019 selection | 109 | +18.9% | [+4.1%, +34.1%] | +9.1% | +8.3% | 59% |
| 2019 out-of-selection | 72 | +2.4% | [-20.4%, +26.1%] | -8.7% | -8.9% | 49% |
| 2020 selection | 49 | +27.2% | [-0.8%, +53.6%] | +18.5% | +3.1% | 61% |
| 2020 out-of-selection | 33 | +61.4% | [+12.5%, +129.6%] | +49.9% | +16.7% | 70% |
| 2021 selection | 43 | +4.0% | [-17.1%, +23.0%] | -5.5% | -9.9% | 56% |
| 2021 out-of-selection | 24 | -2.2% | [-29.5%, +23.9%] | -14.8% | -30.3% | 58% |
| 2022 out-of-selection | 68 | +13.5% | [-5.0%, +34.2%] | +3.0% | +0.7% | 57% |
| 2023 out-of-selection | 144 | +13.8% | [-0.3%, +27.3%] | +5.4% | +7.7% | 53% |
| 2024 out-of-selection | 138 | +6.7% | [-7.8%, +23.5%] | -6.2% | +0.1% | 48% |
| 2025 out-of-selection | 79 | +12.4% | [-11.3%, +31.7%] | +1.4% | +1.9% | 54% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 172 | +46.2% | [+36.3%, +56.5%] | +38.7% | +41.9% | 77% |
| 0.5-1 x implied | 190 | +74.7% | [+63.6%, +86.5%] | +65.6% | +68.0% | 85% |
| |move| >= 1 x implied | 243 | -61.1% | [-67.7%, -54.1%] | -75.7% | -64.3% | 11% |

Trades losing more than 100% of risk at exit midpoints: 40 of 613 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 604 | +13.1% | [+5.7%, +20.6%] | +4.0% | +10.5% | 53% |

## `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 1546 | +4.7% | [-1.6%, +12.0%] | -10.5% | +3.1% | 41% |
| 2018 selection | 163 | +16.7% | [-3.5%, +35.6%] | +0.0% | +6.1% | 48% |
| 2018 out-of-selection | 105 | +20.1% | [-0.8%, +39.4%] | +2.9% | +3.1% | 47% |
| 2019 selection | 171 | +18.5% | [+2.2%, +36.7%] | +5.7% | +7.0% | 43% |
| 2019 out-of-selection | 118 | +7.5% | [-15.4%, +32.7%] | -8.0% | -9.0% | 40% |
| 2020 selection | 141 | +21.5% | [+7.5%, +37.7%] | +10.7% | +12.5% | 52% |
| 2020 out-of-selection | 81 | +41.3% | [+5.8%, +87.3%] | +30.7% | +18.4% | 49% |
| 2021 selection | 154 | -2.4% | [-17.5%, +10.6%] | -15.4% | -11.4% | 40% |
| 2021 out-of-selection | 116 | -2.7% | [-24.7%, +19.4%] | -19.0% | -15.4% | 40% |
| 2022 out-of-selection | 272 | +4.9% | [-10.3%, +22.0%] | -5.8% | -0.3% | 45% |
| 2023 out-of-selection | 339 | +5.6% | [-9.5%, +20.9%] | -5.8% | -0.2% | 37% |
| 2024 out-of-selection | 320 | -5.7% | [-20.0%, +8.7%] | -26.5% | -13.3% | 36% |
| 2025 out-of-selection | 195 | -0.8% | [-17.1%, +15.6%] | -19.7% | -9.3% | 41% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 481 | +138.7% | [+128.1%, +149.8%] | +128.1% | +134.8% | 97% |
| 0.5-1 x implied | 397 | -15.4% | [-21.4%, -8.9%] | -28.3% | -17.8% | 34% |
| |move| >= 1 x implied | 669 | -79.8% | [-83.4%, -76.2%] | -99.7% | -81.4% | 4% |

Trades losing more than 100% of risk at exit midpoints: 130 of 1558 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 1546 | +7.6% | [+1.6%, +14.8%] | -3.4% | +6.0% | 41% |

## `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 659 | +14.3% | [+7.1%, +21.9%] | +1.7% | +11.9% | 47% |
| 2018 selection | 85 | +33.5% | [+0.7%, +66.3%] | +22.3% | +18.6% | 59% |
| 2018 out-of-selection | 52 | +19.8% | [-3.0%, +45.8%] | +4.3% | +1.0% | 50% |
| 2019 selection | 105 | +10.6% | [-2.3%, +25.8%] | -0.6% | +2.7% | 48% |
| 2019 out-of-selection | 74 | +19.6% | [-5.6%, +48.5%] | +7.5% | +2.5% | 43% |
| 2020 selection | 55 | +29.9% | [-1.0%, +66.8%] | +18.3% | +3.0% | 49% |
| 2020 out-of-selection | 33 | +57.4% | [+17.6%, +108.9%] | +46.0% | +18.2% | 67% |
| 2021 selection | 60 | +3.0% | [-21.1%, +26.9%] | -9.4% | -12.3% | 47% |
| 2021 out-of-selection | 36 | +10.6% | [-9.9%, +36.4%] | -5.2% | -9.4% | 53% |
| 2022 out-of-selection | 75 | +34.2% | [+13.5%, +55.1%] | +23.7% | +21.5% | 57% |
| 2023 out-of-selection | 132 | +6.4% | [-11.0%, +24.9%] | -2.7% | -1.7% | 44% |
| 2024 out-of-selection | 172 | +5.6% | [-5.1%, +16.4%] | -9.0% | -1.1% | 44% |
| 2025 out-of-selection | 85 | +3.1% | [-20.5%, +26.5%] | -10.6% | -9.4% | 39% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 192 | -46.5% | [-51.4%, -41.3%] | -56.7% | -49.1% | 9% |
| 0.5-1 x implied | 197 | +42.9% | [+32.3%, +54.3%] | +33.9% | +37.2% | 68% |
| |move| >= 1 x implied | 271 | +36.2% | [+22.0%, +50.2%] | +19.4% | +31.0% | 58% |

Trades losing more than 100% of risk at exit midpoints: 14 of 669 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 659 | +15.0% | [+7.9%, +22.4%] | +3.3% | +12.6% | 47% |

## `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 300 | -0.4% | [-6.5%, +6.0%] | -4.9% | -2.7% | 55% |
| 2018 selection | 32 | +19.4% | [-2.1%, +45.4%] | +15.4% | +2.5% | 66% |
| 2018 out-of-selection | 19 | +11.4% | [-19.0%, +45.1%] | +4.2% | -14.5% | 58% |
| 2019 selection | 37 | +12.5% | [-8.8%, +35.8%] | +8.7% | -2.1% | 65% |
| 2019 out-of-selection | 20 | -5.3% | [-25.8%, +17.8%] | -10.4% | -27.2% | 50% |
| 2020 selection | 45 | +22.3% | [+8.3%, +40.3%] | +16.8% | +12.1% | 73% |
| 2020 out-of-selection | 23 | -5.3% | [-24.5%, +12.4%] | -9.0% | -21.0% | 57% |
| 2021 selection | 47 | +0.5% | [-10.5%, +13.2%] | -3.1% | -8.9% | 64% |
| 2021 out-of-selection | 25 | -4.0% | [-16.2%, +12.2%] | -8.0% | -19.5% | 48% |
| 2022 out-of-selection | 89 | -4.5% | [-16.0%, +7.8%] | -8.5% | -10.1% | 53% |
| 2023 out-of-selection | 62 | +0.7% | [-14.1%, +13.7%] | -3.2% | -7.7% | 58% |
| 2024 out-of-selection | 38 | +9.3% | [-10.9%, +26.8%] | +3.7% | -5.4% | 61% |
| 2025 out-of-selection | 24 | -0.2% | [-19.0%, +14.8%] | -4.7% | -15.6% | 58% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 93 | +39.7% | [+35.5%, +44.4%] | +36.5% | +37.2% | 99% |
| 0.5-1 x implied | 85 | +40.8% | [+31.7%, +49.5%] | +37.3% | +35.0% | 84% |
| |move| >= 1 x implied | 123 | -58.7% | [-64.2%, -53.1%] | -64.9% | -61.4% | 3% |

Trades losing more than 100% of risk at exit midpoints: 4 of 301 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 300 | -0.4% | [-6.5%, +6.0%] | -4.6% | -2.7% | 55% |

## `through:double_calendar_straddle_2w|P-4->hold_front|none|standard`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 821 | +9.7% | [+5.2%, +14.3%] | +2.9% | +8.0% | 51% |
| 2018 selection | 113 | +22.5% | [+7.1%, +41.7%] | +14.2% | +14.5% | 58% |
| 2018 out-of-selection | 54 | +12.9% | [-3.7%, +32.8%] | +5.5% | +0.3% | 48% |
| 2019 selection | 124 | +6.5% | [-4.5%, +18.3%] | +0.0% | -0.7% | 42% |
| 2019 out-of-selection | 72 | +12.5% | [-7.2%, +31.2%] | +6.0% | +0.5% | 53% |
| 2020 selection | 103 | +15.8% | [-4.1%, +38.9%] | +9.8% | +3.4% | 50% |
| 2020 out-of-selection | 48 | +20.5% | [-9.6%, +63.2%] | +14.3% | -5.0% | 52% |
| 2021 selection | 135 | +3.6% | [-6.6%, +15.2%] | -2.1% | -1.1% | 52% |
| 2021 out-of-selection | 68 | +16.9% | [+2.2%, +32.9%] | +10.2% | +7.9% | 60% |
| 2022 out-of-selection | 137 | +6.3% | [-1.8%, +15.2%] | +0.9% | +1.6% | 53% |
| 2023 out-of-selection | 177 | +2.4% | [-6.3%, +11.0%] | -3.0% | -1.3% | 45% |
| 2024 out-of-selection | 177 | +14.2% | [+6.2%, +22.6%] | +5.3% | +9.1% | 51% |
| 2025 out-of-selection | 88 | +4.5% | [-6.7%, +13.8%] | -3.1% | -2.5% | 49% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 244 | -25.4% | [-29.6%, -20.9%] | -31.0% | -27.7% | 14% |
| 0.5-1 x implied | 244 | +32.1% | [+25.2%, +39.2%] | +26.0% | +27.9% | 74% |
| |move| >= 1 x implied | 335 | +18.6% | [+10.7%, +26.3%] | +10.5% | +15.6% | 60% |

Trades losing more than 100% of risk at exit midpoints: 1 of 830 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 821 | +9.7% | [+5.2%, +14.3%] | +3.0% | +8.1% | 51% |

