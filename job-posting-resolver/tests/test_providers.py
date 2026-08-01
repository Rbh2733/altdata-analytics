"""Unit tests for provider parsing + URL detection, against fixtures (no network).

All company names and board slugs in these tests and fixtures are fictional.
"""
import json
import pathlib

from ats_resolver_mcp.models import WorkplaceType
from ats_resolver_mcp.providers import ashby, greenhouse, icims, lever, smartrecruiters, workday
from ats_resolver_mcp.providers.careers_page import parse_page

FIX = pathlib.Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text())


def test_greenhouse_parse_infers_remote_from_location():
    posts = greenhouse.parse_jobs(load("greenhouse_jobs.json"), "acme")
    assert len(posts) == 2
    assert posts[0].title == "Senior Customer Insights Analyst"
    assert posts[0].workplace_type == WorkplaceType.REMOTE.value
    assert posts[0].job_id == "5012345"
    assert posts[0].department == "Analytics"
    assert posts[1].workplace_type == WorkplaceType.UNKNOWN.value


def test_lever_parse_uses_explicit_workplace_type():
    posts = lever.parse_jobs(load("lever_postings.json"), "foglinedata")
    assert posts[0].workplace_type == WorkplaceType.REMOTE.value
    assert posts[1].workplace_type == WorkplaceType.HYBRID.value
    assert posts[0].posted_at  # epoch ms converted to ISO date
    assert posts[0].url.endswith("abc-123")
    assert posts[0].description_excerpt


def test_ashby_parse_uses_is_remote():
    posts = ashby.parse_jobs(load("ashby_jobs.json"), "acme")
    assert posts[0].workplace_type == WorkplaceType.REMOTE.value
    assert posts[1].workplace_type == WorkplaceType.UNKNOWN.value


def test_smartrecruiters_parse_builds_public_url_and_remote():
    posts = smartrecruiters.parse_jobs(load("smartrecruiters_postings.json"), "pinebrook")
    assert posts[0].url == "https://jobs.smartrecruiters.com/pinebrook/sr-1"
    assert posts[0].workplace_type == WorkplaceType.UNKNOWN.value
    assert posts[1].workplace_type == WorkplaceType.REMOTE.value


def test_from_url_detection_each_platform():
    assert greenhouse.Greenhouse().from_url("https://boards.greenhouse.io/foglinedata/jobs/123").token == "foglinedata"
    assert lever.Lever().from_url("https://jobs.lever.co/pinebrook/abc").token == "pinebrook"
    assert ashby.Ashby().from_url("https://jobs.ashbyhq.com/acme/xyz").token == "acme"
    assert smartrecruiters.SmartRecruiters().from_url("https://jobs.smartrecruiters.com/Pinebrook/77").token == "Pinebrook"


def test_greenhouse_embed_url_token():
    ref = greenhouse.Greenhouse().from_url("https://boards.greenhouse.io/embed/job_board?for=acme")
    assert ref.token == "acme"


def test_from_url_returns_none_for_foreign_host():
    assert lever.Lever().from_url("https://boards.greenhouse.io/acme") is None


def test_careers_page_parse_infers_remote_and_finds_ats_links():
    html = (
        "<html><head><title>Careers - Acme</title></head><body>"
        "<h1>Open Roles</h1><p>We are a remote-first company.</p>"
        "<a href='https://boards.greenhouse.io/acme/jobs/1'>Analyst</a>"
        "<a href='/about'>About</a></body></html>"
    )
    r = parse_page(html, "https://acme.example.com/careers")
    assert r["workplace_type"] == "remote"
    assert any("greenhouse" in link["href"] for link in r["links"])


# --------------------------------------------------------------------------
# Detection confidence: the empty-envelope false negative.
#
# Several ATS APIs answer HTTP 200 with a well-formed but EMPTY payload for a slug
# that does not exist. SmartRecruiters returns {"content": [], "totalFound": 0} for
# literally any string. Detecting on envelope shape alone therefore resolved every
# unknown company to whichever provider was probed last, and the caller then reported
# "no postings matched" for a board that never existed.
# --------------------------------------------------------------------------

import asyncio

from ats_resolver_mcp.providers import detect_ats


def _run(coro):
    return asyncio.run(coro)


def _fake_probe(payload):
    async def probe(url, params=None):
        return payload
    return probe


def test_smartrecruiters_detect_marks_empty_envelope_low_confidence(monkeypatch):
    monkeypatch.setattr(smartrecruiters, "probe_json",
                        _fake_probe({"content": [], "totalFound": 0}))
    ref = _run(smartrecruiters.SmartRecruiters().detect(["notarealcompany"]))
    assert ref is not None                 # envelope was valid, so a ref still comes back
    assert ref.observed_count == 0
    assert ref.confidence == "low"         # but it must not read as a confirmed board


def test_smartrecruiters_detect_high_confidence_on_real_board(monkeypatch):
    monkeypatch.setattr(smartrecruiters, "probe_json",
                        _fake_probe({"content": [{"id": "1"}], "totalFound": 67}))
    ref = _run(smartrecruiters.SmartRecruiters().detect(["realboard"]))
    assert ref.observed_count == 67        # totalFound wins over the limit=1 page size
    assert ref.confidence == "high"


def test_greenhouse_and_ashby_detect_flag_empty_boards(monkeypatch):
    monkeypatch.setattr(greenhouse, "probe_json", _fake_probe({"jobs": []}))
    monkeypatch.setattr(ashby, "probe_json", _fake_probe({"jobs": []}))
    assert _run(greenhouse.Greenhouse().detect(["acme"])).confidence == "low"
    assert _run(ashby.Ashby().detect(["acme"])).confidence == "low"


def test_lever_detect_flags_empty_list(monkeypatch):
    monkeypatch.setattr(lever, "probe_json", _fake_probe([]))
    ref = _run(lever.Lever().detect(["acme"]))
    assert ref.observed_count == 0 and ref.confidence == "low"


def test_registry_prefers_a_board_with_postings_over_an_empty_one(monkeypatch):
    """Greenhouse answers empty, SmartRecruiters has real postings: pick SmartRecruiters."""
    monkeypatch.setattr(greenhouse, "probe_json", _fake_probe({"jobs": []}))
    monkeypatch.setattr(lever, "probe_json", _fake_probe(None))
    monkeypatch.setattr(ashby, "probe_json", _fake_probe(None))
    monkeypatch.setattr(smartrecruiters, "probe_json",
                        _fake_probe({"content": [{"id": "1"}], "totalFound": 12}))
    _mute_html_providers(monkeypatch)
    ref = _run(detect_ats("Acme Analytics"))
    assert ref.platform == "smartrecruiters"
    assert ref.confidence == "high"


def test_registry_returns_low_confidence_when_every_board_is_empty(monkeypatch):
    """All providers answer empty-but-valid: return something, but never claim confidence."""
    monkeypatch.setattr(greenhouse, "probe_json", _fake_probe({"jobs": []}))
    monkeypatch.setattr(lever, "probe_json", _fake_probe([]))
    monkeypatch.setattr(ashby, "probe_json", _fake_probe({"jobs": []}))
    monkeypatch.setattr(smartrecruiters, "probe_json",
                        _fake_probe({"content": [], "totalFound": 0}))
    _mute_html_providers(monkeypatch)
    ref = _run(detect_ats("Definitely Not A Real Company"))
    assert ref is not None
    assert ref.confidence == "low"


def _mute_html_providers(monkeypatch):
    """iCIMS and Workday sit last in the chain. Registry tests MUST silence them or the
    suite makes live network calls, which the repo's fixture-only test rule forbids."""
    async def no_text(url, params=None):
        return None

    async def no_post(url, payload):
        return None

    monkeypatch.setattr(icims, "probe_text", no_text)
    monkeypatch.setattr(workday, "probe_post_json", no_post)


def test_workday_parse_builds_public_url_and_infers_remote():
    posts = workday.parse_jobs(load("workday_jobs.json"), "pinebrook", "wd1", "Pinebrook")
    assert len(posts) == 2
    assert posts[0].title == "Senior Financial Analyst"
    assert posts[0].url == ("https://pinebrook.wd1.myworkdayjobs.com/en-US/Pinebrook"
                            "/job/Austin-TX/Senior-Financial-Analyst_REQ-1001")
    assert posts[0].job_id == "REQ-1001"
    assert posts[1].workplace_type == WorkplaceType.REMOTE.value


def test_workday_from_url_extracts_tenant_shard_and_site():
    ref = workday.Workday().from_url(
        "https://sailpoint.wd1.myworkdayjobs.com/en-US/SailPoint/job/Staff-Product-Analyst_R013388")
    assert ref.token == "sailpoint"
    assert ref.extra["shard"] == "wd1"
    assert ref.extra["site"] == "SailPoint"   # the en-US locale segment is skipped
    assert ref.detected_via == "hint_url"


def test_icims_parse_strips_title_label_and_reads_location():
    html = (FIX / "icims_board.html").read_text()
    posts = icims.parse_jobs(html, "pinebrook")
    assert len(posts) == 2                      # the /about link is not a job
    assert posts[0].title == "Senior Associate, Data Science & Analytics"
    assert posts[0].location == "US-Remote"
    assert posts[0].workplace_type == WorkplaceType.REMOTE.value
    assert posts[0].job_id == "3018"
    assert "%2c" not in posts[0].url            # url-decoded
    assert posts[1].location == "US-TX-Austin"


def test_icims_from_url_handles_both_host_forms():
    p = icims.ICIMS()
    assert p.from_url("https://careers-pinebrook.icims.com/jobs/3018/x/job").token == "pinebrook"
    assert p.from_url("https://pinebrook.icims.com/jobs/3018/x/job").token == "pinebrook"
    assert p.from_url("https://boards.greenhouse.io/pinebrook") is None
