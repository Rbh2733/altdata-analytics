"""Computes the readiness curve for every matched prospect and writes the
three output tables plus the report.

Temporal rule, the only one, enforced here and tested by the leak test:
no readiness input may postdate the player's MLB debut.

  completed seasons before the debut season   season-total splits
  the debut season                            game logs already truncated
                                              at the debut date by the
                                              fetch layer
  seasons after the debut season              excluded entirely
  never-debuted players                       all seasons count

Outputs:
  outputs/readiness_stints.csv     every scored stint with all components
  outputs/readiness_by_season.csv  per player-season readings
  outputs/readiness_summary.csv    one row per player, crossing + debut-day
  outputs/readiness_report.md      headline tables, calibration, disclosures
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import constants as C
from scoring import readiness as R

HIT_SUM = ["gamesPlayed", "plateAppearances", "atBats", "hits", "doubles",
           "triples", "homeRuns", "baseOnBalls", "intentionalWalks",
           "hitByPitch", "sacFlies", "stolenBases", "caughtStealing"]
PIT_SUM = ["gamesPlayed", "inningsPitched", "battersFaced", "earnedRuns",
           "strikeOuts", "baseOnBalls", "hitBatsmen", "homeRuns"]


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load():
    cw = read_csv(config.DATA_DERIVED / "crosswalk.csv")
    universe = {r["mlbam_id"]: r for r in read_csv(config.DATA_RAW / "player_universe.csv")}
    splits = read_csv(config.DATA_DERIVED / "season_splits.csv")
    logs = read_csv(config.DATA_DERIVED / "debut_gamelogs.csv")
    baselines = read_csv(config.DATA_DERIVED / "league_baselines.csv")
    ages = read_csv(config.DATA_DERIVED / "level_ages.csv")
    return cw, universe, splits, logs, baselines, ages


def index_baselines(rows):
    hit, pit = {}, {}
    for r in rows:
        key = (int(r["sport_id"]), int(r["season"]))
        if r["group"] == "hitting":
            hit[key] = R.hitting_baseline(r)
        else:
            pit[key] = R.pitching_baseline(r)
    return hit, pit


def compute_player(pid, person, my_splits, my_logs, hit_base, pit_base, age_map,
                   ranking_position=""):
    """Score one player's career. Pure over its inputs, which is what the
    no-future-leak test exploits.

    ranking_position is the position from the player's earliest ranking-list
    row, the pre-debut-vintage source for the positional adjustment. The
    API's own position label is current-day even in historical payloads
    (verified live), so it is never used for scoring. Found by adversarial
    review 2026-08-01: the old behavior docked MJ Melendez's minor-league
    catcher seasons at the DH rate because he is labeled DH today.
    """
    debut = person.get("mlb_debut_date", "")
    debut_season = int(debut[:4]) if debut else None
    birth = person.get("birth_date", "")
    position = (ranking_position or "").split("/")[0].strip().upper()

    # Group split rows into stints: (season, sport, group) -> [rows]
    stints = defaultdict(list)
    for r in my_splits:
        if not r["season"] or not r["sport_id"]:
            continue
        season, sport = int(r["season"]), int(r["sport_id"])
        if sport == 1 or sport not in C.TRANSLATION_FACTORS:
            continue
        if debut_season is not None and season >= debut_season:
            continue  # debut season comes from truncated logs, later excluded
        # Dominican Summer League stints are excluded from scoring entirely:
        # no cited translation factor covers the DSL, and the rookie-level
        # age baseline pools it with US complex ball, which let DSL
        # seventeen-year-olds max the age cap against leagues they never
        # played in. Found by adversarial review 2026-08-01, disclosed.
        if "dominican" in (r.get("league_name", "") or "").lower():
            continue
        stints[(season, sport, r["group"])].append(r)

    # The stats API emits a blank-team aggregate row alongside per-team rows
    # whenever a player logged time for two teams at one level in one season.
    # Summing all rows double-counts the season exactly (Oneil Cruz showed
    # 876 PA in 210 games). Found by adversarial review 2026-08-01: drop the
    # aggregate whenever named-team rows exist beside it.
    for key, rows in stints.items():
        named = [r for r in rows if (r.get("team_name", "") or "").strip()]
        if named and len(named) < len(rows):
            stints[key] = named

    for r in my_logs:
        season, sport = int(r["season"]), int(r["sport_id"])
        if sport not in C.TRANSLATION_FACTORS:
            continue
        if "dominican" in (r.get("league_name", "") or "").lower():
            continue
        # Defense in depth: the fetch layer already truncated at the debut
        # date, but enforce the fence here too so a corrupted or hand-edited
        # log file cannot leak a post-debut game into a readiness input.
        if debut and (not r.get("game_date") or r["game_date"] >= debut):
            continue
        stints[(season, sport, r["group"])].append(r)

    out = []
    for (season, sport, group), rows in sorted(stints.items()):
        is_debut_stint = debut_season is not None and season == debut_season
        if group == "hitting":
            line = R.sum_rows(rows, HIT_SUM)
            lvl, mlb = hit_base.get((sport, season)), hit_base.get((1, season))
            if not lvl or not mlb:
                continue
            age = R.player_age_at(birth, season)
            res = R.hitter_stint(line, lvl, mlb, sport, age,
                                 age_map.get((sport, season)), position)
        else:
            line = R.sum_rows(rows, PIT_SUM)
            lvl, mlb = pit_base.get((sport, season)), pit_base.get((1, season))
            if not lvl or not mlb:
                continue
            age = R.player_age_at(birth, season)
            res = R.pitcher_stint(line, lvl, mlb, sport, age,
                                  age_map.get((sport, season)))
        res.update({"mlbam_id": pid, "player": person.get("full_name", ""),
                    "season": season, "sport_id": sport,
                    "level": C.SPORT_LABELS.get(sport, str(sport)),
                    "group": group,
                    "pre_debut_truncated": "yes" if is_debut_stint else ""})
        out.append(res)
    return out


def season_readings(stint_rows):
    by_season = defaultdict(list)
    for s in stint_rows:
        by_season[s["season"]].append(s)
    readings = []
    for season in sorted(by_season):
        rows = by_season[season]
        scored = [r for r in rows if r["verdict"] == "scored"]
        vol = sum(r["pa"] + r["bf"] for r in scored)
        vol_all = sum(r["pa"] + r["bf"] for r in rows)
        base = sum(r["base_war"] for r in scored)
        credit = sum(r["age_credit_war"] for r in scored)
        adj = base + credit
        min_needed = C.MIN_RATE_PA
        if vol >= min_needed:
            rate600, verdict = adj * 600 / vol, "scored"
        else:
            rate600 = None
            verdict = (f"insufficient_sample ({int(vol)} of {int(vol_all)} "
                       f"PA+BF scored, need {min_needed})")
        readings.append({
            "season": season, "n_stints": len(rows), "n_scored": len(scored),
            "volume": int(vol), "volume_all": int(vol_all),
            "base_war": round(base, 2),
            "age_credit_war": round(credit, 2), "adj_war": round(adj, 2),
            "rate_per_600": None if rate600 is None else round(rate600, 2),
            "verdict": verdict,
            "truncated": any(r.get("pre_debut_truncated") for r in rows),
        })
    return readings


def pick_debut_reading(readings, debut_season):
    """Choose the reading that stands for 'his score when the majors called'.

    Preference order (corrected 2026-08-01 after adversarial review): a
    SCORED debut-season stint wins; otherwise the last scored season before
    the debut carries, even when a sub-minimum debut-season tune-up exists.
    The old rule let a 20-PA April stub bury a full scored prior season.
    Returns (reading or None, basis label).
    """
    in_season = [r for r in readings if r["season"] == debut_season]
    prior_scored = [r for r in readings
                    if r["season"] < debut_season and r["verdict"] == "scored"]
    if in_season and in_season[0]["verdict"] == "scored":
        return in_season[0], "debut_season"
    if prior_scored:
        basis = f"carried_from_{prior_scored[-1]['season']}"
        if in_season:
            basis += f"_over_{in_season[0]['volume_all']}pa_tuneup"
        return prior_scored[-1], basis
    if in_season:
        return in_season[0], in_season[0]["verdict"]
    return None, "no_pre_debut_stint_data"


def main():
    cw, universe, splits, logs, baselines, ages = load()
    hit_base, pit_base = index_baselines(baselines)
    age_map = {(int(a["sport_id"]), int(a["season"])): float(a["avg_age"]) for a in ages}

    splits_by_pid = defaultdict(list)
    for r in splits:
        splits_by_pid[r["mlbam_id"]].append(r)
    logs_by_pid = defaultdict(list)
    for r in logs:
        logs_by_pid[r["mlbam_id"]].append(r)

    players = {}
    cohorts = defaultdict(list)
    ranking_pos = {}
    for r in cw:
        if r["mlbam_id"]:
            players[r["mlbam_id"]] = r
            cohorts[r["mlbam_id"]].append(f"{r['cohort']}#{r['rank']}")
            # earliest cohort's position wins: the oldest pre-debut vintage
            key = (r["cohort"], r["position"])
            if r["mlbam_id"] not in ranking_pos or key[0] < ranking_pos[r["mlbam_id"]][0]:
                ranking_pos[r["mlbam_id"]] = key

    all_stints, all_seasons, summary = [], [], []
    for pid in sorted(players):
        person = universe.get(pid)
        if not person:
            continue
        stint_rows = compute_player(pid, person, splits_by_pid.get(pid, []),
                                    logs_by_pid.get(pid, []),
                                    hit_base, pit_base, age_map,
                                    ranking_position=ranking_pos.get(pid, ("", ""))[1])
        readings = season_readings(stint_rows)
        all_stints.extend(stint_rows)
        for rd in readings:
            rd.update({"mlbam_id": pid, "player": person.get("full_name", "")})
            all_seasons.append(rd)

        crossing = next((r["season"] for r in readings
                         if r["verdict"] == "scored" and r["adj_war"] > 0), "")
        base_crossing = next((r["season"] for r in readings
                              if r["verdict"] == "scored" and r["base_war"] > 0), "")
        debut = person.get("mlb_debut_date", "")
        debut_reading = ""
        debut_base = ""
        debut_rate = ""
        debut_verdict = "never_debuted" if not debut else "no_pre_debut_stint_data"
        if debut:
            pick, basis = pick_debut_reading(readings, int(debut[:4]))
            if pick:
                debut_reading = pick["adj_war"]
                debut_base = pick["base_war"]
                debut_rate = pick["rate_per_600"] if pick["rate_per_600"] is not None else ""
                debut_verdict = basis

        summary.append({
            "mlbam_id": pid, "player": person.get("full_name", ""),
            "position": ranking_pos.get(pid, ("", ""))[1],
            "position_today": person.get("primary_position", ""),
            "cohorts": ";".join(cohorts[pid]),
            "mlb_debut_date": debut,
            "n_seasons_scored": sum(1 for r in readings if r["verdict"] == "scored"),
            "first_crossing_season": crossing,
            "first_base_crossing_season": base_crossing,
            "debut_day_adj_war": debut_reading,
            "debut_day_base_war": debut_base,
            "debut_day_rate_per_600": debut_rate,
            "debut_reading_basis": debut_verdict,
        })

    config.OUTPUTS.mkdir(parents=True, exist_ok=True)

    def write(name, rows, fieldnames):
        path = config.OUTPUTS / name
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n",
                               extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: ("" if r.get(k) is None else
                                (round(r[k], 3) if isinstance(r[k], float) else r[k]))
                            for k in fieldnames})
        print(f"wrote {len(rows)} rows to {path}")

    stint_fields = ["mlbam_id", "player", "season", "level", "sport_id", "group",
                    "pre_debut_truncated", "verdict", "detail", "pa", "bf", "g",
                    "woba", "fip", "native_rate", "savings9", "raa_mlb", "wsb",
                    "rep", "pos_adj", "age_years", "base_war", "age_credit_war",
                    "adj_war"]
    write("readiness_stints.csv", all_stints, stint_fields)
    season_fields = ["mlbam_id", "player", "season", "n_stints", "n_scored",
                     "volume", "volume_all", "base_war", "age_credit_war",
                     "adj_war", "rate_per_600", "verdict", "truncated"]
    write("readiness_by_season.csv", all_seasons, season_fields)
    summary_fields = ["mlbam_id", "player", "position", "position_today", "cohorts",
                      "mlb_debut_date", "n_seasons_scored",
                      "first_crossing_season", "first_base_crossing_season",
                      "debut_day_adj_war", "debut_day_base_war",
                      "debut_day_rate_per_600", "debut_reading_basis"]
    write("readiness_summary.csv", summary, summary_fields)

    # Calibration table: what a dead-average regular at each level-season
    # scores under this chain, hitters per 600 PA, pitchers per 600 BF.
    calib = []
    for (sport, season), lvl in sorted(hit_base.items()):
        if sport == 1 or (1, season) not in hit_base:
            continue
        tf = C.TRANSLATION_FACTORS.get(sport)
        if tf is None:
            continue
        mlb = hit_base[(1, season)]

        def h_calib(factor):
            return round(((lvl["rpa"] * factor - mlb["rpa"]) * 600
                          + C.REPLACEMENT_RUNS_PER_600) / C.RUNS_PER_WIN, 2)

        def p_calib(factor):
            if (sport, season) not in pit_base or (1, season) not in pit_base:
                return ""
            lp, mp = pit_base[(sport, season)], pit_base[(1, season)]
            pen9 = mp["r9"] - lp["r9"] * factor
            ip600 = 600 * lp["ip"] / lp["bf"] if lp["bf"] else 0
            return round((-pen9 * ip600 / 9 + C.REPLACEMENT_RUNS_PER_600) / C.RUNS_PER_WIN, 2)

        calib.append({"level": C.SPORT_LABELS[sport], "season": season,
                      "avg_hitter_war_per_600pa": h_calib(tf),
                      "avg_pitcher_war_per_600bf": p_calib(tf),
                      "avg_hitter_war_per_600pa_blended": h_calib(tf / C.BLENDED_SCALE_DIVISOR),
                      "avg_pitcher_war_per_600bf_blended": p_calib(tf / C.BLENDED_SCALE_DIVISOR)})
    write("calibration_table.csv", calib,
          ["level", "season", "avg_hitter_war_per_600pa", "avg_pitcher_war_per_600bf",
           "avg_hitter_war_per_600pa_blended", "avg_pitcher_war_per_600bf_blended"])

    print(f"\n{len(summary)} players scored")
    crossers = [s for s in summary if s["first_crossing_season"]]
    debuted = [s for s in summary if s["mlb_debut_date"]]
    print(f"  {len(crossers)} crossed zero at some point, "
          f"{len(summary) - len(crossers)} never did")
    print(f"  {len(debuted)} debuted, {len(summary) - len(debuted)} have not")


if __name__ == "__main__":
    main()
