"""Greenhouse Job Board API (public, no auth).

List:   GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs[?content=true]
Detail: GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}

Greenhouse has no dedicated remote flag in the list schema, so work arrangement is
inferred from location.name ("Remote", "Remote - US") and, on detail, the description.
"""
from __future__ import annotations

from typing import List, Optional

from ..http_client import get_json, probe_json
from ..models import Posting
from ..normalize import infer_workplace_type
from .base import ATSProvider, BoardRef, host_of, path_parts, query_param, excerpt

API = "https://boards-api.greenhouse.io/v1/boards"


def parse_jobs(data, token: str) -> List[Posting]:
    jobs = data.get("jobs", []) if isinstance(data, dict) else []
    out: List[Posting] = []
    for j in jobs:
        loc = (j.get("location") or {}).get("name")
        depts = j.get("departments") or []
        dept = depts[0].get("name") if depts and isinstance(depts[0], dict) else None
        out.append(Posting(
            title=j.get("title", ""),
            location=loc,
            workplace_type=infer_workplace_type(location=loc),
            department=dept,
            url=j.get("absolute_url"),
            posted_at=j.get("updated_at"),
            source="greenhouse",
            job_id=str(j["id"]) if j.get("id") is not None else None,
        ))
    return out


def parse_job_detail(j, token: str) -> Posting:
    loc = (j.get("location") or {}).get("name")
    ex = excerpt(j.get("content"))
    return Posting(
        title=j.get("title", ""),
        location=loc,
        workplace_type=infer_workplace_type(location=loc, extra=ex),
        url=j.get("absolute_url"),
        posted_at=j.get("updated_at"),
        source="greenhouse",
        job_id=str(j["id"]) if j.get("id") is not None else None,
        description_excerpt=ex,
    )


class Greenhouse(ATSProvider):
    name = "greenhouse"

    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        for slug in candidates:
            data = await probe_json(f"{API}/{slug}/jobs")
            if isinstance(data, dict) and "jobs" in data:
                return BoardRef(platform=self.name, token=slug)
        return None

    def from_url(self, url: str) -> Optional[BoardRef]:
        h = host_of(url)
        if "greenhouse.io" not in h:
            return None
        for_token = query_param(url, "for")  # embedded board: ...?for={token}
        if for_token:
            return BoardRef(platform=self.name, token=for_token, detected_via="hint_url")
        parts = path_parts(url)
        if "boards-api" in h and len(parts) >= 3 and parts[0] == "v1" and parts[1] == "boards":
            return BoardRef(platform=self.name, token=parts[2], detected_via="hint_url")
        if parts:
            return BoardRef(platform=self.name, token=parts[0], detected_via="hint_url")
        return None

    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        data = await get_json(f"{API}/{board.token}/jobs")
        return parse_jobs(data, board.token)[:limit]

    async def get_job(self, board: BoardRef, job_id: Optional[str] = None,
                      url: Optional[str] = None) -> Optional[Posting]:
        if url and not job_id:
            parts = path_parts(url)
            if "jobs" in parts:
                i = parts.index("jobs")
                if i + 1 < len(parts):
                    job_id = parts[i + 1]
        if job_id:
            data = await get_json(f"{API}/{board.token}/jobs/{job_id}")
            if isinstance(data, dict) and data.get("id") is not None:
                return parse_job_detail(data, board.token)
        return await super().get_job(board, job_id=job_id, url=url)
