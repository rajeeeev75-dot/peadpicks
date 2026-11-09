# PEAD research (7105 results, 2020-11-13 to 2026-11-08; filters tested: 38)

Search period (TRAIN): up to 2025-12-08 (3922 results). Unseen period (TEST): after it (3183 results).
Returns are from the close of the first session after the result. Excess = minus the Nifty over the same days. Alpha = minus the average of all results in the same month.

## 1. The starting point: every result

| Period | Results | 20d excess avg | 20d median | Up vs Nifty | 60d excess avg |
|---|---|---|---|---|---|
| All | 6527 | -0.79% | -2.43% | 39.4% | -2.21% |
| TRAIN | 3922 | -1.55% | -3.16% | 37.1% | -5.18% |
| TEST | 2605 | +0.37% | -1.52% | 43.0% | +3.13% |

A negative start means that buying any result lost to the Nifty, so a filter has to rescue it, not just add to it.

| Year | Results | 20d excess avg | median |
|---|---|---|---|
| 2021 | 24 | +8.64% | +2.03% |
| 2022 | 28 | -2.00% | -2.52% |
| 2023 | 29 | +2.89% | +0.52% |
| 2024 | 962 | +4.32% | +1.26% |
| 2025 | 3007 | -3.58% | -4.50% |
| 2026 | 3053 | +0.49% | -1.39% |

## 2. One filter at a time (which numbers carry information?)

Rank correlation (IC) of each filter with the 20-day alpha, and the average alpha of the lowest-to-highest fifth of results. 'Years same sign' counts calendar years in which the filter pointed the same way.

| Filter | IC | z | Years same sign | Lowest fifth ... highest fifth (avg 20d alpha %) |
|---|---|---|---|---|
| price | +0.104 | +8.4 | 2/3 | -0.6 / -1.0 / +0.1 / +0.7 / +0.8 |
| positive growth items (of 6) | +0.101 | +8.2 | 3/3 | -1.1 / -0.6 / -0.0 / +0.5 / +2.4 |
| quarters of profit growth in a row | +0.098 | +7.9 | 3/3 | -0.5 / +0.7 / +1.2 |
| daily turnover Rs crore | +0.096 | +7.8 | 2/3 | -0.7 / -0.2 / -0.2 / +0.0 / +1.0 |
| distance from 52-week high % | +0.091 | +7.4 | 3/3 | -0.9 / -0.9 / -0.7 / +0.5 / +1.9 |
| daily volatility % | -0.088 | -7.0 | 3/3 | -0.0 / +0.4 / +0.5 / +0.2 / -1.1 |
| worst profit YoY, last 4 qtrs | +0.085 | +6.8 | 3/3 | -1.1 / +0.6 / +0.7 / +0.8 |
| operating margin % | +0.084 | +6.8 | 3/3 | -0.4 / -0.8 / -0.2 / +0.5 / +0.9 |
| net margin % | +0.084 | +6.8 | 3/3 | -1.1 / -0.6 / -0.1 / +0.7 / +0.9 |
| profit YoY % | +0.083 | +6.7 | 3/3 | -1.7 / -0.8 / +0.5 / +1.3 / +0.7 |
| average YoY growth % | +0.080 | +6.4 | 3/3 | -1.4 / -0.9 / +0.2 / +1.2 / +0.9 |
| PEAD score | +0.079 | +6.4 | 3/3 | -1.1 / -0.9 / +0.0 / +0.3 / +1.6 |
| sales YoY % | +0.071 | +5.7 | 3/3 | -1.2 / -0.7 / -0.1 / +0.8 / +1.2 |
| quarters of sales growth in a row | +0.068 | +5.5 | 3/3 | -0.6 / +1.0 / +0.7 / +0.1 |
| 12-month return before result | +0.070 | +5.4 | 3/3 | -1.0 / -1.0 / +0.1 / +0.6 / +1.6 |
| growth-to-PE | +0.068 | +5.2 | 3/3 | -1.0 / +0.1 / +1.1 / +1.1 |
| acceleration | +0.062 | +5.0 | 2/3 | -0.5 / -1.1 / +0.9 / +0.6 / +0.1 |
| avg profit YoY, last 4 qtrs | +0.060 | +4.8 | 3/3 | -1.4 / -0.7 / +0.9 / +0.8 / +0.3 |
| % above 200-day average | +0.059 | +4.6 | 3/3 | -0.5 / -1.0 / -0.2 / +0.3 / +1.5 |
| 6-month strength vs Nifty | +0.053 | +4.2 | 3/3 | -0.5 / -0.6 / -0.4 / +0.1 / +1.4 |

## 3. Best combinations found on TRAIN, judged on unseen TEST

| Rule (all must be true) | TRAIN n | TRAIN 20d excess | TEST n | TEST 20d excess | TEST alpha | TEST up vs Nifty | TEST median | Years positive |
|---|---|---|---|---|---|---|---|---|
| forward P/E at most 48.95 AND quarters of sales growth in a row at least 2 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 2.139 | 164 | +1.0% | 154 | +0.0% | -0.2% | 47% | -0.7% | 1/2 |
| volume surge (x) at least 1.158 AND 12-month return before result at most 17.11 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 2.139 | 218 | +0.3% | 155 | +0.8% | +0.4% | 47% | -0.6% | 3/3 |
| EBITDA margin change QoQ at least -1.065 AND 12-month return before result at most 43.37 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 2.139 | 220 | +0.4% | 130 | +1.5% | +1.4% | 51% | +0.2% | 3/3 |
| P/E vs own history at most 1.273 AND sales QoQ % at most 15.81 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 2.139 | 138 | -0.0% | 150 | +0.7% | +0.5% | 49% | -0.1% | 2/2 |
| quarters of sales growth in a row at least 3 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 2.139 | 151 | +0.6% | 173 | +0.7% | +0.5% | 48% | -0.3% | 2/2 |
| 12-month return before result at most 43.37 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 1.798 | 231 | -0.5% | 128 | +0.6% | +0.4% | 52% | +0.2% | 2/3 |
| P/E vs own history at least 0.745 AND distance from 52-week high % at least -12.52 AND daily volatility % at most 2.139 | 138 | +0.2% | 149 | +1.6% | +1.3% | 48% | -0.4% | 1/2 |
| positive growth items (of 6) at least 5 AND 12-month return before result at least -15.12 | 738 | +1.4% | 502 | +2.9% | +2.7% | 52% | +0.5% | 3/4 |
| P/E vs own history at least 0.875 AND daily turnover Rs crore at least 32.38 | 188 | -0.4% | 239 | +0.9% | +0.7% | 51% | +0.1% | 1/2 |
| daily turnover Rs crore at least 10.64 AND Nifty % above 200-day average at most 2.289 | 460 | -0.9% | 790 | +1.5% | +1.0% | 49% | -0.2% | 2/3 |
| PEAD score at least 49.5 | 786 | -0.1% | 749 | +1.6% | +1.4% | 48% | -0.4% | 4/5 |
| net margin % at least 9.872 | 1356 | -0.6% | 920 | +0.9% | +0.5% | 46% | -0.8% | 4/6 |
| worst profit YoY, last 4 qtrs at least -20.29 | 1962 | -0.2% | 1105 | +1.3% | +1.0% | 47% | -0.8% | 4/6 |
| 6-month strength vs Nifty at least 1.928 | 1316 | -0.0% | 926 | +1.4% | +0.9% | 46% | -1.2% | 4/6 |
| operating margin % at least 15.55 | 1373 | -1.0% | 961 | +1.0% | +0.6% | 47% | -0.6% | 3/4 |

Shrinkage check: these 15 rules averaged +2.69% alpha on TRAIN and +0.87% on TEST. The second number is what to expect going forward; the gap is luck the search picked up.

## 4. Ideas you asked about, tested as written (fixed thresholds, nothing tuned)

| Idea | All n | 20d excess | Alpha | Up vs Nifty | Median | TEST n | TEST 20d excess | NSE-dated n | NSE-dated 20d excess |
|---|---|---|---|---|---|---|---|---|---|
| Your original combo: Excellent + volume 2x + positive reaction | 174 | +0.7% | +1.0% | 43% | -1.5% | 99 | +1.6% | 27 | +2.8% |
| Score 55+ and first-day reaction 5%+ | 629 | +1.9% | +2.4% | 47% | -0.6% | 355 | +2.7% | 81 | +4.0% |
| Score 55+ and low volume surge (under 2x) | 147 | +2.7% | +3.2% | 48% | -1.6% | 6 | +1.9% | 140 | +2.8% |
| Growth at a fair price: score 55+, forward P/E 20 or less | 774 | +0.8% | +1.3% | 44% | -1.4% | 404 | +1.9% | 157 | +2.3% |
| Cheap and growing: score 55+, growth-to-PE 1.2+ | 1065 | +0.9% | +1.6% | 45% | -1.3% | 537 | +2.0% | 221 | +2.5% |
| Momentum: score 55+, 6-month return 20%+, within 15% of 52-week high | 251 | +3.8% | +3.8% | 56% | +2.2% | 119 | +3.7% | 64 | +9.4% |
| Durable: score 55+, profit grew 4+ quarters in a row, 5+ of 6 items positive | 216 | +1.5% | +2.4% | 49% | -0.4% | 149 | +3.2% | 3 | - |
| Beaten-down turnaround: score 55+, 6-month return under 0 | 552 | -0.2% | +0.9% | 41% | -1.7% | 301 | +1.0% | 93 | -2.8% |
| Liquid only: score 55+, reaction 3%+, turnover Rs 2 crore a day or more | 451 | +2.3% | +3.1% | 48% | -0.5% | 247 | +3.6% | 68 | +2.6% |

## 5. How the best rule behaves as a trade

Rule: **volume surge (x) at least 1.158 AND 12-month return before result at most 17.11 AND daily turnover Rs crore at least 32.38 AND daily volatility % at most 2.139**

| Hold for | Trades | Avg return | Avg vs Nifty | Median vs Nifty | Up vs Nifty |
|---|---|---|---|---|---|
| 5 days | 406 | -0.09% | -0.16% | -0.28% | 46% |
| 10 days | 389 | -0.10% | +0.02% | -0.20% | 47% |
| 20 days | 373 | -0.19% | +0.50% | -0.34% | 47% |
| 40 days | 366 | -0.59% | +0.54% | +0.18% | 51% |
| 60 days | 339 | +0.72% | +1.08% | -0.22% | 49% |

| Exit rule (close-based stop) | Trades | Avg return | Median | Winners |
|---|---|---|---|---|
| stop 8% / 20 days | 373 | -0.33% | -1.36% | 42% |
| stop 12% / 20 days | 373 | -0.25% | -1.05% | 44% |
| stop 8% / 60 days | 339 | -0.32% | -4.93% | 41% |
| stop 12% / 60 days | 339 | -0.42% | -1.98% | 47% |

Typical worst dip inside the first 20 days: median -4.1%, 1 trade in 4 dipped -7.1% or worse.

Frequency: about 72 qualifying results a year across the whole universe. Median daily turnover of these stocks: Rs 101.2 crore.

## How to read this honestly

* A rule is only interesting if its TEST numbers are positive, its TEST count is at least 30, and it is positive in most years.
* Averages here are pulled up by a few big winners. Look at the median and the share of winners as well as the average.
* Results are before brokerage, taxes and slippage. Small, thinly traded stocks can cost 1-3% to enter and exit, which can erase an edge of that size.
* Announcement dates marked 'spike' were inferred from a volume jump, not taken from the exchange, so some entries are a day off.
* Past results only. General information, not advice.
