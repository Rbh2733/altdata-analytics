"""Unit tests for provider parsing + URL detection, against fixtures (no network).

All company names and board slugs in these tests and fixtures are fictional.
"""
import json
import pathlib

from ats_resolver_mcp.models import WorkplaceType
from ats_resolver_mcp.providers import ashby, greenhouse, lever, smartrecruiters
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
