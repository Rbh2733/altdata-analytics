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


def test_pitcher_small_sample_refused_with_count():
    row = {"battersFaced": 59, "inningsPitched": "14.0", "gamesPlayed": 4,
           "earnedRuns": 5, "strikeOuts": 12, "baseOnBalls": 4,
           "hitBatsmen": 0, "homeRuns": 1}
    lvl = {"lg_fip": 4.5, "fip_const": 3.2, "r9": 5.0, "bf": 100000, "ip": 25000}
    mlb = {"lg_fip": 4.2, "fip_const": 3.1, "r9": 4.6, "bf": 180000, "ip": 43000}
    res = R.pitcher_stint(row, lvl, mlb, 12, None, None)
    assert res["verdict"] == "insufficient_sample"
    assert "59 BF" in res["detail"]


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


def test_pitcher_age_credit_cannot_manufacture_a_false_positive_crossing():
    lvl = {"lg_fip": 4.20, "fip_const": 3.00, "r9": 4.60, "bf": 100000, "ip": 23000}
    mlb = {"lg_fip": 4.20, "fip_const": 3.10, "r9": 4.60, "bf": 180000, "ip": 43000}
    row = {"battersFaced": 300, "inningsPitched": "70.0", "gamesPlayed": 15,
           "strikeOuts": 30, "baseOnBalls": 40, "hitBatsmen": 5, "homeRuns": 15}
    res = R.pitcher_stint(row, lvl, mlb, 12, 15.0, 25.0)
    assert res["base_war"] < 0
    assert res["age_credit_war"] > 0
    assert res["adj_war"] <= 0


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
    assert C.AGE_FIP_RUNS_PER_YEAR[11] == pytest.approx(
        C.AGE_FIP_RUNS_PER_YEAR[12] / 2)


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


# --------------------------------------------------------------------------
# Pitcher diagnostics (whip, babip, bb9, k_pct, bb_pct, gb_pct, role),
# added 2026-08-01, Session 21's parked items 1, 2, and 4. All independent
# of the WAR chain above, tested in isolation against hand computation.

def _diag_row(**overrides):
    row = {"baseOnBalls": 20, "hits": 55, "homeRuns": 6, "strikeOuts": 65,
           "atBats": 220, "sacFlies": 3, "gamesPlayed": 12, "gamesStarted": 10,
           "groundOuts": 150, "airOuts": 100, "battersFaced": 260,
           "numberOfPitches": 950}
    row.update(overrides)
    return row


def test_pitcher_diagnostics_hand_computed():
    d = R.pitcher_diagnostics(_diag_row(), ip=60.0)
    assert d["whip"] == pytest.approx((20 + 55) / 60.0)
    assert d["babip"] == pytest.approx(round((55 - 6) / (220 - 65 - 6 + 3), 3))
    assert d["bb9"] == pytest.approx(9 * 20 / 60.0)
    assert d["k_pct"] == pytest.approx(65 / 260)
    assert d["bb_pct"] == pytest.approx(round(20 / 260, 3))
    assert d["gb_pct"] == pytest.approx(150 / 250)
    assert d["gs"] == 10
    assert d["start_frac"] == pytest.approx(round(10 / 12, 3))
    assert d["ip_per_start"] == pytest.approx(6.0)
    assert d["p_per_gs"] == pytest.approx(95.0)
    assert d["ip_per_appearance"] == pytest.approx(5.0)   # 60 IP / 12 G
    assert d["role"] == "starter"   # 10/12 = 0.833 clears the 0.80 threshold


def test_ip_per_appearance_flags_a_short_leash_regardless_of_role():
    """Added 2026-08-02 after Reid caught a real case (Jacob Misiorowski's
    2024 AAA stint): a pitcher kept on a strict pitch count can show short
    outings in BOTH his starts and his relief appearances, which
    start_frac alone reads as a role change. ip_per_appearance is IP over
    EVERY appearance, not just starts, so it reads the same "kept short"
    signal whether the games happened to be labeled starts or relief."""
    # 14 games, 2 of them starts, 17.2 innings total (thirds notation),
    # Misiorowski's real 2024 AAA line.
    row = _diag_row(gamesPlayed=14, gamesStarted=2)
    d = R.pitcher_diagnostics(row, ip=17 + 2 / 3)
    assert d["role"] == "reliever"                 # 2/14 = 0.143, below the floor
    assert d["ip_per_appearance"] == pytest.approx((17 + 2 / 3) / 14, abs=0.01)
    assert d["ip_per_appearance"] < 1.5             # short across the board, not just the "starts"


def test_pitcher_diagnostics_babip_guards_nonpositive_denominator():
    """A tiny or extreme sample can push AB - K - HR + SF to zero or below.
    Reported as None (a real refusal), never a nonsensical or negative
    BABIP."""
    d = R.pitcher_diagnostics(_diag_row(atBats=10, strikeOuts=15, homeRuns=0,
                                        sacFlies=0), ip=10.0)
    assert d["babip"] is None


def test_pitcher_diagnostics_true_reliever_has_no_start_workload_rates():
    """gamesStarted=0: start_frac is a real zero (he has a start rate, it's
    just zero), but ip_per_start and p_per_gs have nothing to divide by and
    must be None, not zero or a division error."""
    d = R.pitcher_diagnostics(_diag_row(gamesStarted=0, gamesPlayed=10), ip=12.0)
    assert d["start_frac"] == 0.0
    assert d["ip_per_start"] is None
    assert d["p_per_gs"] is None
    assert d["role"] == "reliever"


def test_pitcher_diagnostics_role_bands():
    starter = R.pitcher_diagnostics(_diag_row(gamesStarted=8, gamesPlayed=10), ip=50.0)
    swing = R.pitcher_diagnostics(_diag_row(gamesStarted=5, gamesPlayed=10), ip=50.0)
    reliever = R.pitcher_diagnostics(_diag_row(gamesStarted=1, gamesPlayed=10), ip=50.0)
    assert starter["role"] == "starter"      # 0.80, at the threshold
    assert swing["role"] == "swingman"       # 0.50, inside the band
    assert reliever["role"] == "reliever"    # 0.10, below the floor


def test_pitcher_diagnostics_blank_role_when_no_games_played():
    d = R.pitcher_diagnostics(_diag_row(gamesPlayed=0, gamesStarted=0), ip=0.0)
    assert d["start_frac"] is None
    assert d["role"] == ""


def test_pitcher_stint_carries_diagnostics_only_when_scored():
    lvl = {"lg_fip": 4.50, "fip_const": 3.00, "r9": 5.00, "bf": 100000, "ip": 23000}
    mlb = {"lg_fip": 4.20, "fip_const": 3.10, "r9": 4.60, "bf": 180000, "ip": 43000}
    row = dict(_diag_row(), inningsPitched="60.0", hitBatsmen=0)
    scored = R.pitcher_stint(row, lvl, mlb, 12, None, None)
    assert scored["verdict"] == "scored"
    assert scored["whip"] == pytest.approx((20 + 55) / 60.0)
    assert scored["role"] == "starter"

    small = R.pitcher_stint({**row, "battersFaced": 10}, lvl, mlb, 12, None, None)
    assert small["verdict"] == "insufficient_sample"
    assert "whip" not in small
