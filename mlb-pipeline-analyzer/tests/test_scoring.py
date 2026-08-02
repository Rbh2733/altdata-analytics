"""Known-answer tests for every arithmetic piece of the readiness chain.

All synthetic, all offline. Hand-computed expectations, not snapshots of
the pipeline's own output, so a formula bug cannot certify itself.
"""

import pytest

import constants as C
from scoring import readiness as R


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
    res = R.hitter_stint(line, lvl_zero, mlb, 12, None, None, ["1B"])
    tf = C.TRANSLATION_FACTORS[12]
    expected_raa = (lvl["rpa"] * tf - mlb["rpa"]) * 600
    rep = C.REPLACEMENT_RUNS_PER_600
    pos = C.POSITION_ADJ_PER_162["1B"] * 150 / 162
    assert res["base_war"] == pytest.approx((expected_raa + rep + pos) / 10, abs=1e-9)
    assert res["age_credit_war"] == 0.0   # no ages supplied, no credit


def test_hitter_small_sample_refused_with_count():
    res = R.hitter_stint(_league_average_line(pa=39), _lvl_hit(), _mlb_hit(),
                         12, None, None, ["SS"])
    assert res["verdict"] == "insufficient_sample"
    assert "39 PA" in res["detail"]
    assert res["adj_war"] == 0.0


def test_age_credit_cannot_manufacture_a_false_positive_crossing():
    """Found 2026-08-01: age credit could push a genuinely below-
    replacement performance into a positive adj_war (Sixto Sanchez's
    entire positive debut-day score turned out to be manufactured this
    way). Below-replacement production capped at 0, never rescued into
    a false 'ready' reading, however large the age credit."""
    lvl, mlb = _lvl_hit(rpa=0.05), _mlb_hit()  # bad enough native rate to force base_war negative
    line = _league_average_line(600)
    res = R.hitter_stint(line, lvl, mlb, 12, 15.0, 25.0, ["SS"])  # extreme age gap, huge credit
    assert res["base_war"] < 0
    assert res["age_credit_war"] > 0
    assert res["adj_war"] <= 0


def test_age_credit_still_applies_in_full_above_replacement():
    """The cap only fires on negative base_war. A stint that already
    clears replacement keeps its full credit and can go further positive."""
    lvl, mlb = _lvl_hit(), _mlb_hit()
    elite_line = dict(_league_average_line(600), hits=250, doubles=40, homeRuns=30,
                      baseOnBalls=60)  # clearly above-average, base_war must be positive
    no_credit = R.hitter_stint(elite_line, lvl, mlb, 12, None, None, ["SS"])
    with_credit = R.hitter_stint(elite_line, lvl, mlb, 12, 20.0, 25.0, ["SS"])
    assert no_credit["base_war"] >= 0
    assert with_credit["adj_war"] == pytest.approx(with_credit["base_war"] + with_credit["age_credit_war"])
    assert with_credit["adj_war"] > no_credit["adj_war"]


def test_age_credit_capped_at_three_years():
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    # Player 19.0, league average 25.0: gap 6.0, must cap at 3.0.
    capped = R.hitter_stint(line, lvl, mlb, 12, 19.0, 25.0, ["SS"])
    exact3 = R.hitter_stint(line, lvl, mlb, 12, 22.0, 25.0, ["SS"])
    assert capped["age_years"] == 3.0
    assert capped["age_credit_war"] == pytest.approx(exact3["age_credit_war"])
    # And symmetric on the old-for-level side.
    old = R.hitter_stint(line, lvl, mlb, 12, 30.0, 25.0, ["SS"])
    assert old["age_years"] == -3.0
    assert old["age_credit_war"] < 0


def test_age_credit_hand_computed_double_a():
    lvl, mlb = _lvl_hit(rpa=0.13), _mlb_hit()
    line = _league_average_line(600)
    res = R.hitter_stint(line, lvl, mlb, 12, 23.0, 25.0, ["SS"])
    # 2 years x (25 wRC+ pts / 100) x 0.13 R/PA x 600 PA x TF / 10 runs-per-win
    expected = 2.0 * 0.25 * 0.13 * 600 * C.TRANSLATION_FACTORS[12] / 10
    assert res["age_credit_war"] == pytest.approx(expected)


def test_aaa_age_credit_is_half_of_aa():
    assert C.AGE_WRC_POINTS_PER_YEAR[11] == pytest.approx(
        C.AGE_WRC_POINTS_PER_YEAR[12] / 2)


def test_position_adjustment_scales_with_games():
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    line_half = dict(line, gamesPlayed=75)
    ss_full = R.hitter_stint(line, lvl, mlb, 12, None, None, ["SS"])
    ss_half = R.hitter_stint(line_half, lvl, mlb, 12, None, None, ["SS"])
    dh_full = R.hitter_stint(line, lvl, mlb, 12, None, None, ["DH"])
    assert ss_full["pos_adj"] == pytest.approx(7.5 * 150 / 162, abs=0.05)
    assert ss_half["pos_adj"] == pytest.approx(7.5 * 75 / 162, abs=0.05)
    assert dh_full["base_war"] < ss_full["base_war"]


def test_cf_scores_at_shortstop_value():
    """Reid's ruling 2026-08-01, round two: 'SS is to the infield as CF
    is to the outfield.' A player confirmed as CF (always via a manual
    override, never automatically, since ranking lists never print 'CF')
    is graded exactly like a shortstop, not the old blended outfield
    average."""
    assert C.POSITION_ADJ_PER_162["CF"] == C.POSITION_ADJ_PER_162["SS"]
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    cf_res = R.hitter_stint(line, lvl, mlb, 12, None, None, ["CF"])
    ss_res = R.hitter_stint(line, lvl, mlb, 12, None, None, ["SS"])
    assert cf_res["pos_adj"] == pytest.approx(ss_res["pos_adj"])


def test_of_secondary_is_weaker_than_of_standalone():
    """Reid's ruling 2026-08-01, round two: standalone 'OF' (a player's
    entire listing) keeps the original blended value, since an unflagged
    burner center fielder could still be sitting in that bucket. 'OF' as
    a secondary position alongside an infield spot (always how it appears
    in combos in the real data) drops to the pure corner rate, the
    fallback signal of a player who didn't stick in the infield."""
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    of_alone = R.hitter_stint(line, lvl, mlb, 12, None, None, ["OF"])
    of_with_ss = R.hitter_stint(line, lvl, mlb, 12, None, None, ["SS", "OF"])
    assert of_alone["pos_adj"] == pytest.approx(C.POSITION_ADJ_PER_162["OF"] * 150 / 162, abs=0.05)
    ss_val = C.POSITION_ADJ_PER_162["SS"]
    of_secondary_val = C.POSITION_ADJ_PER_162["OF_SECONDARY"]
    assert of_with_ss["pos_adj"] == pytest.approx((ss_val + of_secondary_val) / 2 * 150 / 162, abs=0.05)
    # the secondary rate must be strictly weaker than standalone OF
    assert C.POSITION_ADJ_PER_162["OF_SECONDARY"] < C.POSITION_ADJ_PER_162["OF"]


def test_inf_scores_at_shortstop_value():
    """Reid's ruling 2026-08-01: a player listed simply 'INF' is graded at
    shortstop's value, not a blended average, since the label itself is
    the high-value signal (competent across the whole infield), not a
    hedge to be watered down."""
    assert C.POSITION_ADJ_PER_162["INF"] == C.POSITION_ADJ_PER_162["SS"]
    lvl, mlb = _lvl_hit(), _mlb_hit()
    line = _league_average_line(600)
    inf_res = R.hitter_stint(line, lvl, mlb, 12, None, None, ["INF"])
    ss_res = R.hitter_stint(line, lvl, mlb, 12, None, None, ["SS"])
    assert inf_res["pos_adj"] == pytest.approx(ss_res["pos_adj"])


