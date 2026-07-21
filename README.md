# altdata-analytics

Independent research on technology and subscription markets, and the alternative-data methods behind it. I am Reid Nelson, an independent TMT research analyst in Austin, TX; the written research lives at [reidn33.substack.com](https://reidn33.substack.com), and this repository holds the technical layer: pipelines, measurement notebooks, dashboards, and analysis you can run and check rather than take on faith.

This repository was previously named `streaming-analytics`; old links redirect here.

## Projects

### [vendor-resolution-lab](vendor-resolution-lab/)

An end-to-end entity-resolution and AI-tagging pipeline for vendor spend data: raw card-feed merchant strings matched to a canonical vendor table in stages (normalize, exact, fuzzy with a review band, AI tagger for the tail), with a validation harness, QA expectations, drift monitoring, and a DuckDB SQL layer. Deterministic synthetic data, so every number in its README reproduces from a clean copy. A live Claude adapter ships alongside the deterministic mock tagger.

### [databricks-measurement](databricks-measurement/)

A reproducible PySpark notebook joining three sources on a household-ID spine and running panel-weighted logistic regression, with the data-quality catches documented rather than hidden. Metrics and the naive-join failure it guards against are in the directory README.

### [streaming-altdata-ecosystem](streaming-altdata-ecosystem/)

A research map of the streaming alternative-data ecosystem: the layers between raw consumer behavior and investor-grade signal, and the companies operating at each one.

### Dashboards and analyses

- [Subscription Economy Research dashboard](https://rbh2733.github.io/altdata-analytics/), served from `index.html`: coverage universe, growth deceleration, bundle penetration, and operating-margin comparisons across the major subscription platforms.
- Four analysis PDFs at the repository root (SVOD ad-tier inflection, competitive positioning, competitive architecture).
- `media-tiered-taxonomy-great-sorting.html`, an interactive rendering of the media taxonomy the published essays are built on.

### substack-staging

Staging for essays in progress before they publish.

## Method, in one paragraph

The same operation runs through everything here: find what consensus is pricing, find the structural layer it skipped, measure the gap. The repository exists because measurement claims should be inspectable; where data cannot be published, it is generated deterministically and labeled as such, and where a number is reported, the code that produced it is committed next to it.
