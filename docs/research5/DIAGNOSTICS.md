# Research5 post-freeze diagnostics

Exploratory breakdowns of the five frozen policies after all stages were evaluated. None of these groupings was pre-registered as a gate, and none can change the frozen set or the verdict.

## `long_straddle|E-2->E-1|R<=0.9|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 580 | +1.0% | [+0.2%, +1.9%] | -0.1% | +0.7% | 48% |
| 2018 selection | 55 | +8.9% | [+3.4%, +15.8%] | +7.6% | +3.1% | 71% |
| 2018 out-of-selection | 48 | +0.7% | [-1.1%, +2.6%] | -0.5% | -0.7% | 50% |
| 2019 selection | 71 | +2.7% | [+1.1%, +4.8%] | +1.6% | +1.1% | 55% |
| 2019 out-of-selection | 54 | -1.5% | [-4.5%, +1.1%] | -2.7% | -3.1% | 37% |
| 2020 selection | 40 | -1.6% | [-3.4%, +0.7%] | -2.7% | -3.4% | 32% |
| 2020 out-of-selection | 37 | +0.4% | [-1.7%, +2.5%] | -1.0% | -1.9% | 51% |
| 2021 selection | 62 | -0.3% | [-2.9%, +2.2%] | -1.6% | -2.3% | 42% |
| 2021 out-of-selection | 59 | -0.6% | [-2.7%, +2.2%] | -1.9% | -2.3% | 36% |
| 2022 out-of-selection | 48 | +4.1% | [+1.0%, +7.2%] | +2.9% | +1.9% | 65% |
| 2023 out-of-selection | 164 | +1.5% | [-0.7%, +3.4%] | +0.5% | +0.5% | 47% |
| 2024 out-of-selection | 124 | +1.2% | [-0.4%, +2.6%] | +0.1% | +0.2% | 50% |
| 2025 out-of-selection | 46 | +1.5% | [-1.0%, +4.3%] | +0.2% | -0.4% | 54% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 521 | -0.4% | [-1.2%, +0.3%] | -1.6% | -0.7% | 42% |
| 0.5-1 x implied | 56 | +12.7% | [+10.7%, +14.7%] | +11.4% | +10.8% | 98% |
| |move| >= 1 x implied | 3 | +38.0% | [+31.0%, +44.0%] | +36.4% | n/a | 100% |

Trades losing more than 100% of risk at exit midpoints: 0 of 582 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 580 | +1.0% | [+0.2%, +1.9%] | -0.1% | +0.7% | 48% |

## `long_strangle|E-2->E-1|R<=0.9|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 469 | +1.9% | [+0.4%, +3.4%] | +0.6% | +1.3% | 48% |
| 2018 selection | 46 | +18.6% | [+6.2%, +33.8%] | +17.1% | +5.2% | 67% |
| 2018 out-of-selection | 41 | -0.3% | [-3.5%, +2.9%] | -1.9% | -2.5% | 46% |
| 2019 selection | 60 | +4.3% | [+0.7%, +8.6%] | +3.0% | +1.0% | 60% |
| 2019 out-of-selection | 44 | -0.1% | [-4.8%, +4.1%] | -1.4% | -3.7% | 36% |
| 2020 selection | 39 | -3.0% | [-6.2%, +1.0%] | -4.2% | -6.5% | 23% |
| 2020 out-of-selection | 29 | +2.1% | [-3.3%, +8.7%] | +0.5% | -3.4% | 41% |
| 2021 selection | 57 | -0.7% | [-5.4%, +3.8%] | -2.0% | -4.2% | 42% |
| 2021 out-of-selection | 47 | -1.1% | [-4.6%, +3.8%] | -2.2% | -4.4% | 36% |
| 2022 out-of-selection | 32 | +7.6% | [+2.9%, +13.0%] | +6.4% | +2.6% | 59% |
| 2023 out-of-selection | 133 | +2.7% | [-0.9%, +5.6%] | +1.5% | +0.9% | 50% |
| 2024 out-of-selection | 108 | +2.7% | [-0.4%, +5.3%] | +1.4% | +1.0% | 53% |
| 2025 out-of-selection | 35 | +0.8% | [-2.7%, +4.7%] | -0.6% | -2.0% | 49% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 424 | -0.4% | [-1.6%, +0.8%] | -1.7% | -0.9% | 42% |
| 0.5-1 x implied | 43 | +22.0% | [+18.4%, +25.9%] | +20.6% | +18.2% | 100% |
| |move| >= 1 x implied | 2 | +63.3% | [+54.7%, +71.9%] | +61.3% | n/a | 100% |

Trades losing more than 100% of risk at exit midpoints: 0 of 471 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 469 | +1.9% | [+0.4%, +3.4%] | +0.6% | +1.3% | 48% |

## `short_iron_condor_wide|E-1->after_release|R>=1.0|standard`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 1181 | -1.6% | [-3.4%, +0.2%] | -2.9% | -1.7% | 64% |
| 2018 selection | 99 | -0.4% | [-6.1%, +5.4%] | -1.9% | -1.9% | 65% |
| 2018 out-of-selection | 57 | -0.1% | [-9.0%, +7.2%] | -1.7% | -2.7% | 65% |
| 2019 selection | 105 | +5.1% | [+0.3%, +9.5%] | +4.0% | +3.8% | 73% |
| 2019 out-of-selection | 84 | +0.1% | [-6.6%, +6.6%] | -1.1% | -1.6% | 67% |
| 2020 selection | 134 | +4.7% | [+0.2%, +8.6%] | +3.6% | +3.9% | 72% |
| 2020 out-of-selection | 87 | +1.5% | [-3.6%, +6.3%] | +0.1% | +0.0% | 67% |
| 2021 selection | 144 | -0.7% | [-5.3%, +3.4%] | -2.0% | -1.7% | 65% |
| 2021 out-of-selection | 91 | -0.1% | [-5.1%, +4.7%] | -2.0% | -1.8% | 64% |
| 2022 out-of-selection | 267 | -3.9% | [-7.4%, -0.3%] | -5.1% | -4.5% | 61% |
| 2023 out-of-selection | 248 | -1.9% | [-6.3%, +2.2%] | -3.0% | -2.5% | 64% |
| 2024 out-of-selection | 223 | -0.6% | [-5.2%, +3.1%] | -2.0% | -1.4% | 64% |
| 2025 out-of-selection | 124 | -2.6% | [-10.5%, +6.0%] | -4.1% | -3.9% | 66% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 478 | +17.8% | [+17.0%, +18.6%] | +16.7% | +17.7% | 96% |
| 0.5-1 x implied | 328 | +10.2% | [+9.0%, +11.4%] | +9.1% | +9.9% | 84% |
| |move| >= 1 x implied | 375 | -36.6% | [-39.7%, -33.6%] | -38.3% | -37.2% | 6% |

Trades losing more than 100% of risk at exit midpoints: 5 of 1189 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 1181 | -1.6% | [-3.4%, +0.3%] | -2.9% | -1.7% | 64% |

## `short_iron_fly_2x|E-1->after_release|R>=1.0|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 702 | -0.3% | [-3.4%, +2.8%] | -1.5% | -0.8% | 58% |
| 2018 selection | 43 | -3.0% | [-15.2%, +12.1%] | -4.5% | -10.7% | 51% |
| 2018 out-of-selection | 22 | -5.5% | [-23.9%, +14.3%] | -6.8% | -18.0% | 55% |
| 2019 selection | 62 | +9.4% | [+0.8%, +17.9%] | +8.5% | +5.6% | 68% |
| 2019 out-of-selection | 47 | -0.2% | [-15.6%, +15.2%] | -1.5% | -7.5% | 57% |
| 2020 selection | 84 | +10.2% | [+1.9%, +17.0%] | +9.3% | +7.2% | 70% |
| 2020 out-of-selection | 46 | +6.3% | [-3.1%, +15.2%] | +5.2% | +1.7% | 67% |
| 2021 selection | 94 | -1.3% | [-8.6%, +5.3%] | -2.6% | -4.2% | 56% |
| 2021 out-of-selection | 49 | -4.8% | [-15.3%, +5.0%] | -6.2% | -10.2% | 53% |
| 2022 out-of-selection | 197 | -2.4% | [-7.6%, +2.7%] | -3.6% | -3.9% | 57% |
| 2023 out-of-selection | 160 | -2.5% | [-10.3%, +4.9%] | -3.5% | -4.4% | 59% |
| 2024 out-of-selection | 121 | +4.2% | [-2.7%, +10.3%] | +2.9% | +1.8% | 60% |
| 2025 out-of-selection | 60 | +3.9% | [-6.8%, +15.6%] | +2.7% | -0.8% | 57% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 277 | +32.7% | [+30.8%, +34.7%] | +31.7% | +32.1% | 98% |
| 0.5-1 x implied | 199 | +9.4% | [+7.5%, +11.5%] | +8.4% | +8.7% | 70% |
| |move| >= 1 x implied | 226 | -49.4% | [-52.8%, -46.2%] | -50.8% | -50.4% | 0% |

Trades losing more than 100% of risk at exit midpoints: 2 of 707 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 702 | -0.3% | [-3.4%, +2.8%] | -1.5% | -0.8% | 58% |

## `short_iron_condor|E-1->after_release|R>=1.4|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 498 | -1.2% | [-4.9%, +2.7%] | -3.3% | -2.0% | 57% |
| 2018 selection | 48 | -1.9% | [-13.0%, +8.2%] | -3.7% | -8.3% | 56% |
| 2018 out-of-selection | 28 | -3.7% | [-17.9%, +6.7%] | -6.5% | -13.2% | 64% |
| 2019 selection | 53 | +8.9% | [-4.0%, +21.8%] | +7.1% | +3.5% | 64% |
| 2019 out-of-selection | 31 | +4.3% | [-9.0%, +19.5%] | +2.3% | -7.0% | 55% |
| 2020 selection | 65 | +8.5% | [-0.7%, +18.0%] | +6.6% | +4.5% | 68% |
| 2020 out-of-selection | 49 | +7.0% | [-4.0%, +18.1%] | +5.2% | +1.5% | 61% |
| 2021 selection | 52 | -0.8% | [-12.6%, +9.3%] | -2.8% | -6.4% | 62% |
| 2021 out-of-selection | 22 | -5.8% | [-16.0%, +2.6%] | -8.5% | -17.3% | 50% |
| 2022 out-of-selection | 155 | -3.2% | [-9.7%, +3.3%] | -5.0% | -5.2% | 57% |
| 2023 out-of-selection | 81 | -0.7% | [-9.3%, +8.2%] | -2.6% | -4.9% | 56% |
| 2024 out-of-selection | 85 | -0.2% | [-10.0%, +9.9%] | -2.3% | -4.1% | 59% |
| 2025 out-of-selection | 47 | -6.2% | [-23.1%, +9.6%] | -8.7% | -12.8% | 55% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 204 | +32.9% | [+30.1%, +36.0%] | +31.2% | +32.0% | 96% |
| 0.5-1 x implied | 145 | +6.5% | [+3.9%, +9.3%] | +4.7% | +5.0% | 63% |
| |move| >= 1 x implied | 149 | -55.5% | [-60.2%, -51.0%] | -58.3% | -57.2% | 0% |

Trades losing more than 100% of risk at exit midpoints: 5 of 499 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 498 | -1.2% | [-4.9%, +2.7%] | -3.2% | -2.0% | 57% |

