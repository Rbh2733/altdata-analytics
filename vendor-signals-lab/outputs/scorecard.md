# Scorecard

Vendors: 480. Scored quarters: 10 (2023Q3 to 2025Q4).

## Rank quality (median Spearman across scored quarters, composite vs forward true growth)

| tier | median spearman |
|---|---|
| A | 0.597 |
| B | 0.563 |
| C | 0.281 |
| blended (reference only) | 0.382 |

## Lead-lag summary (source vs truth inflection)

| source | type | n_events | n_present | n_detected | detection_rate | median_lead_vs_regime_change | median_lead_vs_revenue |
|---|---|---|---|---|---|---|---|
| jobs | acceleration | 84 | 32 | 23 | 71.9% | 0.0 | 2.0 |
| jobs | stall | 192 | 75 | 51 | 68.0% | 0.0 | 2.0 |
| spend | acceleration | 84 | 24 | 21 | 87.5% | 0.0 | 2.0 |
| spend | stall | 192 | 44 | 41 | 93.2% | 1.0 | 3.0 |
| web | acceleration | 84 | 63 | 60 | 95.2% | 0.5 | 2.5 |
| web | stall | 192 | 163 | 156 | 95.7% | 1.0 | 3.0 |

## Inflection precision/recall grid (k quarters, by type and tier)

| k | type | tier | n_flags | n_events | precision | recall |
|---|---|---|---|---|---|---|
| 1 | acceleration | A | 112 | 8 | 7.1% | 100.0% |
| 1 | acceleration | B | 417 | 31 | 6.5% | 87.1% |
| 1 | acceleration | C | 353 | 45 | 6.2% | 48.9% |
| 1 | stall | A | 87 | 18 | 17.2% | 88.9% |
| 1 | stall | B | 400 | 67 | 14.2% | 80.6% |
| 1 | stall | C | 367 | 107 | 14.7% | 52.3% |
| 2 | acceleration | A | 112 | 8 | 7.1% | 100.0% |
| 2 | acceleration | B | 417 | 31 | 7.2% | 96.8% |
| 2 | acceleration | C | 353 | 45 | 7.6% | 60.0% |
| 2 | stall | A | 87 | 18 | 19.5% | 100.0% |
| 2 | stall | B | 400 | 67 | 16.5% | 94.0% |
| 2 | stall | C | 367 | 107 | 18.8% | 66.4% |

## Outcome validation

- Shutdowns: 25 total; among the 25 with a scored composite two quarters prior, 80.0% sat in the bottom population quartile. Median composite one quarter before shutdown: 28.2 vs population median 50.0. 3 shutdown vendor(s) scored above 50 one quarter prior.
  - V0136 (tier C): composite 52.6 the quarter before shutting down in 2024Q4.
  - V0269 (tier C): composite 51.3 the quarter before shutting down in 2025Q4.
  - V0285 (tier B): composite 53.6 the quarter before shutting down in 2025Q3.
- Funding: 156 of 166 rounds scored; median composite one quarter before a raise: 50.0 vs population median 50.0. Impurity by design: most rounds come from a uniform base hazard unrelated to health, so a median cannot see the thin accelerator tilt.
- Disclosed acquisitions (25 priced): band hit rate 32.0%, within-one-band 48.0%, median abs log10 error 0.559. This is deliberately the least flattering table: without a reported-actuals anchor, levels are bands.

