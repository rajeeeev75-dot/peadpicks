# PEAD research (3490 results, 2020-11-13 to 2026-11-05; filters tested: 38)

Search period (TRAIN): up to 2025-12-04 (1922 results). Unseen period (TEST): after it (1568 results).
Returns are from the close of the first session after the result. Excess = minus the Nifty over the same days. Alpha = minus the average of all results in the same month.

## 1. The starting point: every result

| Period | Results | 20d excess avg | 20d median | Up vs Nifty | 60d excess avg |
|---|---|---|---|---|---|
| All | 3221 | -0.72% | -2.19% | 39.8% | -2.22% |
| TRAIN | 1922 | -1.50% | -3.12% | 36.7% | -4.98% |
| TEST | 1299 | +0.43% | -1.12% | 44.3% | +2.71% |

A negative start means that buying any result lost to the Nifty, so a filter has to rescue it, not just add to it.

| Year | Results | 20d excess avg | median |
|---|---|---|---|
| 2024 | 484 | +4.35% | +0.76% |
| 2025 | 1472 | -3.71% | -4.47% |
| 2026 | 1492 | +0.64% | -0.90% |

## 2. One filter at a time (which numbers carry information?)

Rank correlation (IC) of each filter with the 20-day alpha, and the average alpha of the lowest-to-highest fifth of results. 'Years same sign' counts calendar years in which the filter pointed the same way.

| Filter | IC | z | Years same sign | Lowest fifth ... highest fifth (avg 20d alpha %) |
|---|---|---|---|---|
| quarters of profit growth in a row | +0.111 | +6.3 | 3/3 | -0.6 / +0.6 / +1.5 |
| net margin % | +0.108 | +6.1 | 3/3 | -1.6 / -0.7 / -0.2 / +0.9 / +1.5 |
| positive growth items (of 6) | +0.107 | +6.1 | 3/3 | -1.2 / -0.3 / -0.0 / +0.0 / +2.8 |
| operating margin % | +0.095 | +5.4 | 3/3 | -1.1 / -1.0 / +0.5 / +0.7 / +0.8 |
| daily turnover Rs crore | +0.095 | +5.4 | 2/3 | -1.0 / -0.3 / -0.3 / +0.7 / +0.8 |
| profit YoY % | +0.093 | +5.3 | 3/3 | -1.8 / -1.0 / +0.1 / +1.5 / +1.0 |
| average YoY growth % | +0.093 | +5.3 | 3/3 | -1.6 / -1.3 / +0.2 / +1.1 / +1.4 |
| price | +0.093 | +5.3 | 2/3 | -0.3 / -1.3 / +0.1 / +0.6 / +0.8 |
| PEAD score | +0.089 | +5.0 | 3/3 | -1.3 / -0.9 / -0.1 / +0.1 / +2.1 |
| worst profit YoY, last 4 qtrs | +0.082 | +4.7 | 3/3 | -1.5 / -0.8 / +0.4 / +1.0 / +0.8 |
| growth-to-PE | +0.075 | +4.0 | 3/3 | -1.0 / +0.0 / +1.0 / +1.4 |
| avg profit YoY, last 4 qtrs | +0.067 | +3.8 | 3/3 | -1.6 / -0.7 / +0.9 / +0.8 / +0.6 |
| daily volatility % | -0.066 | -3.7 | 3/3 | -0.2 / +0.3 / +0.7 / +0.8 / -1.3 |
| sales YoY % | +0.060 | +3.4 | 3/3 | -1.5 / -0.3 / +0.1 / +0.6 / +1.0 |
| acceleration | +0.059 | +3.3 | 3/3 | -0.5 / -1.4 / +1.4 / +0.5 / -0.0 |
| profit QoQ % | +0.058 | +3.3 | 3/3 | -1.1 / -0.6 / +0.1 / +0.9 / +0.6 |
| EBITDA margin change QoQ | +0.056 | +3.2 | 3/3 | -1.4 / -0.1 / -0.1 / +0.8 / +0.7 |
| quarters of sales growth in a row | +0.056 | +3.2 | 2/3 | -0.5 / +0.9 / +0.5 / -0.0 |
| EBITDA margin change YoY | +0.055 | +3.1 | 3/3 | -0.6 / -1.1 / -0.1 / +1.3 / +0.4 |
| distance from 52-week high % | +0.054 | +3.1 | 3/3 | -0.4 / -1.1 / -1.0 / +0.6 / +1.7 |

## 3. Best combinations found on TRAIN, judged on unseen TEST

| Rule (all must be true) | TRAIN n | TRAIN 20d excess | TEST n | TEST 20d excess | TEST alpha | TEST up vs Nifty | TEST median | Years positive |
|---|---|---|---|---|---|---|---|---|
| P/E vs own history at most 1.239 AND sales QoQ % at most 15.86 AND daily turnover Rs crore at least 37.83 AND daily volatility % at most 2.156 | 61 | +0.8% | 63 | +0.5% | +0.5% | 51% | +0.2% | 2/2 |
| sales YoY % at most 28 AND quarters of sales growth in a row at least 2 AND daily turnover Rs crore at least 37.83 AND daily volatility % at most 2.156 | 77 | +1.0% | 62 | +1.6% | +1.5% | 53% | +0.6% | 2/2 |
| EBITDA margin change QoQ at least 0 AND acceleration at least -200.1 AND daily turnover Rs crore at least 37.83 AND daily volatility % at most 2.156 | 83 | +1.0% | 42 | +0.6% | +0.5% | 45% | -1.5% | 2/3 |
| sales QoQ % at most 15.86 AND 1-month return before result at least -2.787 AND daily turnover Rs crore at least 37.83 AND daily volatility % at most 2.156 | 89 | +1.2% | 57 | +0.3% | +0.1% | 53% | +0.5% | 2/3 |
| quarters of sales growth in a row at least 2 AND avg profit YoY, last 4 qtrs at most 86.98 AND 6-month return before result at most 22.86 AND daily turnover Rs crore at least 37.83 | 123 | +0.3% | 98 | +1.2% | +0.9% | 51% | +0.3% | 2/2 |
| worst profit YoY, last 4 qtrs at most 4.098 AND daily turnover Rs crore at least 37.83 AND daily volatility % at most 3.251 | 174 | +0.8% | 130 | +1.1% | +0.9% | 52% | +0.3% | 3/3 |
| net margin % at least 6.554 AND positive growth items (of 6) at least 4 AND daily volatility % at most 3.251 | 436 | +1.3% | 376 | +1.0% | +0.7% | 47% | -0.7% | 2/3 |
| daily turnover Rs crore at least 37.83 AND daily volatility % at most 1.831 | 116 | -0.2% | 66 | +1.6% | +1.3% | 59% | +0.6% | 2/3 |
| P/E vs own history at most 1.05 AND daily turnover Rs crore at least 37.83 | 78 | +0.1% | 117 | +0.9% | +0.8% | 50% | +0.1% | 2/2 |
| net margin % at least 6.554 AND distance from 52-week high % at least -12.58 | 257 | +3.3% | 172 | +1.5% | +1.2% | 50% | +0.1% | 2/3 |
| PEAD score at least 48.7 AND distance from 52-week high % at least -12.58 | 108 | +6.6% | 118 | +1.6% | +1.3% | 53% | +0.8% | 3/3 |
| quarters of sales growth in a row at least 3 AND daily turnover Rs crore at least 37.83 | 140 | +0.3% | 150 | +0.2% | +0.0% | 51% | +0.1% | 2/2 |
| P/E vs own history at most 1.239 AND distance from 52-week high % at least -12.58 | 87 | +0.0% | 140 | +2.2% | +2.0% | 51% | +0.5% | 1/2 |
| P/E vs own history at least 0.8739 AND daily turnover Rs crore at least 37.83 | 91 | +0.2% | 111 | +0.3% | +0.0% | 50% | -0.0% | 1/2 |
| sales YoY % at least 9.064 AND net margin % at least 6.554 | 533 | +0.6% | 455 | +1.4% | +1.0% | 50% | -0.0% | 2/3 |

Shrinkage check: these 15 rules averaged +3.89% alpha on TRAIN and +0.86% on TEST. The second number is what to expect going forward; the gap is luck the search picked up.

## 4. Ideas you asked about, tested as written (fixed thresholds, nothing tuned)

| Idea | All n | 20d excess | Alpha | Up vs Nifty | Median | TEST n | TEST 20d excess | NSE-dated n | NSE-dated 20d excess |
|---|---|---|---|---|---|---|---|---|---|
| Your original combo: Excellent + volume 2x + positive reaction | 81 | +1.5% | +1.7% | 43% | -0.8% | 53 | -0.7% | 10 | +14.3% |
| Score 55+ and first-day reaction 5%+ | 307 | +2.5% | +3.0% | 50% | -0.2% | 190 | +2.9% | 36 | +4.4% |
| Score 55+ and low volume surge (under 2x) | 80 | +3.5% | +3.7% | 52% | +1.0% | 4 | +3.9% | 76 | +3.5% |
| Growth at a fair price: score 55+, forward P/E 20 or less | 337 | +1.6% | +2.0% | 45% | -1.0% | 196 | +2.5% | 62 | +3.9% |
| Cheap and growing: score 55+, growth-to-PE 1.2+ | 509 | +1.5% | +2.1% | 47% | -0.7% | 278 | +2.3% | 96 | +3.9% |
| Momentum: score 55+, 6-month return 20%+, within 15% of 52-week high | 129 | +4.4% | +3.8% | 60% | +3.6% | 59 | +2.1% | 38 | +10.5% |
| Durable: score 55+, profit grew 4+ quarters in a row, 5+ of 6 items positive | 113 | +1.9% | +2.7% | 52% | +0.6% | 81 | +3.2% | 1 | - |
| Beaten-down turnaround: score 55+, 6-month return under 0 | 265 | +0.9% | +2.0% | 45% | -1.0% | 157 | +2.9% | 43 | -3.9% |
| Liquid only: score 55+, reaction 3%+, turnover Rs 2 crore a day or more | 230 | +3.8% | +4.5% | 52% | +0.4% | 129 | +4.3% | 34 | +3.3% |

## 5. How the best rule behaves as a trade

Rule: **P/E vs own history at most 1.239 AND sales QoQ % at most 15.86 AND daily turnover Rs crore at least 37.83 AND daily volatility % at most 2.156**

| Hold for | Trades | Avg return | Avg vs Nifty | Median vs Nifty | Up vs Nifty |
|---|---|---|---|---|---|
| 5 days | 139 | -0.07% | -0.15% | -0.22% | 47% |
| 10 days | 130 | -0.05% | +0.33% | +0.08% | 52% |
| 20 days | 124 | -0.04% | +0.67% | +0.07% | 50% |
| 40 days | 124 | -0.71% | +0.95% | +1.07% | 55% |
| 60 days | 117 | +0.10% | +1.31% | +1.20% | 53% |

| Exit rule (close-based stop) | Trades | Avg return | Median | Winners |
|---|---|---|---|---|
| stop 8% / 20 days | 124 | -0.21% | -0.61% | 48% |
| stop 12% / 20 days | 124 | +0.01% | -0.19% | 48% |
| stop 8% / 60 days | 118 | -1.52% | -7.05% | 37% |
| stop 12% / 60 days | 118 | -0.96% | -2.41% | 43% |

Typical worst dip inside the first 20 days: median -3.7%, 1 trade in 4 dipped -6.4% or worse.

Frequency: about 25 qualifying results a year across the whole universe. Median daily turnover of these stocks: Rs 122.7 crore.

## How to read this honestly

* A rule is only interesting if its TEST numbers are positive, its TEST count is at least 30, and it is positive in most years.
* Averages here are pulled up by a few big winners. Look at the median and the share of winners as well as the average.
* Results are before brokerage, taxes and slippage. Small, thinly traded stocks can cost 1-3% to enter and exit, which can erase an edge of that size.
* Announcement dates marked 'spike' were inferred from a volume jump, not taken from the exchange, so some entries are a day off.
* Past results only. General information, not advice.
