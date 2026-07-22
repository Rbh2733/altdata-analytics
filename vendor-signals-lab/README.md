# Vendor Signals Lab

Private software and AI vendors disclose almost nothing: no quarterly reports, no reported revenue, no analyst consensus. Investors who need to track them anyway are left with exhaust: hiring activity, web traffic, and the sliver of customer spend that happens to cross an observable payment rail. This lab builds that measurement problem end to end: a simulated population of 420 fictional private vendors with a knowable ground truth, three deliberately imperfect exhaust streams derived from it, and an estimation and evaluation stack that turns the exhaust into a coverage-aware operating-health composite, scored against the truth it never reads.

This lab's sibling, `panel-estimation-lab`, calibrates its estimators to quarterly reported actuals. This one removes that anchor on purpose, because private vendors report nothing. What replaces it: every vendor-quarter carries an explicit coverage tier (A, B, or C) so no number claims precision it doesn't have; claims are rank-based rather than level-based; size is reported as a half-decade band, never a point; and the closest thing to ground truth this lab ever sees is a sparse set of outcome events (fundings, shutdowns, and a handful of disclosed acquisition prices). "Signal" is used throughout in its plain measurement sense: a measured indicator of operating health, nothing more. **This lab measures operating health and recommends nothing.**

Every number below was produced by this code and ships in `outputs/` so it is checkable without running anything.

**Three measured numbers, upfront.** The composite's rank quality by tier is **0.700 (A) vs 0.312 (C)**, a real gradient, and the blended 0.479 is reported only for reference because it oversells what tier C actually knows. The recovered lead structure holds where it was designed to hold and not everywhere: jobs leads revenue realization by a **stable 2 quarters** in both the frozen run and the seed-12 robustness check, while web and spend's leads move around (2.5-3.0 quarters) and swap order between seeds, which is disclosed rather than smoothed over. On outcomes, **13 of 23 shutdown vendors (56.5%)** sat in the bottom composite quartile two quarters before shutting down; 3 did not, and are named below with the mechanism.

## What this demonstrates

- **Sample and panel precision under real coverage gaps.** Three exhaust sources with different coverage, lag, and noise, combined into a single composite that is honest about how much of the population it can actually see (tier A 12.6%, B 42.7%, C 44.7% of vendor-quarters).
- **A natural instinct for anomalies, made mechanical.** Four planted pathologies, each caught by a fixed, data-independent rule, with population-wide firing counts reported alongside the catches so false-positive pressure is visible, not hidden.
- **Proactive use of an AI tool with a validation harness.** A deterministic mock title-classifier ships as the default (95.3% accuracy on 150 hand-labeled titles) with an optional live Claude adapter behind the same interface and a row-coverage guarantee.
- **SQL fluency.** A five-cut DuckDB layer over the shop's own outputs: coverage pivots, a percentile leaderboard, a lead-lag cut expressed as window functions, an anomaly report, and a share-shift cut, none of it touching truth.
- **Intellectual honesty about a genuinely hard measurement problem.** No reported actuals exist here by design; the README's own limitations section names every place the generator made the shop's life easier than a real one would be.

## The world, and why synthetic

Ground truth is only knowable in a simulation: nobody hands a real analyst the true ARR of a private company to grade an estimate against. So the lab builds a population of 420 fictional vendors (any resemblance to real software or AI companies is unintended) across five segments, each following a 12-quarter latent health trajectory: `simulation/params.py` fixes an archetype mix of steady growth (40%), acceleration (20%), stall (20%), decline (12%), and wind-down (8%), each with one or two random change points. Hiring responds to a plan change immediately; web usage catches up fully one quarter later; ARR realizes the new growth rate gradually, a third of the delta at the quarter after the change, the rest by two quarters after. That staggered construction is the whole basis of the lead-lag physics measured in the Results section below, and that section reports whatever actually emerged, including where it didn't fully hold.

Outcome events (funding, shutdown, acquisition) come from a per-vendor runway and hazard model, also in `simulation/outcomes.py`, and live only in `data/truth/`, read only by `evaluation/`. Real funding announcements are public in the real world and a real shop would consume them; keeping them judge-only here costs realism but buys a clean out-of-sample outcome check, and that tradeoff is deliberate.

## The three exhaust families

| source | coverage | lag vs revenue realization | noise | one distortion |
|---|---|---|---|---|
| job postings | 42.9% of vendors tracked, but 70.7% of employment (skewed to larger vendors) | leads by 2 quarters (median, both seeds) | background 3% legitimate re-lists | repost storm: same requisitions re-listed every 2-3 weeks |
| web traffic | 91.4% of vendors covered (skews away from the smallest) | leads by ~1 quarter, but this moved between seeds | level off by 2-3x per vendor forever; usable only as log-growth | one vendor's traffic goes to 6x for 5 weeks |
| customer spend panel | 34.0% of vendors ever in a payment channel (segment-dependent, 7.1% to 60.0%) | ~0 to slightly negative (moved between seeds) | 5-8% relative noise on growth | one vendor's descriptor fragments into two new, unmapped strings |

A tracked vendor with zero postings that quarter is an **observed zero** (`tracked_zero`, informative: hiring froze), not a missing read; an untracked vendor is genuinely missing. The same zero-vs-missing distinction applies to spend (`present` / `thin` / `absent`, gated on 8+ transactions over the trailing 2 quarters).

## Coverage tiers: the philosophy

There is no anchor to calibrate against, so the only honest move is to say, per vendor-quarter, exactly how much was actually observed, and let every downstream claim inherit that uncertainty rather than launder it. Tier is purely mechanical: A = all three sources present that quarter, B = two, C = one or zero (`estimation/coverage.py`). The tier mix and its drivers, final scored quarter:

| segment | A | B | C | typical reason for C |
|---|---|---|---|---|
| devtools | 18 | 35 | 37 | self-serve spend channel exists but many vendors are still small |
| data_infrastructure | 0 | 29 | 56 | invoice-billed; almost no spend-panel visibility at all |
| ai_applications | 13 | 42 | 40 | widest dispersion; also the coverage-cliff segment |
| security | 4 | 20 | 46 | enterprise motion, weakest spend-panel presence |
| vertical_saas | 13 | 40 | 27 | best-covered non-devtools segment |

`data_infrastructure` never reaches tier A at all in this run: invoice billing genuinely has near-zero spend-panel visibility, and the composite says so structurally rather than pretending otherwise. No downstream table in this README reports an unstratified accuracy number for this reason.

## The four pathologies, and what they cost uncorrected

| pathology | vendor / window | magnitude | detected by | naive cost |
|---|---|---|---|---|
| bot-traffic spike | V0019 (devtools), 2024-04/05 | traffic x6 for 5 weeks | monthly log-return z = 8.39 vs trailing 6 months | a false acceleration flag on a steady vendor |
| job repost storm | V0339 (security), 2024Q3-Q4 | raw 102 and 93 postings vs 30 and 32 unique | unique/raw ratio 0.294 and 0.344 (population baseline near 1.0) | naive hiring-intensity overstated ~3x |
| descriptor fragmentation | V0382 (vertical_saas), 2025Q1 | known descriptor fades over 3 weeks, two unmapped strings take over | panelist overlap 1.00, amount ratio 0.97-0.99, cadence ratio 1.20-1.21, all three agreeing | naive composite crashes to 22.5 (a false stall); honestly time-fenced, the correction cannot apply yet either (23.4, same flag) since the bridge evidence above only accrues by 2025Q4, three quarters later |
| coverage cliff | ai_applications segment, 2025Q2-Q3 | covered-vendor count 0 vs a trailing mean of 36.2 and 27.0 | segment-level covered count drop > 50% | a mass false-stall read across ~40 vendors if spend absence were mistaken for spend decline |

Population-wide firing counts, reported because a rule with a hidden false-positive rate is not a rule anyone should trust: the bot-spike z-rule raises 51 raw candidates and 49 survive the no-corroboration filter (48 of them background, not the plant), full-history diagnostic counts; the per-quarter time-fenced production read applies 42 of those 49 corrections, per the fourth disclosed fix in the Honesty protocol section; the relist-collapse window also absorbs 3,683 postings elsewhere in the population that are not storm duplicates, mostly coincidental title-plus-location collisions from a deliberately narrow title bank (13 engineering titles, 4 locations) rather than genuine re-lists, a real cost of the correction, not a free lunch. No pathology-affected vendor also carries a truth inflection in its affected quarters; this was verified before the freeze.

## Results

**Rank quality** (median Spearman, composite vs true forward ARR growth, across the 10 scored quarters):

| tier | median spearman |
|---|---|
| A | 0.700 |
| B | 0.510 |
| C | 0.312 |
| blended (reference only) | 0.479 |

The blended number is withheld from the headline on purpose: it launders tier-C ignorance through tier-A precision. The gradient is the actual finding.

**Lead-lag** (first quarter each source's own percentile crosses the flagger's +/-15-point rule, relative to the regime change and to revenue realization; a source can only detect where present, so the denominator is reported too):

| source | type | n_events | n_present | n_detected | detection rate | median lead vs regime change | median lead vs revenue |
|---|---|---|---|---|---|---|---|
| jobs | acceleration | 83 | 33 | 30 | 90.9% | 0.0 | 2.0 |
| jobs | stall | 177 | 67 | 47 | 70.1% | 0.0 | 2.0 |
| spend | acceleration | 83 | 25 | 22 | 88.0% | 0.0 | 2.0 |
| spend | stall | 177 | 58 | 56 | 96.6% | 1.0 | 3.0 |
| web | acceleration | 83 | 75 | 71 | 94.7% | 1.0 | 3.0 |
| web | stall | 177 | 153 | 144 | 94.1% | 1.0 | 3.0 |

Jobs' 2-quarter lead over revenue realization is the one number in this table that survived the seed-12 robustness check exactly. Web and spend's leads did not: they average 3.0 and 2.5 quarters respectively under seed 11 and swap to 2.5 and 3.0 under seed 12. This is measured and reported as measured, not smoothed into a cleaner story; the per-source percentile-delta detector has more timing noise for these two sources than the generator's own physics would predict on its own, and that gap is a property of the detection method, not a law of the underlying construction. Caveat: lead conditional on detection is optimistically biased by construction, which is why detection rate is welded to every lead number above it, never quoted alone.

**Inflection precision/recall** (k = 1 and 2 quarters, greedy one-to-one matching; full grid, every cell's event count shown so thin cells are never read as conclusions):

| k | type | tier | n_flags | n_events | precision | recall |
|---|---|---|---|---|---|---|
| 1 | acceleration | A | 112 | 9 | 8.0% | 100.0% |
| 1 | acceleration | B | 425 | 30 | 6.6% | 93.3% |
| 1 | acceleration | C | 311 | 44 | 8.4% | 59.1% |
| 1 | stall | A | 109 | 22 | 15.6% | 77.3% |
| 1 | stall | B | 396 | 59 | 11.6% | 74.6% |
| 1 | stall | C | 316 | 96 | 17.7% | 60.4% |
| 2 | acceleration | A | 112 | 9 | 8.0% | 100.0% |
| 2 | acceleration | B | 425 | 30 | 7.1% | 100.0% |
| 2 | acceleration | C | 311 | 44 | 10.3% | 72.7% |
| 2 | stall | A | 109 | 22 | 18.3% | 90.9% |
| 2 | stall | B | 396 | 59 | 13.4% | 88.1% |
| 2 | stall | C | 316 | 96 | 21.5% | 71.9% |

Recall is respectable (59-100%); precision is not (7-22%). This is the headline honest weak spot and section "honest failures" below explains the mechanism rather than just the number.

**Outcome validation** (the centerpiece, deliberately its least flattering table):

- Shutdowns: 23 total. Among the 23 with a scored composite two quarters prior, **56.5%** sat in the bottom population quartile; median composite one quarter before shutdown was **25.7** vs a population median of 50.0. Three shutdown vendors scored *above* 50 the quarter before shutting down: V0168 (tier C, composite 59.3, shut down 2025Q4), V0170 (tier B, composite 68.5, shut down 2024Q2), V0341 (tier C, composite 67.2, shut down 2025Q2). V0168 is exactly the failure mode this design predicted (see below).
- Funding: 129 of 135 rounds scored. Median composite one quarter before a raise was **50.0**, identical to the population median. This is impurity by design, not a null result being misread: the hazard model raises funding odds for strugglers on runway pressure as much as for accelerators, and the two effects cancel almost exactly in this run.
- Disclosed acquisitions (22 priced, graded at the acquisition quarter itself rather than the later disclosure quarter, since exhaust darkens the quarter after acquisition by design and that is exactly when the disclosure lands): band hit rate **40.9%**, within-one-band **68.2%**, median absolute log10 error **0.236** (about 1.7x). This sits within the design's own expectation of "roughly half to two thirds correct-band," which is a low bar restated honestly: without a reported-actuals anchor, size is a band, not a number.

## Honest failures

**1. A pathology that fooled the naive read, and a correction that cannot arrive in real time.** V0382's descriptor fragmentation: the naive (descriptor-map-only, no bridge) composite at 2025Q1 collapses to **22.5** and fires a false stall flag. An earlier build of this pipeline reported an honestly-time-fenced-looking QA correction of 68.9 with no flag at the same quarter; that number was wrong, produced by handing `detect_descriptor_fragmentation` a full year of future spend data for every historical quarter's read (fixed and disclosed in the Honesty protocol section below). Corrected properly, the bridge that reconnects the new descriptor to V0382 is built from panelist-overlap, amount-ratio, and cadence evidence that only accrues from transactions dated through 2025Q4, three quarters after the plant fires: a shop that only knows what happened by 2025Q1 has no bridge to apply yet, so the honestly time-fenced composite that quarter is **23.4**, still firing the stall flag, effectively indistinguishable from naive (`outputs/naive_vs_qa.csv` carries both trajectories for every vendor-quarter, so this is checkable). The corrected read is not silent about the gap: `outputs/coverage_matrix.csv` shows V0382 genuinely demoted to tier C at 2025Q3, spend reading "absent" that quarter rather than patched by hindsight, and the bridge only resolves at 2025Q4, per `outputs/qa_report.md`'s full-history diagnostic. The honest finding is not "QA caught it," it's that this QA rule, as built, is retrospective rather than real-time: a live deployment would not have caught the false stall until three quarters after it mattered. The repost storm is the pathology that genuinely is caught the same quarter, because dedupe only needs evidence from postings dated on or before the one it is deduping: V0339's naive composite hits **89.0** at 2024Q4 and fires a false acceleration flag; corrected, it is **76.3**, no flag.

**2. A vendor the composite got badly wrong.** V0168, a tier-C, web-only devtools vendor: its composite is built from a single noisy source with tier-C shrinkage already pulling it toward 50, and even so it spiked to **59.3** the quarter immediately before the vendor shut down (2025Q4), the exact "tier-C web-only decliner" failure mode the design intent predicted before any run. A single noisy source with three-source-confidence shrinkage still is not enough insulation against a genuine surprise read.

## Architecture and fences

```
simulation/   THE WORLD (only importer of params.py)
estimation/   THE SHOP (loader.py is the sole gateway; cannot import simulation or evaluation)
evaluation/   THE JUDGE (only reader of data/truth/; never imports simulation)
sql/          shop-side DuckDB layer; truth never registered as a view
data/exhaust/ data/public/   what the shop can read
data/truth/                  what only the judge can read
outputs/                     everything committed and checkable
```

Three enforcement layers, each with a test: (1) an AST walk confirms no module under `estimation/` or `sql/` imports `simulation` or `evaluation`, no string literal in those packages names a truth path, and `simulation.params` is imported nowhere outside `simulation/`. (2) `estimation/loader.py` is the only I/O gateway on the shop side; it resolves every path and raises `PermissionError` outside `data/exhaust/` and `data/public/`, including `..` traversal, and a monkeypatched `builtins.open` during a full estimation run opens nothing under `data/truth/`. (3) `loader.as_of(quarter)` returns exhaust dated inside or before that quarter (spend carries an extra one-month publication lag on top). The delete-the-future test physically truncates every exhaust and truth row after 2024Q4 in a copied tree and asserts the pipeline's quarter-<=2024Q4 outputs are byte-identical to the same pipeline run on the full tree, restricted the same way. `run_all.py` runs generation, estimation, and evaluation as three separate stages; the estimation stage receives only exhaust and public paths.

## The AI tagger

`estimation/tagger_mock.py` is a deterministic keyword-rule classifier (no network, no key) and ships the published numbers: **95.3%** accuracy on 150 hand-labeled titles, with one designed confusion surviving by construction (`Support Engineering Manager` and its variants fall through to the generic "engineer" rule and get tagged engineering against a true label of support, 7 of 44 support rows). `estimation/tagger_claude.py` is a drop-in behind the same interface: batched strict JSON, gated on `ANTHROPIC_API_KEY`, verifying every batch returns every sent row exactly once and failing loudly (never falling back to the mock) on a missing key or a dropped row. Function mix is a supplementary reported cut only and is never a composite input, so the tagger's blast radius on every headline number above is zero by construction. Named generator convenience: the template-generated titles flatter a keyword classifier; 95.3% is a property of this dataset, not a general claim.

## The SQL layer

`python sql/run_sql.py` runs five cuts via DuckDB and writes `outputs/sql_report.md`: a coverage-tier pivot by segment and quarter (the ai_applications coverage-cliff quarters read as a visible anomaly in the pivot itself); a composite leaderboard, top and bottom 5 per tier, where a tier-C extreme literally cannot appear post-shrinkage; a lead-lag cut expressed with window functions, demonstrating hiring-first ordering inside SQL without ever touching truth; an anomaly report (posting-volume outliers, corrected traffic months, spend-row counts by segment-month around the cliff); and a spend-share-shift cut by segment via `LAG`, with the cliff quarters footnoted as a measurement artifact rather than a market move. `postings_tagged`, `traffic_clean`, and `spend_resolved` are rebuilt in memory from the same estimation-layer functions the QA pass uses and registered as views directly, rather than committed as CSVs, since committing them would roughly double `data/exhaust/`'s size to store row-level duplicates of information already in `coverage_matrix.csv` and `level_bands.csv`. Truth is never registered as a view.

## Run it

```
pip install -r requirements.txt
python run_all.py              # generate, QA, estimate, score (about a minute)
python sql/run_sql.py          # analytical SQL over the outputs (a few seconds)
python robustness_check.py     # seed-12 rerun plus threshold/equal-weight checks, excluded from the run_all budget
pytest                         # 71 tests, including the fences and determinism
```

Python 3.10+; dependencies are numpy, pandas, duckdb, and scipy, all offline. `run_all.py` takes about a minute; `data/` (8.6 MB) and `outputs/` (1.6 MB) total about 10.3 MB, both well under the 20 MB cap, and `tests/test_determinism.py` proves the rerun is byte-identical by regenerating everything twice and comparing bytes. Paths in this document are relative to `/path/to/altdata-analytics/vendor-signals-lab`.

## Honesty protocol

World parameters, plant specs, composite weights, shrinkage, tier rules, presence rules, QA thresholds, and inflection thresholds were frozen in `simulation/params.py`, `estimation/qa.py`, `estimation/composite.py`, and `estimation/inflection.py` before any scoring ran. Pre-freeze inspections performed and disclosed: disclosure count landed at 22 (comfortably above the 6-disclosure minimum, no seed redraw needed); no planted-pathology vendor carries a truth inflection in its affected quarters (verified directly). The scorecard ran once; this README's numbers are that one run. Four post-freeze fixes are disclosed. Two are the narrow, cosmetic kind: the disclosed-acquisition grading originally compared the level-band estimate against the *disclosure* quarter, which is guaranteed dark (exhaust stops the quarter after acquisition, exactly the disclosure lag), producing a meaningless 100% miss; it now grades at the acquisition quarter itself, the shop's last live read. And `estimation/levels.py` originally stamped a vendor-quarter with zero source coverage as level_band `<1M`, the same label a genuinely observed small vendor gets; it now stamps a distinct `no_data` band (`level_method` stays `none`) so an absence of evidence is never rendered as evidence of smallness. Neither of those two changed any generator parameter, threshold, or weight; the first moved only the disclosed-acquisition table (which never graded a `none`-method row either way), the second moved only `level_bands.csv`'s band label for the 349 (6.9%) fully dark vendor-quarters.

The third is not cosmetic and is disclosed at length because it is the kind of bug this lab exists to catch in someone else's pipeline. `estimation/features_spend.py` built the descriptor-fragmentation bridge and the coverage-cliff flags once per production run, from `shop.as_of(final_q)`, and applied that single, 2025Q4-informed bridge to every historical quarter's spend read, including quarters before the bridge's own evidence existed. Concretely: `compute(shop, "2025Q4")`'s read of 2025Q1 used bridge evidence that only accrues from transactions dated through 2025Q4, three quarters of hindsight a point-in-time system would not have had. This inflated V0382's 2025Q1 composite from an honest 23.4 to a fabricated 68.9 and is exactly the number the "Honest failures" section above and the original headline both leaned on as proof the QA layer works in real time; it does not, not that quarter. The fix re-derives both the fragmentation bridge and the coverage-cliff flags fresh per quarter from `shop.as_of(t)`, mirroring the property `features_jobs.compute` already had (its dedupe is backward-looking-only by construction) and adding the equivalent unit-level delete-the-future test for spend (`tests/test_features.py::test_features_spend_unit_delete_the_future`). `estimation/qa.py`'s `detect_coverage_cliff` was also bounded defensively to the horizon actually present in whatever slice it is handed, rather than always walking the full 12-quarter calendar, so it no longer depends on every caller truncating correctly downstream. This fix changed real numbers, not just narration: rank quality by tier, the inflection precision/recall grid, spend's lead-lag detection counts, the shutdown and disclosed-acquisition outcome tables, and the seed-12 robustness numbers all moved by fractions of a point to several points, reported above as measured from the corrected run. What did not move: `outputs/qa_report.md` (a full-history diagnostic that legitimately uses the whole run's data, not a point-in-time production read), the tagger report, the coverage-tier mix at the final scored quarter, jobs' and web's own lead-lag numbers, and funding validation. No generator parameter, plant spec, composite weight, shrinkage constant, or threshold was touched; only the temporal scope of two QA detectors' inputs changed.

The fourth is the same species of bug as the third, found in the sibling module by looking for the same shape. `estimation/features_web.py` ran the bot-spike no-corroboration check once per production run, from `shop.as_of(final_q)`: the spend it corroborated against was resolved through a descriptor-fragmentation bridge built with full-run hindsight, and, more consequentially in this dataset, its quarterly spend totals were complete in hindsight but not at their own close (the panel's one-month publication lag means a quarter's last spend month is never visible as of that same quarter's end). The fix mirrors the third exactly: the bridge, the resolved spend, and the corroborating jobs and spend growth reads are re-derived per quarter t from `shop.as_of(t)`, with the matching unit-level delete-the-future check in `tests/test_features.py::test_features_web_unit_delete_the_future`, built on a fixture where a post-t bridge genuinely flips quarter t's keep-or-correct decision (the committed world's spike and fragmentation plants sit on unrelated vendors, so the bridge half of the leak is latent here; the test was verified to fail against the pre-fix implementation). What moved in this dataset is the lag half, and it cuts the opposite way from the third fix: honestly time-fenced, a spend-covered vendor's quarter-t corroboration compares a two-month partial quarter against a complete prior one, a built-in log(2/3) = -0.41 skew that clears the 0.35 no-move threshold by itself, so seven spike corrections the hindsight run applied are now withheld, including the planted V0019's 2024-04 month: the production feature read applies 42 of the 49 corrections the full-history diagnostic in `outputs/qa_report.md` reports (that report is unchanged and legitimately full-history, as before; V0019's quarter flags did not change either way because its uncorrected May month already saturated the web percentile). Downstream movement, reported as measured: 206 of 5,040 vendor-quarter composites moved, 14 by more than one point, the largest V0241 2025Q2 (92.3 to 57.7); seven accel/stall flags flipped; rank quality by tier moved from 0.698/0.510/0.314 to 0.700/0.510/0.312 (blended 0.480 to 0.479); three cells of the inflection grid moved by one flag each at both k values; one lead-lag detail row moved (V0241's web stall detection, 2025Q1 to 2025Q3) with every summary median, detection count, and rate unchanged; three shutdown-detail t-2 composites moved without changing the 56.5% bottom-quartile share, the 25.7 median, or the above-50 trio; and the robustness report's numbers moved as re-listed below. What did not move: `outputs/qa_report.md`, the tagger report, `coverage_matrix.csv`, `level_bands.csv`, the lead-lag summary table, and the funding and disclosed-acquisition validations. As with the third fix, no generator parameter, plant spec, composite weight, shrinkage constant, or threshold was touched; only the temporal scope of one QA corrector's inputs changed.

Post-freeze robustness, all labeled as such, computed in `robustness_check.py` and committed in `outputs/robustness_seed_check.md`:

- **Seed-12 rerun**: the tier rank-quality gradient survives in ordering (frozen seed A 0.700 > B 0.510 > C 0.312; seed 12 A 0.553 > B 0.522 > C 0.279, monotonic in both seeds) but the margin between A and B collapses under seed 12, from 19 points to 3, a much closer call than the frozen run alone would suggest and reported as such rather than rounded up to "the gradient holds." Jobs' 2-quarter lead over revenue is exactly stable across seeds. Web and spend's lead ordering does **not** survive (they swap between 2.5 and 3.0 quarters); more strikingly, the descriptor-fragmentation plant is **not caught under seed 12** (0 bridges found, vs 2 under the frozen seed, itself now only caught three quarters after the plant fires, see the honesty-protocol fix above). Both are reported as measured failures of generalization, not smoothed away: a QA rule tuned against one seed's noise draw is not guaranteed to survive a different one, which is itself the honest lesson of running this check at all.
- **Threshold sensitivity** (10 / 15 / 20-point delta, k=2, floor/ceiling held fixed at the frozen 55/45 so only the delta moves, population-pooled across type and tier, `tests/test_inflection.py` reproduces these exactly): precision rises smoothly (10.6% -> 12.7% -> 14.7%) as recall falls (85.8% -> 81.5% -> 71.2%) and flag volume drops (2,100 -> 1,669 -> 1,255). No cliff, no threshold that looks obviously "right"; the frozen 15-point choice (the middle column, identical to the headline k=2 grid's population totals) sits in the middle of a smooth tradeoff.
- **Equal-weights composite** (1/3 jobs, web, spend instead of 0.35/0.20/0.45, `tests/test_composite.py` reproduces these exactly): the tier gradient survives (A 0.720, B 0.493, C 0.312, tier C is unchanged since it is usually built from a single source regardless of weighting) with only a few points of movement in A and B, so the headline gradient is not an artifact of the specific frozen weights.
- **Shuffle test** (in `tests/test_evaluation_math.py`): permuting composites within quarter collapses a genuine 0.8+ Spearman correlation to under 0.15, confirming the rank-quality metric is actually measuring something and not a construction artifact.

## Limitations, stated plainly

- The job-tracking curve is calibrated exactly to three stated reference points (25% at 15 employees, 50% at 40, 90% at 200); applied to this population's actual (smaller-skewed) headcount distribution, it yields 42.9% of vendors tracked covering 70.7% of employment, both below the design's own rough expectation (~62% / ~85%). Reported as measured, not re-tuned to hit the target.
- The relist-collapse window absorbs 3,683 background postings population-wide, not "a handful": most are coincidental title-plus-location collisions from a deliberately narrow title bank (13 engineering titles, 4 locations), not real re-lists. A real ATS-backed fingerprint would use a stable requisition id and not have this problem; this dataset's title bank makes the correction more expensive than a real one would be.
- The fragmentation and repost-storm plant vendors are force-included in their exhaust channel (spend-in-channel, jobs-tracked) rather than left to the population draw, so the plant is guaranteed visible; disclosed here as a generator convenience, not discovered by the shop.
- Inflection precision is genuinely weak (7-22%): the composite's percentile-rank construction is more volatile quarter to quarter than the underlying archetypes are, so the +/-15-point rule fires on ordinary re-ranking noise far more often than on real regime changes. Recall stays healthy because true transitions are usually large; precision does not, because so are plenty of non-events. The threshold-sensitivity check above shows this is a smooth tradeoff, not a bug at one specific number.
- No uncertainty intervals on the composite. A panelist-style bootstrap does not transfer cleanly to a three-source percentile composite with tier-dependent shrinkage; this is the natural next stage, declined here rather than shipped half-built.
- Hand-set, frozen composite weights (0.35 / 0.20 / 0.45), not learned: 420 synthetic vendors is not enough signal to fit a weighting without it grading its own homework.
- QA finds exactly the four pathologies its author planted (a floor on difficulty, not a ceiling), and the seed-12 check above shows even that floor is not guaranteed to hold under different noise.
- The level-band chain (`estimation/levels.py`) uses one fixed, deliberately crude assumption for the whole world (2% panel share, fixed dollars-per-visit and employees-per-open-role by segment); it is meant to be humbled by the disclosed-acquisition table, and it is.
- 349 of 5,040 level-band rows (6.9%) carry `level_method == "none"`: zero sources observed that vendor-quarter. These are stamped `level_band == "no_data"`, a non-size label distinct from the real bands, rather than folded into `<1M`; nothing downstream reads `level_method` to filter or reweight them, so a consumer of `level_bands.csv` who ignores the method column and only reads the band column will see `no_data` rows sitting alongside the six real bands and should treat them as missing, not as a measured size.
- Single-machine scale, method over deployment. Nothing here estimates any real company, and the vendors do not exist.

This is descriptive measurement research on synthetic data; it is not investment advice.
