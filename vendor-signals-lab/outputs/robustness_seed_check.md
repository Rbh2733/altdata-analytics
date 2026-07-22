# Robustness check (seed 12 vs seed 11, plus two frozen-seed sensitivity checks)

Seed 11 (frozen, committed run) vs seed 12 (this check, isolated temp directory, not committed).

## Lead ordering (source, mean of median lead vs revenue realization)

- seed 11: ['web', 'spend', 'jobs'] {'jobs': 2.0, 'spend': 2.5, 'web': 3.0}
- seed 12: ['spend', 'web', 'jobs'] {'jobs': 2.0, 'spend': 3.0, 'web': 2.5}
- ordering unchanged: False

## Tier rank-quality gradient (median Spearman by tier)

- seed 11: {'A': 0.700094831673779, 'B': 0.509816801833908, 'C': 0.3116511005174215}
- seed 12: {'A': 0.5530594405594406, 'B': 0.5218362237998828, 'C': 0.2786181706978979}
- both monotonic A>B>C: True / True

## Pathologies still caught (seed 12 QA report excerpt)

```
## P1: bot-traffic spike (z > 4 on the monthly log-return, trailing 6 months, no corroborating jobs/spend move)
- Raw z>4 candidates across the population: 49
- Surviving after the no-corroboration filter: 46
## P2: job repost storm (unique fingerprints / raw postings < 0.4)
- Vendor-quarters flagged: 8
## P3: descriptor fragmentation (panelist overlap > 0.5, amount ratio >= 0.6, cadence ratio in [0.8, 1.25], all three agree)
- Bridges found: 0
## P4: coverage cliff (segment covered-vendor count drops > 50% vs trailing 4-quarter mean)
- Segment-quarters flagged: 2
```

## Threshold sensitivity (delta = 10/15/20 points, k=2, floor/ceiling held fixed at 55/45, population-pooled across type and tier, seed 11 frozen outputs)

| delta | n_flags | n_events | precision | recall |
|---|---|---|---|---|
| 10 | 2100 | 260 | 10.6% | 85.8% |
| 15 | 1669 | 260 | 12.7% | 81.5% |
| 20 | 1255 | 260 | 14.7% | 71.2% |

## Equal-weights composite (1/3 jobs, web, spend vs the frozen 0.35/0.2/0.45, seed 11 frozen outputs)

- frozen weights tier gradient: {'A': 0.700094831673779, 'B': 0.509816801833908, 'C': 0.3116511005174215}
- equal weights tier gradient: {'A': 0.7196112064036592, 'B': 0.49322686906436014, 'C': 0.3116511005174215}

