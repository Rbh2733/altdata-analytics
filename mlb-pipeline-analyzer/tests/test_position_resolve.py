"""Tests for scoring/position_resolve.py, Reid's ruling 2026-08-01: a
multi-position ranking-list entry is averaged across every position it
named, except the 7 cases Reid reviewed by hand, which use his specific
call outright. INF's shortstop-level grading lives in constants.py, not
here, see test_scoring.py for that.
"""

from scoring.position_resolve import resolve_position


def test_single_position_stands_as_is():
    assert resolve_position("C") == {"positions": ["C"], "basis": "single"}
    assert resolve_position("RHP") == {"positions": ["RHP"], "basis": "single"}


def test_inf_single_label_is_still_just_single():
    """INF's shortstop-level value is a constants-table fact, not a
    resolution branch, so it flows through the ordinary single-position
    path exactly like any other one-token listing."""
    res = resolve_position("INF")
    assert res == {"positions": ["INF"], "basis": "single"}


def test_pure_infield_combo_is_averaged_not_maxed():
    """Corrected 2026-08-01: an earlier version of this rule took the
    highest-valued position among a pure-infield combo. Reid corrected
    that, every slash combo averages, infield included, no exceptions
    outside the 7 reviewed cases."""
    res = resolve_position("2B/3B")
    assert res == {"positions": ["2B", "3B"], "basis": "averaged"}
    res = resolve_position("SS/2B")
    assert res == {"positions": ["SS", "2B"], "basis": "averaged"}


def test_outfield_combo_is_also_just_averaged():
    """The center-field-as-premium-outfield-spot idea was raised and
    explicitly deferred by Reid 2026-08-01, small sample, not significant
    yet. OF-including combos average like everything else."""
    res = resolve_position("SS/OF")
    assert res == {"positions": ["SS", "OF"], "basis": "averaged"}


def test_three_way_combo_averages_all_three():
    res = resolve_position("2B/SS/OF")
    assert res == {"positions": ["2B", "SS", "OF"], "basis": "averaged"}


def test_order_in_the_listed_string_is_preserved():
    """Averaging is order-independent arithmetically, but the positions
    list should still reflect the original listing order for readability
    in the output."""
    assert resolve_position("3B/SS")["positions"] == ["3B", "SS"]
    assert resolve_position("SS/3B")["positions"] == ["SS", "3B"]


def test_manual_override_wins_outright():
    """A human call on a previously flagged case (Tyler Soderstrom, games
    data leaned left field, Reid's real-world knowledge says his identity
    as a prospect is catcher) overrides everything else, labeled distinctly
    so it never blends into the automated resolution's earned accuracy."""
    res = resolve_position("C/1B", manual_override="C")
    assert res == {"positions": ["C"], "basis": "reid_confirmed"}


def test_manual_override_beats_even_a_case_that_would_average_fine():
    res = resolve_position("3B/2B", manual_override="1B")
    assert res == {"positions": ["1B"], "basis": "reid_confirmed"}


def test_manual_override_can_itself_be_multi_position():
    """Miguel Vargas: listed 3B/OF/1B, Reid's override drops OF entirely,
    corrected to 3B/1B, still averaged between the remaining two, not
    collapsed to a single picked winner."""
    res = resolve_position("3B/OF/1B", manual_override="3B/1B")
    assert res == {"positions": ["3B", "1B"], "basis": "reid_confirmed"}


def test_no_override_falls_through_to_averaging():
    assert resolve_position("2B/3B", manual_override=None)["basis"] == "averaged"
    assert resolve_position("2B/3B", manual_override="")["basis"] == "averaged"


def test_empty_listing_returns_empty():
    assert resolve_position("") == {"positions": [], "basis": "single"}
