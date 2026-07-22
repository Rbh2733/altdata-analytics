"""Last-resort fallback: fetch a company careers/posting page and parse the HTML.

Lowest reliability in the chain; used only when no ATS API is detected. Returns a
best-effort read: a workplace-type inference from the visible text plus any links that
look like job postings or ATS boards (so the caller can pivot back to an ATS).
"""
from __future__ import annotations

from typing import Any, Dict

from bs4 import BeautifulSoup

from ..http_client import get_text
from ..normalize import infer_workplace_type
from .base import excerpt

_ATS_HINTS = ("greenhouse", "lever.co", "ashbyhq", "smartrecruiters", "myworkdayjobs",
              "jobvite", "icims", "workable", "bamboohr", "/job", "/careers", "/positions")


def parse_page(html_text: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html_text, "html.parser")
    title = soup.title.string.strip() if (soup.title and soup.title.string) else None
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else None
    text = soup.get_text(" ", strip=True)
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        label = a.get_text(strip=True)
        if label and any(k in href.lower() for k in _ATS_HINTS) and href not in seen:
            seen.add(href)
            links.append({"label": label[:120], "href": href})
    wt = infer_workplace_type(extra=text[:6000])
    return {
        "title": h1_text or title,
        "url": url,
        "workplace_type": wt.value,
        "excerpt": excerpt(text, 400),
        "links": links[:25],
    }


class CareersPage:
    """Standalone fallback (not part of the slug-detection registry)."""
    name = "careers_page"

    async def fetch(self, url: str) -> Dict[str, Any]:
        html_text = await get_text(url)
        return parse_page(html_text, url)
