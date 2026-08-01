"""Known-answer tests for every arithmetic piece of the readiness chain.

All synthetic, all offline. Hand-computed expectations, not snapshots of
the pipeline's own output, so a formula bug cannot certify itself.
"""

import pytest

import constants as C
from scoring import readiness as R


def test_parse_ip_thirds_notation():
    assert R.parse_ip("5.2") == pytest.approx(5 + 2 / 3)
    assert R.parse_ip("0.1") == pytest.approx(1 / 3)
    assert R.parse_ip("12") == 12.0
    assert R.parse_ip("") == 0.0
    assert R.parse_ip(None) == 0.0


def test_sum_rows_innings_in_thirds():
    rows = [{"inningsPitched": "5.2"}, {"inningsPitched": "3.2"}]
    out = R.sum_rows(rows, ["inningsPitched"])
    assert out["inningsPitched"] == "9.1"   # 17 + 11 thirds = 28 thirds


def test_woba_hand_computed():
    # 10 AB, 3 H of which 1 HR and 1 double, 2 BB (0 IBB), 1 HBP, 1 SF.
    row = {"atBats": 10, "hits": 3, "doubles": 1, "triples": 0, "homeRuns": 1,
           "baseOnBalls": 2, "intentionalWalks": 0, "hitByPitch": 1, "sacFlies": 1}
    w = C.WOBA_WEIGHTS
    num = w["bb"] * 2 + w["hbp"] * 1 + w["s1"] * 1 + w["s2"] * 1 + w["hr"] * 1
    den = 10 + 2 + 1 + 1
    got, got_den = R.woba(row)
    assert got == pytest.approx(num / den)
    assert got_den == den


def test_fip_core_hand_computed():
    row = {"inningsPitched": "18.0", "homeRuns": 2, "baseOnBalls": 6,
           "hitBatsmen": 1, "strikeOuts": 20}
    core, ip = R.fip_core(row)
    assert ip == 18.0
    assert core == pytest.approx((13 * 2 + 3 * 7 - 2 * 20) / 18)


def _lvl_hit(rpa=0.13, woba_lg=0.320):
    return {"woba_lg": woba_lg, "rpa": rpa, "pa": 100000}


def _mlb_hit(rpa=0.12):
    return {"woba_lg": 0.315, "rpa": rpa, "pa": 180000}


def _league_average_line(pa=600):
    """A synthetic line whose wOBA exactly equals the league's."""
    return {"plateAppearances": pa, "gamesPlayed": 150, "atBats": pa,
            "hits": 0, "doubles": 0, "triples": 0, "homeRuns": 0,
            "baseOnBalls": 0, "intentionalWalks": 0, "hitByPitch": 0,
            "sacFlies": 0, "stolenBases": 0, "caughtStealing": 0}


def test_average_hitter_calibration_identity():
    """A league-average bat's base WAR must equal the calibration formula:
    ((level_rpa x TF - mlb_rpa) x PA + replacement + position) / 10."""
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    # Force his wOBA equal to league by setting league wOBA to his (zero).
    lvl_zero = {"woba_lg": 0.0, "rpa": lvl["rpa"], "pa": lvl["pa"]}
    res = R.hitter_stint(line, lvl_zero, mlb, 12, None, None, "1B")
    tf = C.TRANSLATION_FACTORS[12]
    expected_raa = (lvl["rpa"] * tf - mlb["rpa"]) * 600
    rep = C.REPLACEMENT_RUNS_PER_600
    pos = C.POSITION_ADJ_PER_162["1B"] * 150 / 162
    assert res["base_war"] == pytest.approx((expected_raa + rep + pos) / 10, abs=1e-9)
    assert res["age_credit_war"] == 0.0   # no ages supplied, no credit


def test_hitter_small_sample_refused_with_count():
    res = R.hitter_stint(_league_average_line(pa=39), _lvl_hit(), _mlb_hit(),
                         12, None, None, "SS")
    assert res["verdict"] == "insufficient_sample"
    assert "39 PA" in res["detail"]
    assert res["adj_war"] == 0.0


def test_pitcher_small_sample_refused_with_count():
    row = {"battersFaced": 59, "inningsPitched": "14.0", "gamesPlayed": 4,
           "earnedRuns": 5, "strikeOuts": 12, "baseOnBalls": 4,
           "hitBatsmen": 0, "homeRuns": 1}
    lvl = {"lg_fip": 4.5, "fip_const": 3.2, "r9": 5.0, "bf": 100000, "ip": 25000}
    mlb = {"lg_fip": 4.2, "fip_const": 3.1, "r9": 4.6, "bf": 180000, "ip": 43000}
    res = R.pitcher_stint(row, lvl, mlb, 12, None, None)
    assert res["verdict"] == "insufficient_sample"
    assert "59 BF" in res["detail"]


def test_age_credit_capped_at_three_years():
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    # Player 19.0, league average 25.0: gap 6.0, must cap at 3.0.
    capped = R.hitter_stint(line, lvl, mlb, 12, 19.0, 25.0, "SS")
    exact3 = R.hitter_stint(line, lvl, mlb, 12, 22.0, 25.0, "SS")
    assert capped["age_years"] == 3.0
    assert capped["age_credit_war"] == pytest.approx(exact3["age_credit_war"])
    # And symmetric on the old-for-level side.
    old = R.hitter_stint(line, lvl, mlb, 12, 30.0, 25.0, "SS")
    assert old["age_years"] == -3.0
    assert old["age_credit_war"] < 0


def test_age_credit_hand_computed_double_a():
    lvl, mlb = _lvl_hit(rpa=0.13), _mlb_hit()
    line = _league_average_line(600)
    res = R.hitter_stint(line, lvl, mlb, 12, 23.0, 25.0, "SS")
    # 2 years x (25 wRC+ pts / 100) x 0.13 R/PA x 600 PA x TF / 10 runs-per-win
    expected = 2.0 * 0.25 * 0.13 * 600 * C.TRANSLATION_FACTORS[12] / 10
    assert res["age_credit_war"] == pytest.approx(expected)


def test_aaa_age_credit_is_half_of_aa():
    assert C.AGE_WRC_POINTS_PER_YEAR[11] == pytest.approx(
        C.AGE_WRC_POINTS_PER_YEAR[12] / 2)
    assert C.AGE_FIP_RUNS_PER_YEAR[11] == pytest.approx(
        C.AGE_FIP_RUNS_PER_YEAR[12] / 2)


def test_position_adjustment_scales_with_games():
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    line_half = dict(line, gamesPlayed=75)
    ss_full = R.hitter_stint(line, lvl, mlb, 12, None, None, "SS")
    ss_half = R.hitter_stint(line_half, lvl, mlb, 12, None, None, "SS")
    dh_full = R.hitter_stint(line, lvl, mlb, 12, None, None, "DH")
    assert ss_full["pos_adj"] == pytest.approx(7.5 * 150 / 162, abs=0.05)
    assert ss_half["pos_adj"] == pytest.approx(7.5 * 75 / 162, abs=0.05)
    assert dh_full["base_war"] < ss_full["base_war"]


def test_pitcher_average_calibration_identity():
    """An exactly league-average pitcher's base WAR must equal
    (-penalty x IP/9 + replacement) / 10."""
    lvl = {"lg_fip": 4.50, "fip_const": 3.00, "r9": 5.00, "bf": 100000, "ip": 23000}
    mlb = {"lg_fip": 4.20, "fip_const": 3.10, "r9": 4.60, "bf": 180000, "ip": 43000}
    # Build a line whose FIP equals lg_fip exactly: core = 1.50 over 100 IP.
    # 13*HR + 3*(BB+HBP) - 2*K = 150  ->  HR 10, BB+HBP 10, K 5: 130+30-10=150.
    row = {"battersFaced": 430, "inningsPitched": "100.0", "gamesPlayed": 25,
           "strikeOuts": 5, "baseOnBalls": 10, "hitBatsmen": 0, "homeRuns": 10}
    res = R.pitcher_stint(row, lvl, mlb, 12, None, None)
    tf = C.TRANSLATION_FACTORS[12]
    pen9 = mlb["r9"] - lvl["r9"] * tf
    expected = (-pen9 * 100 / 9 + C.REPLACEMENT_RUNS_PER_600 / 600 * 430) / 10
    assert res["savings9"] == pytest.approx(0.0, abs=1e-9)
    assert res["base_war"] == pytest.approx(expected, abs=1e-9)
