# Cross-Screen Measurement: Conversion Drivers (PySpark)

A self-contained PySpark workflow that demonstrates cross-screen panel
measurement engineering on synthetic data: **SQL / Python / Databricks / Spark**.

The problem is industry-generic. Cross-screen ad measurement means joining
disparate sources that never agreed on a schema: ad exposure files from a
publisher, conversion data from a measurement partner, and panel weights from a
household measurement panel. The join key is a household ID, and every source
spells it slightly differently. This notebook runs that task end to end and
keeps the failure modes visible instead of editing them out.

---

## What it demonstrates

The workflow decomposes into the operations that define technical data analysis
regardless of tool or buzzword:

| # | Operation | What it shows | Measurement task it maps to |
|---|-----------|---------------|------------------------------|
| 1 | **Retrieve** | Read three disparate CSVs into Spark | extracting data from source systems |
| 2 | **Link (naive)** | Quantify rows silently lost to key drift | the trap that separates real join fluency |
| 3 | **Shape** | Normalize keys, dedupe, handle nulls | the unglamorous 70-80% of the work |
| 4 | **Link (correct)** | Panel-as-spine join, no double-counting | custom matches and joins across disparate sources |
| 5 | **Reduce** | Weighted conversion rate by segment + window rank; saturation curve | conversion rate by audience segment |
| 6 | **Infer** | Weighted logistic regression, coefficients as drivers | drivers analysis via statistical modeling |
| 7 | **Translate** | Two-panel chart for a non-technical reader | making results accessible beyond the analyst |

The Config block at the top makes the whole thing a **reusable template**:
re-point the data path, swap the campaign key, or extend the model formula, and
the same operations rerun unchanged.

---

## The data (synthetic, deterministic, honest)

`generate_sample_data.py` builds three messy sources for 4,000 panel households,
seeded (SEED=42) so every run reproduces identically:

- `ad_exposure.csv` - publisher-side impression log. Messy on purpose: the
  `household_id` key drifts in case and whitespace, ~5% null devices, ~3%
  double-logged rows.
- `conversions.csv` - measurement-partner purchase events.
- `panel.csv` - the canonical household universe with clean keys, audience
  segments (~4% missing), viewing profiles, and panel weights.

A real causal signal is baked in so the drivers analysis has something true to
recover: conversion rises with exposure frequency but **saturates** past ~6
exposures; streaming-heavy viewers convert better than linear-heavy; high-HHI
cordcutters are the strongest segment. The logistic regression recovers this
ordering, which is how you know the pipeline works rather than just runs.

---

## How to run

### Option A: Databricks Community Edition (recommended, zero local install)
1. Create a free account at community.cloud.databricks.com.
2. Run `python generate_sample_data.py` locally once to produce the three CSVs
   (or upload them from a prior run).
3. Upload the CSVs to DBFS, e.g. `/FileStore/measurement/`.
4. Import `measurement_drivers.ipynb`, set `DATA = "/FileStore/measurement"` in
   the Config cell, attach to the free cluster, **Run All**.

Running it there confirms the workflow on Databricks itself, not just in a
local Spark session.

### Option B: Local
```bash
pip install pyspark matplotlib pandas   # PySpark needs Java 11+ installed
jupyter notebook measurement_drivers.ipynb
```
Keep `DATA = "data"`. The first cell auto-generates the sample data if it's
missing, so a fresh clone runs with no separate step.

---

## Validated output (what a clean run produces)

```
naive inner join matched 2256 of 3232 exposure rows
  -> 976 rows silently lost to key drift
exposure dedup: 3232 -> 3150 rows
master households: 4000 | converted: 572

rank  segment              households  avg_freq  weighted_cvr
1     Cordcutter_HHI_High  781         3.04      0.1915
...
6     Linear_Loyalist      739         3.03      0.1096

AUC: 0.676
Conversion drivers (by |coefficient|):
  +0.6682  segment_Cordcutter_HHI_High
  +0.3465  viewing_profile_Streaming-heavy
  +0.1717  exposure_frequency
```

---

## Files

| File | Purpose |
|------|---------|
| `measurement_drivers.ipynb` | The workflow. Self-documenting (markdown Why + code How per step). |
| `generate_sample_data.py` | Deterministic messy-data generator. |
| `data/` | Generated CSVs + output chart (git-ignored; regenerable). |
| `requirements.txt` | pyspark, pandas, matplotlib. |

---

*Built June 2026. Synthetic, deterministic data only; a fresh clone reproduces
every figure above.*
