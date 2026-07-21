"""Deterministic stand-in for the LLM tagger.

The validation harness (holdout scoring, drift checks, QA sampling) is
model-agnostic. This mock lets the whole lab run reproducibly with no API
key, so the numbers in the README are checkable by anyone. Swap in
tagger_claude.py for a live model behind the same interface.

Interface: tag(rows) -> list of dicts with vendor_guess, category_guess,
confidence, new_vendor_flag. A row is a resolver output dict.
"""

from difflib import SequenceMatcher

CATEGORY_KEYWORDS = [
    ("AI and ML Platforms", ["AI", "ML", "GPT", "CLAUDE", "LLM", "NEURAL", "VECTOR", "MODEL"]),
    ("Cloud Infrastructure", ["CLOUD", "COMPUTE", "HOST", "SERVER", "GRID", "EDGE", "CDN"]),
    ("Data Infrastructure", ["DATA", "DB", "ANALYTIC", "WAREHOUSE", "PIPELINE", "QUERY"]),
    ("Developer Tools", ["DEV", "CODE", "GIT", "CI", "BUILD", "SYSTEMS", "LABS"]),
    ("Security", ["SEC", "AUTH", "TRUST", "SHIELD", "GUARD"]),
    ("Payments and Fintech", ["PAY", "BILL", "FIN", "CARD", "TREASURY"]),
    ("SaaS Productivity", ["DOC", "TEAM", "WORK", "MEET", "NOTE"]),
]


def _loose_vendor_guess(core: str, vendors):
    best, best_score = None, 0.0
    for v in vendors:
        for a in v["aliases"]:
            s = SequenceMatcher(None, core, a).ratio()
            if s > best_score:
                best, best_score = v, s
    if best is not None and best_score >= 0.60:
        return best, round(best_score, 3)
    return None, round(best_score, 3)


def _category_guess(core: str) -> str:
    scores = []
    for cat, kws in CATEGORY_KEYWORDS:
        hits = sum(1 for kw in kws if kw in core)
        scores.append((hits, cat))
    hits, cat = max(scores)
    return cat if hits > 0 else "Unclassified"


def tag(rows, vendors):
    out = []
    for r in rows:
        core = r["core"]
        vendor, score = _loose_vendor_guess(core, vendors)
        if vendor is not None:
            out.append({"raw_id": r["raw_id"], "vendor_guess": vendor["vendor"],
                        "category_guess": vendor["category"],
                        "confidence": score, "new_vendor_flag": 0})
        else:
            out.append({"raw_id": r["raw_id"], "vendor_guess": "",
                        "category_guess": _category_guess(core),
                        "confidence": score, "new_vendor_flag": 1})
    return out
