# Glossary, outputs/ spreadsheets

Plain-language column reference for the four CSVs in this folder. See
`readiness_report.md` for the narrative version and the project README for
where every constant comes from.

Core idea to hold in mind while reading any of these: **base** is the score
from production alone, **age credit** is a separate bonus for being young
for the level, and **adjusted (adj)** is base plus age credit. Above zero
means the tool judges that production (translated to MLB terms) already
beats a freely available replacement player.

**Two different scores, not one, per Reid's ruling 2026-08-01.** Readiness
Score is total value banked, how much he'd already proven by a given day,
naturally larger the more he played. Rate Score restates the same
performance as if he'd gotten a full 600-PA season, how good he was per
opportunity, independent of how much opportunity he actually got. They can
disagree sharply for a player with a short but excellent pre-debut window,
a modest Readiness Score (a small window to bank value in) next to a
high Rate Score. Neither is "the real one." They answer different
questions.

**Scope: hitters only, as of 2026-08-02.** These CSVs no longer carry any
pitching columns or rows. Pitcher scoring is preserved at the
`pitcher-work-2026-08-02` git tag, see the project README.

---

## readiness_summary.csv

One row per prospect. The headline file.

| Column | Meaning |
|---|---|
| `mlbam_id` | The player's official MLB ID number. |
| `player` | Name. |
| `position` | Position(s) as printed on the player's earliest ranking-list appearance. Can be more than one, slash-separated (e.g. "SS/2B"), when the list itself named multiple fits. |
| `position_used_for_scoring` | The position(s) actually feeding his position credit. Equal to `position` when only one was listed and untouched. When more than one was listed, this shows every one being averaged together, unless a manual review overrode it. |
| `position_resolution` | How `position_used_for_scoring` was decided. `single` = only one position was ever listed, nothing to resolve (this includes players listed simply "INF," who are graded at shortstop's value directly, see the README). `averaged` = more than one position was listed, and the position credit is the plain average across every one of them (a listed "OF" alongside an infield spot is valued as a weaker, fallback-outfield spot in that average, see the README). `reid_confirmed` = a case reviewed and settled by hand, including every player confirmed as a real center fielder, graded at shortstop's value (see `data/raw/position_overrides.csv` for the reasoning behind each one). |
| `position_today` | The position he's actually playing right now, measured from real games played this season, not a database label (that label was found to run stale, see README). Reference only, this column itself is not used in the score. |
| `cohorts` | Which Top 100 list(s) the player was ranked on, and at what rank (e.g. `2022#97` = ranked 97th on the 2022 list). |
| `mlb_debut_date` | Date of the player's first MLB game. Blank if he hasn't debuted. |
| `n_seasons_scored` | How many of his minor-league seasons had enough playing time to produce a real score (see the sample-size note below). |
| `first_crossing_season` | The first season his adjusted score (base + age credit) went above zero. Blank if it never did. |
| `first_base_crossing_season` | Same, but production alone, no age credit. Blank if it never did. |
| `debut_day_adj_war` | **Readiness Score.** His total value banked (base + age credit) as of the day he arrived in MLB, over however many at-bats or innings he actually had. Grows with playing time. |
| `debut_day_base_war` | Same reading, production only, no age credit. |
| `debut_day_rate_per_600` | **Rate Score.** The same debut-day performance restated as "wins per 600 plate appearances," a full-season-equivalent workload, so a guy with a short hot stretch and a guy with a long good season can be compared on quality alone, independent of how much either one actually played. Higher is better. Blank when even the rate couldn't clear the sample-size floor (see `outputs/readiness_at_debut.xlsx`, shown there as "n/a, sample too small"). |
| `debut_reading_basis` | Where the debut-day number came from. `debut_season` = built from his own debut-year games. `carried_from_20XX` = his debut year didn't have enough at-bats, so his last full prior season stands in. `_over_Npa_tuneup` appended means a short debut-season stint existed but wasn't big enough to trust, so the fuller earlier season is used instead. `never_debuted` = hasn't reached MLB. |

---

## readiness_by_season.csv

One row per player per season. The full season-by-season readiness curve
that `readiness_summary.csv` boils down to one number.

| Column | Meaning |
|---|---|
| `mlbam_id`, `player`, `season` | Who, and which year. |
| `n_stints` | How many separate stops he had that season (levels, teams). |
| `n_scored` | Of those stops, how many had enough playing time to score. |
| `volume` | Total plate appearances across only the stops that scored. |
| `volume_all` | Same total, but including stops that didn't have enough playing time to score. Shows what got left out. |
| `base_war` | Production-only score for the whole season, summed across scored stops. |
| `age_credit_war` | Age bonus for the whole season, summed across scored stops. |
| `adj_war` | `base_war` + `age_credit_war`. The season's headline number. |
| `rate_per_600` | **Rate Score**, for this one season. The season score restated per 600 PA, for comparing seasons of different length on quality alone. Blank if the season didn't clear the minimum playing time to trust a rate. |
| `verdict` | `scored` if the season produced a real number. Otherwise, a plain-English refusal like "76 of 97 PA+BF scored, need 100," meaning there wasn't enough data to trust a season-level rate, so none is reported rather than a shaky one. |
| `truncated` | `True` if this was the player's debut season, meaning only games before his MLB call-up were counted, not the whole year. |

---

## readiness_stints.csv

One row per player per level per season, the finest-grained file, one
level below `readiness_by_season.csv` (a player who spent time at two
levels in one season gets two rows here, summed into one row there).

| Column | Meaning |
|---|---|
| `mlbam_id`, `player`, `season`, `level`, `sport_id`, `group` | Who, when, what level, MLB's internal level code, and the stat group (always `hitting`). |
| `pre_debut_truncated` | `yes` if this stint's games were cut off the day before his MLB debut. |
| `verdict` | `scored` or `insufficient_sample` (not enough playing time at this one stop to trust a number). |
| `detail` | Plain-English playing-time count, e.g. "223 PA" or "76 PA (need 100)." |
| `pa` | Plate appearances. |
| `g` | Games played. |
| `woba` | Weighted on-base average for the stint, a single number summarizing all of a hitter's offense (walks, hits by type, home runs), weighted by how much each actually contributes to winning. |
| `native_rate` | The player's run-production rate stated in his own level's terms, before any MLB translation. |
| `raa_mlb` | Runs above (or below) an average MLB player, after translating his level performance to MLB terms. The core production number. |
| `wsb` | Runs added by stolen-base activity (translated to MLB terms). |
| `rep` | The "replacement level" credit, a standard baseline adjustment reflecting that even a bare-minimum MLB fill-in player has some value. |
| `pos_adj` | Bonus or penalty for defensive position (e.g. shortstop gets a bonus, first base a penalty), scaled to games played. |
| `age_years` | Years younger (positive) or older (negative) than the level's actual average age that season, capped at 3 either direction. |
| `base_war` | This stint's production-only score, in wins. `(raa_mlb + wsb + rep + pos_adj) / 10`. |
| `age_credit_war` | This stint's age bonus, in wins. |
| `adj_war` | `base_war + age_credit_war`. This stint's final readiness contribution. |

---

## position_review_needed.csv

Not a scores file. A short list, one row per player whose real current
position matches none of the positions his ranking-list entry originally
named. These players are scored on the old first-listed position for now
(not guessed at further) until reviewed by hand.

| Column | Meaning |
|---|---|
| `player`, `listed_positions` | Who, and what the ranking list originally said. |
| `currently_scored_as` | Which of the listed positions his score is using in the meantime. |
| `real_current_position` | What he's actually playing now, and `games_at_that_position`, `season_measured` for how solid that read is. |
| `all_positions_played` | His full games-by-position breakdown for that season, most-played first, so you can see the whole picture, not just the top spot. |
| `reason` | Why he's flagged, no match among the original list, or no current-season data to check against yet. |

## calibration_table.csv

Not about any individual player. This shows what a perfectly
**average** regular player at each level and season scores under this
tool's math, so you can judge how generous or strict the zero line
actually is. If the "average" reading at a level is well above zero, that
level's readings run generous; if it's near zero, the level is well
calibrated.

| Column | Meaning |
|---|---|
| `level`, `season` | Which level and year. |
| `avg_hitter_war_per_600pa` | What a league-average hitter at this level scores, per 600 plate appearances. |
| `avg_hitter_war_per_600pa_blended` | The same number recomputed on a slightly different translation scale (see README), included as a sensitivity check rather than a second opinion to prefer. |

---

## Reading the files together

Start with `readiness_summary.csv` for any one player's headline story.
Drop into `readiness_by_season.csv` to see his year-by-year trajectory.
Drop into `readiness_stints.csv` only when you want to see exactly which
level, and which raw numbers, produced a given season's score. Use
`calibration_table.csv` any time a score looks surprisingly high or low,
to check whether that's the player or just how generous that level runs.
