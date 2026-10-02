# Research6 post-freeze diagnostics

Exploratory breakdowns of the five frozen policies after all stages were evaluated. None of these groupings was pre-registered as a gate, and none can change the frozen set or the verdict.

## `atm_put_calendar|E-1->hold_front|R>=1.2|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 639 | +2.4% | [-6.3%, +10.5%] | -12.7% | -0.5% | 43% |
| 2018 selection | 81 | +10.5% | [-15.8%, +34.8%] | -3.0% | -6.6% | 46% |
| 2018 out-of-selection | 35 | +31.4% | [-9.0%, +70.2%] | +11.5% | -2.1% | 54% |
| 2019 selection | 72 | +38.0% | [+7.9%, +66.5%] | +26.7% | +11.5% | 49% |
| 2019 out-of-selection | 48 | +9.6% | [-20.0%, +41.6%] | -5.3% | -12.1% | 48% |
| 2020 selection | 94 | +19.7% | [+0.1%, +42.0%] | +11.0% | +8.1% | 56% |
| 2020 out-of-selection | 55 | +16.1% | [-9.0%, +43.9%] | +7.1% | -5.2% | 51% |
| 2021 selection | 70 | +5.6% | [-12.4%, +23.0%] | -6.6% | -10.2% | 46% |
| 2021 out-of-selection | 41 | -11.4% | [-29.0%, +11.1%] | -27.2% | -42.2% | 34% |
| 2022 out-of-selection | 189 | +5.9% | [-11.5%, +24.5%] | -5.3% | -1.4% | 45% |
| 2023 out-of-selection | 91 | -4.6% | [-23.1%, +12.0%] | -18.1% | -18.9% | 40% |
| 2024 out-of-selection | 108 | -10.3% | [-29.9%, +8.1%] | -32.6% | -25.9% | 35% |
| 2025 out-of-selection | 72 | -0.6% | [-30.3%, +29.1%] | -18.9% | -15.4% | 46% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 208 | +116.2% | [+105.0%, +128.1%] | +105.7% | +109.9% | 96% |
| 0.5-1 x implied | 163 | -12.1% | [-19.5%, -5.2%] | -25.8% | -15.5% | 40% |
| |move| >= 1 x implied | 268 | -77.1% | [-83.8%, -70.3%] | -96.6% | -81.0% | 4% |

Trades losing more than 100% of risk at exit midpoints: 44 of 639 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 639 | +5.0% | [-3.3%, +12.8%] | -6.1% | +2.1% | 43% |

## `atm_straddle_calendar|E-1->hold_front|R>=1.2|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 702 | +6.0% | [-1.6%, +13.7%] | -7.7% | +3.0% | 43% |
| 2018 selection | 90 | +9.0% | [-13.7%, +31.7%] | -5.3% | -4.8% | 44% |
| 2018 out-of-selection | 42 | +5.5% | [-24.5%, +38.1%] | -10.6% | -20.8% | 45% |
| 2019 selection | 85 | +23.7% | [+0.8%, +44.2%] | +12.7% | +4.2% | 45% |
| 2019 out-of-selection | 60 | +29.0% | [-1.1%, +61.7%] | +15.2% | +8.0% | 52% |
| 2020 selection | 85 | +29.1% | [+4.8%, +56.0%] | +19.8% | +14.4% | 55% |
| 2020 out-of-selection | 54 | -3.1% | [-27.0%, +22.8%] | -12.1% | -23.8% | 43% |
| 2021 selection | 79 | +5.5% | [-12.1%, +20.0%] | -6.4% | -8.5% | 46% |
| 2021 out-of-selection | 35 | -11.4% | [-37.3%, +19.3%] | -23.8% | -42.3% | 34% |
| 2022 out-of-selection | 189 | +5.0% | [-9.8%, +21.6%] | -4.6% | -2.8% | 42% |
| 2023 out-of-selection | 110 | +1.6% | [-12.3%, +13.8%] | -9.3% | -8.7% | 42% |
| 2024 out-of-selection | 134 | +10.1% | [-7.6%, +29.7%] | -12.2% | -4.2% | 42% |
| 2025 out-of-selection | 78 | +4.5% | [-25.8%, +32.5%] | -11.3% | -13.0% | 42% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 241 | +116.7% | [+105.0%, +130.0%] | +107.3% | +110.1% | 96% |
| 0.5-1 x implied | 175 | -15.3% | [-22.1%, -8.7%] | -28.3% | -19.1% | 31% |
| |move| >= 1 x implied | 286 | -74.2% | [-79.1%, -69.3%] | -92.1% | -76.7% | 5% |

Trades losing more than 100% of risk at exit midpoints: 40 of 702 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 702 | +7.3% | [-0.2%, +15.1%] | -4.3% | +4.3% | 43% |

## `double_diagonal_put|E-1->after_release|R>=1.2|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 303 | -1.0% | [-6.0%, +4.4%] | -6.1% | -3.0% | 55% |
| 2018 selection | 42 | +12.5% | [-3.7%, +28.8%] | +7.0% | +2.1% | 69% |
| 2018 out-of-selection | 19 | -11.9% | [-28.6%, +11.4%] | -20.2% | -30.5% | 42% |
| 2019 selection | 45 | +14.8% | [+3.6%, +24.4%] | +10.6% | +7.3% | 67% |
| 2019 out-of-selection | 23 | +11.8% | [-1.7%, +23.2%] | +6.4% | +1.9% | 70% |
| 2020 selection | 58 | +12.1% | [+0.9%, +24.5%] | +7.5% | +6.0% | 69% |
| 2020 out-of-selection | 34 | -4.4% | [-27.3%, +17.4%] | -9.5% | -17.8% | 44% |
| 2021 selection | 42 | +3.7% | [-9.7%, +14.4%] | -0.0% | -3.0% | 60% |
| 2021 out-of-selection | 19 | +0.5% | [-13.3%, +17.7%] | -4.7% | -15.2% | 63% |
| 2022 out-of-selection | 100 | +3.5% | [-4.6%, +13.4%] | -0.6% | -1.6% | 62% |
| 2023 out-of-selection | 41 | -11.0% | [-28.5%, +3.1%] | -15.8% | -23.0% | 41% |
| 2024 out-of-selection | 36 | +0.4% | [-13.7%, +14.2%] | -5.3% | -11.5% | 53% |
| 2025 out-of-selection | 31 | -3.6% | [-17.9%, +9.9%] | -10.1% | -15.2% | 58% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 113 | +33.3% | [+27.6%, +39.5%] | +29.3% | +29.7% | 93% |
| 0.5-1 x implied | 84 | +11.9% | [+6.6%, +17.5%] | +7.4% | +7.7% | 68% |
| |move| >= 1 x implied | 106 | -47.7% | [-53.6%, -42.0%] | -54.7% | -50.5% | 5% |

Trades losing more than 100% of risk at exit midpoints: 6 of 303 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 303 | -0.4% | [-5.4%, +4.8%] | -5.2% | -2.4% | 55% |

## `atm_call_calendar|E-1->hold_front|R>=1.2|tight`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 729 | -0.0% | [-6.9%, +7.0%] | -13.9% | -2.8% | 40% |
| 2018 selection | 94 | +0.7% | [-13.5%, +14.0%] | -11.4% | -11.6% | 45% |
| 2018 out-of-selection | 44 | -9.7% | [-39.3%, +18.5%] | -27.9% | -39.1% | 34% |
| 2019 selection | 84 | +25.1% | [+4.7%, +46.2%] | +12.8% | +6.9% | 45% |
| 2019 out-of-selection | 54 | +19.9% | [-7.5%, +49.5%] | +4.5% | -1.4% | 50% |
| 2020 selection | 99 | +24.7% | [+2.2%, +51.7%] | +14.9% | +10.9% | 53% |
| 2020 out-of-selection | 58 | +1.9% | [-23.3%, +30.7%] | -9.4% | -19.7% | 43% |
| 2021 selection | 75 | +6.9% | [-13.8%, +24.2%] | -5.2% | -8.0% | 47% |
| 2021 out-of-selection | 42 | -0.5% | [-26.9%, +31.8%] | -13.2% | -29.2% | 36% |
| 2022 out-of-selection | 207 | +1.2% | [-12.8%, +15.7%] | -8.4% | -5.0% | 41% |
| 2023 out-of-selection | 102 | +0.9% | [-12.1%, +13.3%] | -10.5% | -9.3% | 43% |
| 2024 out-of-selection | 130 | -4.6% | [-21.0%, +12.7%] | -25.9% | -19.4% | 36% |
| 2025 out-of-selection | 92 | -5.4% | [-23.3%, +11.5%] | -20.7% | -15.5% | 37% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 227 | +107.8% | [+96.4%, +119.9%] | +98.4% | +101.2% | 96% |
| 0.5-1 x implied | 195 | -14.0% | [-20.3%, -7.1%] | -27.4% | -17.6% | 32% |
| |move| >= 1 x implied | 307 | -70.9% | [-75.6%, -66.2%] | -88.4% | -74.0% | 4% |

Trades losing more than 100% of risk at exit midpoints: 41 of 729 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 729 | +1.0% | [-5.6%, +7.9%] | -10.4% | -1.7% | 40% |

## `double_calendar_straddle_2w|E-2->hold_front|TSw>=1.3|standard`

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D pooled (out of selection) | 745 | +2.8% | [-1.7%, +7.5%] | -4.6% | +1.0% | 45% |
| 2018 selection | 92 | +9.7% | [-5.4%, +26.0%] | +2.5% | +0.3% | 48% |
| 2018 out-of-selection | 55 | +13.9% | [-1.5%, +28.3%] | +6.7% | +0.6% | 51% |
| 2019 selection | 128 | +10.4% | [+0.4%, +21.1%] | +4.3% | +4.0% | 50% |
| 2019 out-of-selection | 86 | +1.3% | [-13.4%, +14.8%] | -5.0% | -5.4% | 50% |
| 2020 selection | 64 | +21.0% | [+0.8%, +37.6%] | +15.5% | +10.0% | 58% |
| 2020 out-of-selection | 41 | -2.6% | [-19.0%, +14.9%] | -9.2% | -16.5% | 44% |
| 2021 selection | 76 | +2.6% | [-7.8%, +13.9%] | -3.8% | -4.2% | 51% |
| 2021 out-of-selection | 56 | +14.1% | [-4.4%, +36.3%] | +5.2% | -0.3% | 50% |
| 2022 out-of-selection | 94 | +6.8% | [-3.5%, +16.4%] | +0.9% | -0.1% | 49% |
| 2023 out-of-selection | 169 | -5.3% | [-16.4%, +5.7%] | -11.1% | -9.5% | 40% |
| 2024 out-of-selection | 149 | +2.7% | [-7.7%, +11.7%] | -6.7% | -4.4% | 42% |
| 2025 out-of-selection | 95 | +4.0% | [-9.8%, +16.3%] | -5.4% | -2.8% | 44% |

Out-of-selection trades by realized stock move entry->exit relative to the entry implied move:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| |move| < 0.5 x implied | 252 | -27.8% | [-31.6%, -23.7%] | -33.2% | -30.1% | 13% |
| 0.5-1 x implied | 183 | +33.4% | [+26.4%, +40.7%] | +26.7% | +28.5% | 76% |
| |move| >= 1 x implied | 310 | +9.6% | [+1.1%, +18.7%] | +0.1% | +6.2% | 53% |

Trades losing more than 100% of risk at exit midpoints: 7 of 752 (exit quotes whose midpoints exceed the no-arbitrage package bound). Capping each at the theoretical maximum loss plus fees, as holding to expiry would allow:

| Group | Events | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Excl. best 5 | Win rate |
|---|---|---|---|---|---|---|
| B+C+D capped | 745 | +3.0% | [-1.4%, +7.6%] | -4.1% | +1.3% | 45% |

