# Cross-Screen Measurement: Conversion Drivers (PySpark)

A self-contained PySpark workflow that demonstrates the full arc of technical
measurement-science work on the Samba TV stack: **SQL / Python / Databricks / Spark**.

Built as the Databricks fluency proof for the **Measurement Analyst (Technical
Measurement Operations)** role. The data model is lifted directly from the job
description's own example, so the notebook isn't a generic Spark demo: it is the
literal task the team does, run end to end.

---

## What it proves

The job asks for *"absolute technical fluency in SQL, Python, Databricks, BigQuery"*
and the ability to *"perform custom matches and/or joins from disparate sources
(e.g. ad exposure files from a publisher, conversion data from a measurement
partner, and panel weights from the Samba measurement panel)."*

This notebook does exactly that, decomposed into the six operations that define
all technical data analysis regardless of tool or buzzword:

| # | Operation | What it shows | JD line it answers |
|---|-----------|---------------|--------------------|
| 1 | **Retrieve** | Read three disparate CSVs into Spark | "extract data from databases" |
| 2 | **Link (naive)** | Quantify rows silently lost to key drift | the trap that separates real join fluency |
| 3 | **Shape** | Normalize keys, dedupe, handle nulls | the unglamorous 70-80% of the job |
| 4 | **Link (correct)** | Panel-as-spine join, no double-counting | "custom matches and/or joins from disparate sources" |
| 5 | **Reduce** | Weighted conversion rate by segment + window rank; saturation curve | "conversion rate by audience segment" |
| 6 | **Infer** | Weighted logistic regression, coefficients as drivers | "drivers analysis... statistical analyses, modeling" |
| 7 | **Translate** | Two-panel chart for a non-technical reader | "visualize data to make it more accessible" |

The Config block at the top makes the whole thing a **reusable template**, which
answers the JD's *"turn common requests into repeatable processes (e.g. templates,
workbooks)."*

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

This is the most honest version of the proof: it runs *on Databricks*.

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

*Sibling to `dbt-spotify-project` in the analytics-engineering track of the
skill-development portfolio. Built June 2026 as targeted gap-closing for the
Samba TV Measurement Analyst application.*
