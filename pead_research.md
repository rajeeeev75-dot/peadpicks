# PEAD research (10581 results, 2020-11-13 to 2026-11-13; filters tested: 38)

Search period (TRAIN): up to 2025-12-09 (5822 results). Unseen period (TEST): after it (4759 results).
Returns are from the close of the first session after the result. Excess = minus the Nifty over the same days. Alpha = minus the average of all results in the same month.

## 1. The starting point: every result

| Period | Results | 20d excess avg | 20d median | Up vs Nifty | 60d excess avg |
|---|---|---|---|---|---|
| All | 9668 | -0.89% | -2.47% | 39.3% | -2.11% |
| TRAIN | 5822 | -1.54% | -3.07% | 37.0% | -5.02% |
| TEST | 3846 | +0.09% | -1.64% | 42.7% | +3.18% |

A negative start means that buying any result lost to the Nifty, so a filter has to rescue it, not just add to it.

| Year | Results | 20d excess avg | median |
|---|---|---|---|
| 2021 | 36 | +8.28% | +1.16% |
| 2022 | 51 | -0.29% | -1.99% |
| 2023 | 62 | +4.30% | +1.88% |
| 2024 | 1360 | +4.37% | +1.61% |
| 2025 | 4461 | -3.56% | -4.46% |
| 2026 | 4608 | +0.20% | -1.53% |

## 2. One filter at a time (which numbers carry information?)

Rank correlation (IC) of each filter with the 20-day alpha, and the average alpha of the lowest-to-highest fifth of results. 'Years same sign' counts calendar years in which the filter pointed the same way.

| Filter | IC | z | Years same sign | Lowest fifth ... highest fifth (avg 20d alpha %) |
|---|---|---|---|---|
| positive growth items (of 6) | +0.108 | +10.6 | 3/3 | -1.1 / -0.6 / -0.2 / +0.6 / +2.4 |
| price | +0.107 | +10.5 | 2/3 | -0.8 / -0.9 / +0.2 / +0.5 / +0.7 |
| daily turnover Rs crore | +0.106 | +10.4 | 2/3 | -0.7 / -0.6 / -0.2 / +0.3 / +1.0 |
| quarters of profit growth in a row | +0.099 | +9.7 | 3/3 | -0.6 / +0.7 / +1.2 |
| net margin % | +0.093 | +9.1 | 3/3 | -1.2 / -0.8 / -0.0 / +0.7 / +1.1 |
| distance from 52-week high % | +0.091 | +8.9 | 2/3 | -1.1 / -0.7 / -0.5 / +0.3 / +1.7 |
| operating margin % | +0.089 | +8.8 | 3/3 | -0.8 / -0.9 / -0.1 / +0.6 / +1.0 |
| worst profit YoY, last 4 qtrs | +0.088 | +8.7 | 3/3 | -1.1 / +0.2 / +0.6 / +1.1 |
| PEAD score | +0.086 | +8.4 | 3/3 | -1.3 / -0.9 / +0.0 / +0.2 / +1.7 |
| profit YoY % | +0.081 | +8.0 | 3/3 | -1.7 / -0.8 / +0.5 / +1.2 / +0.6 |
| daily volatility % | -0.081 | -7.9 | 2/3 | -0.1 / +0.3 / +0.4 / +0.3 / -1.0 |
| average YoY growth % | +0.080 | +7.9 | 3/3 | -1.6 / -0.8 / +0.2 / +1.0 / +1.0 |
| quarters of sales growth in a row | +0.077 | +7.5 | 3/3 | -0.7 / +0.8 / +0.4 / +0.5 |
| 12-month return before result | +0.075 | +7.1 | 3/3 | -1.3 / -0.9 / -0.0 / +0.5 / +1.5 |
| sales YoY % | +0.070 | +6.9 | 3/3 | -1.3 / -0.5 / -0.3 / +0.8 / +1.1 |
| growth-to-PE | +0.073 | +6.8 | 3/3 | -1.1 / +0.2 / +1.2 / +1.1 |
| acceleration | +0.065 | +6.3 | 2/3 | -0.4 / -1.1 / +0.5 / +0.3 / +0.5 |
| avg profit YoY, last 4 qtrs | +0.058 | +5.7 | 3/3 | -1.4 / -0.8 / +0.8 / +0.8 / +0.4 |
| % above 200-day average | +0.058 | +5.5 | 3/3 | -0.7 / -0.8 / -0.3 / +0.2 / +1.4 |
| EBITDA margin change YoY | +0.053 | +5.2 | 3/3 | -0.9 / -0.7 / +0.1 / +0.8 / +0.5 |

## 3. Best combinations found on TRAIN, judged on unseen TEST

| Rule (all must be true) | TRAIN n | TRAIN 20d excess | TEST n | TEST 20d excess | TEST alpha | TEST up vs Nifty | TEST median | Years positive |
|---|---|---|---|---|---|---|---|---|
| quarters of sales growth in a row at least 2 AND 12-month return before result at least -28.9 AND daily turnover Rs crore at least 34.32 AND daily volatility % at most 2.81 | 434 | -0.3% | 395 | +1.3% | +1.2% | 52% | +0.4% | 2/3 |
| quarters of sales growth in a row at least 2 AND 12-month return before result at least -28.9 AND daily turnover Rs crore at least 11.56 AND daily volatility % at most 2.133 | 471 | -1.0% | 401 | +0.7% | +0.7% | 49% | -0.2% | 3/4 |
| 12-month return before result at most 15.89 AND daily turnover Rs crore at least 34.32 AND daily volatility % at most 2.133 | 341 | -0.4% | 212 | +0.1% | -0.0% | 47% | -0.5% | 2/3 |
| P/E vs own history at least 0.7466 AND daily turnover Rs crore at least 34.32 AND daily volatility % at most 2.133 | 241 | -0.7% | 244 | +0.8% | +0.7% | 51% | +0.1% | 1/2 |
| positive growth items (of 6) at least 3 AND daily turnover Rs crore at least 34.32 AND daily volatility % at most 2.133 | 437 | -0.2% | 289 | +0.7% | +0.6% | 51% | +0.2% | 2/3 |
| daily turnover Rs crore at least 34.32 AND daily volatility % at most 2.81 AND Nifty % above 200-day average at most -1.163 | 150 | -1.9% | 353 | +0.6% | +0.2% | 48% | -0.8% | 1/2 |
| quarters of sales growth in a row at least 2 AND run-up in the 20 days before at most 5.682 AND daily turnover Rs crore at least 34.32 | 466 | -0.9% | 381 | +0.6% | +0.6% | 49% | -0.2% | 2/3 |
| quarters of sales growth in a row at least 2 AND avg profit YoY, last 4 qtrs at most 35.07 AND daily turnover Rs crore at least 34.32 | 387 | -0.6% | 298 | +0.8% | +0.6% | 50% | +0.0% | 2/3 |
| net margin % at least 6.548 AND Nifty % above 200-day average at most 2.282 | 992 | -0.9% | 1786 | +0.9% | +0.7% | 47% | -0.7% | 2/4 |
| P/E vs own history at least 0.7466 AND distance from 52-week high % at least -12.81 | 367 | -0.5% | 579 | +1.8% | +1.8% | 51% | +0.4% | 3/4 |
| positive growth items (of 6) at least 5 AND % above 200-day average at least -10.18 | 1199 | +0.8% | 846 | +2.2% | +2.4% | 52% | +0.4% | 4/5 |
| quarters of sales growth in a row at least 3 AND daily turnover Rs crore at least 34.32 | 414 | -0.3% | 494 | +1.0% | +1.0% | 51% | +0.4% | 2/3 |
| price at least 142.2 AND positive growth items (of 6) at least 5 | 1235 | +0.2% | 894 | +2.0% | +2.1% | 52% | +0.5% | 3/4 |
| PEAD score at least 49.7 AND acceleration at most -4.104 | 622 | +1.7% | 604 | +1.5% | +1.6% | 48% | -0.6% | 3/4 |
| net margin % at least 10.13 | 2016 | -0.4% | 1376 | +0.7% | +0.6% | 47% | -0.7% | 4/6 |

Shrinkage check: these 15 rules averaged +2.69% alpha on TRAIN and +0.99% on TEST. The second number is what to expect going forward; the gap is luck the search picked up.

## 4. Ideas you asked about, tested as written (fixed thresholds, nothing tuned)

| Idea | All n | 20d excess | Alpha | Up vs Nifty | Median | TEST n | TEST 20d excess | NSE-dated n | NSE-dated 20d excess |
|---|---|---|---|---|---|---|---|---|---|
| Your original combo: Excellent + volume 2x + positive reaction | 260 | +0.5% | +1.2% | 41% | -2.0% | 158 | +1.2% | 34 | +2.1% |
| Score 55+ and first-day reaction 5%+ | 930 | +1.9% | +2.7% | 48% | -0.6% | 527 | +2.3% | 117 | +4.8% |
| Score 55+ and low volume surge (under 2x) | 213 | +2.4% | +2.8% | 49% | -1.2% | 13 | +4.7% | 197 | +2.4% |
| Growth at a fair price: score 55+, forward P/E 20 or less | 1151 | +0.8% | +1.4% | 45% | -1.4% | 615 | +1.2% | 216 | +3.3% |
| Cheap and growing: score 55+, growth-to-PE 1.2+ | 1582 | +0.9% | +1.6% | 45% | -1.3% | 812 | +1.5% | 312 | +2.8% |
| Momentum: score 55+, 6-month return 20%+, within 15% of 52-week high | 375 | +3.6% | +3.8% | 56% | +1.8% | 188 | +3.2% | 83 | +8.5% |
| Durable: score 55+, profit grew 4+ quarters in a row, 5+ of 6 items positive | 324 | +1.3% | +2.5% | 48% | -0.8% | 227 | +2.3% | 4 | - |
| Beaten-down turnaround: score 55+, 6-month return under 0 | 827 | -0.2% | +1.0% | 43% | -1.7% | 442 | +0.8% | 140 | -1.9% |
| Liquid only: score 55+, reaction 3%+, turnover Rs 2 crore a day or more | 670 | +2.5% | +3.4% | 50% | -0.1% | 377 | +3.3% | 93 | +3.5% |

## 5. How the best rule behaves as a trade

Rule: **positive growth items (of 6) at least 5 AND % above 200-day average at least -10.18**

| Hold for | Trades | Avg return | Avg vs Nifty | Median vs Nifty | Up vs Nifty |
|---|---|---|---|---|---|
| 5 days | 2207 | -0.36% | -0.49% | -0.89% | 43% |
| 10 days | 2123 | -0.13% | -0.06% | -1.08% | 45% |
| 20 days | 2045 | +1.10% | +1.42% | -0.67% | 47% |
| 40 days | 2005 | +0.74% | +1.68% | -0.69% | 48% |
| 60 days | 1911 | +0.37% | +0.75% | -1.95% | 44% |

| Exit rule (close-based stop) | Trades | Avg return | Median | Winners |
|---|---|---|---|---|
| stop 8% / 20 days | 2045 | +0.83% | -2.40% | 41% |
| stop 12% / 20 days | 2045 | +1.02% | -1.22% | 45% |
| stop 8% / 60 days | 1911 | -0.70% | -8.32% | 29% |
| stop 12% / 60 days | 1911 | -0.85% | -8.36% | 37% |

Typical worst dip inside the first 20 days: median -5.7%, 1 trade in 4 dipped -10.1% or worse.

Frequency: about 382 qualifying results a year across the whole universe. Median daily turnover of these stocks: Rs 11.5 crore.

## How to read this honestly

* A rule is only interesting if its TEST numbers are positive, its TEST count is at least 30, and it is positive in most years.
* Averages here are pulled up by a few big winners. Look at the median and the share of winners as well as the average.
* Results are before brokerage, taxes and slippage. Small, thinly traded stocks can cost 1-3% to enter and exit, which can erase an edge of that size.
* Announcement dates marked 'spike' were inferred from a volume jump, not taken from the exchange, so some entries are a day off.
* Past results only. General information, not advice.
