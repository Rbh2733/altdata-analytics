"""iCIMS hosted boards (public, no auth, HTML only).

iCIMS exposes no public JSON API, so this provider reads the compact iframe view of the
board search page and parses the job rows:

    https://careers-{token}.icims.com/jobs/search?ss=1&in_iframe=1&pr={page}

That view is roughly a fifth the size of the full page and carries the same rows. Each row
is a labelled block, "Job Locations | <location> | Title | <title> | <excerpt>", with the
title anchored to /jobs/{id}/{slug}/job.

Board tokens are predictable, which is why detection works here from the company name alone
(unlike Workday). Both the careers-{token} and bare {token} host forms are probed.

This is an HTML read of a public listing page, single-page and low-volume, in the same
spirit as the careers_page fallback: it never crawls, and it paginates only far enough to
satisfy the caller's limit.
"""
from __future__ import annotations

import re
from typing import List, Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..http_client import get_text, probe_text
from ..models import Posting
from ..normalize import infer_workplace_type
from .base import ATSProvider, BoardRef, host_of

_JOB_HREF = re.compile(r"/jobs/(\d+)/")
_HOST_RE = re.compile(r"^(?:careers-)?([a-z0-9\-]+)\.icims\.com$", re.I)
_LOC_RE = re.compile(r"Job\s+Locations?\s*\|\s*([^|]+)")
PAGE_SIZE = 12  # iCIMS default rows per search page


def board_url(token: str, page: int = 0, careers_prefix: bool = True) -> str:
    host = f"careers-{token}" if careers_prefix else token
    return f"https://{host}.icims.com/jobs/search?ss=1&in_iframe=1&pr={page}"


def parse_jobs(html: str, token: str) -> List[Posting]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set = set()
    out: List[Posting] = []
    for a in soup.find_all("a", href=True):
        m = _JOB_HREF.search(a["href"])
        if not m:
            continue
        job_id = m.group(1)
        if job_id in seen:
            continue
        seen.add(job_id)

        title = a.get_text(" ", strip=True)
        title = re.sub(r"^Title\s*", "", title).strip()
        if not title:
            continue

        # walk up to the enclosing row to pick up the labelled location field
        loc = None
        node = a
        for _ in range(6):
            node = node.parent
            if node is None:
                break
            classes = " ".join(node.get("class") or []).lower()
            if "row" in classes:
                lm = _LOC_RE.search(node.get_text(" | ", strip=True))
                if lm:
                    loc = lm.group(1).strip()
                break

        out.append(Posting(
            title=title,
            location=loc,
            workplace_type=infer_workplace_type(location=loc),
            department=None,
            url=unquote(a["href"]),
            posted_at=None,
            source="icims",
            job_id=job_id,
        ))
    return out


class ICIMS(ATSProvider):
    name = "icims"

    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        for slug in candidates:
            for prefix in (True, False):
                html = await probe_text(board_url(slug, 0, prefix))
                if not html or "icims" not in html.lower():
                    continue
                n = len(parse_jobs(html, slug))
                return BoardRef(platform=self.name, token=slug, observed_count=n,
                                confidence="high" if n > 0 else "low",
                                extra={"careers_prefix": prefix})
        return None

    def from_url(self, url: str) -> Optional[BoardRef]:
        h = host_of(url)
        m = _HOST_RE.match(h)
        if not m:
            return None
        return BoardRef(platform=self.name, token=m.group(1), detected_via="hint_url",
                        extra={"careers_prefix": h.startswith("careers-")})

    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        prefix = board.extra.get("careers_prefix", True)
        out: List[Posting] = []
        page = 0
        while len(out) < limit and page < 12:  # hard page cap, never crawl
            html = await get_text(board_url(board.token, page, prefix))
            batch = parse_jobs(html, board.token)
            if not batch:
                break
            known = {p.job_id for p in out}
            fresh = [p for p in batch if p.job_id not in known]
            if not fresh:
                break
            out.extend(fresh)
            if len(batch) < PAGE_SIZE:
                break
            page += 1
        return out[:limit]
