"""Provider registry and the detection chain.

Detection order matters: providers are probed in a fixed order, all of them public
unauthenticated JSON APIs. The company-site HTML scraper is a separate fallback,
invoked by the caller only when detect_ats returns None.
"""
from __future__ import annotations

from typing import List, Optional

from ..normalize import slug_candidates
from .base import ATSProvider, BoardRef
from .greenhouse import Greenhouse
from .lever import Lever
from .ashby import Ashby
from .smartrecruiters import SmartRecruiters

_PROVIDERS: List[ATSProvider] = [Greenhouse(), Lever(), Ashby(), SmartRecruiters()]


def all_providers() -> List[ATSProvider]:
    return list(_PROVIDERS)


def provider_by_name(name: str) -> Optional[ATSProvider]:
    for p in _PROVIDERS:
        if p.name == name:
            return p
    return None


def from_any_url(url: str) -> Optional[BoardRef]:
    """Identify the ATS and board directly from a URL (the aggregator redirect target)."""
    for p in _PROVIDERS:
        ref = p.from_url(url)
        if ref:
            return ref
    return None


async def detect_ats(company: str, hint_url: Optional[str] = None) -> Optional[BoardRef]:
    """Resolve a company to an ATS board: hint_url first (exact), then slug probing."""
    if hint_url:
        ref = from_any_url(hint_url)
        if ref:
            return ref
    candidates = slug_candidates(company)
    for p in _PROVIDERS:
        ref = await p.detect(candidates)
        if ref:
            return ref
    return None
