"""Unit tests for the pure normalization helpers (no network)."""
from ats_resolver_mcp.models import Posting, WorkplaceType
from ats_resolver_mcp.normalize import (
    best_match,
    infer_workplace_type,
    slug_candidates,
    title_match_score,
)


def test_slug_candidates_apostrophe():
    c = slug_candidates("Grimble's Fine Foods")
    assert "grimblesfinefoods" in c
    assert "grimbles-fine-foods" in c


def test_slug_candidates_strips_legal_suffix():
    assert slug_candidates("Acme, Inc.")[0] == "acme"


def test_slug_candidates_numbers():
    assert "1901provisions" in slug_candidates("1901 Provisions")


def test_infer_explicit_remote_overrides_city():
    assert infer_workplace_type(location="New York", explicit="remote") == WorkplaceType.REMOTE


def test_infer_explicit_hybrid_priority():
    # Some ATS platforms report "Hybrid Remote"; it must resolve to hybrid, not remote.
    assert infer_workplace_type(explicit="Hybrid Remote") == WorkplaceType.HYBRID


def test_infer_location_remote():
    assert infer_workplace_type(location="Remote - US") == WorkplaceType.REMOTE


def test_infer_location_hybrid():
    assert infer_workplace_type(location="Austin, TX (Hybrid)") == WorkplaceType.HYBRID


def test_infer_bare_city_unknown():
    assert infer_workplace_type(location="Chicago, IL") == WorkplaceType.UNKNOWN


def test_title_match_exact():
    assert title_match_score("Market Research Analyst", "Market Research Analyst") >= 0.95


def test_title_match_all_query_tokens_present():
    assert title_match_score("research analyst", "Senior Market Research Analyst") == 1.0


def test_title_match_low_for_unrelated():
    assert title_match_score("software engineer", "Customer Insights Analyst") < 0.5


def test_best_match_picks_correct_posting():
    postings = [
        Posting(title="Sales Engineer", source="x"),
        Posting(title="Market Research Analyst", source="x"),
    ]
    match, score = best_match("market research analyst", postings)
    assert match is not None
    assert match.title == "Market Research Analyst"
    assert score >= 0.95


def test_best_match_returns_none_below_threshold():
    postings = [Posting(title="Warehouse Associate", source="x")]
    match, _ = best_match("market intelligence analyst", postings)
    assert match is None
