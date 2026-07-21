"""Entity resolution: raw merchant strings to canonical vendors.

Three stages, cheapest first, each stage only touching what the prior one
could not settle:
  1. exact        normalized string equals a known alias, or contains one as
                  a whole-token span (longest alias wins, so "TWILIO SENDGRID"
                  resolves to SendGrid, not Twilio)
  2. fuzzy        blocked candidate set scored with difflib plus token
                  containment; auto-accept at or above AUTO_T, review band
                  between REVIEW_T and AUTO_T
  3. (tail)       everything else goes to the tagger (see tagger_*.py)

Scores and methods travel with every row so the evaluation can price each
stage's precision separately instead of reporting one blended number.
"""

import csv
import math
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from normalize import normalize

DATA = Path(__file__).resolve().parent.parent / "data"
AUTO_T = 0.90
REVIEW_T = 0.78


def load_vendors():
    vendors = []
    with open(DATA / "canonical_vendors.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            aliases = [normalize(a) for a in row["aliases"].split("|")]
            vendors.append({"vendor": row["vendor"], "category": row["category"],
                            "aliases": sorted(set(a for a in aliases if a))})
    return vendors


def build_indexes(vendors):
    exact = {}
    blocks = defaultdict(set)
    for i, v in enumerate(vendors):
        for a in v["aliases"]:
            exact[a] = i
            blocks[a[:3]].add(i)
            for tok in a.split():
                blocks[tok[:3]].add(i)
    # containment scans longest-first so the most specific alias wins
    by_length = sorted(exact.items(), key=lambda kv: -len(kv[0]))
    return exact, blocks, by_length


def contains_alias(core: str, alias: str) -> bool:
    """Whole-token containment, checking every occurrence, not just the first."""
    start = 0
    while True:
        i = core.find(alias, start)
        if i < 0:
            return False
        before_ok = i == 0 or not core[i - 1].isalnum()
        j = i + len(alias)
        after_ok = j == len(core) or not core[j].isalnum()
        if before_ok and after_ok:
            return True
        start = i + 1


def fuzzy_score(core: str, alias: str) -> float:
    ratio = SequenceMatcher(None, core, alias).ratio()
    core_toks, alias_toks = set(core.split()), set(alias.split())
    overlap = len(core_toks & alias_toks) / max(1, len(alias_toks))
    prefix = 0.15 if core.startswith(alias[: max(4, len(alias) // 2)]) else 0.0
    return min(1.0, 0.55 * ratio + 0.35 * overlap + prefix)


def band_floor(score: float) -> float:
    """Round toward the band so the printed score never crosses a threshold."""
    return math.floor(score * 1000) / 1000


def resolve_one(core: str, vendors, exact, blocks, by_length):
    if core in exact:
        return vendors[exact[core]], "exact", 1.0
    for a, i in by_length:
        if len(a) >= 3 and contains_alias(core, a):
            return vendors[i], "exact", 0.98
    cand = set()
    for tok in core.split():
        cand |= blocks.get(tok[:3], set())
    if not cand:
        cand = set(range(len(vendors)))
    best, best_score = None, 0.0
    for i in cand:
        for a in vendors[i]["aliases"]:
            s = fuzzy_score(core, a)
            if s > best_score:
                best, best_score = i, s
    if best is not None and best_score >= AUTO_T:
        return vendors[best], "fuzzy_auto", band_floor(best_score)
    if best is not None and best_score >= REVIEW_T:
        return vendors[best], "review", band_floor(best_score)
    return None, "unmatched", band_floor(best_score)


def run():
    vendors = load_vendors()
    exact, blocks, by_length = build_indexes(vendors)
    out = []
    with open(DATA / "transactions.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            core = normalize(row["raw_string"])
            vendor, method, score = resolve_one(core, vendors, exact, blocks, by_length)
            out.append({
                "raw_id": row["raw_id"], "week": row["week"],
                "raw_string": row["raw_string"], "amount": row["amount"],
                "core": core, "method": method, "score": score,
                "vendor": vendor["vendor"] if vendor else "",
                "category": vendor["category"] if vendor else "",
            })
    return out


if __name__ == "__main__":
    rows = run()
    from collections import Counter
    print(Counter(r["method"] for r in rows))
