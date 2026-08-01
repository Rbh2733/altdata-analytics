"""Pulls every matched prospect's career season splits, debut-season game
logs, league baselines, and level average ages.

Four derived files, all written to data/derived/:

  season_splits.csv    one row per (player, season, level, team) stat line,
                       hitting and pitching, minors and MLB
  debut_gamelogs.csv   per-game rows for each debuted player's debut-season
                       minor-league stints, ALREADY truncated to games
                       strictly before the MLB debut date. The truncation
                       happens here, at the data boundary, so nothing
                       downstream can accidentally read a post-debut game.
  league_baselines.csv summed team totals per (level, season, group), the
                       denominators for every league-average comparison
  level_ages.csv       average player age per (level, season), measured at
                       July 1 from that season's actual rosters

Call budget: roughly one yearByYear call per (player, group, level), one
teams-stats call per (level, season, group), one bulk players call per
(level, season). All cached by ingestion.api, so a rerun costs zero calls.
"""

import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import constants
from ingestion import api

HIT_FIELDS = ["gamesPlayed", "plateAppearances", "atBats", "hits", "doubles",
              "triples", "homeRuns", "baseOnBalls", "intentionalWalks",
              "hitByPitch", "sacFlies", "stolenBases", "caughtStealing", "runs"]
PIT_FIELDS = ["gamesPlayed", "gamesStarted", "inningsPitched", "battersFaced",
              "earnedRuns", "runs", "strikeOuts", "baseOnBalls", "hitBatsmen",
              "homeRuns"]

PITCHER_POSITIONS = {"P", "SP", "RP", "RHP", "LHP"}


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def groups_for(position: str) -> list[str]:
    pos = (position or "").strip().upper()
    if pos in PITCHER_POSITIONS:
        return ["pitching"]
    if pos == "TWP":
        return ["hitting", "pitching"]
    return ["hitting"]


def split_row(pid, group, s):
    st = s.get("stat", {})
    fields = HIT_FIELDS if group == "hitting" else PIT_FIELDS
    row = {
        "mlbam_id": pid,
        "group": group,
        "season": s.get("season", ""),
        "sport_id": s.get("sport", {}).get("id", ""),
        "team_name": s.get("team", {}).get("name", ""),
        "league_name": s.get("league", {}).get("name", ""),
    }
    for f in fields:
        row[f] = st.get(f, "")
    return row


def gamelog_row(pid, group, season, sport_id, s):
    row = split_row(pid, group, s)
    row["season"] = season
    row["sport_id"] = sport_id
    row["game_date"] = s.get("date", "")
    return row


def main():
    crosswalk = read_csv(config.DATA_DERIVED / "crosswalk.csv")
    universe = {r["mlbam_id"]: r for r in read_csv(config.DATA_RAW / "player_universe.csv")}

    players = {}
    for r in crosswalk:
        pid = r["mlbam_id"]
        if pid and pid in universe:
            players[pid] = universe[pid]
    print(f"{len(players)} unique matched players to fetch")

    splits = []
    debut_logs = []
    needed_pairs = set()      # (sport_id, season) for minors baselines + ages
    needed_mlb_seasons = set()

    for i, (pid, person) in enumerate(sorted(players.items()), 1):
        groups = groups_for(person.get("primary_position", ""))
        debut = person.get("mlb_debut_date", "")

        my_rows = []
        for group in groups:
            for sport_id in constants.MINOR_SPORT_IDS + [1]:
                if sport_id == 15:
                    continue  # second pass below, only for pre-2021 careers
                for s in api.year_by_year(int(pid), group, sport_id):
                    my_rows.append(split_row(pid, group, s))

        seasons_seen = [int(r["season"]) for r in my_rows if r["season"]]
        if seasons_seen and min(seasons_seen) <= 2020:
            for group in groups:
                for s in api.year_by_year(int(pid), group, 15):
                    my_rows.append(split_row(pid, group, s))

        for r in my_rows:
            if r["season"] and r["sport_id"] and int(r["sport_id"]) != 1:
                needed_pairs.add((int(r["sport_id"]), int(r["season"])))
            if r["season"]:
                needed_mlb_seasons.add(int(r["season"]))
        splits.extend(my_rows)

        # Debut-season minor-league game logs, truncated at the debut date
        # right here, at the data boundary.
        if debut:
            debut_season = int(debut[:4])
            debut_sports = {int(r["sport_id"]) for r in my_rows
                            if r["season"] and int(r["season"]) == debut_season
                            and r["sport_id"] and int(r["sport_id"]) != 1}
            for group in groups:
                for sport_id in sorted(debut_sports):
                    for g in api.game_log(int(pid), debut_season, group, sport_id):
                        if g.get("date", "") and g["date"] < debut:
                            debut_logs.append(
                                gamelog_row(pid, group, debut_season, sport_id, g))

        if i % 20 == 0 or i == len(players):
            print(f"  {i}/{len(players)} players fetched "
                  f"({len(splits)} split rows, {len(debut_logs)} debut-log rows)")

    # League baselines: hitting and pitching for every minor (sport, season)
    # pair plus MLB for every season touched.
    baselines = []
    pairs = sorted(needed_pairs) + [(1, s) for s in sorted(needed_mlb_seasons)]
    for sport_id, season in pairs:
        for group in ("hitting", "pitching"):
            fields = HIT_FIELDS if group == "hitting" else PIT_FIELDS
            teams = api.teams_stats(sport_id, season, group)
            if not teams:
                continue
            agg = {f: 0.0 for f in fields}
            ip_thirds = 0
            for t in teams:
                st = t.get("stat", {})
                for f in fields:
                    if f == "inningsPitched":
                        raw = str(st.get(f, "0") or "0")
                        whole, _, frac = raw.partition(".")
                        ip_thirds += int(whole or 0) * 3 + int(frac or 0)
                    else:
                        agg[f] += float(st.get(f, 0) or 0)
            row = {"sport_id": sport_id, "season": season, "group": group,
                   "n_teams": len(teams)}
            for f in fields:
                if f == "inningsPitched":
                    row[f] = round(ip_thirds / 3, 1)
                else:
                    row[f] = int(agg[f])
            baselines.append(row)
    print(f"baselines: {len(baselines)} (level, season, group) rows")

    # Level average ages at July 1, from each season's actual rosters.
    ages = []
    for sport_id, season in sorted(needed_pairs):
        people = api.sports_players(sport_id, season)
        ref = date(season, constants.AGE_REF_MONTH, constants.AGE_REF_DAY)
        vals = []
        for p in people:
            bd = p.get("birthDate")
            if bd:
                y, m, d = map(int, bd.split("-"))
                vals.append((ref - date(y, m, d)).days / 365.25)
        if vals:
            ages.append({"sport_id": sport_id, "season": season,
                         "avg_age": round(sum(vals) / len(vals), 2),
                         "n_players": len(vals)})
    print(f"level ages: {len(ages)} (level, season) rows")

    config.DATA_DERIVED.mkdir(parents=True, exist_ok=True)

    def write(name, rows, fieldnames):
        path = config.DATA_DERIVED / name
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n",
                               extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {path}")

    split_fields = (["mlbam_id", "group", "season", "sport_id", "team_name",
                     "league_name"] + sorted(set(HIT_FIELDS + PIT_FIELDS)))
    write("season_splits.csv", splits, split_fields)
    write("debut_gamelogs.csv", debut_logs, split_fields + ["game_date"])
    base_fields = ["sport_id", "season", "group", "n_teams"] + sorted(set(HIT_FIELDS + PIT_FIELDS))
    write("league_baselines.csv", baselines, base_fields)
    write("level_ages.csv", ages, ["sport_id", "season", "avg_age", "n_players"])


if __name__ == "__main__":
    main()
