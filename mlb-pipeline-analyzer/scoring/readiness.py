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


def pitcher_diagnostics(row, ip: float) -> dict:
    """Independent rate diagnostics reported alongside FIP, added 2026-08-01
    (Session 21's parked items 1, 2, and 4). Raw and level-native, never
    translated to MLB terms and never fed into the WAR chain above, same
    "diagnostic column, not a scoring input" framing FIP itself already
    carries at small samples.

    whip       (BB + H) / IP. Standard construction.
    babip      (H - HR) / (AB - K - HR + SF), pitcher's BABIP-against,
               standard FanGraphs construction. None if the balls-in-play
               denominator is not positive (can happen in a tiny sample).
    bb9        9 * BB / IP.
    k_pct, bb_pct   K / BF and BB / BF. None if BF is zero (never should be,
               the caller only reaches here past the BF minimum).
    gb_pct     groundOuts / (groundOuts + airOuts). An OUTS-ONLY
               approximation of true ground-ball rate, disclosed: ground
               balls that go for hits are not in this API's per-stint stat
               line and are not counted in either term, so this reads a
               true grounder-heavy approach reasonably but is not the full
               batted-ball GB% a Statcast-based source would report.
    start_frac, ip_per_start, p_per_gs   gamesStarted / gamesPlayed, IP per
               start, and pitches per start. None (not zero) when
               gamesStarted is zero, a true reliever, division has nothing
               to divide.
    ip_per_appearance   IP / gamesPlayed (every appearance, not just
               starts). Added 2026-08-02 after Reid flagged a real case
               (Jacob Misiorowski's 2024 AAA stint, verified live against
               the per-game log): a hard-throwing, health-flagged prospect
               kept on a strict pitch count can show short outings in BOTH
               his starts and his relief appearances, which start_frac
               alone reads as a role change when it may really be workload
               management. This project has no injury or transaction
               context to tell those apart (same gap Phase 2's parked
               rehab-assignment detection ran into), so this is reported
               as a raw, undiagnosed number: a low reading here is a
               caveat on how to read `role`, not a claim about why usage
               looked that way. See the project README's honesty section.
    role       "starter" / "swingman" / "reliever" from start_frac against
               the in-house bands in constants.py. A literal games-started
               ratio, not a verdict, read it alongside ip_per_appearance
               above. Blank if gamesPlayed is zero (should not happen past
               the BF gate, guarded anyway).
    """
    bb, h, hr, k = _f(row, "baseOnBalls"), _f(row, "hits"), _f(row, "homeRuns"), _f(row, "strikeOuts")
    ab, sf = _f(row, "atBats"), _f(row, "sacFlies")
    gp, gs = _f(row, "gamesPlayed"), _f(row, "gamesStarted")
    go, ao = _f(row, "groundOuts"), _f(row, "airOuts")
    bf = _f(row, "battersFaced")
    pitches = _f(row, "numberOfPitches")

    whip = (bb + h) / ip if ip else None

    bip_denom = ab - k - hr + sf
    babip = (h - hr) / bip_denom if bip_denom > 0 else None

    bb9 = 9 * bb / ip if ip else None
    k_pct = k / bf if bf else None
    bb_pct = bb / bf if bf else None

    go_ao_denom = go + ao
    gb_pct = go / go_ao_denom if go_ao_denom > 0 else None

    start_frac = gs / gp if gp else None
    ip_per_start = ip / gs if gs else None
    p_per_gs = pitches / gs if gs else None
    ip_per_appearance = ip / gp if gp else None

    if start_frac is None:
        role = ""
    elif start_frac >= C.ROLE_START_THRESHOLD:
        role = "starter"
    elif start_frac < C.ROLE_SWING_FLOOR:
        role = "reliever"
    else:
        role = "swingman"

    return {
        "whip": round(whip, 2) if whip is not None else None,
        "babip": round(babip, 3) if babip is not None else None,
        "bb9": round(bb9, 2) if bb9 is not None else None,
        "k_pct": round(k_pct, 3) if k_pct is not None else None,
        "bb_pct": round(bb_pct, 3) if bb_pct is not None else None,
        "gb_pct": round(gb_pct, 3) if gb_pct is not None else None,
        "gs": gs,
        "start_frac": round(start_frac, 3) if start_frac is not None else None,
        "ip_per_start": round(ip_per_start, 1) if ip_per_start is not None else None,
        "p_per_gs": round(p_per_gs, 1) if p_per_gs is not None else None,
        "ip_per_appearance": round(ip_per_appearance, 2) if ip_per_appearance is not None else None,
        "role": role,
    }


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

    # Same cap as the hitter chain, found 2026-08-01: age credit can
    # rescue a below-replacement performance up to a neutral read, never
    # manufacture a false positive crossing. Sixto Sanchez's entire
    # positive debut-day score was manufactured this way before the cap,
    # his actual pitching that year was already below replacement.
    adj_war = base_war + credit if base_war >= 0 else min(base_war + credit, 0.0)

    diag = pitcher_diagnostics(row, ip)

    return {"verdict": "scored", "detail": f"{int(bf)} BF, {ip:.1f} IP",
            "pa": 0.0, "bf": bf, "g": _f(row, "gamesPlayed"),
            "fip": round(fip_p, 2), "savings9": round(savings9, 2),
            "raa_mlb": round(raa_mlb, 1), "rep": round(rep, 1),
            "age_years": None if years is None else round(years, 1),
            "base_war": base_war, "age_credit_war": credit,
            "adj_war": adj_war, **diag}


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
