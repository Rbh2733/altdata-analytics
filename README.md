# altdata-analytics

Independent research on technology and subscription markets, and the alternative-data methods behind it. I am Reid Nelson, an independent TMT research analyst in Austin, TX; the written research lives at [reidn33.substack.com](https://reidn33.substack.com), and this repository holds the technical layer: pipelines, measurement notebooks, dashboards, and analysis you can run and check rather than take on faith.

This repository was previously named `streaming-analytics`; old links redirect here.

## Projects

Start here: [panel-estimation-lab](panel-estimation-lab/) and [vendor-signals-lab](vendor-signals-lab/) are the two measurement labs, [market-data-pipeline](market-data-pipeline/) and [vendor-resolution-lab](vendor-resolution-lab/) the two data pipelines. Every number in their READMEs reproduces from a clean copy.

### [panel-estimation-lab](panel-estimation-lab/)

A panel estimation lab built in a simulated world where the truth is knowable: 200,000 consumers, six fictional subscription and e-commerce services, a deliberately biased transaction panel with four planted feed pathologies, and a four-rung estimation ladder (naive scale-up, raking to census margins, QA corrections, ratio calibration to reported actuals) backtested over 8 quarters against exact ground truth. Naive scale-up misses quarterly revenue by 30.6% on average; the full method lands at 2.7%, and the failures (gross adds and churn wrong by roughly 2x at every rung) are printed in the scorecard rather than dropped from it. A leakage guard enforced by package structure and 46 tests keeps the estimator from ever reading the answer key, a DuckDB layer runs the cohort and concentration analysis shop-side, and every artifact regenerates byte-identically.

### [vendor-signals-lab](vendor-signals-lab/)

A private-vendor operating-health measurement lab built without the anchor its sibling relies on: private companies disclose no reported actuals to calibrate against, so this one replaces calibration with coverage-aware honesty instead. Three deliberately imperfect exhaust streams (hiring, web traffic, customer spend) on 420 fictional vendors feed a coverage-tiered composite that scores itself against synthetic ground truth on rank quality, lead-lag timing, and real shutdown and funding outcomes, printing its weak spots (thin inflection precision, a QA rule that only catches its own plant three quarters late, a rank gradient that partly collapses under a second seed) alongside the wins. It measures operating health and recommends nothing.

### [market-data-pipeline](market-data-pipeline/)

A multi-source fundamentals reconciliation pipeline: the same metrics ingested from SEC EDGAR, Financial Modeling Prep, and Polygon, normalized to one canonical model, with disagreement measured and classified (dropped scale factors, fiscal-versus-calendar window misalignment, stale pre-restatement values) before each group resolves through an explicit source-reliability hierarchy: regulatory filings over commercial vendors over derived estimates. The disagreement report is the product; the resolved table is the byproduct. Offline by default on deterministic fixtures with committed outputs and 37 offline tests (two of which assert byte-identical reproduction), plus a live mode against the real APIs.

### [vendor-resolution-lab](vendor-resolution-lab/)

An end-to-end entity-resolution and AI-tagging pipeline for vendor spend data: raw card-feed merchant strings matched to a canonical vendor table in stages (normalize, exact, fuzzy with a review band, AI tagger for the tail), with a validation harness, QA expectations, drift monitoring, and a DuckDB SQL layer. Deterministic synthetic data, so every number in its README reproduces from a clean copy. A live Claude adapter ships alongside the deterministic mock tagger.

### [dbt-streaming-analytics](dbt-streaming-analytics/)

A dbt-core plus DuckDB warehouse over a synthetic music-streaming catalog: staging, intermediate, and marts layers in a star schema, 60 automated tests (50 generic, 10 singular), documentation as code, and an optional Streamlit dashboard. The 85,000-row seed regenerates byte-identically from a committed script, so the entire warehouse is a pure function of one file; the layering and testing patterns are the point, and the fictional data is labeled as such throughout.

### [databricks-measurement](databricks-measurement/)

A reproducible PySpark notebook joining three sources on a household-ID spine and running panel-weighted logistic regression, with the data-quality catches documented rather than hidden. Metrics and the naive-join failure it guards against are in the directory README.

### [ats-resolver](ats-resolver/)

An entity-resolution and data-reliability tool packaged as a local MCP server: job postings resolved from lossy aggregator metadata back to the authoritative applicant-tracking-system record (Greenhouse, Lever, Ashby, SmartRecruiters), through an explicit reliability hierarchy in which dedicated API fields beat inference from posting text, which beats a last-resort HTML scrape, and unstated facts resolve to unknown rather than to a guess. A small instance of the general alternative-data problem: the convenient feed is a lossy derivative of the system of record.

### [streaming-altdata-ecosystem](streaming-altdata-ecosystem/)

A research map of the streaming alternative-data ecosystem: the layers between raw consumer behavior and investor-grade signal, and the companies operating at each one.

### Dashboards and analyses

- [Subscription Economy Research dashboard](https://rbh2733.github.io/altdata-analytics/), served from `index.html`: coverage universe, growth deceleration, bundle penetration, and operating-margin comparisons across the major subscription platforms.
- Three analysis PDFs at the repository root (SVOD ad-tier inflection, competitive positioning, competitive architecture).
- `media-tiered-taxonomy-great-sorting.html`, an interactive rendering of the media taxonomy the published essays are built on.

## Method, in one paragraph

The same operation runs through everything here: find what consensus is pricing, find the structural layer it skipped, measure the gap. The repository exists because measurement claims should be inspectable; where data cannot be published, it is generated deterministically and labeled as such, and where a number is reported, the code that produced it is committed next to it.
