"""Shared async HTTP helpers.

stdio MCP servers must never write to stdout, so nothing here prints; failures either
raise AtsHttpError (surfaced as a tool result) or return None for detection probes.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx

DEFAULT_TIMEOUT = 20.0
PROBE_TIMEOUT = 10.0
USER_AGENT = "job-posting-resolver/0.1 (+local)"
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/html;q=0.8, */*;q=0.5",
}


class AtsHttpError(Exception):
    """Unrecoverable HTTP problem, carrying an actionable message for the caller."""


def _client(timeout: float = DEFAULT_TIMEOUT) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, headers=HEADERS, follow_redirects=True)


async def get_json(url: str, params: Optional[dict] = None, timeout: float = DEFAULT_TIMEOUT) -> Any:
    async with _client(timeout) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def get_text(url: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    async with _client(timeout) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def probe_json(url: str, params: Optional[dict] = None, timeout: float = PROBE_TIMEOUT) -> Optional[Any]:
    """Return parsed JSON if the endpoint returns 200 JSON, else None.

    Used for ATS detection: a 404 or decode failure simply means 'not this ATS / not
    this slug', which is a normal, expected outcome and must not raise.
    """
    try:
        async with _client(timeout) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            return resp.json()
    except (httpx.HTTPError, ValueError):
        return None


def http_error_message(e: Exception, context: str = "") -> str:
    """Consistent, actionable error text."""
    prefix = f"Error ({context}): " if context else "Error: "
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 404:
            return prefix + "not found (404). The board slug or URL is likely wrong; try ats_resolve with a hint_url."
        if code == 403:
            return prefix + "access denied (403). The ATS may be gating its API; fall back to ats_scrape_careers_page."
        if code == 429:
            return prefix + "rate limited (429). Wait and retry, or reduce the number of probes."
        return prefix + f"HTTP {code} from the ATS endpoint."
    if isinstance(e, httpx.TimeoutException):
        return prefix + "request timed out. The ATS may be slow; retry once or use a hint_url."
    if isinstance(e, AtsHttpError):
        return prefix + str(e)
    return prefix + f"unexpected {type(e).__name__}: {e}"
