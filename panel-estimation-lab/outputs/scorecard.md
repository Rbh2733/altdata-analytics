# Backtest Scorecard

Scored quarters: 2023Q1 through 2024Q4 (the four 2022 quarters are warmup and feed calibration history only). 6 companies x 8 quarters per method and KPI. APE = |estimate - truth| / truth; MAPE averages APE over companies and quarters. Median APE runs alongside because MAPE is outlier-dominated by design here.

## MAPE by method and KPI

| kpi | m1 MAPE (median APE) | m2 MAPE (median APE) | m3 MAPE (median APE) | m4 MAPE (median APE) |
|---|---|---|---|---|
| revenue | 30.6% (29.8%) | 24.9% (21.1%) | 20.8% (20.6%) | 2.7% (1.8%) |
| actives | 21.2% (16.9%) | 15.5% (9.1%) | 6.5% (6.0%) | 3.2% (2.5%) |
| gross_adds | 104.1% (36.3%) | 95.3% (32.6%) | 113.1% (69.5%) | 113.1% (72.6%) |
| churn_rate | 178.3% (185.8%) | 112.8% (100.1%) | 86.1% (67.8%) | 86.1% (67.8%) |
| arpu | 22.5% (25.2%) | 20.2% (16.5%) | 19.5% (18.4%) | 3.6% (2.1%) |
| market_share | 13.2% (8.2%) | 9.2% (4.0%) | 3.3% (2.8%) | 2.5% (1.6%) |

## Revenue MAPE by method and quarter

| quarter | m1 | m2 | m3 | m4 | pathology |
|---|---|---|---|---|---|
| 2023Q1 | 34.1% | 21.2% | 21.2% | 3.0% |  |
| 2023Q2 | 17.6% | 17.6% | 17.6% | 5.0% | recruitment_wave |
| 2023Q3 | 18.2% | 18.2% | 21.6% | 3.7% | duplicate_feed_day |
| 2023Q4 | 23.9% | 21.1% | 21.1% | 3.1% |  |
| 2024Q1 | 31.1% | 25.6% | 21.5% | 2.1% | supplier_outage |
| 2024Q2 | 33.4% | 26.1% | 20.5% | 1.7% | descriptor_change |
| 2024Q3 | 42.8% | 34.6% | 21.5% | 2.0% |  |
| 2024Q4 | 44.2% | 34.4% | 21.0% | 0.8% |  |

## Pathology quarters: revenue MAPE, uncorrected vs corrected

| pathology | quarter | m1 | m2 | m3 | m4 |
|---|---|---|---|---|---|
| duplicate_feed_day | 2023Q3 | 18.2% | 18.2% | 21.6% | 3.7% |
| recruitment_wave | 2023Q2 | 17.6% | 17.6% | 17.6% | 5.0% |
| supplier_outage | 2024Q1 | 31.1% | 25.6% | 21.5% | 2.1% |
| descriptor_change | 2024Q2 | 33.4% | 26.1% | 20.5% | 1.7% |

## 90% interval coverage (bootstrap, panelist resampling, B=400)

| method | kpi | covered / cells | coverage |
|---|---|---|---|
| m1 | actives | 7/48 | 14.6% |
| m1 | revenue | 1/48 | 2.1% |
| m2 | actives | 15/48 | 31.2% |
| m2 | revenue | 0/48 | 0.0% |
| m3 | actives | 19/48 | 39.6% |
| m3 | revenue | 0/48 | 0.0% |
| m4 | actives | 31/48 | 64.6% |
| m4 | revenue | 43/48 | 89.6% |
