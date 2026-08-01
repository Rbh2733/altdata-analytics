# mlb-pipeline-analyzer

A minor-league readiness score, computed honestly from public data, for the
players on three real Top 100 prospect lists (2022, 2023, 2024).

For every ranked prospect, the pipeline computes an age-adjusted,
position-adjusted minor-league production WAR, season by season across his
minor-league career, calibrated so that a score above zero means his
translated production alone already beats a freely available
replacement-level major leaguer. For players who reached MLB, the final
reading is computed as of the day they arrived, from game logs cut off the
day before their debut, so the score never sees a single post-debut game.

What this project deliberately does not do yet: grade the score against
MLB outcomes. That comparison layer is designed and parked by the owner's
sequencing decision. Nothing here claims the score works. The outputs are
the score itself, its components, and a calibration table that shows its
known biases plainly.

## The chain, per player, per level, per season

1. wOBA from the full component line (FIP for pitchers).
2. His absolute run-production rate in his own league's terms, the league's
   measured runs per plate appearance plus his wOBA gap converted to runs.
3. Translated to MLB terms with the level's translation factor, then
   compared against the real MLB average rate of the same season.
4. Replacement offset, 20.5 runs per 600 PA (per 600 batters faced for
   pitchers, an in-house symmetry choice, disclosed).
5. Position adjustment, standard constants scaled to games played.
6. Age credit per year younger than the level's measured average age,
   capped at three years, reported as its own severable column.
7. Runs to wins at ten per win.

Completed seasons use season totals. Debut seasons use game logs truncated
at the debut date. Seasons after the debut are excluded entirely.

## Constants and their provenance

Every constant lives in `constants.py` with its citation attached.

| Constant | Value | Source |
|---|---|---|
| Translation factors | AAA .78, AA .68, A+ .58, A .49, SS-A .40, ROK .34 | Clay Davenport league difficulty ratings, collapsed to levels; corroborated by Szymborski (AAA .82), Hall of Miller and Eric (.80/.72), Rosenblum (.825 wOBA) |
| Age credit | 25 wRC+ pts/yr (A-AA hitters), 1.0/0.5 FIP runs (pitchers), AAA takes half AA | Stoltz, Excessive Prospect Analysis 2022; AAA taper in-house, direction per KATOH and Davenport 2025 |
| wOBA weights | FanGraphs 2023 constants, scale 1.204 | FanGraphs guts table |
| Replacement | 20.5 runs per 600 PA | FanGraphs unified replacement convention |
| Position adjustment | C +12.5 to DH -17.5 per 162 games | standard published convention |
| Runs per win | 10 | standard approximation |

## Honesty section

Things that were wrong, are generous, or are in-house in this build,
stated rather than hidden.

1. **A calibration flaw was caught before any code was written.** The first
   draft of the chain translated only the runs-above-level-average residual,
   which scores a dead-average Triple-A regular at +2.05 wins per 600 PA.
   It was replaced with the whole-rate construction above. The correction
   is logged, not erased.
2. **An adversarial review of the built pipeline found four more defects,
   all fixed with regression tests the same day.** The stats API emits a
   blank-team aggregate row beside per-team rows for multi-team seasons and
   the pipeline summed both, exactly doubling 40 player-seasons (one player
   showed 876 PA in 210 games). The positional adjustment read the API's
   current-day position label, which docked a minors catcher at the DH rate
   because of a post-debut relabel; it now uses the position on the
   player's earliest ranking-list row, pre-debut by construction. The wOBA
   scale shipped as 1.157, the 2019 value, mislabeled 2023; the 2023 value
   is 1.204. And a sub-minimum debut-season tune-up blocked the carry to a
   player's last full scored season, printing refusals for players with
   rich prior years.
3. **The age credit, not the translation factor, is the dominant source of
   generosity.** Measured in the report, the credit averages roughly three
   times the base signal across scored seasons, and about a quarter of
   crossing seasons cross on the credit alone. It is a predictive-weight
   equivalence (Stoltz 2022), larger than what open-source implementations
   use, and it ships as its own column so it is always severable.
4. **Triple-A readings run generous.** Today's inflated Triple-A run
   environments meet a 2016-vintage translation factor, and the calibration
   table in every output shows the result. Where zero really sits is a
   question for the grading layer, not an assumption.
5. **Dominican Summer League stints are excluded from scoring.** No cited
   translation factor covers the DSL, and the rookie-level age baseline
   pools it with US complex ball, which let DSL teenagers max the age cap
   against leagues they never played in.
6. **Two of 300 ranking rows are resolved by hand.** Two genuine name
   collisions (two real Greg Joneses, two real Jacob Wilsons) are declined
   by the matcher, correctly, and resolved by a curated override table with
   written provenance (`data/raw/manual_overrides.csv`), labeled
   `manual_override` and excluded from the matcher's earned accuracy.
7. **Production only, with season-level league context.** No defense, no
   park effects, no baserunning beyond steals, so a glove-first shortstop
   is undersold by construction. The player's own inputs are strictly
   pre-debut, while league baselines and level average ages are
   full-season aggregates per the season-totals design ruling.

## Run order

```
python scripts/ingest_prospects.py     # xlsx -> prospect_rankings.csv
python scripts/fetch_universe.py       # multi-season player universe
python scripts/build_crosswalk.py      # names -> ids, with metrics
python scripts/fetch_stats.py          # careers, debut logs, baselines, ages
python scripts/compute_readiness.py    # the score
python scripts/write_report.py         # the report
python -m pytest tests/                # the proofs
```

All API responses are cached to `data/cache/` (gitignored), so a rerun
costs zero network calls and the test suite runs offline.

## Tests

The load-bearing one is `tests/test_no_future_leak.py`, which feeds a
synthetic career laced with five kinds of post-debut poison through the
real production code path, physically deletes the poison, and requires the
readiness output to be byte-identical, with vacuity guards proving the
poison would have mattered and the clean career actually scores. The
matcher carries a 19-case adversarial suite of real name traps, including
two real players separated only by an accent and a collision whose only
correct answer is to decline.

## Data and terms

All data comes from the public MLB Stats API, fetched politely (throttled,
cached, no bulk redistribution) for individual, non-commercial research.
Raw responses are not redistributed in this repository. Rankings are from
publicly published Top 100 prospect lists, used as identifiers and
evaluation cohorts.
