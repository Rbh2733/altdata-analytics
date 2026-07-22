# QA report

Shop-side only: every rule below is computed from data/exhaust/ and data/public/, never from data/truth/.

## P1: bot-traffic spike (z > 4 on the monthly log-return, trailing 6 months, no corroborating jobs/spend move)

- Raw z>4 candidates across the population: 66
- Surviving after the no-corroboration filter: 60
  - V0031 2025-10: z=6.92
  - V0259 2024-10: z=6.71
  - V0381 2025-08: z=6.57
  - V0221 2025-07: z=6.33
  - V0318 2025-10: z=6.32
  - V0421 2024-07: z=6.13
  - V0072 2025-05: z=5.86
  - V0119 2025-11: z=5.73
  - V0170 2025-02: z=5.70
  - V0363 2024-03: z=5.66

## P2: job repost storm (unique fingerprints / raw postings < 0.4)

- Vendor-quarters flagged: 5
  - V0208 2025Q2: raw=353, unique=140, ratio=0.397
  - V0208 2025Q3: raw=418, unique=148, ratio=0.354
  - V0208 2025Q4: raw=505, unique=155, ratio=0.307
  - V0290 2024Q3: raw=21, unique=5, ratio=0.238
  - V0290 2024Q4: raw=18, unique=5, ratio=0.278
- Relist-collapse window collapsed 5476 postings population-wide beyond first listings, a total that includes the flagged storm quarters (counted, not hidden).

## P3: descriptor fragmentation (panelist overlap > 0.5, amount ratio >= 0.6, cadence ratio in [0.8, 1.25], all three agree)

- Bridges found: 1
  - 'HARBORZONE INC' -> V0347: overlap=1.000, amount_ratio=0.955, cadence_ratio=1.243

## P4: coverage cliff (segment covered-vendor count drops > 50% vs trailing 4-quarter mean)

- Segment-quarters flagged: 2
  - ai_applications 2025Q2: n_covered=0, trailing_mean=44.0
  - ai_applications 2025Q3: n_covered=0, trailing_mean=33.0

