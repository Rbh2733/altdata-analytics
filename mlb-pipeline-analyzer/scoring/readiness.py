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
  pitchers  FIP savings vs level average -> translated -> minus the
            level-quality penalty (an average level pitcher is worse than an
            average MLB pitcher by the same translation logic) -> scale by
            innings -> add the replacement offset (per batter faced, an
            in-house symmetry choice, disclosed) -> wins.
  age       the Stoltz equivalence per year younger than the level's
            measured average age, capped, denominated in level-native runs,
            translated with the same factor, reported as its own column so
            it is always severable from the production score.

Every constant lives in constants.py with its citation.
"""

from datetime import date

import constants as C


def parse_ip(raw) -> float:
    """Innings in thirds notation: '5.2' means 5 and two thirds."""
    s = str(raw or "0") or "0"
    whole, _, frac = s.partition(".")
    return (int(whole or 0) * 3 + int(frac or 0)) / 3


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


def fip_core(row) -> tuple[float, float]:
    """((13*HR + 3*(BB+HBP) - 2*K) / IP, IP) without the league constant."""
    ip = parse_ip(row.get("inningsPitched"))
    if not ip:
        return 0.0, 0.0
    core = (13 * _f(row, "homeRuns")
            + 3 * (_f(row, "baseOnBalls") + _f(row, "hitBatsmen"))
            - 2 * _f(row, "strikeOuts")) / ip
    return core, ip


def hitting_baseline(base_row) -> dict:
    """Derived league-average numbers from a summed hitting baseline row."""
    w, _ = woba(base_row)
    pa = _f(base_row, "plateAppearances")
    return {
        "woba_lg": w,
        "rpa": _f(base_row, "runs") / pa if pa else 0.0,
        "pa": pa,
    }


def pitching_baseline(base_row) -> dict:
    """Derived league numbers from a summed pitching baseline row.

    lg FIP equals lg ERA by construction of the FIP constant, and R9 is
    runs allowed per nine, the run environment in pitcher terms.
    """
    ip = float(base_row.get("inningsPitched", 0) or 0)
    er, r = _f(base_row, "earnedRuns"), _f(base_row, "runs")
    era = 9 * er / ip if ip else 0.0
    core = ((13 * _f(base_row, "homeRuns")
             + 3 * (_f(base_row, "baseOnBalls") + _f(base_row, "hitBatsmen"))
             - 2 * _f(base_row, "strikeOuts")) / ip) if ip else 0.0
    return {
        "lg_fip": era,
        "fip_const": era - core,
        "r9": 9 * r / ip if ip else 0.0,
        "bf": _f(base_row, "battersFaced"),
        "ip": ip,
    }


def player_age_at(birth_date: str, season: int) -> float | None:
    if not birth_date:
        return None
    y, m, d = map(int, birth_date.split("-"))
    ref = date(season, C.AGE_REF_MONTH, C.AGE_REF_DAY)
    return (ref - date(y, m, d)).days / 365.25


def hitter_stint(row, lvl_hit: dict, mlb_hit: dict, sport_id: int,
                 player_age: float | None, avg_age: float | None,
                 position: str) -> dict:
    """Score one hitting stint. Returns every component, refuses under the
    stint minimum with the count attached."""
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
    pos = C.POSITION_ADJ_PER_162.get((position or "").upper(), 0.0) * g / 162
    base_war = (raa_mlb + wsb + rep + pos) / C.RUNS_PER_WIN

    credit = 0.0
    years = None
    if player_age is not None and avg_age is not None:
        years = max(-C.AGE_CAP_YEARS, min(C.AGE_CAP_YEARS, avg_age - player_age))
        pts = C.AGE_WRC_POINTS_PER_YEAR[sport_id]
        credit = years * (pts / 100) * lvl_hit["rpa"] * pa * tf / C.RUNS_PER_WIN

    return {"verdict": "scored", "detail": f"{int(pa)} PA",
            "pa": pa, "bf": 0.0, "g": g,
            "woba": round(w_p, 3), "native_rate": round(native_rate, 4),
            "raa_mlb": round(raa_mlb, 1), "wsb": round(wsb, 1),
            "rep": round(rep, 1), "pos_adj": round(pos, 1),
            "age_years": None if years is None else round(years, 1),
            "base_war": base_war, "age_credit_war": credit,
            "adj_war": base_war + credit}


def pitcher_stint(row, lvl_pit: dict, mlb_pit: dict, sport_id: int,
                  player_age: float | None, avg_age: float | None) -> dict:
    """Score one pitching stint, symmetric construction to the hitter chain."""
    tf = C.TRANSLATION_FACTORS[sport_id]
    core, ip = fip_core(row)
    bf = _f(row, "battersFaced")
    if bf < C.MIN_STINT_BF:
        return {"verdict": "insufficient_sample",
                "detail": f"{int(bf)} BF (need {C.MIN_STINT_BF})",
                "pa": 0.0, "bf": bf, "g": _f(row, "gamesPlayed"),
                "base_war": 0.0, "age_credit_war": 0.0, "adj_war": 0.0}

    fip_p = core + lvl_pit["fip_const"]
    savings9 = lvl_pit["lg_fip"] - fip_p
    pen9 = mlb_pit["r9"] - lvl_pit["r9"] * tf
    raa_mlb = (savings9 * tf - pen9) * ip / 9
    rep = C.REPLACEMENT_RUNS_PER_600 / 600 * bf
    base_war = (raa_mlb + rep) / C.RUNS_PER_WIN

    credit = 0.0
    years = None
    if player_age is not None and avg_age is not None:
        years = max(-C.AGE_CAP_YEARS, min(C.AGE_CAP_YEARS, avg_age - player_age))
        coef = C.AGE_FIP_RUNS_PER_YEAR[sport_id]
        credit = years * coef * ip / 9 * tf / C.RUNS_PER_WIN

    return {"verdict": "scored", "detail": f"{int(bf)} BF, {ip:.1f} IP",
            "pa": 0.0, "bf": bf, "g": _f(row, "gamesPlayed"),
            "fip": round(fip_p, 2), "savings9": round(savings9, 2),
            "raa_mlb": round(raa_mlb, 1), "rep": round(rep, 1),
            "age_years": None if years is None else round(years, 1),
            "base_war": base_war, "age_credit_war": credit,
            "adj_war": base_war + credit}


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
