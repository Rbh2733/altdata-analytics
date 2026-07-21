#!/usr/bin/env python3
"""ats_resolver_mcp: resolve a company's ATS and read authoritative role data.

Chain: aggregator hit -> ATS (Greenhouse/Lever/Ashby/SmartRecruiters)
                       -> company careers page (last-resort HTML scrape).

Tools:
  ats_resolve              Detect which ATS a company uses (+ board token).
  ats_list_jobs            List live postings (normalized), with title/location filters.
  ats_get_job              Full detail for one posting (work arrangement + excerpt).
  ats_verify_remote        One-shot: is a named role remote / hybrid / onsite?
  ats_scrape_careers_page  Last-resort HTML read when no ATS API is detected.
"""
from __future__ import annotations

import json
from typing import List

from mcp.server.fastmcp import FastMCP

from .http_client import http_error_message
from .models import (
    GetJobInput,
    ListJobsInput,
    Posting,
    ResolveAtsInput,
    ResponseFormat,
    ScrapeCareersInput,
    VerifyRemoteInput,
    WorkplaceType,
)
from .normalize import best_match, filter_postings, postings_to_markdown
from .providers import CareersPage, detect_ats, provider_by_name

mcp = FastMCP("ats_resolver_mcp")

_READONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,  # talks to external ATS endpoints
}

_NO_ATS = (
    "No ATS detected for '{company}'. The board slug could not be guessed from the name. "
    "Next steps: (1) call this again with hint_url set to the aggregator's redirect or the "
    "company careers link, or (2) use ats_scrape_careers_page on the company careers URL."
)


def _dump(postings: List[Posting]) -> list:
    return [p.model_dump() for p in postings]


def _verdict_from(workplace_type: str) -> str:
    """Map a workplace_type to a verdict string the caller can act on."""
    return {
        WorkplaceType.REMOTE.value: "remote-eligible",
        WorkplaceType.HYBRID.value: "hybrid",
        WorkplaceType.ONSITE.value: "onsite",
        WorkplaceType.UNKNOWN.value: "ambiguous",
    }.get(workplace_type, "ambiguous")


def _verify_markdown(r: dict) -> str:
    lines = [
        f"# verify_remote: {r['title']} at {r['company']}",
        "",
        f"- Verdict: {r['verdict']}",
        f"- Workplace type: {r['workplace_type']}",
    ]
    if r.get("matched_title"):
        lines.append(f"- Matched posting: {r['matched_title']} (match confidence {r.get('confidence')})")
    if r.get("location"):
        lines.append(f"- Location: {r['location']}")
    if r.get("source"):
        lines.append(f"- Source: {r['source']}")
    if r.get("url"):
        lines.append(f"- URL: {r['url']}")
    if r.get("reason"):
        lines.append(f"- Note: {r['reason']}")
    return "\n".join(lines)


@mcp.tool(name="ats_resolve", annotations={"title": "Resolve company ATS", **_READONLY})
async def ats_resolve(params: ResolveAtsInput) -> str:
    """Detect which ATS a company uses and return its board token.

    Tries, in order: a hint_url (exact, instant) then slug-probing Greenhouse, Lever,
    Ashby, SmartRecruiters. This is the first move in the
    aggregator -> ATS -> company-site chain.

    Args:
        params (ResolveAtsInput): company (name or slug) and optional hint_url.

    Returns:
        str: JSON {company, platform, board_token, detected_via, extra}, or guidance if
        no ATS was found (use a hint_url or fall back to ats_scrape_careers_page).
    """
    try:
        board = await detect_ats(params.company, hint_url=params.hint_url)
        if not board:
            return _NO_ATS.format(company=params.company)
        return json.dumps({
            "company": params.company,
            "platform": board.platform,
            "board_token": board.token,
            "detected_via": board.detected_via,
            "extra": board.extra,
        }, indent=2)
    except Exception as e:
        return http_error_message(e, "resolve")


@mcp.tool(name="ats_list_jobs", annotations={"title": "List ATS postings", **_READONLY})
async def ats_list_jobs(params: ListJobsInput) -> str:
    """List a company's live postings from its ATS, normalized across platforms.

    Each posting carries an authoritative-where-available work arrangement
    (remote/hybrid/onsite), location, department, url, and posted date.

    Args:
        params (ListJobsInput): company, optional hint_url, optional title query,
            optional location filter, limit, response_format.

    Returns:
        str: Markdown (default) or JSON. JSON schema:
        {company, platform, count, postings: [{title, company, location,
        workplace_type, department, url, posted_at, source, job_id}]}.
    """
    try:
        board = await detect_ats(params.company, hint_url=params.hint_url)
        if not board:
            return _NO_ATS.format(company=params.company)
        provider = provider_by_name(board.platform)
        fetch_limit = max(params.limit, 100) if params.query or params.location else params.limit
        postings = await provider.list_jobs(board, limit=fetch_limit)
        postings = filter_postings(postings, query=params.query, location=params.location)[:params.limit]
        for p in postings:
            if not p.company:
                p.company = params.company
        if params.response_format == ResponseFormat.JSON:
            return json.dumps({
                "company": params.company,
                "platform": board.platform,
                "count": len(postings),
                "postings": _dump(postings),
            }, indent=2)
        if not postings:
            return (f"No postings matched for '{params.company}' on {board.platform} "
                    f"(query={params.query!r}, location={params.location!r}).")
        return postings_to_markdown(postings, f"{params.company} via {board.platform}")
    except Exception as e:
        return http_error_message(e, "list_jobs")


@mcp.tool(name="ats_get_job", annotations={"title": "Get one ATS posting", **_READONLY})
async def ats_get_job(params: GetJobInput) -> str:
    """Fetch full detail for a single posting, including the work-arrangement line.

    Provide either job_id (from ats_list_jobs) or a direct posting url. When a url is an
    ATS posting link, the platform and board are resolved from it directly.

    Args:
        params (GetJobInput): company, job_id OR url, response_format.

    Returns:
        str: Markdown (default) or JSON Posting {title, company, location,
        workplace_type, department, url, posted_at, source, job_id, description_excerpt}.
    """
    try:
        if not params.job_id and not params.url:
            return "Error: provide either job_id (from ats_list_jobs) or url."
        board = await detect_ats(params.company, hint_url=params.url)
        if not board:
            return _NO_ATS.format(company=params.company)
        provider = provider_by_name(board.platform)
        posting = await provider.get_job(board, job_id=params.job_id, url=params.url)
        if not posting:
            return (f"Job not found for '{params.company}' on {board.platform} "
                    f"(job_id={params.job_id!r}, url={params.url!r}).")
        if not posting.company:
            posting.company = params.company
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(posting.model_dump(), indent=2)
        return postings_to_markdown([posting], f"{posting.title} at {params.company}")
    except Exception as e:
        return http_error_message(e, "get_job")


@mcp.tool(name="ats_verify_remote", annotations={"title": "Verify role work arrangement", **_READONLY})
async def ats_verify_remote(params: VerifyRemoteInput) -> str:
    """Authoritatively answer 'is this role remote?' for a named role at a company.

    One-shot: resolves the ATS, finds the best title match among live postings, and
    (when the listing's arrangement is unknown but a detail endpoint exists) fetches
    the detail for a firmer read. Verdicts:
      - remote-eligible : the posting states a fully remote arrangement
      - hybrid / onsite : the posting states a hybrid or onsite arrangement
      - ambiguous       : arrangement not stated; verify manually
      - not-found       : no title match on the board; verify manually
      - unresolved      : no ATS detected; try a hint_url or ats_scrape_careers_page

    Args:
        params (VerifyRemoteInput): company, title, optional hint_url, response_format.

    Returns:
        str: Markdown (default) or JSON {company, title, matched_title, found, verdict,
        workplace_type, location, source, url, confidence, reason}.
    """
    try:
        board = await detect_ats(params.company, hint_url=params.hint_url)
        if not board:
            r = {"company": params.company, "title": params.title, "found": False,
                 "verdict": "unresolved", "workplace_type": "unknown", "source": None,
                 "url": None, "confidence": 0.0,
                 "reason": "No ATS detected. Provide hint_url or use ats_scrape_careers_page, then verify manually."}
            return json.dumps(r, indent=2) if params.response_format == ResponseFormat.JSON else _verify_markdown(r)

        provider = provider_by_name(board.platform)
        postings = await provider.list_jobs(board, limit=100)
        match, score = best_match(params.title, postings)
        if not match:
            r = {"company": params.company, "title": params.title, "found": False,
                 "verdict": "not-found", "workplace_type": "unknown", "source": board.platform,
                 "url": None, "confidence": round(score, 3),
                 "reason": f"No title match for '{params.title}' among {len(postings)} live postings on {board.platform}."}
            return json.dumps(r, indent=2) if params.response_format == ResponseFormat.JSON else _verify_markdown(r)

        wt = match.workplace_type
        if wt == WorkplaceType.UNKNOWN.value and (match.job_id or match.url):
            try:
                detailed = await provider.get_job(board, job_id=match.job_id, url=match.url)
                if detailed and detailed.workplace_type != WorkplaceType.UNKNOWN.value:
                    match, wt = detailed, detailed.workplace_type
            except Exception:
                pass

        r = {"company": params.company, "title": params.title, "matched_title": match.title,
             "found": True, "verdict": _verdict_from(wt), "workplace_type": wt,
             "location": match.location, "source": match.source, "url": match.url,
             "confidence": round(score, 3), "reason": ""}
        return json.dumps(r, indent=2) if params.response_format == ResponseFormat.JSON else _verify_markdown(r)
    except Exception as e:
        return http_error_message(e, "verify_remote")


@mcp.tool(name="ats_scrape_careers_page", annotations={"title": "Scrape company careers page", **_READONLY})
async def ats_scrape_careers_page(params: ScrapeCareersInput) -> str:
    """Last-resort fallback: fetch a careers/posting page and parse the HTML.

    Use only when ats_resolve returns no ATS. Lowest reliability in the chain. Returns an
    inferred work arrangement plus any links that look like job postings or ATS boards, so
    you can pivot back to an authoritative ATS read via ats_resolve(hint_url=that link).

    Args:
        params (ScrapeCareersInput): url, response_format.

    Returns:
        str: Markdown (default) or JSON {title, url, workplace_type, excerpt, links}.
    """
    try:
        data = await CareersPage().fetch(params.url)
        if params.response_format == ResponseFormat.JSON:
            return json.dumps(data, indent=2)
        lines = [
            f"# Careers page: {data.get('title') or params.url}",
            "",
            f"- URL: {params.url}",
            f"- Inferred workplace: {data.get('workplace_type')}",
            "",
        ]
        if data.get("excerpt"):
            lines += ["Excerpt:", data["excerpt"], ""]
        links = data.get("links") or []
        if links:
            lines.append("Job / ATS links found:")
            for l in links:
                lines.append(f"- {l['label']}: {l['href']}")
            lines.append("")
        lines.append("Note: lowest-reliability fallback. If a link above points to a supported ATS "
                     "(greenhouse/lever/ashby/smartrecruiters), re-run ats_resolve "
                     "with that URL as hint_url for an authoritative read.")
        return "\n".join(lines)
    except Exception as e:
        return http_error_message(e, "scrape_careers_page")


if __name__ == "__main__":
    mcp.run()
