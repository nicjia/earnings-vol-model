# Research7 sample E: untouched expanded universe

Evaluated 2026-10-03T07:33:38.653378+00:00. Rules were fixed in research7/e_hypotheses.json (commit ec109b9) before the expanded data was downloaded. Midpoint fills unless stated; gates: weekly-bootstrap lower 95% bound > 0, mean > 0 at 25% half-spread, mean > 0 excluding best 5, >= 100 events and >= 40 issuers; post-hoc rules also need Holm-adjusted p < 0.05 over the 14 listed.

**10 of 23 rules passed.**

| Kind | Rule | Events | Mean (mid) | 95% bootstrap | Mean 25% | Mean 50% | Excl. best 5 | t | Holm p | Lag mean | Passed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen | `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight` | 223 | +3.4% | [-8.5%, +15.4%] | -10.6% | -24.6% | -1.2% | +0.55 |  | +10.7% | no |
| frozen | `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight` | 706 | +5.1% | [-5.3%, +15.5%] | -14.1% | -33.3% | +1.3% | +0.96 |  | +6.8% | no |
| frozen | `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` | 194 | +8.5% | [-4.1%, +21.2%] | -5.3% | -19.2% | +2.0% | +1.29 |  | +12.8% | no |
| frozen | `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight` | 75 | +10.4% | [-3.6%, +24.3%] | +5.8% | +1.1% | +2.4% | +1.46 |  | +12.1% | no |
| frozen | `through:double_calendar_straddle_2w|P-4->hold_front|none|standard` | 301 | +5.0% | [-2.6%, +12.4%] | -2.8% | -10.6% | +2.0% | +1.26 |  | +7.2% | no |
| replication | `pre:long_straddle|P-1->P|R<=0.9|tight` | 341 | +2.0% | [+0.7%, +3.2%] | +0.6% | -0.8% | +1.5% | +3.16 |  | +3.1% | **yes** |
| replication | `pre:long_strangle|P-1->P|R<=0.9|tight` | 252 | +4.0% | [+2.0%, +6.0%] | +2.5% | +1.0% | +2.9% | +3.98 |  | +4.3% | **yes** |
| replication | `through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight` | 133 | +3.6% | [-4.0%, +11.5%] | -3.7% | -11.0% | +0.0% | +0.90 |  | +4.4% | no |
| replication | `through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard` | 174 | +2.1% | [-5.6%, +9.8%] | -4.2% | -10.5% | -2.4% | +0.53 |  | +4.6% | no |
| post-hoc | `pre:long_straddle|P-1->P|R<=0.9|tight` | 341 | +2.0% | [+0.7%, +3.2%] | +0.6% | -0.8% | +1.5% | +3.16 | 0.005 | +3.1% | **yes** |
| post-hoc | `pre:long_straddle|P-4->P|HR>=1.0|standard` | 651 | +3.4% | [+1.7%, +5.2%] | +1.3% | -0.9% | +2.5% | +3.70 | 0.001 | +3.1% | **yes** |
| post-hoc | `pre:long_straddle|P-4->P|HR>=1.0|tight` | 473 | +3.0% | [+1.4%, +4.6%] | +1.5% | -0.1% | +2.1% | +3.52 | 0.002 | +2.1% | **yes** |
| post-hoc | `pre:long_straddle|P-9->P|none|tight` | 1393 | +4.6% | [+2.2%, +7.1%] | +2.7% | +0.8% | +4.0% | +3.73 | 0.001 | +4.0% | **yes** |
| post-hoc | `pre:long_strangle|P-1->P|HR>=1.0|tight` | 355 | +2.8% | [+1.0%, +4.6%] | +1.2% | -0.3% | +2.0% | +3.13 | 0.005 | +2.9% | **yes** |
| post-hoc | `pre:long_strangle|P-1->P|R<=0.9|tight` | 252 | +4.0% | [+2.0%, +6.0%] | +2.5% | +1.0% | +2.9% | +3.98 | 0.000 | +4.3% | **yes** |
| post-hoc | `through:double_calendar_straddle_2w|P-1->hold_front|R>=1.2|standard` | 199 | +5.7% | [-0.7%, +12.4%] | -1.0% | -7.6% | +2.2% | +1.73 | 0.169 | +7.0% | no |
| post-hoc | `through:double_calendar_straddle_2w|P-4->hold_front|D<=1.0|standard` | 123 | +11.2% | [+1.1%, +22.1%] | +3.8% | -3.5% | +4.7% | +2.08 | 0.093 | +3.1% | no |
| post-hoc | `through:double_calendar_straddle_2w|P-4->hold_front|TSw>=1.15|standard` | 175 | +7.3% | [-2.9%, +18.3%] | -1.8% | -10.9% | +2.0% | +1.35 | 0.265 | +9.7% | no |
| post-hoc | `through:short_iron_condor_wide|P-1->Q|R>=1.2|tight` | 84 | +0.6% | [-7.7%, +8.2%] | -0.2% | -1.1% | -1.3% | +0.15 | 0.883 | -3.8% | no |
| post-hoc | `through:short_iron_condor_wide|P-1->Q|R>=1.4|tight` | 60 | -1.9% | [-11.8%, +6.9%] | -2.9% | -3.8% | -4.8% | -0.40 | 0.883 | -6.8% | no |
| post-hoc | `through:short_iron_fly_2x|P-1->Q+4|D<=1.0|standard` | 83 | +23.5% | [+14.5%, +32.5%] | +21.7% | +19.8% | +18.9% | +5.06 | 0.000 | +14.8% | no |
| post-hoc | `through:short_iron_fly_2x|P-4->Q+4|R>=1.0|standard` | 545 | +6.6% | [+3.1%, +10.0%] | +3.5% | +0.3% | +6.0% | +3.74 | 0.001 | +10.0% | **yes** |
| post-hoc | `through:short_iron_fly_2x|P-4->Q+4|none|standard` | 595 | +8.3% | [+5.0%, +11.5%] | +5.3% | +2.2% | +7.7% | +4.99 | 0.000 | +11.5% | **yes** |

## Splits by name group and release timing

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight` expanded_2017 | 64 | 24 | +10.5% | [-12.3%, +34.2%] | -6.3% | -23.1% | -4.4% | 55% | -221.0% |
| `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight` added_2020 | 159 | 37 | +0.5% | [-11.8%, +13.7%] | -12.3% | -25.2% | -5.4% | 46% | -185.1% |
| `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight` before open | 47 | 15 | +5.4% | [-15.0%, +26.4%] | -7.9% | -21.2% | -12.2% | 47% | -123.9% |
| `through:double_calendar_put_1w|P-4->hold_front|TSw>=1.15|tight` after close | 176 | 52 | +2.8% | [-9.0%, +16.5%] | -11.3% | -25.5% | -2.9% | 49% | -221.0% |
| `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight` expanded_2017 | 288 | 66 | +5.7% | [-8.4%, +19.7%] | -19.7% | -45.1% | -1.0% | 41% | -217.8% |
| `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight` added_2020 | 418 | 62 | +4.7% | [-8.3%, +18.9%] | -10.3% | -25.2% | -1.5% | 39% | -395.8% |
| `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight` before open | 213 | 56 | +8.1% | [-8.0%, +25.4%] | -12.8% | -33.7% | -1.3% | 40% | -233.2% |
| `through:atm_put_calendar_1w|P-1->hold_front|TSw>=1.15|tight` after close | 491 | 89 | +4.1% | [-7.2%, +16.2%] | -14.3% | -32.6% | -1.0% | 40% | -395.8% |
| `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` expanded_2017 | 49 | 22 | +6.9% | [-15.5%, +30.9%] | -11.0% | -28.9% | -13.5% | 41% | -129.3% |
| `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` added_2020 | 145 | 40 | +9.1% | [-4.8%, +23.0%] | -3.4% | -15.9% | +0.2% | 40% | -225.6% |
| `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` before open | 43 | 22 | +23.1% | [-4.7%, +53.1%] | +7.5% | -8.1% | -3.9% | 49% | -96.3% |
| `through:double_calendar_straddle_1w|P-4->hold_front|TSw>=1.15|standard` after close | 151 | 49 | +4.4% | [-8.9%, +17.8%] | -9.0% | -22.3% | -3.5% | 38% | -225.6% |
| `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight` expanded_2017 | 28 | 14 | +6.9% | [-16.1%, +32.8%] | +2.3% | -2.2% | -14.3% | 39% | -85.4% |
| `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight` added_2020 | 47 | 19 | +12.5% | [-2.8%, +26.8%] | +7.8% | +3.1% | +2.6% | 68% | -92.6% |
| `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight` before open | 32 | 18 | +7.9% | [-10.5%, +27.0%] | +3.3% | -1.2% | -7.8% | 56% | -85.4% |
| `through:double_diagonal_put_1w|P-4->hold_front|R>=1.4|tight` after close | 40 | 20 | +14.2% | [-4.1%, +33.6%] | +9.4% | +4.6% | +0.9% | 60% | -92.6% |
| `through:double_calendar_straddle_2w|P-4->hold_front|none|standard` expanded_2017 | 128 | 35 | -4.3% | [-12.2%, +3.6%] | -13.7% | -23.1% | -9.8% | 39% | -106.2% |
| `through:double_calendar_straddle_2w|P-4->hold_front|none|standard` added_2020 | 173 | 48 | +11.9% | [+1.0%, +23.1%] | +5.3% | -1.4% | +7.0% | 51% | -92.0% |
| `through:double_calendar_straddle_2w|P-4->hold_front|none|standard` before open | 102 | 34 | +8.7% | [-3.6%, +21.6%] | +0.9% | -6.9% | +0.4% | 48% | -106.2% |
| `through:double_calendar_straddle_2w|P-4->hold_front|none|standard` after close | 194 | 65 | +3.4% | [-4.7%, +12.4%] | -4.4% | -12.1% | -0.6% | 45% | -95.1% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` expanded_2017 | 144 | 54 | +1.5% | [-0.0%, +3.0%] | -0.2% | -1.8% | +0.5% | 50% | -19.6% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` added_2020 | 197 | 52 | +2.4% | [+0.6%, +4.2%] | +1.2% | -0.0% | +1.6% | 56% | -15.8% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` before open | 81 | 41 | -0.2% | [-1.8%, +1.6%] | -1.7% | -3.2% | -1.6% | 40% | -17.1% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` after close | 260 | 77 | +2.7% | [+1.2%, +4.3%] | +1.4% | +0.0% | +2.1% | 58% | -19.6% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` expanded_2017 | 83 | 35 | +2.8% | [+0.1%, +5.9%] | +1.2% | -0.5% | +0.1% | 51% | -24.0% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` added_2020 | 169 | 42 | +4.6% | [+2.0%, +7.0%] | +3.2% | +1.7% | +3.3% | 59% | -24.6% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` before open | 43 | 22 | +1.6% | [-1.5%, +5.2%] | +0.0% | -1.5% | -1.4% | 47% | -15.0% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` after close | 209 | 62 | +4.5% | [+2.1%, +6.7%] | +3.0% | +1.5% | +3.3% | 58% | -24.6% |
| `through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight` expanded_2017 | 46 | 18 | +2.8% | [-10.4%, +16.0%] | -5.1% | -13.1% | -7.4% | 57% | -79.9% |
| `through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight` added_2020 | 87 | 35 | +4.0% | [-6.2%, +14.9%] | -2.9% | -9.8% | -0.8% | 64% | -104.9% |
| `through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight` before open | 38 | 16 | +4.2% | [-9.5%, +16.5%] | -3.8% | -11.8% | -4.6% | 63% | -78.4% |
| `through:double_diagonal_put_1w|P-1->Q|D<=1.0|tight` after close | 94 | 42 | +3.3% | [-5.8%, +13.5%] | -3.7% | -10.7% | -1.8% | 61% | -104.9% |
| `through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard` expanded_2017 | 79 | 35 | +8.0% | [-3.0%, +18.9%] | +0.3% | -7.4% | -0.5% | 47% | -98.5% |
| `through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard` added_2020 | 95 | 36 | -2.8% | [-12.0%, +6.4%] | -7.9% | -13.1% | -9.1% | 40% | -80.0% |
| `through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard` before open | 73 | 30 | +3.3% | [-7.0%, +13.0%] | -2.8% | -8.9% | -4.5% | 44% | -98.5% |
| `through:double_calendar_straddle_2w|P->hold_front|R>=1.2|standard` after close | 98 | 46 | +1.1% | [-8.4%, +10.7%] | -5.4% | -11.9% | -6.2% | 42% | -80.0% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` expanded_2017 | 144 | 54 | +1.5% | [-0.0%, +3.0%] | -0.2% | -1.8% | +0.5% | 50% | -19.6% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` added_2020 | 197 | 52 | +2.4% | [+0.6%, +4.2%] | +1.2% | -0.0% | +1.6% | 56% | -15.8% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` before open | 81 | 41 | -0.2% | [-1.8%, +1.6%] | -1.7% | -3.2% | -1.6% | 40% | -17.1% |
| `pre:long_straddle|P-1->P|R<=0.9|tight` after close | 260 | 77 | +2.7% | [+1.2%, +4.3%] | +1.4% | +0.0% | +2.1% | 58% | -19.6% |
| `pre:long_straddle|P-4->P|HR>=1.0|standard` expanded_2017 | 378 | 102 | +3.6% | [+1.6%, +5.6%] | +1.0% | -1.5% | +2.4% | 51% | -32.7% |
| `pre:long_straddle|P-4->P|HR>=1.0|standard` added_2020 | 273 | 56 | +3.2% | [+0.4%, +5.9%] | +1.6% | +0.1% | +1.3% | 49% | -43.3% |
| `pre:long_straddle|P-4->P|HR>=1.0|standard` before open | 260 | 76 | +2.8% | [+0.1%, +5.1%] | +0.3% | -2.2% | +1.3% | 49% | -43.3% |
| `pre:long_straddle|P-4->P|HR>=1.0|standard` after close | 389 | 96 | +3.8% | [+1.6%, +6.1%] | +1.9% | +0.0% | +2.4% | 51% | -34.3% |
| `pre:long_straddle|P-4->P|HR>=1.0|tight` expanded_2017 | 232 | 75 | +3.2% | [+1.1%, +5.3%] | +1.4% | -0.4% | +1.7% | 53% | -32.7% |
| `pre:long_straddle|P-4->P|HR>=1.0|tight` added_2020 | 241 | 51 | +2.8% | [+0.4%, +5.1%] | +1.5% | +0.2% | +1.2% | 50% | -43.3% |
| `pre:long_straddle|P-4->P|HR>=1.0|tight` before open | 169 | 60 | +2.4% | [+0.1%, +4.8%] | +0.8% | -0.9% | +0.5% | 51% | -43.3% |
| `pre:long_straddle|P-4->P|HR>=1.0|tight` after close | 303 | 78 | +3.3% | [+1.0%, +5.5%] | +1.8% | +0.4% | +1.9% | 52% | -34.3% |
| `pre:long_straddle|P-9->P|none|tight` expanded_2017 | 797 | 179 | +5.4% | [+2.4%, +8.8%] | +3.2% | +1.0% | +4.3% | 46% | -61.4% |
| `pre:long_straddle|P-9->P|none|tight` added_2020 | 596 | 114 | +3.6% | [+0.4%, +7.0%] | +2.0% | +0.4% | +2.5% | 44% | -47.7% |
| `pre:long_straddle|P-9->P|none|tight` before open | 618 | 152 | +4.5% | [+1.5%, +7.5%] | +2.4% | +0.3% | +3.3% | 47% | -45.4% |
| `pre:long_straddle|P-9->P|none|tight` after close | 768 | 183 | +4.8% | [+1.6%, +8.2%] | +3.0% | +1.2% | +3.7% | 45% | -61.4% |
| `pre:long_strangle|P-1->P|HR>=1.0|tight` expanded_2017 | 136 | 49 | +1.6% | [-0.9%, +4.2%] | -0.2% | -2.1% | -0.1% | 50% | -42.1% |
| `pre:long_strangle|P-1->P|HR>=1.0|tight` added_2020 | 219 | 43 | +3.5% | [+1.3%, +5.8%] | +2.1% | +0.7% | +2.3% | 56% | -31.7% |
| `pre:long_strangle|P-1->P|HR>=1.0|tight` before open | 100 | 41 | +2.0% | [-1.0%, +5.2%] | +0.3% | -1.4% | -0.2% | 52% | -42.1% |
| `pre:long_strangle|P-1->P|HR>=1.0|tight` after close | 253 | 61 | +3.0% | [+1.1%, +5.0%] | +1.5% | +0.0% | +2.0% | 55% | -31.7% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` expanded_2017 | 83 | 35 | +2.8% | [+0.1%, +5.9%] | +1.2% | -0.5% | +0.1% | 51% | -24.0% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` added_2020 | 169 | 42 | +4.6% | [+2.0%, +7.0%] | +3.2% | +1.7% | +3.3% | 59% | -24.6% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` before open | 43 | 22 | +1.6% | [-1.5%, +5.2%] | +0.0% | -1.5% | -1.4% | 47% | -15.0% |
| `pre:long_strangle|P-1->P|R<=0.9|tight` after close | 209 | 62 | +4.5% | [+2.1%, +6.7%] | +3.0% | +1.5% | +3.3% | 58% | -24.6% |
| `through:short_iron_fly_2x|P-4->Q+4|R>=1.0|standard` expanded_2017 | 378 | 132 | +3.0% | [-0.9%, +6.8%] | -0.4% | -3.9% | +2.0% | 62% | -103.1% |
| `through:short_iron_fly_2x|P-4->Q+4|R>=1.0|standard` added_2020 | 167 | 74 | +14.9% | [+9.5%, +20.2%] | +12.3% | +9.8% | +13.2% | 72% | -100.2% |
| `through:short_iron_fly_2x|P-4->Q+4|R>=1.0|standard` before open | 234 | 98 | +1.0% | [-3.6%, +5.8%] | -2.4% | -5.7% | -0.3% | 59% | -103.1% |
| `through:short_iron_fly_2x|P-4->Q+4|R>=1.0|standard` after close | 307 | 119 | +11.6% | [+7.0%, +16.0%] | +8.6% | +5.7% | +10.5% | 70% | -96.1% |
| `through:short_iron_fly_2x|P-4->Q+4|none|standard` expanded_2017 | 399 | 137 | +3.3% | [-0.6%, +7.1%] | -0.0% | -3.4% | +2.4% | 62% | -103.4% |
| `through:short_iron_fly_2x|P-4->Q+4|none|standard` added_2020 | 196 | 81 | +18.4% | [+13.6%, +23.1%] | +16.1% | +13.7% | +17.1% | 75% | -100.2% |
| `through:short_iron_fly_2x|P-4->Q+4|none|standard` before open | 247 | 102 | +1.8% | [-2.8%, +6.3%] | -1.5% | -4.9% | +0.6% | 59% | -103.4% |
| `through:short_iron_fly_2x|P-4->Q+4|none|standard` after close | 343 | 127 | +13.8% | [+9.4%, +17.9%] | +11.0% | +8.2% | +12.9% | 72% | -96.1% |

## Walk-forward selector on sample E

| Year | Policy chosen from earlier E years | OOS events | OOS mean (mid) | OOS mean 25% |
|---|---|---|---|---|
| 2020 | `through:atm_straddle_calendar_month|P-4->hold_front|none|standard` | 53 | +0.7% | -14.7% |
| 2021 | `through:atm_straddle_calendar_month|P-4->hold_front|none|standard` | 178 | +13.0% | +2.0% |
| 2022 | `through:atm_put_calendar_1w|P->hold_front|D<=1.0|standard` | 85 | -2.4% | -18.6% |
| 2023 | `pre:long_strangle|P-4->P|R<=0.9|standard` | 61 | +4.3% | +2.6% |
| 2024 | `pre:long_straddle|P-9->P|R<=0.9|standard` | 45 | +8.0% | +6.3% |
| 2025 | `pre:long_strangle|P-9->P|R<=0.9|standard` | 13 | +13.6% | +11.7% |

| Sample | Events | Issuers | Mean (mid) | 95% weekly bootstrap | Mean 25% cost | Mean 50% cost | Excl. best 5 | Win rate | Worst |
|---|---|---|---|---|---|---|---|---|---|
| 2020-2025 OOS | 435 | 187 | +6.8% | [-0.3%, +13.8%] | -3.2% | -13.2% | +2.5% | 49% | -118.9% |

Illustrative account: +70.5% at mid, -28.5% at 25% cost.

