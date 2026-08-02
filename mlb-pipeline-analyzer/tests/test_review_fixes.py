"""Regression tests for the defects found by the 2026-08-01 adversarial
review. Each test pins the fix for one confirmed finding so it cannot
silently return.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.compute_readiness import (compute_player, pick_debut_reading,
                                       pick_ranking_position, season_readings)

PID = "999002"
PERSON = {
    "mlbam_id": PID, "full_name": "Fix Regression", "birth_date": "2001-06-01",
    "primary_position": "DH", "mlb_debut_date": "",
}

HIT_BASE = {
    (12, 2022): {"woba_lg": 0.320, "rpa": 0.130, "pa": 150000},
    (16, 2022): {"woba_lg": 0.330, "rpa": 0.135, "pa": 90000},
    (1, 2022): {"woba_lg": 0.312, "rpa": 0.120, "pa": 180000},
}
AGES = {(12, 2022): 24.5, (16, 2022): 20.5}


def _hit(season, sport, pa, hits, team="Some Team", league="Some League"):
    return {"mlbam_id": PID, "group": "hitting", "season": str(season),
            "sport_id": str(sport), "team_name": team, "league_name": league,
            "gamesPlayed": str(max(1, pa // 4)), "plateAppearances": str(pa),
            "atBats": str(pa), "hits": str(hits), "doubles": "0", "triples": "0",
            "homeRuns": "0", "baseOnBalls": "0", "intentionalWalks": "0",
            "hitByPitch": "0", "sacFlies": "0", "stolenBases": "0",
            "caughtStealing": "0"}


def test_blank_team_aggregate_row_not_double_counted():
    """The API's blank-team season-total row must be dropped when per-team
    rows exist (the Oneil Cruz 876-PA-in-210-games defect)."""
    splits = [
        _hit(2022, 12, 375, 110, team="Team A"),
        _hit(2022, 12, 63, 20, team="Team B"),
        _hit(2022, 12, 438, 130, team=""),        # the aggregate
    ]
    stints = compute_player(PID, PERSON, splits, [], HIT_BASE, AGES,
                            positions=["SS"])
    assert len(stints) == 1
    assert stints[0]["pa"] == 438.0


def test_solo_blank_team_row_still_counts():
    """A bucket whose only row lacks a team name is a real record, not an
    aggregate beside per-team rows, and must be kept."""
    stints = compute_player(PID, PERSON, [_hit(2022, 12, 200, 60, team="")],
                            [], HIT_BASE, AGES, positions=["SS"])
    assert len(stints) == 1
    assert stints[0]["pa"] == 200.0


def test_dsl_stints_excluded():
    """Dominican Summer League stints must not be scored: no cited
    translation factor covers the DSL and the rookie age baseline pools it
    with US complex ball."""
    dsl = [_hit(2022, 16, 250, 80, league="Dominican Summer League")]
    complex_ball = [_hit(2022, 16, 250, 80, league="Arizona Complex League")]
    assert compute_player(PID, PERSON, dsl, [], HIT_BASE, AGES,
                          positions=["SS"]) == []
    assert len(compute_player(PID, PERSON, complex_ball, [], HIT_BASE, AGES,
                              positions=["SS"])) == 1


def test_position_comes_from_ranking_not_todays_label():
    """The MJ Melendez defect: the API's current-day position label must
    never influence scoring. Only the ranking-list position may."""
    splits = [_hit(2022, 12, 400, 120)]
    as_dh_today = dict(PERSON, primary_position="DH")
    as_c_today = dict(PERSON, primary_position="C")
    r1 = compute_player(PID, as_dh_today, splits, [], HIT_BASE, AGES,
                        positions=["C"])
    r2 = compute_player(PID, as_c_today, splits, [], HIT_BASE, AGES,
                        positions=["C"])
    assert r1 == r2
    assert r1[0]["pos_adj"] > 0        # catcher credit, not DH dock


def test_single_resolved_position_buckets():
    """compute_player takes an already-resolved position list (splitting
    and averaging a multi-position ranking-list entry is resolve_position's
    job, tested in test_position_resolve.py). This confirms the SS bucket
    applies correctly, and that INF grades at shortstop's value per Reid's
    2026-08-01 ruling, not the old blended average."""
    splits = [_hit(2022, 12, 400, 120)]
    ss = compute_player(PID, PERSON, splits, [], HIT_BASE, AGES, positions=["SS"])
    inf = compute_player(PID, PERSON, splits, [], HIT_BASE, AGES, positions=["INF"])
    assert ss[0]["pos_adj"] == pytest.approx(7.5 * 100 / 162, abs=0.05)
    assert inf[0]["pos_adj"] == pytest.approx(ss[0]["pos_adj"])


def test_season_rollup_reapplies_the_age_credit_cap():
    """Found 2026-08-01: hitter_stint/pitcher_stint cap age credit so it
    can't manufacture a false positive crossing from a below-replacement
    stint, but season_readings summed base_war and age_credit_war fresh
    rather than reusing each stint's own capped adj_war, silently undoing
    the fix at the season level (Sixto Sanchez's real regression case)."""
    stints = [{"season": 2019, "pa": 0.0, "bf": 150.0, "verdict": "scored",
              "base_war": -0.5, "age_credit_war": 0.9}]
    readings = season_readings(stints)
    assert readings[0]["base_war"] == -0.5
    assert readings[0]["age_credit_war"] == 0.9
    assert readings[0]["adj_war"] <= 0  # would be +0.4 uncapped


def _reading(season, verdict, adj=1.0, vol_all=400):
    return {"season": season, "verdict": verdict, "adj_war": adj,
            "base_war": adj - 0.3, "rate_per_600": 2.0 if verdict == "scored" else None,
            "volume": vol_all if verdict == "scored" else 0,
            "volume_all": vol_all, "n_stints": 1, "n_scored": 1,
            "age_credit_war": 0.3, "truncated": False}


def test_debut_pick_prefers_scored_debut_season():
    readings = [_reading(2023, "scored"), _reading(2024, "scored", adj=2.0)]
    pick, basis = pick_debut_reading(readings, 2024)
    assert basis == "debut_season"
    assert pick["adj_war"] == 2.0


def test_debut_pick_carries_over_insufficient_tuneup():
    """The Rutschman defect: a sub-minimum debut-season stub must not bury
    a fully scored prior season."""
    readings = [_reading(2023, "scored", adj=3.1),
                _reading(2024, "insufficient_sample (20 of 20 PA+BF scored, need 100)",
                         adj=0.2, vol_all=20)]
    pick, basis = pick_debut_reading(readings, 2024)
    assert pick["adj_war"] == 3.1
    assert basis == "carried_from_2023_over_20pa_tuneup"


def test_debut_pick_reports_refusal_when_nothing_scored():
    readings = [_reading(2024, "insufficient_sample (20 of 76 PA+BF scored, need 100)",
                         adj=0.2, vol_all=76)]
    pick, basis = pick_debut_reading(readings, 2024)
    assert pick is not None
    assert basis.startswith("insufficient_sample")


def test_pick_ranking_position_prefers_most_recent_cohort():
    """Reid's ruling 2026-08-01 when the 2025 cohort was added: a repeat
    player's CURRENT listing wins, not his earliest. Reversed from the
    original earliest-wins design."""
    pairs = [("2022", "SS"), ("2024", "SS/3B"), ("2025", "3B")]
    assert pick_ranking_position(pairs) == ("2025", "3B")


def test_pick_ranking_position_order_independent():
    pairs = [("2025", "3B"), ("2022", "SS"), ("2024", "SS/3B")]
    assert pick_ranking_position(pairs) == ("2025", "3B")


def test_pick_ranking_position_single_cohort_unaffected():
    assert pick_ranking_position([("2023", "OF")]) == ("2023", "OF")


def test_refusal_label_reports_total_volume():
    """The label must show total volume including refused stints, not the
    fictitious zero of scored-only volume."""
    stints = compute_player(PID, PERSON, [_hit(2022, 12, 39, 12)], [],
                            HIT_BASE, AGES, positions=["SS"])
    readings = season_readings(stints)
    assert "39" in readings[0]["verdict"]
