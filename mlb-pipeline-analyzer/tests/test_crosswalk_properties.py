"""Entity-matcher properties, run against the real committed data.

The load-bearing guarantees, carried over from the earlier project's suite:
the adversarial hard-case set passes whole, genuine collisions are declined
rather than guessed, no two distinct source names ever merge into one id,
and the same name resolves identically across cohorts.
"""

import csv

import pytest

import config
from matching.normalize_name import normalize
from matching.resolve_prospect import resolve_all, resolve_one, build_index


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def universe():
    return _read(config.DATA_RAW / "player_universe.csv")


@pytest.fixture(scope="module")
def index(universe):
    return build_index(universe)


@pytest.fixture(scope="module")
def crosswalk():
    path = config.DATA_DERIVED / "crosswalk.csv"
    if not path.exists():
        pytest.skip("crosswalk not built yet")
    return _read(path)


def test_hard_cases_all_correct(universe, index):
    """Every adversarial case resolves to its expected id, and the
    genuinely-unresolvable cases decline."""
    cases = _read(config.DATA_RAW / "hard_case_names.csv")
    assert len(cases) >= 19
    failures = []
    for case in cases:
        row = {"player": case["variant_name"],
               "position": case.get("position", ""),
               "current_level": case.get("current_level", "")}
        res = resolve_one(row, index)
        expected = case["expected_mlbam_id"].strip()
        got = str(res["player"]["mlbam_id"]) if res["player"] else ""
        if expected == "":
            if got != "":
                failures.append(f"{case['variant_name']}: guessed {got}, "
                                f"expected decline")
        elif got != expected:
            failures.append(f"{case['variant_name']}: got {got or res['method']}, "
                            f"expected {expected}")
    assert not failures, "\n".join(failures)


def test_two_julio_rodriguezes_stay_distinct(index):
    """Two real players whose names differ only by an accent must not merge.
    The position tiebreaker separates them."""
    of_row = {"player": "Julio Rodriguez", "position": "OF", "current_level": "MLB"}
    p_row = {"player": "Julio Rodriguez", "position": "RHP", "current_level": "AAA"}
    of_res = resolve_one(of_row, index)
    p_res = resolve_one(p_row, index)
    if of_res["player"] and p_res["player"]:
        assert of_res["player"]["mlbam_id"] != p_res["player"]["mlbam_id"]


def test_no_many_to_one_merges(crosswalk):
    """No two distinct source names may resolve to the same player id."""
    by_id = {}
    for r in crosswalk:
        if not r["mlbam_id"]:
            continue
        core = normalize(r["player"])
        prior = by_id.setdefault(r["mlbam_id"], core)
        assert prior == core, (
            f"id {r['mlbam_id']} claimed by both '{prior}' and '{core}'")


def test_cross_cohort_consistency(crosswalk):
    """A name appearing in multiple cohorts must resolve to the same id
    every time."""
    by_name = {}
    for r in crosswalk:
        prior = by_name.setdefault(normalize(r["player"]), r["mlbam_id"])
        assert prior == r["mlbam_id"], (
            f"'{r['player']}' resolves inconsistently across cohorts")


def test_full_coverage_with_disclosed_overrides(crosswalk):
    """All 300 rows matched, and any manual overrides are visible as their
    own method, never folded into the matcher's earned accuracy."""
    assert len(crosswalk) == 300
    assert all(r["mlbam_id"] for r in crosswalk)
    overrides = [r for r in crosswalk if r["method"] == "manual_override"]
    for r in overrides:
        assert r["disambiguated_by"] == "curated"
