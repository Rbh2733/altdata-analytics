"""Workday CXS job-search API (public, no auth).

List: POST https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
      body {"appliedFacets":{},"limit":20,"offset":0,"searchText":""}
      -> {"total": N, "jobPostings": [{title, externalPath, locationsText, postedOn}]}

Public posting URL: https://{tenant}.{wd}.myworkdayjobs.com/en-US/{site}{externalPath}

Detection honesty: a Workday board is addressed by THREE unknowns (tenant, the wdN shard,
and the site name), so guessing all three from a company name is unreliable. from_url is
exact and is the intended path. detect() runs a deliberately small best-effort matrix over
the most common shards and site names and gives up rather than probing dozens of URLs.
"""
from __future__ import annotations

import asyncio
import re
from typing import List, Optional

from ..http_client import post_json, probe_post_json
from ..models import Posting
from ..normalize import infer_workplace_type
from .base import ATSProvider, BoardRef, host_of, path_parts

_HOST_RE = re.compile(r"^([a-z0-9\-]+)\.(wd\d+)\.myworkdayjobs\.com$", re.I)
_SHARDS = ("wd1", "wd5", "wd3")
# Trimmed 2026-07-25 after measuring: each probe is a fresh TLS connection against a
# wildcard-DNS host, so matrix size is wall-clock. "External" plus the capitalised slug
# covered every Workday board that resolved in the 90-company scan (SailPoint, Comscore,
# Acrisure, DraftKings, Datasite). Anything beyond that is a slug problem, not a site one.
_SITES = ("External",)
_PROBE_TIMEOUT = 6.0  # a live CXS endpoint answers well inside this


def cxs_url(tenant: str, shard: str, site: str) -> str:
    return f"https://{tenant}.{shard}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"


def parse_jobs(data, tenant: str, shard: str, site: str) -> List[Posting]:
    items = data.get("jobPostings", []) if isinstance(data, dict) else []
    base = f"https://{tenant}.{shard}.myworkdayjobs.com/en-US/{site}"
    out: List[Posting] = []
    for j in items:
        loc = j.get("locationsText")
        path = j.get("externalPath") or ""
        out.append(Posting(
            title=j.get("title", ""),
            location=loc,
            workplace_type=infer_workplace_type(location=loc),
            department=None,
            url=(base + path) if path else None,
            posted_at=j.get("postedOn"),
            source="workday",
            job_id=(path.rsplit("_", 1)[-1] if "_" in path else None),
        ))
    return out


class Workday(ATSProvider):
    name = "workday"

    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        """Best-effort only, and deliberately CONCURRENT.

        A Workday board is addressed by three unknowns (tenant, wdN shard, site), so
        detection is a matrix rather than a single lookup. The first version walked that
        matrix sequentially, which was a real mistake: *.myworkdayjobs.com resolves via
        wildcard DNS, so a miss costs a full round trip (~4s measured) instead of failing
        fast on DNS. Sequentially that is ~47s per slug candidate and ~140s per company,
        which made a 90-company scan unusable.

        The probes are independent, so they run together and the first hit wins. Per-company
        cost becomes roughly one round trip instead of the sum of all of them. The matrix is
        also trimmed to the primary slug candidate only; alternate slugs are a slug-derivation
        problem better solved by a careers-page pivot than by multiplying probes here.
        """
        if not candidates:
            return None
        slug = candidates[0]
        combos = [(shard, site)
                  for shard in _SHARDS
                  for site in (slug.capitalize(),) + _SITES]

        async def probe(shard: str, site: str):
            data = await probe_post_json(
                cxs_url(slug, shard, site),
                {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""},
                timeout=_PROBE_TIMEOUT,
            )
            if isinstance(data, dict) and "jobPostings" in data:
                return shard, site, int(data.get("total") or len(data.get("jobPostings") or []))
            return None

        results = await asyncio.gather(*(probe(s, t) for s, t in combos),
                                       return_exceptions=True)
        hits = [r for r in results if isinstance(r, tuple)]
        if not hits:
            return None
        # prefer a board that actually has postings over an empty-but-valid one
        hits.sort(key=lambda h: -h[2])
        shard, site, n = hits[0]
        return BoardRef(platform=self.name, token=slug, observed_count=n,
                        confidence="high" if n > 0 else "low",
                        extra={"shard": shard, "site": site})

    def from_url(self, url: str) -> Optional[BoardRef]:
        m = _HOST_RE.match(host_of(url))
        if not m:
            return None
        tenant, shard = m.group(1), m.group(2).lower()
        # path is /{locale}/{site}/... ; locale segments look like en-US
        parts = path_parts(url)
        site = None
        for p in parts:
            if re.fullmatch(r"[a-z]{2}-[A-Z]{2}", p):
                continue
            site = p
            break
        if not site:
            return None
        return BoardRef(platform=self.name, token=tenant, detected_via="hint_url",
                        extra={"shard": shard, "site": site})

    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        shard = board.extra.get("shard", "wd1")
        site = board.extra.get("site", "External")
        out: List[Posting] = []
        offset = 0
        while len(out) < limit:
            page = min(20, limit - len(out))
            data = await post_json(
                cxs_url(board.token, shard, site),
                {"appliedFacets": {}, "limit": page, "offset": offset, "searchText": ""},
            )
            batch = parse_jobs(data, board.token, shard, site)
            if not batch:
                break
            out.extend(batch)
            offset += len(batch)
            if offset >= int(data.get("total") or 0):
                break
        return out[:limit]
