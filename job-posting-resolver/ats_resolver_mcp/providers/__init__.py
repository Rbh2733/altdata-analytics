"""ATS provider package: registry pattern, one provider per platform."""
from .base import ATSProvider, BoardRef
from .careers_page import CareersPage, parse_page
from .registry import all_providers, detect_ats, from_any_url, provider_by_name

__all__ = [
    "ATSProvider",
    "BoardRef",
    "CareersPage",
    "parse_page",
    "all_providers",
    "detect_ats",
    "from_any_url",
    "provider_by_name",
]
