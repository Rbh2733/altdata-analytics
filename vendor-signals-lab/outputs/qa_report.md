# QA report

Shop-side only: every rule below is computed from data/exhaust/ and data/public/, never from data/truth/.

## P1: bot-traffic spike (z > 4 on the monthly log-return, trailing 6 months, no corroborating jobs/spend move)

- Raw z>4 candidates across the population: 51
- Surviving after the no-corroboration filter: 49
  - V0019 2024-04: z=8.39
  - V0278 2025-02: z=6.70
  - V0265 2024-11: z=5.84
  - V0319 2024-08: z=5.81
  - V0016 2025-11: z=5.66
  - V0241 2025-11: z=5.60
  - V0157 2023-10: z=5.57
  - V0327 2025-12: z=5.29
  - V0167 2025-02: z=5.27
  - V0327 2023-11: z=5.21

## P2: job repost storm (unique fingerprints / raw postings < 0.4)

- Vendor-quarters flagged: 2
  - V0339 2024Q3: raw=102, unique=30, ratio=0.294
  - V0339 2024Q4: raw=93, unique=32, ratio=0.344
- Relist-collapse window also absorbed 3683 legitimate background re-lists elsewhere in the population (counted, not hidden).

## P3: descriptor fragmentation (panelist overlap > 0.5, amount ratio >= 0.6, cadence ratio in [0.8, 1.25], all three agree)

- Bridges found: 2
  - 'KELPDEEP' -> V0382: overlap=1.000, amount_ratio=0.990, cadence_ratio=1.208
  - 'SQ *KELPDEEP' -> V0382: overlap=1.000, amount_ratio=0.969, cadence_ratio=1.203

## P4: coverage cliff (segment covered-vendor count drops > 50% vs trailing 4-quarter mean)

- Segment-quarters flagged: 2
  - ai_applications 2025Q2: n_covered=0, trailing_mean=36.2
  - ai_applications 2025Q3: n_covered=0, trailing_mean=27.0

