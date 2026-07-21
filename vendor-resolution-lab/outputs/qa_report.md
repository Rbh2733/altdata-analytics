# QA Report

## Expectations

| Check | Result | Detail |
|---|---|---|
| raw_id uniqueness | PASS | 60000 rows, 60000 distinct ids |
| referential integrity (assigned vendor exists in master) | PASS | 0 violations |
| amount sanity (all positive) | PASS | 0 violations |
| normalization non-empty | PASS | 0 empty cores |

## Weekly auto-match rate (exact + fuzzy_auto)

| Week | Auto-match rate |
|---|---|
| 1 | 90.5% |
| 2 | 90.9% |
| 3 | 90.1% |
| 4 | 90.9% |
| 5 | 91.1% |
| 6 | 90.6% |
| 7 | 82.6% |
| 8 | 82.7% |

## Drift alerts

- Week 7: auto-match rate 82.6% vs trailing-3-week mean 90.9%. Degraded beyond the 3pp threshold. Most common leading tokens among non-auto-matched strings this week: PYUSD (339 rows), PP (98 rows), STRIPE (90 rows). Investigate new processor formats and new-vendor candidates before this feeds anything downstream.
- Week 8: auto-match rate 82.7% vs trailing-3-week mean 88.1%. Degraded beyond the 3pp threshold. Most common leading tokens among non-auto-matched strings this week: PYUSD (327 rows), WEB (111 rows), STRIPE (93 rows). Investigate new processor formats and new-vendor candidates before this feeds anything downstream.

## Headline metrics

- Coverage: 97.9% of rows assigned a canonical vendor
- exact: n=53143, precision 99.90%
- fuzzy_auto: n=69, precision 100.00%
- tagger_review: n=300, precision 100.00%
- tagger_tail: n=5236, precision 97.17%
- False merges of novel-vendor rows: 126
- Novel-vendor detection: 1063 of 1189 novel rows flagged (89.4% recall); 1063 of 1252 flags are truly novel (84.9% precision)
