"""Delete-the-future for the player's own stat rows.

The rule: none of the player's own stat rows may postdate his MLB debut.
The test builds a synthetic career laced with poison, post-debut rows of
every kind the data can contain, runs the REAL production code path
(compute_player, not a reimplementation), then physically deletes the
poison and runs it again. The two results must be identical to the last
digit. If any poison row was contributing anything, the deletion changes
the output and the test fails.

SCOPE, stated precisely so this test does not overclaim: it proves the
fence on the player's own rows only. League baselines and level average
ages are full-season aggregates by design (the season-totals ruling) and
are held fixed across both runs here, and the positional adjustment takes
the pre-debut ranking-list position by construction (see
test_review_fixes.py for that channel's own regression test).

Poison varieties planted:
  1. a minor-league season split from AFTER the debut season (an optioned-
     down year, the Holliday-2026 case observed in real data)
  2. a minor-league season split IN the debut season (season totals that
     mix pre- and post-debut games, which is why debut seasons must come
     from truncated game logs instead)
  3. a debut-season game log row dated ON the debut date
  4. a debut-season game log row dated AFTER the debut date (a post-
     demotion game)
  5. an MLB season split (never a readiness input at all)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.compute_readiness import compute_player, season_readings

PID = "999001"
PERSON = {
    "mlbam_id": PID, "full_name": "Test Prospect", "birth_date": "2002-04-15",
    "primary_position": "SS", "mlb_debut_date": "2024-05-01",
}

HIT_BASE = {
    (12, 2023): {"woba_lg": 0.320, "rpa": 0.130, "pa": 150000},
    (11, 2024): {"woba_lg": 0.330, "rpa": 0.140, "pa": 150000},
    (11, 2025): {"woba_lg": 0.330, "rpa": 0.140, "pa": 150000},
    (1, 2023): {"woba_lg": 0.315, "rpa": 0.121, "pa": 180000},
    (1, 2024): {"woba_lg": 0.312, "rpa": 0.119, "pa": 180000},
    (1, 2025): {"woba_lg": 0.312, "rpa": 0.119, "pa": 180000},
}
AGE_MAP = {(12, 2023): 24.5, (11, 2024): 26.0, (11, 2025): 26.0}


def _hit(season, sport, pa, hits, **kw):
    row = {"mlbam_id": PID, "group": "hitting", "season": str(season),
           "sport_id": str(sport), "team_name": "T", "league_name": "L",
           "gamesPlayed": str(max(1, pa // 4)), "plateAppearances": str(pa),
           "atBats": str(pa), "hits": str(hits), "doubles": "0", "triples": "0",
           "homeRuns": "0", "baseOnBalls": "0", "intentionalWalks": "0",
           "hitByPitch": "0", "sacFlies": "0", "stolenBases": "0",
           "caughtStealing": "0"}
    row.update({k: str(v) for k, v in kw.items()})
    return row


CLEAN_SPLITS = [
    _hit(2023, 12, 400, 120),          # full pre-debut AA season
]
CLEAN_LOGS = [
    dict(_hit(2024, 11, 60, 22), game_date="2024-04-10"),
    dict(_hit(2024, 11, 45, 15), game_date="2024-04-25"),
]

POISON_SPLITS = [
    _hit(2025, 11, 300, 150),                       # post-debut-season minors
    _hit(2024, 11, 200, 90),                        # debut-season season split
    dict(_hit(2024, 1, 500, 160), sport_id="1"),    # MLB split
]
POISON_LOGS = [
    dict(_hit(2024, 11, 4, 4), game_date="2024-05-01"),   # ON the debut date
    dict(_hit(2024, 11, 30, 20), game_date="2024-08-15"), # post-demotion game
]


def _run(splits, logs):
    stints = compute_player(PID, PERSON, splits, logs, HIT_BASE, AGE_MAP)
    return stints, season_readings(stints)


def test_deleting_the_future_changes_nothing():
    poisoned_stints, poisoned_readings = _run(CLEAN_SPLITS + POISON_SPLITS,
                                              CLEAN_LOGS + POISON_LOGS)
    clean_stints, clean_readings = _run(CLEAN_SPLITS, CLEAN_LOGS)

    assert poisoned_stints == clean_stints
    assert poisoned_readings == clean_readings


def test_the_poison_would_have_mattered():
    """Vacuity guard: prove the poison rows are not inert. Feeding them to a
    player with no debut date (so nothing is fenced) must change the result,
    otherwise the leak test above passes for the wrong reason."""
    undated = dict(PERSON, mlb_debut_date="")
    with_poison = compute_player(PID, undated, CLEAN_SPLITS + POISON_SPLITS,
                                 [], HIT_BASE, AGE_MAP)
    without = compute_player(PID, undated, CLEAN_SPLITS, [], HIT_BASE, AGE_MAP)
    assert with_poison != without


def test_clean_career_actually_scores():
    """Vacuity guard two: the clean career must produce real scored stints,
    otherwise identical-empty-outputs would satisfy the leak test."""
    stints, readings = _run(CLEAN_SPLITS, CLEAN_LOGS)
    scored = [s for s in stints if s["verdict"] == "scored"]
    assert len(scored) == 2          # 2023 AA split + merged 2024 AAA logs
    assert any(r["truncated"] for r in readings)
    assert all(s["season"] < 2025 for s in stints)


def test_debut_day_stint_is_only_pre_debut_games():
    """The 2024 reading must be built from exactly the two pre-debut log
    rows, 105 PA, not from the poisoned 200 PA season split."""
    stints, _ = _run(CLEAN_SPLITS + POISON_SPLITS, CLEAN_LOGS + POISON_LOGS)
    debut_stints = [s for s in stints if s["season"] == 2024]
    assert len(debut_stints) == 1
    assert debut_stints[0]["pa"] == 105.0
    assert debut_stints[0]["pre_debut_truncated"] == "yes"
