"""SmartRecruiters Posting API (public, no auth).

List: GET https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100
      -> {"content": [...], "totalFound": N}
Public posting URL: https://jobs.smartrecruiters.com/{token}/{postingId}

location.remote boolean is authoritative.
"""
from __future__ import annotations

from typing import List, Optional

from ..http_client import get_json, probe_json
from ..models import Posting
from ..normalize import infer_workplace_type
from .base import ATSProvider, BoardRef, host_of, path_parts

API = "https://api.smartrecruiters.com/v1/companies"


def parse_jobs(data, token: str) -> List[Posting]:
    items = data.get("content", []) if isinstance(data, dict) else []
    out: List[Posting] = []
    for j in items:
        loc_obj = j.get("location") or {}
        city, region, country = loc_obj.get("city"), loc_obj.get("region"), loc_obj.get("country")
        remote = loc_obj.get("remote")
        loc_str = ", ".join([x for x in (city, region, country) if x]) or ("Remote" if remote else None)
        pid = j.get("id")
        dept = j.get("department")
        dept_label = dept.get("label") if isinstance(dept, dict) else None
        out.append(Posting(
            title=j.get("name", ""),
            location=loc_str,
            workplace_type=infer_workplace_type(location=loc_str, explicit=("remote" if remote else None)),
            department=dept_label,
            url=f"https://jobs.smartrecruiters.com/{token}/{pid}" if pid else j.get("ref"),
            posted_at=j.get("releasedDate"),
            source="smartrecruiters",
            job_id=str(pid) if pid else None,
        ))
    return out


class SmartRecruiters(ATSProvider):
    name = "smartrecruiters"

    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        for slug in candidates:
            data = await probe_json(f"{API}/{slug}/postings", params={"limit": 1})
            if isinstance(data, dict) and "content" in data:
                return BoardRef(platform=self.name, token=slug)
        return None

    def from_url(self, url: str) -> Optional[BoardRef]:
        h = host_of(url)
        if "smartrecruiters.com" not in h:
            return None
        parts = path_parts(url)
        if parts:
            return BoardRef(platform=self.name, token=parts[0], detected_via="hint_url")
        return None

    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        data = await get_json(f"{API}/{board.token}/postings", params={"limit": min(limit, 100)})
        return parse_jobs(data, board.token)[:limit]
