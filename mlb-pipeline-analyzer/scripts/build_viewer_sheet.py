"""Builds the viewer-friendly workbook Reid actually opens and reads,
rather than analyzes with a script. Four tabs:

  Readiness at Debut   the original simple overview, one row per debuted
                       player: player, position, both scores, debut date.
  Pitchers             every debuted pitcher's full stint-level diagnostic
                       line(s) for whichever season fed his debut-day
                       reading, added 2026-08-02 on Reid's request after
                       the Misiorowski role/pitch-count finding made clear
                       the overview tab alone hides exactly the texture
                       (role, IP/appearance, WHIP, BABIP...) that catches
                       cases like his.
  Hitters              same idea, the hitting-side stint diagnostics.
  Formula Key          plain-language explanation of every column on the
                       two diagnostic tabs, so the workbook is readable on
                       its own without opening README.md or GLOSSARY.md.

Not a new calculation anywhere. Every number here already exists in
outputs/readiness_summary.csv and outputs/readiness_stints.csv; this is
strictly a reshaping into something meant to be opened and skimmed. A
player's debut-day reading can be built from more than one level-season
stint (a mid-season promotion, most commonly); when it is, he gets one row
per stint on the Pitchers/Hitters tab, all carrying the same season-level
Readiness/Rate Score and Reading Basis, so the season total and the
per-level components are both visible without cross-referencing a CSV by
hand.
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

import config

BASIS_RE = re.compile(r"^carried_from_(\d{4})")


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def debut_target_season(row):
    """Which season's stint rows fed this player's debut-day reading.
    'carried_from_YYYY' (with or without the '_over_Npa_tuneup' suffix) ->
    YYYY. 'debut_season', OR a season-level RATE refusal string (e.g.
    "insufficient_sample (76 of 97 PA+BF scored, need 100)", two real
    cases, Schanuel and Kurtz: their debut season had one stint that
    scored on its own but didn't clear the season-total rate floor,
    pick_debut_reading() still carries that season's base_war/adj_war,
    per compute_readiness.py's own basis assignment) -> the debut year.
    Only never_debuted/no_pre_debut_stint_data have no season to show."""
    basis = row["debut_reading_basis"]
    m = BASIS_RE.match(basis)
    if m:
        return int(m.group(1))
    if basis in ("never_debuted", "no_pre_debut_stint_data"):
        return None
    return int(row["mlb_debut_date"][:4])


def num(v, default=""):
    return float(v) if v not in ("", None) else default


def style_header(ws, ncols):
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 30


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def main():
    summary = read_csv(config.OUTPUTS / "readiness_summary.csv")
    stints = read_csv(config.OUTPUTS / "readiness_stints.csv")

    debuted = [r for r in summary if r["mlb_debut_date"] and r["debut_day_adj_war"]]
    debuted.sort(key=lambda r: float(r["debut_day_adj_war"]), reverse=True)

    stints_by_player_season = {}
    for s in stints:
        if s["verdict"] != "scored":
            continue
        stints_by_player_season.setdefault((s["mlbam_id"], s["season"]), []).append(s)

    wb = Workbook()

    # --- Tab 1: the original simple overview, unchanged -------------------
    ws = wb.active
    ws.title = "Readiness at Debut"
    ws.append(["Player", "Position", "Readiness Score at Debut",
               "Rate Score (per 600 PA/BF)", "Debut Date"])
    for r in debuted:
        rate = r["debut_day_rate_per_600"]
        ws.append([r["player"], r["position_used_for_scoring"],
                  round(float(r["debut_day_adj_war"]), 2),
                  round(float(rate), 2) if rate else "n/a, sample too small",
                  r["mlb_debut_date"]])
    style_header(ws, 5)
    set_widths(ws, [24, 12, 24, 26, 14])

    # --- Tab 2: Pitchers, full stint-level diagnostics ---------------------
    wp = wb.create_sheet("Pitchers")
    wp.append(["Player", "Level", "Season", "Reading Basis", "Workload",
               "Role", "Start Frac", "IP/Start", "IP/Appearance", "P/GS",
               "FIP", "WHIP", "BABIP", "BB/9", "K%", "BB%", "GB%",
               "Base WAR (stint)", "Age Credit (stint)",
               "Season Readiness Score", "Season Rate Score", "Debut Date"])
    for r in debuted:
        season = debut_target_season(r)
        if season is None:
            continue
        rows = [s for s in stints_by_player_season.get((r["mlbam_id"], str(season)), [])
                if s["group"] == "pitching"]
        rate = r["debut_day_rate_per_600"]
        rate_disp = round(float(rate), 2) if rate else "n/a, sample too small"
        for s in rows:
            wp.append([
                r["player"], s["level"], season, r["debut_reading_basis"], s["detail"],
                s["role"], num(s["start_frac"]), num(s["ip_per_start"]),
                num(s["ip_per_appearance"]), num(s["p_per_gs"]), num(s["fip"]),
                num(s["whip"]), num(s["babip"]), num(s["bb9"]), num(s["k_pct"]),
                num(s["bb_pct"]), num(s["gb_pct"]), num(s["base_war"]),
                num(s["age_credit_war"]), round(float(r["debut_day_adj_war"]), 2),
                rate_disp, r["mlb_debut_date"],
            ])
    style_header(wp, 22)
    set_widths(wp, [20, 8, 8, 20, 18, 10, 10, 10, 13, 8, 7, 7, 7, 7, 7, 7, 7,
                    15, 15, 18, 18, 13])

    # --- Tab 3: Hitters, full stint-level diagnostics -----------------------
    wh = wb.create_sheet("Hitters")
    wh.append(["Player", "Position (scoring)", "Position Resolution", "Level",
               "Season", "Reading Basis", "Workload", "wOBA", "Native Rate",
               "RAA vs MLB", "Steal Runs", "Replacement", "Position Adj",
               "Age Years", "Base WAR (stint)", "Age Credit (stint)",
               "Season Readiness Score", "Season Rate Score", "Debut Date"])
    for r in debuted:
        season = debut_target_season(r)
        if season is None:
            continue
        rows = [s for s in stints_by_player_season.get((r["mlbam_id"], str(season)), [])
                if s["group"] == "hitting"]
        rate = r["debut_day_rate_per_600"]
        rate_disp = round(float(rate), 2) if rate else "n/a, sample too small"
        for s in rows:
            wh.append([
                r["player"], r["position_used_for_scoring"], r["position_resolution"],
                s["level"], season, r["debut_reading_basis"], s["detail"],
                num(s["woba"]), num(s["native_rate"]), num(s["raa_mlb"]),
                num(s["wsb"]), num(s["rep"]), num(s["pos_adj"]), num(s["age_years"]),
                num(s["base_war"]), num(s["age_credit_war"]),
                round(float(r["debut_day_adj_war"]), 2), rate_disp, r["mlb_debut_date"],
            ])
    style_header(wh, 19)
    set_widths(wh, [20, 16, 16, 8, 8, 20, 14, 8, 10, 10, 10, 11, 11, 9,
                    15, 15, 18, 18, 13])

    # --- Tab 4: Formula key --------------------------------------------------
    wk = wb.create_sheet("Formula Key")
    wk.append(["Column", "Tab(s)", "Meaning", "Formula / Source"])
    KEY_ROWS = [
        ("Reading Basis", "Pitchers, Hitters",
         "Which season the debut-day reading is built from.",
         "'debut_season' = his own debut year. 'carried_from_YYYY' = his debut "
         "year didn't clear the sample floor, so his last full scored prior "
         "season stands in. A '_over_Npa_tuneup' suffix means a short debut-year "
         "stint existed but wasn't big enough to trust over the fuller earlier one."),
        ("Workload", "Pitchers, Hitters",
         "Plain-English playing time for this one stint.",
         "e.g. '260 BF, 60.0 IP' or '223 PA'."),
        ("Role", "Pitchers",
         "starter / swingman / reliever, an in-house label from Start Frac, "
         "not a verdict about why usage looked that way.",
         "starter if Start Frac >= 0.80, reliever if < 0.20, swingman in between. "
         "No single published season-total cutoff exists; these bounds are "
         "in-house, sized to contain the roughly-35-40%-of-appearances "
         "'swingman' band the published research does establish. ALWAYS read "
         "alongside IP/Appearance, see below."),
        ("Start Frac", "Pitchers", "Share of his appearances that were starts.",
         "Games Started / Games Played."),
        ("IP/Start", "Pitchers", "Innings pitched per start.",
         "IP / Games Started. Blank if he had zero starts that stint."),
        ("IP/Appearance", "Pitchers",
         "Innings pitched per appearance, counting every game, not just starts. "
         "Added 2026-08-02 specifically because Role/Start Frac alone can't tell "
         "a real bullpen conversion from a starter being kept on a strict pitch "
         "count (found on Jacob Misiorowski's 2024 AAA stint: BOTH his starts "
         "and his relief outings were short that stretch, 1.26 IP/appearance "
         "against 4.2-4.9 in every other season of his career). A low reading "
         "here is a flag to not take Role at face value, not a diagnosis of why.",
         "IP / Games Played."),
        ("P/GS", "Pitchers", "Pitches thrown per start, a workload-efficiency read.",
         "Pitch count / Games Started. Blank if he had zero starts that stint."),
        ("FIP", "Pitchers",
         "Fielding-independent pitching: performance from only strikeouts, "
         "walks, hit batters, and home runs, the outcomes that don't depend "
         "on his fielders. Raw, level-native, not translated to MLB terms.",
         "(13*HR + 3*(BB+HBP) - 2*K) / IP, plus the level's FIP constant."),
        ("WHIP", "Pitchers", "Baserunners allowed per inning, hits and walks combined.",
         "(BB + H) / IP. Standard construction."),
        ("BABIP", "Pitchers",
         "Batting average on balls in play against him. He has limited control "
         "over this once contact happens, so an unusually high or low reading "
         "(vs. roughly .300 most pitchers drift toward) flags his other numbers "
         "that stint as possibly running on luck, in either direction.",
         "(H - HR) / (AB - K - HR + SF). Standard FanGraphs construction. "
         "Blank if the balls-in-play denominator isn't positive."),
        ("BB/9", "Pitchers", "Walks allowed per nine innings.", "9 * BB / IP."),
        ("K%", "Pitchers", "Strikeouts as a share of batters faced.", "K / BF."),
        ("BB%", "Pitchers", "Walks as a share of batters faced.", "BB / BF."),
        ("GB%", "Pitchers",
         "Ground-ball outs as a share of all outs recorded. An OUTS-ONLY "
         "approximation, ground balls that go for hits aren't in this API's "
         "per-stint line, so this isn't full batted-ball GB% from a "
         "Statcast-based source, it reads real grounder-heavy tendencies "
         "but not the exact rate.",
         "groundOuts / (groundOuts + airOuts)."),
        ("wOBA", "Hitters",
         "Weighted on-base average, one number summarizing all of a hitter's "
         "offense (walks, hits by type, home runs), weighted by how much each "
         "actually contributes to winning. Raw, level-native.",
         "FanGraphs 2023 linear weights."),
        ("Native Rate", "Hitters",
         "His run-production rate stated in his own level's terms, before any "
         "MLB translation.", "Level's runs/PA + his wOBA gap converted to runs."),
        ("RAA vs MLB", "Pitchers, Hitters",
         "Runs above (or below) an average MLB player, after translating his "
         "level performance to MLB terms with the level's translation factor. "
         "The core production number feeding Base WAR.", ""),
        ("Steal Runs", "Hitters", "Runs added by stolen-base activity (translated).",
         "0.20 per SB, -0.41 per CS, translated by the level factor."),
        ("Replacement", "Pitchers, Hitters",
         "Standard baseline credit reflecting that even a bare-minimum MLB "
         "fill-in has some value.",
         "20.5 runs per 600 PA (hitters) or per 600 BF (pitchers, an in-house "
         "symmetry choice)."),
        ("Position Adj", "Hitters",
         "Bonus or penalty for defensive position, scaled to games played.",
         "Standard published per-162-game constants; see README for the "
         "project's specific per-position values and rulings."),
        ("Age Years", "Pitchers, Hitters",
         "Years younger (positive) or older (negative) than the level's actual "
         "measured average age that season, capped at 3 in either direction.", ""),
        ("Base WAR (stint)", "Pitchers, Hitters",
         "This one stint's production-only score, in wins, before any age credit.",
         "(RAA + other run terms) / 10 runs-per-win."),
        ("Age Credit (stint)", "Pitchers, Hitters",
         "This one stint's age bonus, in wins. Capped so it can never turn a "
         "genuinely below-replacement stint into a false positive crossing.", ""),
        ("Season Readiness Score", "Pitchers, Hitters",
         "Total value banked across the WHOLE debut-reading season (summed "
         "across every scored stint that season, which is why it repeats "
         "identically on every stint row for a player who split time across "
         "levels). Naturally larger the more he played.",
         "Sum of that season's stint Base WAR + Age Credit, capped the same way."),
        ("Season Rate Score", "Pitchers, Hitters",
         "The same season restated per 600 PA or BF, a full-season-equivalent "
         "workload, how good he was per opportunity independent of how much "
         "opportunity he got. 'n/a, sample too small' if the season's total "
         "volume didn't clear the rate floor.", "Season Readiness Score * 600 / volume."),
    ]
    for row in KEY_ROWS:
        wk.append(row)
    style_header(wk, 4)
    set_widths(wk, [22, 16, 70, 55])
    for row in wk.iter_rows(min_row=2):
        for cell in row[2:4]:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    out = config.OUTPUTS / "readiness_at_debut.xlsx"
    wb.save(out)
    n_p = sum(1 for _ in wp.iter_rows(min_row=2))
    n_h = sum(1 for _ in wh.iter_rows(min_row=2))
    print(f"wrote {len(debuted)} players to the overview tab, "
          f"{n_p} pitcher stint rows, {n_h} hitter stint rows, to {out}")


if __name__ == "__main__":
    main()
