# mlb-pipeline-analyzer

A minor-league hitter readiness score, computed honestly from public data,
for the hitters on four real Top 100 prospect lists (2022, 2023, 2024,
2025).

**Scope: hitters only.** Pitcher evaluation was built, tested, and
researched extensively (FIP-based translated WAR, role and workload
diagnostics), but pitching needs a genuinely different WAR construction
than hitting, one that hasn't been validated against real published
sabermetric research to this project's own citation standard yet. Rather
than ship an unvalidated fix, that work is paused, not abandoned: it is
fully preserved, code and tests and all, at the `pitcher-work-2026-08-02`
git tag in this repository's history, and is being developed separately.

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

1. wOBA from the full component line.
2. His absolute run-production rate in his own league's terms, the league's
   measured runs per plate appearance plus his wOBA gap converted to runs.
3. Translated to MLB terms with the level's translation factor, then
   compared against the real MLB average rate of the same season.
4. Replacement offset, 20.5 runs per 600 PA.
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
| Age credit | 25 wRC+ pts/yr (A-AA), AAA takes half AA | Stoltz, Excessive Prospect Analysis 2022; AAA taper in-house, direction per KATOH and Davenport 2025 |
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
2. **The team-stats fetch layer was silently building incomplete baselines
   at Rookie level, found 2026-08-01.** MLB's team-stats endpoint caps
   results at 50 rows with no limit parameter passed, and Rookie ball
   genuinely fields 81-90 teams across seasons, so every league-average
   baseline built from that level was quietly missing 22-45% of the real
   team population. Every other level fields 22-30 teams, comfortably
   under the cap, so this was invisible everywhere else. Fixed in
   `ingestion/api.py`'s `teams_stats()` by requesting `limit=200` and
   failing loudly (`RuntimeError`) if the API ever reports more teams than
   it returns, rather than silently building an incomplete baseline again.
   Regression-tested in `tests/test_teams_stats_completeness.py`.
3. **An adversarial review of the built pipeline found four more defects,
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
4. **The age credit, not the translation factor, is the dominant source of
   generosity.** Measured in the report, the credit averages roughly 1.67
   wins against 0.60 wins of base signal across scored seasons (about 2.8x),
   and almost no crossing seasons cross on the credit alone (2 of 423,
   under 1%) for this hitter population. It is a predictive-weight
   equivalence (Stoltz 2022), larger than what open-source implementations
   use, and it ships as its own column so it is always severable.
5. **Triple-A readings run generous.** Today's inflated Triple-A run
   environments meet a 2016-vintage translation factor, and the calibration
   table in every output shows the result. Where zero really sits is a
   question for the grading layer, not an assumption.
6. **Dominican Summer League stints are excluded from scoring.** No cited
   translation factor covers the DSL, and the rookie-level age baseline
   pools it with US complex ball, which let DSL teenagers max the age cap
   against leagues they never played in.
7. **Two of 300 ranking rows are resolved by hand.** Two genuine name
   collisions (two real Greg Joneses, two real Jacob Wilsons) are declined
   by the matcher, correctly, and resolved by a curated override table with
   written provenance (`data/raw/manual_overrides.csv`), labeled
   `manual_override` and excluded from the matcher's earned accuracy.
8. **Production only, with season-level league context.** No defense, no
   park effects, no baserunning beyond steals, so a glove-first shortstop
   is undersold by construction. The player's own inputs are strictly
   pre-debut, while league baselines and level average ages are
   full-season aggregates per the season-totals design ruling.
9. **Center field is valued at shortstop's rate, and secondary "OF" is
   weaker than standalone "OF," per Reid's ruling 2026-08-01, extending
   the multi-position work below.** He put it directly, "SS is to the
   infield as CF is to the outfield," and named a real example, Oneil
   Cruz, a shortstop-caliber defender genuinely moving to center field
   this season. Since ranking lists never print "CF" (verified, zero
   exceptions), a player only reaches that value through a dated,
   reasoned manual review, never automatically, currently 9 players
   (Cruz, Carroll, Crawford, Crow-Armstrong, Rodríguez, Wood, Langford,
   Walker, Rafaela). Separately, "OF" now carries two different values by
   context. Standalone (a player's entire listing is just "OF") keeps the
   original blended value, since a real unflagged center fielder could
   still be sitting there unreviewed. "OF" as a secondary position inside
   a combo, always paired with an infield spot in this data ("SS/OF"),
   drops to the pure corner-outfield rate, Reid's reasoning being that
   this specific combination is the fallback signal of a player who
   didn't stick at an infield spot, not evidence of burner speed. He also
   expanded the manual-review table by 5 more players in the same pass
   (Henderson and Witt pinned to shortstop rather than averaged, Peraza
   moved to the INF bucket, Vargas dropped outfield from his combo
   entirely, and Melendez, deliberately reversed from the earlier
   catcher ruling to outfielder).
10. **Multi-position ranking-list entries are averaged, per Reid's ruling
   2026-08-01, arrived at after two corrections the same day.** 47 of 212
   players were listed with more than one position ("SS/2B"). The old code
   always took whichever was listed first, arbitrarily. The first fix
   tried resolving each case with real games-played data, picking a single
   "winner" position. Reid corrected that twice. Final rule: every
   multi-position listing has its position-adjustment constant averaged
   across all the positions named, infield-only combos included, no
   special-casing, so "SS/2B" is credited the average of shortstop's and
   second base's values, not one or the other. The one exception is a
   small set of cases (7 of the 47) that couldn't be cleanly averaged and
   were reviewed and settled by hand, labeled `reid_confirmed`, dated and
   reasoned in `data/raw/position_overrides.csv`, never blended into the
   automated resolution's own accuracy: three confirmed what real games
   played that season would have suggested (Jung to 1B, Gonzales to 3B,
   Yorke to 3B), two chose a broader outfield credit over a specific
   corner spot on real defensive versatility (Marte, Freeman), and two
   overrode what recent games alone would suggest on real scouting
   knowledge (Walcott stays a shortstop despite a 14-game, DH-only,
   likely-injury-shaped sample, Soderstrom stays a catcher despite 93
   games in left field this season, his real defensive identity). Real
   games-played data (`data/derived/current_position.csv`) still powers
   the separate, display-only `position_today` column, unrelated to any
   of this. Single-position players, including MJ Melendez (the case that
   surfaced this whole question), are entirely unaffected, there is no
   ambiguity in a single listing to resolve. One exception inside the
   single-position case, a player listed simply "INF" is graded at
   shortstop's value directly rather than a blended average, since an
   unspecified "he can play the infield" label is itself the high-value
   signal a scout is making, not a hedge that should be watered down. An
   idea about valuing a real starting center fielder the way a shortstop
   is valued was raised and explicitly deferred, small sample, not
   significant at this stage.
11. **Two scores, not one, per Reid's ruling 2026-08-01.** A player with a
   short but excellent pre-debut window scores unremarkably on total value
   banked, simply because a short window caps how much value there is to
   bank, even when the quality of his production was elite. Rather than
   redefine the whole tool around one answer, both numbers now ship side
   by side, everywhere a debut-day or season reading appears. **Readiness
   Score** is total value banked, naturally larger the more he played.
   **Rate Score** restates the same performance per 600 PA, a
   full-season-equivalent workload, how good he was per opportunity,
   independent of how much opportunity he got. They can and do disagree
   sharply for exactly that kind of player. Neither is "the real one." No
   new computation was needed, `rate_per_600` already existed at the
   season level, it had simply never been given equal billing.
12. **A fourth cohort, 2025, was added 2026-08-01, growing the population
   from 212 to 267 unique players.** No pipeline logic changed, ingestion
   already looped over however many tabs existed. One new real name
   collision surfaced (a repeat of the same Jacob Wilson ambiguity from
   the 2024 cohort, under a new rank), resolved the same way. Alongside
   it, a rule reversal for players who repeat across cohorts, his most
   recent listing now wins, not his earliest (the opposite of the
   original design, which reasoned earliest was closer to pre-debut and
   less contaminated). Checked against the real data before shipping,
   currently changes zero scores, since no repeat player's listed
   position actually differs across years, but it is the correct
   standing rule for whichever cohort is added next.

13. **Scoped to hitters only, 2026-08-02.** Pitcher scoring (FIP-based
   translated WAR, plus WHIP/BABIP/BB9/K%/BB%/GB% and role/workload
   diagnostics) was built, tested, and researched extensively across
   several sessions, including a real bug catch (item 2 above) and a real
   correctness fix (a role label that could misread a strict pitch count
   as a bullpen conversion, caught on a real case and fixed with a new
   `ip_per_appearance` diagnostic). It was paused, not because it was
   wrong, but because a proposed fix for a real, measured hitter/pitcher
   scoring gap turned out to rest on invented, uncited constants once
   checked against real published sabermetric research. Rather than ship
   that or leave a half-validated pitcher score in a public tool, the
   pitcher code and its full test suite are preserved intact at the
   `pitcher-work-2026-08-02` git tag, and pitcher evaluation is being
   developed separately with the same citation discipline as every other
   number in this file.

## Run order

```
python scripts/ingest_prospects.py       # xlsx -> prospect_rankings.csv
python scripts/fetch_universe.py         # multi-season player universe
python scripts/build_crosswalk.py        # names -> ids, with metrics
python scripts/fetch_stats.py            # careers, debut logs, baselines, ages
python scripts/fetch_current_position.py # real games-by-position, for disambiguation
python scripts/compute_readiness.py      # the score
python scripts/write_report.py           # the report
python scripts/write_position_review.py  # flagged multi-position players
python scripts/build_viewer_sheet.py     # simple sheet, both scores, per player
python -m pytest tests/                  # the proofs
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
