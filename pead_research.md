# PEAD research (14135 results, 2020-11-13 to 2026-11-20; filters tested: 38)

Search period (TRAIN): up to 2025-12-12 (7781 results). Unseen period (TEST): after it (6354 results).
Returns are from the close of the first session after the result. Excess = minus the Nifty over the same days. Alpha = minus the average of all results in the same month.

## 1. The starting point: every result

| Period | Results | 20d excess avg | 20d median | Up vs Nifty | 60d excess avg |
|---|---|---|---|---|---|
| All | 12929 | -1.01% | -2.50% | 39.0% | -1.98% |
| TRAIN | 7781 | -1.60% | -3.07% | 36.8% | -4.77% |
| TEST | 5148 | -0.13% | -1.64% | 42.5% | +3.06% |

A negative start means that buying any result lost to the Nifty, so a filter has to rescue it, not just add to it.

| Year | Results | 20d excess avg | median |
|---|---|---|---|
| 2021 | 49 | +9.19% | +1.87% |
| 2022 | 61 | -0.51% | -2.42% |
| 2023 | 75 | +4.32% | +1.01% |
| 2024 | 1755 | +4.32% | +1.55% |
| 2025 | 5976 | -3.52% | -4.43% |
| 2026 | 6216 | -0.08% | -1.59% |

## 2. One filter at a time (which numbers carry information?)

Rank correlation (IC) of each filter with the 20-day alpha, and the average alpha of the lowest-to-highest fifth of results. 'Years same sign' counts calendar years in which the filter pointed the same way.

| Filter | IC | z | Years same sign | Lowest fifth ... highest fifth (avg 20d alpha %) |
|---|---|---|---|---|
| price | +0.102 | +11.6 | 2/3 | -0.9 / -0.7 / +0.4 / +0.5 / +0.6 |
| daily turnover Rs crore | +0.101 | +11.5 | 2/3 | -0.6 / -0.6 / -0.3 / +0.3 / +1.1 |
| positive growth items (of 6) | +0.100 | +11.3 | 3/3 | -1.1 / -0.4 / -0.2 / +0.8 / +2.0 |
| quarters of profit growth in a row | +0.096 | +11.0 | 3/3 | -0.6 / +0.8 / +1.2 |
| distance from 52-week high % | +0.090 | +10.3 | 3/3 | -1.0 / -0.7 / -0.5 / +0.5 / +1.7 |
| PEAD score | +0.085 | +9.7 | 3/3 | -1.2 / -0.9 / -0.0 / +0.2 / +2.0 |
| worst profit YoY, last 4 qtrs | +0.084 | +9.5 | 3/3 | -0.9 / -0.0 / +0.7 / +1.1 |
| average YoY growth % | +0.083 | +9.5 | 3/3 | -1.6 / -0.8 / +0.1 / +1.0 / +1.2 |
| profit YoY % | +0.083 | +9.4 | 3/3 | -1.5 / -1.0 / +0.3 / +1.1 / +1.0 |
| net margin % | +0.084 | +9.4 | 3/3 | -1.1 / -0.4 / -0.1 / +0.6 / +0.9 |
| quarters of sales growth in a row | +0.080 | +9.1 | 3/3 | -0.7 / +0.9 / +0.5 / +0.5 |
| operating margin % | +0.080 | +9.1 | 3/3 | -0.7 / -0.7 / -0.1 / +0.6 / +0.8 |
| daily volatility % | -0.074 | -8.4 | 2/3 | -0.1 / +0.1 / +0.3 / +0.3 / -0.7 |
| sales YoY % | +0.073 | +8.3 | 3/3 | -1.4 / -0.5 / -0.2 / +0.8 / +1.2 |
| acceleration | +0.070 | +8.0 | 2/3 | -0.5 / -0.9 / +0.4 / +0.2 / +0.8 |
| growth-to-PE | +0.073 | +7.9 | 3/3 | -1.1 / +0.2 / +1.3 / +1.2 |
| 12-month return before result | +0.071 | +7.8 | 3/3 | -1.3 / -0.8 / +0.0 / +0.4 / +1.6 |
| avg profit YoY, last 4 qtrs | +0.059 | +6.7 | 3/3 | -1.4 / -0.7 / +0.7 / +0.7 / +0.7 |
| % above 200-day average | +0.056 | +6.2 | 3/3 | -0.8 / -0.8 / -0.3 / +0.1 / +1.5 |
| 6-month strength vs Nifty | +0.052 | +5.8 | 3/3 | -0.6 / -0.6 / -0.5 / +0.1 / +1.5 |

## 3. Best combinations found on TRAIN, judged on unseen TEST

| Rule (all must be true) | TRAIN n | TRAIN 20d excess | TEST n | TEST 20d excess | TEST alpha | TEST up vs Nifty | TEST median | Years positive |
|---|---|---|---|---|---|---|---|---|
| positive growth items (of 6) at least 3 AND quarters of sales growth in a row at least 2 AND daily turnover Rs crore at least 33.76 AND daily volatility % at most 2.126 | 365 | -0.4% | 310 | +0.4% | +0.5% | 49% | -0.1% | 2/3 |
| quarters of sales growth in a row at least 2 AND avg profit YoY, last 4 qtrs at most 34.55 AND daily turnover Rs crore at least 33.76 | 513 | -0.6% | 405 | +0.7% | +0.7% | 49% | -0.2% | 2/3 |
| P/E vs own history at least 0.743 AND daily turnover Rs crore at least 33.76 AND daily volatility % at most 2.126 | 323 | -1.0% | 329 | +0.7% | +0.7% | 48% | -0.2% | 1/2 |
| quarters of sales growth in a row at least 3 AND daily turnover Rs crore at least 33.76 | 557 | -0.0% | 674 | +0.9% | +1.1% | 50% | -0.2% | 1/3 |
| price at least 141 AND positive growth items (of 6) at least 5 | 1683 | +0.1% | 1243 | +1.9% | +2.1% | 51% | +0.2% | 3/5 |
| positive growth items (of 6) at least 5 AND % above 200-day average at least -10.1 | 1625 | +0.5% | 1159 | +1.9% | +2.3% | 49% | -0.1% | 4/5 |
| daily turnover Rs crore at least 11.29 AND Nifty % above 200-day average at most 2.282 | 936 | -1.3% | 1592 | +0.9% | +1.0% | 47% | -0.6% | 2/3 |
| 12-month return before result at most 15.13 AND daily turnover Rs crore at least 33.76 | 743 | -1.1% | 511 | +0.3% | +0.5% | 44% | -1.2% | 2/3 |
| positive growth items (of 6) at least 4 AND daily turnover Rs crore at least 11.29 | 1556 | -0.3% | 1116 | +1.4% | +1.7% | 51% | +0.1% | 2/4 |
| net margin % at least 10.17 AND quarters of sales growth in a row at least 2 | 1385 | -1.3% | 1271 | +0.7% | +0.9% | 46% | -0.8% | 4/6 |
| net margin % at least 6.557 AND Nifty % above 200-day average at most 2.282 | 1314 | -1.2% | 2405 | +0.6% | +0.6% | 46% | -0.9% | 2/5 |
| PEAD score at least 49.8 AND 12-month return before result at least 39.93 | 424 | +4.2% | 275 | +5.0% | +5.3% | 57% | +2.8% | 3/3 |
| Nifty 3-month return at least -2.422 AND Nifty % above 200-day average at most 2.282 | 1436 | +1.2% | 2413 | +0.1% | +0.3% | 42% | -1.5% | 2/3 |
| distance from 52-week high % at least -12.93 | 1557 | +0.8% | 1167 | +1.7% | +1.8% | 49% | -0.2% | 4/6 |
| operating margin % at least 15.97 | 2724 | -0.9% | 1905 | +0.6% | +0.7% | 45% | -0.9% | 4/6 |

Shrinkage check: these 15 rules averaged +2.19% alpha on TRAIN and +1.36% on TEST. The second number is what to expect going forward; the gap is luck the search picked up.

## 4. Ideas you asked about, tested as written (fixed thresholds, nothing tuned)

| Idea | All n | 20d excess | Alpha | Up vs Nifty | Median | TEST n | TEST 20d excess | NSE-dated n | NSE-dated 20d excess |
|---|---|---|---|---|---|---|---|---|---|
| Your original combo: Excellent + volume 2x + positive reaction | 375 | +1.5% | +2.5% | 44% | -1.8% | 221 | +3.0% | 40 | +1.0% |
| Score 55+ and first-day reaction 5%+ | 1250 | +2.0% | +2.9% | 47% | -0.9% | 687 | +2.8% | 144 | +4.4% |
| Score 55+ and low volume surge (under 2x) | 272 | +2.0% | +2.5% | 47% | -2.0% | 19 | +5.6% | 249 | +1.8% |
| Growth at a fair price: score 55+, forward P/E 20 or less | 1571 | +1.0% | +1.7% | 45% | -1.4% | 840 | +1.6% | 277 | +2.5% |
| Cheap and growing: score 55+, growth-to-PE 1.2+ | 2140 | +0.8% | +1.8% | 45% | -1.5% | 1095 | +1.6% | 398 | +2.1% |
| Momentum: score 55+, 6-month return 20%+, within 15% of 52-week high | 514 | +3.5% | +4.1% | 54% | +1.8% | 261 | +3.8% | 105 | +7.7% |
| Durable: score 55+, profit grew 4+ quarters in a row, 5+ of 6 items positive | 456 | +1.1% | +2.6% | 48% | -0.7% | 313 | +1.9% | 5 | - |
| Beaten-down turnaround: score 55+, 6-month return under 0 | 1106 | -0.2% | +1.0% | 42% | -1.9% | 595 | +0.7% | 173 | -2.6% |
| Liquid only: score 55+, reaction 3%+, turnover Rs 2 crore a day or more | 903 | +2.7% | +3.7% | 50% | +0.1% | 493 | +3.7% | 116 | +4.1% |

## 5. How the best rule behaves as a trade

Rule: **price at least 141 AND positive growth items (of 6) at least 5**

| Hold for | Trades | Avg return | Avg vs Nifty | Median vs Nifty | Up vs Nifty |
|---|---|---|---|---|---|
| 5 days | 3160 | -0.24% | -0.41% | -0.96% | 43% |
| 10 days | 3064 | -0.11% | -0.14% | -1.09% | 44% |
| 20 days | 2926 | +0.58% | +0.88% | -0.93% | 46% |
| 40 days | 2872 | +0.37% | +1.24% | -0.47% | 48% |
| 60 days | 2770 | +0.60% | +0.80% | -1.71% | 45% |

| Exit rule (close-based stop) | Trades | Avg return | Median | Winners |
|---|---|---|---|---|
| stop 8% / 20 days | 2926 | +0.49% | -2.41% | 42% |
| stop 12% / 20 days | 2926 | +0.47% | -1.34% | 44% |
| stop 8% / 60 days | 2770 | -0.79% | -8.34% | 30% |
| stop 12% / 60 days | 2770 | -0.89% | -8.32% | 37% |

Typical worst dip inside the first 20 days: median -5.8%, 1 trade in 4 dipped -10.6% or worse.

Frequency: about 541 qualifying results a year across the whole universe. Median daily turnover of these stocks: Rs 14.2 crore.

## How to read this honestly

* A rule is only interesting if its TEST numbers are positive, its TEST count is at least 30, and it is positive in most years.
* Averages here are pulled up by a few big winners. Look at the median and the share of winners as well as the average.
* Results are before brokerage, taxes and slippage. Small, thinly traded stocks can cost 1-3% to enter and exit, which can erase an edge of that size.
* Announcement dates marked 'spike' were inferred from a volume jump, not taken from the exchange, so some entries are a day off.
* Past results only. General information, not advice.
