"""Ashby job board posting API (public, no auth).

List: GET https://api.ashbyhq.com/posting-api/job-board/{token}  -> {"jobs": [...]}

Ashby exposes an explicit isRemote boolean, so remote is authoritative; hybrid/onsite
fall back to location-text inference.
"""
from __future__ import annotations

from typing import List, Optional

from ..http_client import get_json, probe_json
from ..models import Posting
from ..normalize import infer_workplace_type
from .base import ATSProvider, BoardRef, host_of, path_parts, excerpt

API = "https://api.ashbyhq.com/posting-api/job-board"


def parse_jobs(data, token: str) -> List[Posting]:
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out: List[Posting] = []
    for j in jobs:
        loc = j.get("location")
        explicit = "remote" if j.get("isRemote") else None
        out.append(Posting(
            title=j.get("title", ""),
            location=loc,
            workplace_type=infer_workplace_type(location=loc, explicit=explicit),
            department=j.get("department") or j.get("team"),
            url=j.get("jobUrl") or j.get("applyUrl"),
            posted_at=j.get("publishedAt"),
            source="ashby",
            job_id=str(j["id"]) if j.get("id") else None,
            description_excerpt=excerpt(j.get("descriptionPlain")),
        ))
    return out


class Ashby(ATSProvider):
    name = "ashby"

    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        for slug in candidates:
            data = await probe_json(f"{API}/{slug}")
            if isinstance(data, dict) and "jobs" in data:
                return BoardRef(platform=self.name, token=slug)
        return None

    def from_url(self, url: str) -> Optional[BoardRef]:
        h = host_of(url)
        if "ashbyhq.com" not in h:
            return None
        parts = path_parts(url)
        if "job-board" in parts:
            i = parts.index("job-board")
            if i + 1 < len(parts):
                return BoardRef(platform=self.name, token=parts[i + 1], detected_via="hint_url")
        if parts:
            return BoardRef(platform=self.name, token=parts[0], detected_via="hint_url")
        return None

    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        data = await get_json(f"{API}/{board.token}")
        return parse_jobs(data, board.token)[:limit]
