# Robustness check (seed 12 vs seed 11, plus two frozen-seed sensitivity checks)

Seed 11 (frozen, committed run) vs seed 12 (this check, isolated temp directory, not committed).

## Lead ordering (source, mean of median lead vs revenue realization)

- seed 11: ['web', 'spend', 'jobs'] {'jobs': 2.0, 'spend': 2.5, 'web': 2.75}
- seed 12: ['spend', 'web', 'jobs'] {'jobs': 2.0, 'spend': 3.0, 'web': 3.0}
- ordering unchanged: False

## Tier rank-quality gradient (median Spearman by tier)

- seed 11: {'A': 0.5968744044215741, 'B': 0.5628209820654582, 'C': 0.28053333418311593}
- seed 12: {'A': 0.5770733825445072, 'B': 0.5778893900913536, 'C': 0.2784531087238704}
- both monotonic A>B>C: True / False

## Pathologies still caught (seed 12 QA report excerpt)

```
## P1: bot-traffic spike (z > 4 on the monthly log-return, trailing 6 months, no corroborating jobs/spend move)
- Raw z>4 candidates across the population: 73
- Surviving after the no-corroboration filter: 68
## P2: job repost storm (unique fingerprints / raw postings < 0.4)
- Vendor-quarters flagged: 1
## P3: descriptor fragmentation (panelist overlap > 0.5, amount ratio >= 0.6, cadence ratio in [0.8, 1.25], all three agree)
- Bridges found: 2
## P4: coverage cliff (segment covered-vendor count drops > 50% vs trailing 4-quarter mean)
- Segment-quarters flagged: 2
```

## Threshold sensitivity (delta = 10/15/20 points, k=2, floor/ceiling held fixed at 55/45, population-pooled across type and tier, seed 11 frozen outputs)

| delta | n_flags | n_events | precision | recall |
|---|---|---|---|---|
| 10 | 2184 | 276 | 10.5% | 83.3% |
| 15 | 1736 | 276 | 12.5% | 78.6% |
| 20 | 1317 | 276 | 14.2% | 67.8% |

## Equal-weights composite (1/3 jobs, web, spend vs the frozen 0.35/0.2/0.45, seed 11 frozen outputs)

- frozen weights tier gradient: {'A': 0.5968744044215741, 'B': 0.5628209820654582, 'C': 0.28053333418311593}
- equal weights tier gradient: {'A': 0.6303411473222793, 'B': 0.5291790416189097, 'C': 0.28053333418311593}

