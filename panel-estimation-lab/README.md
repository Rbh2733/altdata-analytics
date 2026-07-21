# Panel Estimation Lab

Consumer transaction panels are biased samples of the real economy, and the craft of alternative-data research is turning them into precise estimates of company KPIs. This lab builds a world where the truth is knowable: a simulated population of 200,000 consumers transacting with six fictional subscription and e-commerce services, a deliberately broken observation panel sampled from it, and an estimation stack that provably never peeks at the answer key, then scores itself against it. Every number in this README was produced by this code, and the reports in `outputs/` ship with the project so the numbers are checkable without running anything.

Naive scale-up gets quarterly revenue wrong by **30.6%** on average. The full method gets it to **2.7%**, and its 90% intervals contain the truth in **43 of 48** scored cells. The estimator never sees the truth for the quarter it is estimating, and a test enforces it.

This is descriptive measurement research on synthetic data; it is not investment advice.

## What this demonstrates

- **Precise estimates from sample and panel data, against known ground truth.** Four estimators of increasing sophistication, backtested over 8 quarters x 6 companies, with per-cell error committed to `outputs/scorecard.csv`.
- **Cohort, concentration, penetration, and competitive analyses in SQL.** A DuckDB layer over the post-QA panel: retention triangles, weighted penetration by demographic segment, HHI, and share-shift cuts, in `outputs/sql_report.md`.
- **A natural instinct for spotting data anomalies, made mechanical.** Four planted feed pathologies, each detected by fixed data-independent rules and reported with dates and magnitudes in `outputs/qa_report.md`.
- **Complex data methodologies, honestly evaluated.** Raking to partial census margins, spell reconstruction under imperfect observability, ratio calibration to reported actuals, panelist bootstrap intervals, and a scorecard that prints the failures alongside the wins.
- **A leakage guard enforced by package structure and tests**, not by promises.

## The world, and why synthetic

The method is only demonstrable where truth is known. On real data this scorecard cannot exist: nobody hands you the true subscriber count to grade against. So the lab simulates one. All six companies are fictional; any resemblance to real brands is accidental and unintended.

| company | model | dynamics |
|---|---|---|
| Streambird | video streaming subscription | steady grower; raises price 11.99 to 13.99 in 2024Q3 with a churn spike |
| Aurelo | music streaming subscription | mature, adoption slowly fading |
| Bramblebox | meal-kit subscription | fast grower, 9% monthly churn; young high-income skew |
| Pinefort | retail membership plus purchases | steady, mid-age mid-income |
| Vantry | e-commerce marketplace | grower, Q4 seasonality, one big promo day |
| Glimmerly | fashion e-commerce | flat trend, promo-driven swings, wallet-skewed payments |

Consumers carry demographics (age band x income x region, 48 cells), a shared heavy-user frailty factor, and per-service adoption and churn hazards with distinct demographic signatures. Truth KPIs (revenue, actives, gross adds, churn rate, ARPU, market share) are exact aggregations of population state, committed to `data/truth/truth_kpis.csv`.

Two deliberate choices shape the estimation problem:

- **The census product publishes partial joints only**: the age x income table (12 cells) and the region margin (4 cells), never the full 48-cell joint. This forces raking rather than direct post-stratification, which is how census products actually behave.
- **Companies report revenue and actives only**, rounded to 0.1M and to the nearest thousand (`data/public/reported_actuals.csv`). Churn, ARPU, and share are not reported; the shop estimates what is not disclosed, which is the industry's actual point. The rounding puts a precision floor under calibration, most visible for the smallest company (Aurelo's reported quarters range from 0.6M to 1.0M, so the rounding alone is worth 5 to 8%, and the low quarters sit exactly in the early calibration windows).

## The panel and its defects

The panel targets 6,000 recruits and lands 5,917 at launch (recruitment is itself stochastic), skewed young and high-income (that cell joins at roughly 3.3x the rate of 60+ low-income). Panelists thin by about 1% per month, young ones faster, and each holds 1 to 3 payment instruments of which the panel observes only an enrolled subset (cards enroll at 0.80, the wallet at 0.40, minimum one). On top of that, each panelist has a capture factor (Beta(8,2)) that thins observed rows. Company identity arrives only through merchant descriptor strings. A seventh descriptor, SNACKPOST MARKET, is out-of-scope spend and doubles as the control the alias detector must not merge.

Four pathologies are planted in the feed (never in the truth), one per scored year-quarter:

| pathology | quarter | what happened | detected by | cost if uncorrected |
|---|---|---|---|---|
| duplicated feed day | 2023Q3 | every row dated 2023-08-14 (a Vantry promo day) appears 3x: 2,506 extra rows | 66.7% content-duplicate rate, volume z-score 43.5 | Vantry's quarter inflated about 24% (13.71M vs 11.05M corrected) |
| recruitment wave | 2023Q2 | 1,500 young low-income panelists join in 2023-04 | 29.2% join share, composition L1 distance 0.167 | m1's static denominator jumps 27.5% quarter over quarter |
| supplier outage | 2024Q1 | card_B (about 31% of rows) delivers zero rows for 12 days | a slice otherwise never at zero hits zero | m2 revenue error 25.6% vs 21.5% corrected |
| descriptor change | 2024Q2 | BRAMBLEBOX becomes "BRMB*BOX 0520" plus per-row suffix noise | volume collapse plus a new core whose amounts (59.99 = 59.99), panelist overlap (73.3%), and cadence (1.0x) match | raw grouping reports Bramblebox revenue of 0 from 2024Q3 onward |

Detection thresholds are fixed in `estimation/qa.py` before any run and never reference the plant parameters, which live in `simulation/params.py` where the estimation layer cannot import them.

## Architecture and the leakage guard

```
panel-estimation-lab/
  config.py            seed, calendar, paths, scale (importable by all layers)
  simulation/          THE WORLD: params.py, population, market, truth, panel
  estimation/          THE SHOP: loader, qa, weights, methods, calibrate, uncertainty
  evaluation/          THE JUDGE: scorecard, report
  sql/                 analysis.sql + DuckDB runner (shop-side)
  data/
    panel/             what the shop sees: transactions, panelists
    public/            census margins, reported actuals, company descriptors
    truth/             what only the judge sees
  outputs/             estimates, scorecard, qa_report, sql_report, metrics
  tests/               46 tests, including the fence posts below
```

Three enforcement layers keep the estimator honest:

1. **Package boundary.** No module under `estimation/` or `sql/` imports `simulation` or `evaluation`, and no string literal in those packages names a truth path; `evaluation/` never imports `simulation`. Checked by AST walk in `tests/test_import_boundary.py`. World and pathology parameters live in `simulation/params.py`, which only the simulation package imports; the shared `config.py` holds nothing worth leaking.
2. **Runtime path guard.** Every estimation-side file read goes through `estimation/loader.py`, which resolves the path and raises PermissionError outside `data/panel/` and `data/public/`. A test attacks it directly (including a `..` traversal), and a second test monkeypatches `builtins.open` during a full rung-4 run and asserts no opened path is under the truth directory.
3. **Temporal guard.** Reported actuals are reachable only through `loader.reported_before(quarter)`, which returns strictly earlier quarters. The delete-the-future test rebuilds the pipeline with every reported row at or after the target quarter physically removed from the file and asserts the target quarter's rung-4 estimates are identical: the future is not merely unused, it is unnecessary.

`run_all.py` runs generation, estimation, and evaluation as separate steps; estimation receives only the panel and public paths.

## The methods ladder

All four methods share one interface and run for all 12 quarters; 2023Q1 through 2024Q4 are scored (2022 is warmup that seeds calibration history). MAPE over 48 cells per KPI, median APE in parentheses:

| kpi | m1 naive | m2 weighted | m3 weighted+QA | m4 calibrated |
|---|---|---|---|---|
| revenue | 30.6% (29.8%) | 24.9% (21.1%) | 20.8% (20.6%) | 2.7% (1.8%) |
| actives | 21.2% (16.9%) | 15.5% (9.1%) | 6.5% (6.0%) | 3.2% (2.5%) |
| arpu | 22.5% (25.2%) | 20.2% (16.5%) | 19.5% (18.4%) | 3.6% (2.1%) |
| market_share | 13.2% (8.2%) | 9.2% (4.0%) | 3.3% (2.8%) | 2.5% (1.6%) |
| gross_adds | 104.1% (36.3%) | 95.3% (32.6%) | 113.1% (69.5%) | 113.1% (72.6%) |
| churn_rate | 178.3% (185.8%) | 112.8% (100.1%) | 86.1% (67.8%) | 86.1% (67.8%) |

**m1, naive scale-up.** Raw-descriptor totals times population over *initial* panel size. The static denominator is a deliberate classic mistake: attrition drags the estimate down a few percent per year (34.1% revenue error by 2023Q1), the recruitment wave jumps it 27.5% overnight, and every pathology lands raw. Its per-quarter error trace is the most legible narrative in `outputs/scorecard.md`.

**m2, post-stratification.** Quarterly raking of the active panel to the two published margins, with fixed degenerate-cell collapse rules and weight trimming at 5x the weighted median (the trim guard is armed and logged; in this run no weight ever hit the cap). The payoff is composition: market share MAPE drops from 13.2% to 9.2% and actives improve heavily, because capture roughly cancels in ratios. The payoff is not levels: m2 revenue sits persistently 19 to 26% below truth for five of the six companies (Glimmerly 18.9%, Streambird 19.6%, Aurelo 20.2%, Vantry 22.5%, Pinefort 23.5%), because weighting cannot conjure transactions the panel never observed. The sixth, Bramblebox, is worse still at 44.5%, but for a different reason: without QA, the descriptor change zeroes out its observed revenue from 2024Q3 onward, so its m2 error mixes the capture gap with a missing-data catastrophe that m3 exists to fix. m2 also quietly fixes m1's static denominator; its advantage shows in 2023Q1 and across 2024, while in the wave quarter itself the two land in a near tie, because the wave-inflated numerator happens to cancel m1's downward bias exactly there.

**m3, plus QA corrections.** Dedupe on flagged days, descriptor alias resolution, outage slice reconstruction, and subscription spell logic with a one-month gap tolerance. The outage and descriptor quarters return to m3's own baseline (25.6% to 21.5%, and Bramblebox from a reported 0 back to a continuous series). The duplicate-day quarter is the honest wrinkle: the feed inflation pushed m2 *upward into* its own under-capture bias, so m2's error that quarter was accidentally low (8.2% on Vantry), and removing the duplicates moves m3 back to its own baseline (21.6% that quarter, in line with its 20.8% all-quarter average), which is *numerically worse*. The correction is still right: it removes 2,506 phantom rows exactly, and an estimator that profits from double-counted data is one bug away from disaster. Two wrongs canceling is not a method. The spell logic is also why m3 actives (6.5%) beat m2 (15.5%): a missed monthly charge no longer reads as a cancellation.

**m4, plus ratio calibration.** For revenue and actives, a geometric-mean ratio to reported actuals over the up-to-3 most recent prior quarters, applied to m3; gross adds inherit the actives factor; ARPU and share are re-derived. This is how real shops anchor panel levels, and it is worth 18 points of revenue MAPE here because the capture gap is stable. Its assumptions are stated in `estimation/calibrate.py`, and the scorecard shows where they crack: the designed break (Streambird's price rise) did **not** hurt, because a price change passes through panel amounts and reported revenue alike, leaving the ratio intact; the design intent expected a stale-factor casualty there and none emerged, which is itself a finding. The break that did bite is the recruitment wave: factors for 2023Q2 were learned on the pre-wave panel, and m4's two worst revenue cells are exactly there (Bramblebox +11.0%, Glimmerly +10.1% overshoot). On actives, m4 is worse than m3 in 11 of 48 cells (e.g. Streambird 2023Q1, 2.3% to 5.7%): calibrating to disclosure-rounded actives can inject more noise than it removes when m3 is already close.

What no rung fixes, stated plainly: gross_adds is wrong by about 2x everywhere because capture gaps manufacture false subscription starts (m3's spell starts are inflated by panelists whose charges vanish for two-plus months), and churn_rate carries the mirror-image inflation. Both are printed in the scorecard rather than dropped from it.

## Uncertainty

Panelist-level nonparametric bootstrap, B=400, seeded: the panelist is the sampling unit, and inside each replicate the entire estimator reruns (weights re-raked, corrections reapplied, calibration factors recomputed from the replicate's own prior-quarter estimates). 90% percentile intervals on revenue and actives for all four methods.

| method | revenue coverage | actives coverage |
|---|---|---|
| m1 | 1/48 (2.1%) | 7/48 (14.6%) |
| m2 | 0/48 (0.0%) | 15/48 (31.2%) |
| m3 | 0/48 (0.0%) | 19/48 (39.6%) |
| m4 | 43/48 (89.6%) | 31/48 (64.6%) |

The m1 through m3 rows are the pedagogical center: a bootstrap measures variance, not bias, so a biased estimator gets tight, confidently wrong intervals. Coverage becomes honest only once calibration removes the level bias, and even m4's actives intervals sit under nominal. Caveats, stated as caveats: the bootstrap conditions on the realized panel and on every modeling choice; it captures sampling noise only; interval validity for m4 leans on the same stability assumptions as the point estimator; and none of these intervals account for the bias model itself being wrong, which in a real panel it always partly is. The coverage counts are also one Monte Carlo draw: rerunning the whole world under a different seed moves them by several cells in either direction, so 43 of 48 reads as "roughly nominal", not as a guarantee.

## The SQL layer

`python sql/run_sql.py` runs five cuts via DuckDB and writes `outputs/sql_report.md`: cohort retention triangles by adoption quarter (weighted, window functions), penetration by age x income segment with unweighted and weighted side by side (the composition correction visible in SQL, not just prose), HHI-style market concentration per quarter, quarter-over-quarter competitive share shifts via LAG, and m4 estimates against reported actuals for prior quarters. The SQL layer runs shop-side and truth is never registered as a view, which is stricter than this repo's sibling lab (vendor-resolution-lab registers labels for its accuracy cut); this lab's whole point is the boundary. The descriptor-bridging theme is the sibling lab's problem seen from the panel side.

## Run it

```
pip install -r requirements.txt
python run_all.py          # generate, QA, estimate, bootstrap, score
python sql/run_sql.py      # analytical SQL over the outputs
pytest                     # 46 tests, including the fence and determinism
```

Python 3.10+; dependencies are numpy, pandas, and DuckDB. Offline, no keys, no network. `run_all.py` takes about a minute and the SQL runner well under that; the committed `data/` (15.2 MB) and `outputs/` (SQL report included) regenerate byte-identically, and `tests/test_determinism.py` proves it by regenerating them and comparing bytes. The SQL report is rendered by a fixed-width formatter in `sql/run_sql.py` rather than DuckDB's console renderer, precisely so its bytes cannot depend on the terminal it was generated in. Paths in this document are relative to `/path/to/altdata-analytics/panel-estimation-lab`.

## Honesty protocol

The generator's parameters and seed were frozen before any estimator was scored; the estimators were debugged against the QA report and internal consistency checks (weights summing to the population, spells well-formed), never against truth; the scorecard ran once and its numbers stand. One bug was fixed after that run and is disclosed: the truth builder's prior-quarter actives lookup indexed the wrong month (an off-by-two in stock-flow bookkeeping), which broke the actives identity test. Fixing it changed truth churn-rate denominators (churn MAPE moved by a few points; every other number was untouched, since the estimator never reads truth). No generator magnitudes, calibration windows, trim caps, gap tolerances, or raking settings were changed after scoring.

## Limitations, stated plainly

- A synthetic world is kinder than reality. Real panels contain unknown unknowns; real bias does not come labeled. The QA layer here finds exactly the pathologies its author planted, which is a floor on difficulty, not a ceiling.
- Dedupe is lossless here by construction: the generator nudges amounts on the planted duplicate day so no legitimate row shares a content key with a phantom. Real feeds contain legitimate identical same-day transactions, so content-key dedupe there trades phantom removal against real-row loss and needs a fuzzier key.
- Capture heterogeneity is modeled as stationary per panelist. Real instrument mixes drift, and the outage correction's stable-mix assumption would degrade under drift.
- The one-month gap tolerance leaks churn error by construction: gross adds and churn rate remain wrong by roughly 2x at every rung, and calibration cannot fix KPIs that companies do not report. The scorecard prints this instead of hiding it.
- Spell reconstruction uses the full committed feed; a true nowcast would have provisional right-edge spells and slightly worse early estimates for the newest quarter.
- The wallet-coverage mechanism designed to make Glimmerly the worst-captured company was partially self-corrected by the minimum-one-enrollment rule (wallet-only panelists are always observed), so the emerged capture gaps (18.9% to 23.5%, excluding Bramblebox, whose m2 error is dominated by the descriptor change rather than by capture) are flatter across companies than designed. Reported as measured.
- Single-machine scale, method over deployment. Nothing here estimates any real business, and the companies do not exist.

This is descriptive measurement research on synthetic data; it is not investment advice.
