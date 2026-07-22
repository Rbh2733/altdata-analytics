# Scorecard

Vendors: 420. Scored quarters: 10 (2023Q3 to 2025Q4).

## Rank quality (median Spearman across scored quarters, composite vs forward true growth)

| tier | median spearman |
|---|---|
| A | 0.700 |
| B | 0.510 |
| C | 0.312 |
| blended (reference only) | 0.479 |

## Lead-lag summary (source vs truth inflection)

| source | type | n_events | n_present | n_detected | detection_rate | median_lead_vs_regime_change | median_lead_vs_revenue |
|---|---|---|---|---|---|---|---|
| jobs | acceleration | 83 | 33 | 30 | 90.9% | 0.0 | 2.0 |
| jobs | stall | 177 | 67 | 47 | 70.1% | 0.0 | 2.0 |
| spend | acceleration | 83 | 25 | 22 | 88.0% | 0.0 | 2.0 |
| spend | stall | 177 | 58 | 56 | 96.6% | 1.0 | 3.0 |
| web | acceleration | 83 | 75 | 71 | 94.7% | 1.0 | 3.0 |
| web | stall | 177 | 153 | 144 | 94.1% | 1.0 | 3.0 |

## Inflection precision/recall grid (k quarters, by type and tier)

| k | type | tier | n_flags | n_events | precision | recall |
|---|---|---|---|---|---|---|
| 1 | acceleration | A | 112 | 9 | 8.0% | 100.0% |
| 1 | acceleration | B | 425 | 30 | 6.6% | 93.3% |
| 1 | acceleration | C | 311 | 44 | 8.4% | 59.1% |
| 1 | stall | A | 109 | 22 | 15.6% | 77.3% |
| 1 | stall | B | 396 | 59 | 11.6% | 74.6% |
| 1 | stall | C | 316 | 96 | 17.7% | 60.4% |
| 2 | acceleration | A | 112 | 9 | 8.0% | 100.0% |
| 2 | acceleration | B | 425 | 30 | 7.1% | 100.0% |
| 2 | acceleration | C | 311 | 44 | 10.3% | 72.7% |
| 2 | stall | A | 109 | 22 | 18.3% | 90.9% |
| 2 | stall | B | 396 | 59 | 13.4% | 88.1% |
| 2 | stall | C | 316 | 96 | 21.5% | 71.9% |

## Outcome validation

- Shutdowns: 23 total; among the 23 with a scored composite two quarters prior, 56.5% sat in the bottom population quartile. Median composite one quarter before shutdown: 25.7 vs population median 50.0. 3 shutdown vendor(s) scored above 50 one quarter prior.
  - V0168 (tier C): composite 59.3 the quarter before shutting down in 2025Q4.
  - V0170 (tier B): composite 68.5 the quarter before shutting down in 2024Q2.
  - V0341 (tier C): composite 67.2 the quarter before shutting down in 2025Q2.
- Funding: 129 of 135 rounds scored; median composite one quarter before a raise: 50.0 vs population median 50.0. Impurity by design: runway-pressure raises pull this toward the population median from below.
- Disclosed acquisitions (22 priced): band hit rate 40.9%, within-one-band 68.2%, median abs log10 error 0.236. This is deliberately the least flattering table: without a reported-actuals anchor, levels are bands.

