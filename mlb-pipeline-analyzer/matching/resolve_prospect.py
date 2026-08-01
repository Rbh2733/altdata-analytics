"""Entity resolution: a ranked prospect name to an official MLBAM player id.

Copied from this repo's earlier baseball project. Staged cheapest-first,
each stage only touching what the prior one could not settle:

  1. exact        normalized name matches an indexed name variant exactly.
                  Unambiguous hit only: if a normalized name maps to more
                  than one player, it falls through rather than guessing.
  2. blocked fuzzy  candidates blocked on surname, scored on sequence
                  similarity plus token overlap. Auto-accept at or above
                  AUTO_T, review band down to REVIEW_T.
  3. (tail)       everything else is unmatched, and stays unmatched.

Method and score travel with every row so accuracy can be priced per stage
rather than reported as one blended number that hides where the errors are.

DISAMBIGUATION. Baseball has genuine name collisions. When a name is
ambiguous, the ranking list's own side fields (position, current level) are
used as tiebreakers, and any row resolved that way is labeled so its
accuracy can be measured separately rather than folded into the exact-match
rate it did not earn.
"""

from collections import defaultdict
from difflib import SequenceMatcher

from matching.normalize_name import normalize, name_keys

AUTO_T = 0.92
REVIEW_T = 0.82

# Name fields on the player-universe side worth indexing. Ordered by how
# canonical they are, which matters only for reporting which field earned
# a match, not for correctness.
INDEXED_FIELDS = [
    "full_name",
    "first_last_from_parts",   # synthesized: first_name + last_name
    "use_first_last",          # synthesized: use_name + use_last_name
    "full_fml_name",
]

# Position families, used only to break ties between same-named players.
# Deliberately coarse: the ranking list writes "SS/3B" and "RHP" where the
# API writes "SS" and "P", so only the pitcher/position split is reliable.
_PITCHER_TOKENS = {"RHP", "LHP", "P", "SP", "RP"}


def _is_pitcher_ranking(position: str) -> bool:
    return any(tok in _PITCHER_TOKENS for tok in position.replace("/", " ").split())


def _is_pitcher_api(position: str) -> bool:
    return position.strip().upper() in {"P", "SP", "RP", "TWP"}


def build_index(players: list[dict]) -> dict:
    """Map every normalized name variant to the list of players carrying it."""
    index = defaultdict(list)
    by_surname = defaultdict(list)

    for p in players:
        variants = {
            "full_name": p.get("full_name", ""),
            "first_last_from_parts": f"{p.get('first_name', '')} {p.get('last_name', '')}",
            "use_first_last": f"{p.get('use_name', '')} {p.get('use_last_name', '')}",
            "full_fml_name": p.get("full_fml_name", ""),
        }
        seen_keys = set()
        for field, raw in variants.items():
            if not raw.strip():
                continue
            for key in name_keys(raw):
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                index[key].append((p, field))

        surname = normalize(p.get("last_name", "") or p.get("use_last_name", ""))
        if surname:
            by_surname[surname.split()[-1]].append(p)

    return {"exact": dict(index), "by_surname": dict(by_surname)}


def _fuzzy_score(a: str, b: str) -> float:
    ratio = SequenceMatcher(None, a, b).ratio()
    a_toks, b_toks = set(a.split()), set(b.split())
    overlap = len(a_toks & b_toks) / max(1, len(b_toks))
    return min(1.0, 0.6 * ratio + 0.4 * overlap)


def _disambiguate(candidates, ranking_row):
    """Pick among same-named players using the ranking list's side fields.

    Returns (player, reason) or (None, reason) when still ambiguous.
    """
    if len(candidates) == 1:
        return candidates[0], "unique"

    want_pitcher = _is_pitcher_ranking(ranking_row.get("position", ""))
    by_pos = [p for p in candidates if _is_pitcher_api(p.get("primary_position", "")) == want_pitcher]
    if len(by_pos) == 1:
        return by_pos[0], "position"
    if not by_pos:
        by_pos = candidates

    want_level = ranking_row.get("current_level", "").strip()
    by_level = [p for p in by_pos if p.get("level", "") == want_level]
    if len(by_level) == 1:
        return by_level[0], "position+level"

    return None, f"ambiguous_{len(candidates)}"


def resolve_one(ranking_row: dict, index: dict) -> dict:
    raw = ranking_row["player"]
    core = normalize(raw)

    hits = index["exact"].get(core, [])
    if hits:
        candidates = list({id(p): p for p, _ in hits}.values())
        fields = sorted({f for _, f in hits})
        player, reason = _disambiguate(candidates, ranking_row)
        if player is not None:
            method = "exact" if reason == "unique" else "exact_disambiguated"
            return {
                "method": method, "score": 1.0, "matched_on": ",".join(fields),
                "disambiguated_by": reason, "player": player,
            }
        return {"method": "ambiguous", "score": 1.0, "matched_on": ",".join(fields),
                "disambiguated_by": reason, "player": None}

    surname = core.split()[-1] if core else ""
    pool = index["by_surname"].get(surname, [])
    if not pool:
        return {"method": "unmatched", "score": 0.0, "matched_on": "",
                "disambiguated_by": "no_surname_block", "player": None}

    best, best_score = None, 0.0
    for p in pool:
        for raw_variant in (p.get("full_name", ""),
                            f"{p.get('first_name','')} {p.get('last_name','')}",
                            f"{p.get('use_name','')} {p.get('use_last_name','')}",
                            p.get("full_fml_name", "")):
            if not raw_variant.strip():
                continue
            s = _fuzzy_score(core, normalize(raw_variant))
            if s > best_score:
                best, best_score = p, s

    score = int(best_score * 1000) / 1000
    if best is not None and best_score >= AUTO_T:
        return {"method": "fuzzy_auto", "score": score, "matched_on": "surname_block",
                "disambiguated_by": "fuzzy", "player": best}
    if best is not None and best_score >= REVIEW_T:
        return {"method": "review", "score": score, "matched_on": "surname_block",
                "disambiguated_by": "fuzzy", "player": best}
    return {"method": "unmatched", "score": score, "matched_on": "",
            "disambiguated_by": "below_review_threshold", "player": None}


def resolve_all(ranking_rows: list[dict], players: list[dict]) -> list[dict]:
    index = build_index(players)
    out = []
    for row in ranking_rows:
        res = resolve_one(row, index)
        player = res["player"]
        out.append({
            "cohort": row["cohort"],
            "rank": row["rank"],
            "player": row["player"],
            "position": row["position"],
            "current_level": row["current_level"],
            "method": res["method"],
            "score": res["score"],
            "matched_on": res["matched_on"],
            "disambiguated_by": res["disambiguated_by"],
            "mlbam_id": player["mlbam_id"] if player else "",
            "matched_name": player["full_name"] if player else "",
            "mlb_debut_date": player.get("mlb_debut_date", "") if player else "",
        })
    return out
