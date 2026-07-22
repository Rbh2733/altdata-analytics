"""Provider interface (registry pattern), BoardRef, and small shared helpers.

Each ATS provider implements the same interface, so the registry can iterate them in a
fixed detection order. Parse logic lives in module-level pure functions (parse_jobs) so
tests can exercise it against fixtures with no network.
"""
from __future__ import annotations

import html
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

from pydantic import BaseModel, ConfigDict

from ..models import Posting


class BoardRef(BaseModel):
    """Points at one company's board on one ATS."""
    model_config = ConfigDict(extra="ignore")

    platform: str                 # greenhouse | lever | ashby | smartrecruiters | careers_page
    token: str                    # board slug
    extra: dict = {}              # platform-specific extras
    detected_via: str = "slug"    # slug | hint_url


class ATSProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def detect(self, candidates: List[str]) -> Optional[BoardRef]:
        """Probe this ATS for any candidate slug; return a BoardRef or None."""

    @abstractmethod
    def from_url(self, url: str) -> Optional[BoardRef]:
        """Parse a board/posting URL belonging to this ATS; return BoardRef or None."""

    @abstractmethod
    async def list_jobs(self, board: BoardRef, limit: int = 25) -> List[Posting]:
        ...

    async def get_job(self, board: BoardRef, job_id: Optional[str] = None,
                      url: Optional[str] = None) -> Optional[Posting]:
        """Default: pull the list and match by id or url. Providers override for detail endpoints."""
        jobs = await self.list_jobs(board, limit=200)
        if job_id:
            for j in jobs:
                if j.job_id == str(job_id):
                    return j
        if url:
            u = url.rstrip("/")
            for j in jobs:
                if j.url and j.url.rstrip("/") == u:
                    return j
        return None


# --------------------------- shared helpers ---------------------------

def host_of(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def path_parts(url: str) -> List[str]:
    try:
        return [p for p in urlparse(url).path.split("/") if p]
    except Exception:
        return []


def query_param(url: str, key: str) -> Optional[str]:
    try:
        vals = parse_qs(urlparse(url).query).get(key)
        return vals[0] if vals else None
    except Exception:
        return None


def ms_to_iso(ms) -> Optional[str]:
    """Epoch milliseconds -> ISO date (Lever timestamps)."""
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return None


_TAG_RE = re.compile(r"<[^>]+>")


def excerpt(text: Optional[str], n: int = 240) -> Optional[str]:
    """Strip HTML/whitespace and truncate, for description previews."""
    if not text:
        return None
    clean = html.unescape(_TAG_RE.sub(" ", text))
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return None
    return clean[:n] + ("..." if len(clean) > n else "")
