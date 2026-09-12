# Reference-support diagnosis and retest

The frozen pre-earnings liquidity/cost candidate generated four trades across three events in five additional companies. All four lost after crossing quotes. Two VRTX calls had strikes 395 and 405 while the actual fitted reference strikes spanned 450–510. They were extrapolations, despite the signal's acceptable relative spread. The model's inferred forward also differed from the no-dividend carry forward; extrapolation is not the only possible price-error source.

The targeted adjustment keeps only target strikes bracketed by the fitted reference strikes at the signal date. It uses no future prices. It is evaluated on both the original and additional-company panels, but the latter has now been inspected; these adjusted results must not be called fresh validation. The original frozen additional-company result is preserved separately. A positive reduced sample would not establish an executable edge.

| panel | period | version | fraction | trades | events | all_event_bp | ci_low_bp | ci_high_bp | premium_pct |
|---|---|---|---|---|---|---|---|---|---|
| original | development | original_rule | 0 | 22 | 10 | -1.03 | -1.98 | -0.19 | -8.82 |
| original | development | original_rule | 1 | 22 | 10 | -9.80 | -26.40 | -0.42 | -19.83 |
| original | development | no_extrapolation | 0 | 20 | 10 | -1.98 | -4.66 | -0.19 | -9.68 |
| original | development | no_extrapolation | 1 | 20 | 10 | -4.01 | -8.84 | -0.42 | -17.31 |
| original | later | original_rule | 0 | 9 | 7 | 1.77 | 0.03 | 4.06 | 16.28 |
| original | later | original_rule | 1 | 9 | 7 | 1.55 | -0.05 | 3.74 | 13.10 |
| original | later | no_extrapolation | 0 | 6 | 6 | 1.03 | -0.01 | 2.80 | 12.65 |
| original | later | no_extrapolation | 1 | 6 | 6 | 0.87 | -0.14 | 2.57 | 9.35 |
| original | all | original_rule | 0 | 31 | 17 | 0.18 | -0.80 | 1.44 | 1.52 |
| original | all | original_rule | 1 | 31 | 17 | -4.89 | -14.73 | 0.72 | -6.27 |
| original | all | no_extrapolation | 0 | 26 | 16 | -0.68 | -2.44 | 0.74 | -1.31 |
| original | all | no_extrapolation | 1 | 26 | 16 | -1.90 | -4.85 | 0.33 | -7.31 |
| new_names | later | original_rule | 0 | 4 | 3 | -1.26 | -3.10 | 0.00 | -18.72 |
| new_names | later | original_rule | 1 | 4 | 3 | -4.03 | -10.81 | 0.00 | -26.96 |
| new_names | later | no_extrapolation | 0 | 2 | 2 | -0.98 | -2.66 | 0.00 | -27.55 |
| new_names | later | no_extrapolation | 1 | 2 | 2 | -1.24 | -3.37 | 0.00 | -35.17 |
| new_names | all | original_rule | 0 | 4 | 3 | -1.26 | -3.10 | 0.00 | -18.72 |
| new_names | all | original_rule | 1 | 4 | 3 | -4.03 | -10.81 | 0.00 | -26.96 |
| new_names | all | no_extrapolation | 0 | 2 | 2 | -0.98 | -2.66 | 0.00 | -27.55 |
| new_names | all | no_extrapolation | 1 | 2 | 2 | -1.24 | -3.37 | 0.00 | -35.17 |

## Signal support audit

| panel | sid | event | ids | strike | reference_min | reference_max | within_reference_band |
|---|---|---|---|---|---|---|---|
| original | 101310 | 2016-10-27 00:00:00 | 113311583 | 700.00 | 660.00 | 960.00 | True |
| original | 101121 | 2018-04-25 00:00:00 | 119893195 | 8.00 | 9.00 | 12.00 | False |
| original | 101121 | 2018-04-25 00:00:00 | 119893196 | 8.50 | 9.00 | 12.00 | False |
| original | 101121 | 2018-04-25 00:00:00 | 119893200 | 10.50 | 9.00 | 12.00 | True |
| original | 115422 | 2018-01-22 00:00:00 | 118031166 | 170.00 | 160.00 | 260.00 | True |
| original | 101062 | 2019-06-18 00:00:00 | 120371625 | 240.00 | 210.00 | 307.50 | True |
| original | 101310 | 2020-04-30 00:00:00 | 133663669 | 2820.00 | 1820.00 | 2960.00 | True |
| original | 101310 | 2020-04-30 00:00:00 | 133663670 | 2840.00 | 1820.00 | 2960.00 | True |
| original | 101310 | 2020-04-30 00:00:00 | 133663671 | 2860.00 | 1820.00 | 2960.00 | True |
| original | 101310 | 2020-10-29 00:00:00 | 136289556 | 3950.00 | 2510.00 | 4100.00 | True |
| original | 101062 | 2021-06-17 00:00:00 | 140522818 | 495.00 | 430.00 | 550.00 | True |
| original | 101310 | 2021-04-29 00:00:00 | 134536781 | 3800.00 | 2540.00 | 4100.00 | True |
| original | 101310 | 2021-04-29 00:00:00 | 134752717 | 3950.00 | 2540.00 | 4100.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176180 | 4150.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176181 | 4200.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176182 | 4250.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176183 | 4300.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176184 | 4350.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176208 | 2950.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-07-29 00:00:00 | 136176209 | 3000.00 | 2750.00 | 4500.00 | True |
| original | 101310 | 2021-10-28 00:00:00 | 138091222 | 3800.00 | 2500.00 | 4100.00 | True |
| original | 101310 | 2021-10-28 00:00:00 | 139855349 | 3950.00 | 2500.00 | 4100.00 | True |
| original | 101310 | 2022-04-28 00:00:00 | 143503215 | 3600.00 | 2340.00 | 3700.00 | True |
| original | 101121 | 2023-01-31 00:00:00 | 147054363 | 85.00 | 55.00 | 75.00 | False |
| original | 101121 | 2023-01-31 00:00:00 | 151759577 | 80.00 | 54.00 | 75.00 | False |
| original | 101121 | 2023-01-31 00:00:00 | 151844987 | 80.00 | 54.00 | 75.00 | False |
| original | 101121 | 2024-01-30 00:00:00 | 156287113 | 135.00 | 120.00 | 195.00 | True |
| original | 115422 | 2024-10-17 00:00:00 | 164098282 | 635.00 | 550.00 | 850.00 | True |
| original | 143439 | 2024-01-24 00:00:00 | 159169064 | 190.00 | 180.00 | 290.00 | True |
| original | 101121 | 2025-02-04 00:00:00 | 162907485 | 145.00 | 95.00 | 150.00 | True |
| original | 101310 | 2025-02-06 00:00:00 | 163657087 | 190.00 | 180.00 | 290.00 | True |
| new_names | 106369 | 2023-07-20 00:00:00 | 154966311 | 350.00 | 280.00 | 360.00 | True |
| new_names | 111683 | 2024-11-04 00:00:00 | 164731428 | 395.00 | 450.00 | 510.00 | False |
| new_names | 111683 | 2024-11-04 00:00:00 | 164731430 | 405.00 | 450.00 | 510.00 | False |
| new_names | 154666 | 2024-01-24 00:00:00 | 154797554 | 800.00 | 570.00 | 830.00 | True |

Units are basis points of stock notional averaged across all event opportunities, and supplementary premium-normalized means. The same entry-date delta hedge, fixed pre-earnings exit and execution assumptions are preserved.
