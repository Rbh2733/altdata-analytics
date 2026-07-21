"""Lever postings API (public, no auth).

List: GET https://api.lever.co/v0/postings/{token}?mode=json  -> JSON array

Lever exposes an explicit workplaceType field (remote | on-site | hybrid | unspecified),
so work arrangement is authoritative here.
"""
from __future__ import annotations

from typing import List, Optional

from ..http_client import get_json, probe_json
from ..models import Posting
from ..normalize import infer_workplace_type
from .base import ATSProvider, BoardRef, host_of, path_parts, ms_to_iso, excerpt

API = "https://api.lever.co/v0/postings"


def parse_jobs(data, token: str) -> List[Posting]:
    items = data if isinstance(data, list) else []
    out: List[Posting] = []
    for j in items:
        cats = j.get("categories") or {}
        loc = cats.get("location")
        out.append(Posting(
            title=j.get("text", ""),
            location=loc,
            workplace_type=infer_workplace_type(location=loc, explicit=j.get("workplaceType")),
            department=cats.get("department") or cats.get("team"),
            url=j.get("hostedUrl") or j.get("applyUrl"),
            posted_at=ms_to_iso(j.get("createdAt")),
            source="lever",
            job_id=str(j["id"]) if j.get("id") else None,
            description_excerpt=excerpt(j.get("descriptionPlain") or j.get("description")),
        ))
    return out


class Lever(ATSProvider):
    name = "lever"

    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        for slug in candidates:
            data = await probe_json(f"{API}/{slug}", params={"mode": "json"})
            if isinstance(data, list):
                return BoardRef(platform=self.name, token=slug)
        return None

    def from_url(self, url: str) -> Optional[BoardRef]:
        h = host_of(url)
        if "lever.co" not in h:
            return None
        parts = path_parts(url)
        if "postings" in parts:
            i = parts.index("postings")
            if i + 1 < len(parts):
                return BoardRef(platform=self.name, token=parts[i + 1], detected_via="hint_url")
        if parts:
            return BoardRef(platform=self.name, token=parts[0], detected_via="hint_url")
        return None

    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        data = await get_json(f"{API}/{board.token}", params={"mode": "json"})
        return parse_jobs(data, board.token)[:limit]
