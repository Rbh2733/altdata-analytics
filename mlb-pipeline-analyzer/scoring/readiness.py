"""The readiness score, as pure functions over plain dicts.

Everything here is deterministic arithmetic on data passed in as arguments.
No file reads, no network, no dates-of-today. That purity is what lets the
no-future-leak test feed a synthetic career through the exact production
code path and prove that deleting post-debut rows changes nothing.

The chain, per stint (one player, one level, one season):
  hitters   wOBA -> absolute run-production rate in level terms -> multiply
            by the level translation factor -> subtract the real MLB average
            rate that season -> scale by PA -> add steal runs (translated),
            the replacement offset, and the position adjustment -> wins.
  age       the Stoltz equivalence per year younger than the level's
            measured average age, capped, denominated in level-native runs,
            translated with the same factor, reported as its own column so
            it is always severable from the production score.

Every constant lives in constants.py with its citation.

Scoped to hitters only as of 2026-08-02. Pitcher scoring (FIP-based WAR,
role/workload diagnostics) was built, tested, and researched extensively,
but needs a different WAR construction validated against real sabermetric
research before it ships; that work is preserved at the `pitcher-work-
2026-08-02` git tag and is being developed separately, not deleted.
"""

from datetime import date

import constants as C


def _f(row, key) -> float:
    v = row.get(key, "")
    return float(v) if v not in ("", None) else 0.0


def woba(row) -> tuple[float, float]:
    """(wOBA, denominator) from a component stat line. FanGraphs weights."""
    ab, h = _f(row, "atBats"), _f(row, "hits")
    d2, d3, hr = _f(row, "doubles"), _f(row, "triples"), _f(row, "homeRuns")
    bb, ibb = _f(row, "baseOnBalls"), _f(row, "intentionalWalks")
    hbp, sf = _f(row, "hitByPitch"), _f(row, "sacFlies")
    s1 = h - d2 - d3 - hr
    w = C.WOBA_WEIGHTS
    num = (w["bb"] * (bb - ibb) + w["hbp"] * hbp + w["s1"] * s1
           + w["s2"] * d2 + w["s3"] * d3 + w["hr"] * hr)
    den = ab + bb - ibb + sf + hbp
    return (num / den if den else 0.0), den


def hitting_baseline(base_row) -> dict:
    """Derived league-average numbers from a summed hitting baseline row."""
    w, _ = woba(base_row)
    pa = _f(base_row, "plateAppearances")
    return {
        "woba_lg": w,
        "rpa": _f(base_row, "runs") / pa if pa else 0.0,
        "pa": pa,
    }


def player_age_at(birth_date: str, season: int) -> float | None:
    if not birth_date:
        return None
    y, m, d = map(int, birth_date.split("-"))
    ref = date(season, C.AGE_REF_MONTH, C.AGE_REF_DAY)
    return (ref - date(y, m, d)).days / 365.25


def hitter_stint(row, lvl_hit: dict, mlb_hit: dict, sport_id: int,
                 player_age: float | None, avg_age: float | None,
                 positions: list[str]) -> dict:
    """Score one hitting stint. Returns every component, refuses under the
    stint minimum with the count attached.

    positions is always a list. A single-position player passes a
    one-element list (average of one value is just that value). A
    multi-position listing not covered by a manual review (Reid's ruling
    2026-08-01) passes every position the ranking list named, and the
    position-adjustment constant is the plain average across all of them,
    never a single picked "winner."
    """
    tf = C.TRANSLATION_FACTORS[sport_id]
    pa = _f(row, "plateAppearances")
    g = _f(row, "gamesPlayed")
    if pa < C.MIN_STINT_PA:
        return {"verdict": "insufficient_sample",
                "detail": f"{int(pa)} PA (need {C.MIN_STINT_PA})",
                "pa": pa, "bf": 0.0, "g": g,
                "base_war": 0.0, "age_credit_war": 0.0, "adj_war": 0.0}

    w_p, _ = woba(row)
    wraa_rate = (w_p - lvl_hit["woba_lg"]) / C.WOBA_SCALE
    native_rate = lvl_hit["rpa"] + wraa_rate
    raa_mlb = (native_rate * tf - mlb_hit["rpa"]) * pa
    wsb = (C.SB_RUNS * _f(row, "stolenBases")
           + C.CS_RUNS * _f(row, "caughtStealing")) * tf
    rep = C.REPLACEMENT_RUNS_PER_600 / 600 * pa
    # "OF" as a secondary position in a multi-position listing is valued
    # differently than "OF" as the sole listed position, per Reid's ruling
    # 2026-08-01, see constants.py. Only fires when there is more than one
    # listed position to average across.
    is_secondary = len(positions) > 1
    def _pos_value(p):
        p = p.upper()
        if p == "OF" and is_secondary:
            return C.POSITION_ADJ_PER_162.get("OF_SECONDARY", 0.0)
        return C.POSITION_ADJ_PER_162.get(p, 0.0)
    pos_values = [_pos_value(p) for p in positions] if positions else [0.0]
    pos = (sum(pos_values) / len(pos_values)) * g / 162
    base_war = (raa_mlb + wsb + rep + pos) / C.RUNS_PER_WIN

    credit = 0.0
    years = None
    if player_age is not None and avg_age is not None:
        years = max(-C.AGE_CAP_YEARS, min(C.AGE_CAP_YEARS, avg_age - player_age))
        pts = C.AGE_WRC_POINTS_PER_YEAR[sport_id]
        credit = years * (pts / 100) * lvl_hit["rpa"] * pa * tf / C.RUNS_PER_WIN

    # Age credit can rescue a genuinely below-replacement performance up to
    # a neutral read, never manufacture a false positive crossing. Found
    # 2026-08-01: without this cap, a large enough credit could push a
    # stint whose actual production was below replacement into a positive
    # adj_war, a real player (Sixto Sanchez) whose entire positive
    # debut-day score turned out to be manufactured this way, and cases
    # where age credit inverted the ranking of a verified success below a
    # player who was released. The cap only fires when base_war is
    # negative; a stint that already clears replacement on production
    # alone keeps its full credit and can go further positive.
    adj_war = base_war + credit if base_war >= 0 else min(base_war + credit, 0.0)

    return {"verdict": "scored", "detail": f"{int(pa)} PA",
            "pa": pa, "bf": 0.0, "g": g,
            "woba": round(w_p, 3), "native_rate": round(native_rate, 4),
            "raa_mlb": round(raa_mlb, 1), "wsb": round(wsb, 1),
            "rep": round(rep, 1), "pos_adj": round(pos, 1),
            "age_years": None if years is None else round(years, 1),
            "base_war": base_war, "age_credit_war": credit,
            "adj_war": adj_war}


def sum_rows(rows: list[dict], fields: list[str]) -> dict:
    """Combine multiple stat lines (multi-team stints, game logs) into one,
    innings in thirds handled correctly."""
    out = {}
    for f in fields:
        if f == "inningsPitched":
            thirds = 0
            for r in rows:
                s = str(r.get(f, "0") or "0")
                whole, _, frac = s.partition(".")
                thirds += int(whole or 0) * 3 + int(frac or 0)
            out[f] = f"{thirds // 3}.{thirds % 3}"
        else:
            out[f] = sum(_f(r, f) for r in rows)
    return out
