"""Pure helpers: slug generation, workplace-type inference, title matching, formatting.

Everything here is deterministic and side-effect free, so it is unit-tested against
fixtures with no network access.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .models import Posting, WorkplaceType

_LEGAL = {
    "inc", "llc", "ltd", "limited", "corp", "corporation", "co", "company",
    "plc", "gmbh", "sa", "ag", "nv", "group", "holdings", "the", "and",
}

_REMOTE_KW = ("remote", "work from home", "wfh", "fully distributed", "work anywhere", "anywhere")
_HYBRID_KW = ("hybrid", "flex office", "flexible location")
_ONSITE_KW = ("on-site", "on site", "onsite", "in-office", "in office", "in-person", "in person")


def _tokens(text: str) -> List[str]:
    """Tokenize a name/title into clean alphanumeric tokens (apostrophe-safe).

    Split on whitespace/hyphen/underscore, then strip every non-alphanumeric mark from
    each token, so "Grimble's" becomes "grimbles" without depending on any apostrophe
    code point (robust to file-encoding round-trips).
    """
    out: List[str] = []
    for tok in re.split(r"[\s\-_]+", text.lower()):
        cleaned = re.sub(r"[^a-z0-9]+", "", tok)
        if cleaned:
            out.append(cleaned)
    return out


def slug_candidates(company: str) -> List[str]:
    """Generate likely ATS board slugs from a company name, most-likely first."""
    raw = company.strip().lower()
    toks = [t for t in _tokens(raw) if t not in _LEGAL]
    if not toks:
        toks = _tokens(raw)
    joined = "".join(toks)
    out: List[str] = []
    for cand in (joined, "-".join(toks), "_".join(toks), re.sub(r"[^a-z0-9]", "", raw)):
        if cand and cand not in out:
            out.append(cand)
    return out


def infer_workplace_type(location: Optional[str] = None, extra: Optional[str] = None,
                         explicit: Optional[str] = None) -> WorkplaceType:
    """Map an explicit ATS workplace field, or infer from location text. Explicit wins."""
    if explicit:
        e = explicit.strip().lower()
        if "hybrid" in e:
            return WorkplaceType.HYBRID
        if "remote" in e:
            return WorkplaceType.REMOTE
        if any(k in e for k in ("on-site", "on site", "onsite", "office", "in person", "in-person")):
            return WorkplaceType.ONSITE
    blob = " ".join(x for x in (location, extra) if x).lower()
    if not blob:
        return WorkplaceType.UNKNOWN
    if any(k in blob for k in _HYBRID_KW):
        return WorkplaceType.HYBRID
    if any(k in blob for k in _REMOTE_KW):
        return WorkplaceType.REMOTE
    if any(k in blob for k in _ONSITE_KW):
        return WorkplaceType.ONSITE
    return WorkplaceType.UNKNOWN


def title_match_score(query: str, title: str) -> float:
    """Fraction of query tokens present in the title (0..1), with an exact-substring boost."""
    q = _tokens(query)
    if not q:
        return 0.0
    t = set(_tokens(title))
    overlap = sum(1 for tok in q if tok in t) / len(q)
    if query.strip().lower() in title.strip().lower():
        overlap = max(overlap, 0.95)
    return round(overlap, 3)


def best_match(query: str, postings: List[Posting], threshold: float = 0.5) -> Tuple[Optional[Posting], float]:
    """Return (posting, score) for the best title match above threshold, else (None, best_score)."""
    best: Optional[Posting] = None
    best_score = 0.0
    for p in postings:
        s = title_match_score(query, p.title)
        if s > best_score:
            best, best_score = p, s
    if best is not None and best_score >= threshold:
        return best, best_score
    return None, best_score


def filter_postings(postings: List[Posting], query: Optional[str] = None,
                    location: Optional[str] = None) -> List[Posting]:
    out = postings
    if query:
        ql = query.lower()
        out = [p for p in out if ql in p.title.lower()]
    if location:
        ll = location.lower()
        out = [p for p in out if p.location and ll in p.location.lower()]
    return out


def postings_to_markdown(postings: List[Posting], header: str) -> str:
    lines = [f"# {header}", "", f"{len(postings)} posting(s).", ""]
    for p in postings:
        lines.append(f"## {p.title}")
        if p.company:
            lines.append(f"- Company: {p.company}")
        lines.append(f"- Workplace: {p.workplace_type}")
        if p.location:
            lines.append(f"- Location: {p.location}")
        if p.department:
            lines.append(f"- Department: {p.department}")
        if p.posted_at:
            lines.append(f"- Posted: {p.posted_at}")
        lines.append(f"- Source: {p.source}")
        if p.url:
            lines.append(f"- URL: {p.url}")
        lines.append("")
    return "\n".join(lines).strip()
