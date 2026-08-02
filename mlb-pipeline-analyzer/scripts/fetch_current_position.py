"""Determines each hitter's real current position from actual games played,
not from the API's primaryPosition label (proven unreliable and stale, see
README honesty section).

Reuses data/derived/season_splits.csv, already on disk from the career
pull, to find each player's most recent season and which level(s) he
played at that season, so this needs only a handful of new live calls
(fielding-stats-by-position for that one season, per level), not a fresh
scan per player.

Writes data/derived/current_position.csv: mlbam_id, current_position,
current_position_games, current_position_season. Pitchers are skipped
entirely, their ranking-list position is always a single unambiguous
token (verified against the real data, RHP/LHP never appear in a
multi-position combo).
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from ingestion import api


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fielding_by_position(mlbam_id, season, sport_id):
    """games played at each position, one live-or-cached call."""
    data = api.get_json(f"/v1/people/{mlbam_id}/stats",
                        {"stats": "season", "season": season,
                         "group": "fielding", "sportId": sport_id})
    out = {}
    for s in data.get("stats", [{}])[0].get("splits", []):
        abbr = s.get("position", {}).get("abbreviation", "")
        games = int(s.get("stat", {}).get("games", 0) or 0)
        if abbr:
            out[abbr] = out.get(abbr, 0) + games
    return out


def main():
    splits = read_csv(config.DATA_DERIVED / "season_splits.csv")
    cw = read_csv(config.DATA_DERIVED / "crosswalk.csv")

    by_pid = defaultdict(list)
    for r in splits:
        if r["group"] == "hitting" and r["season"] and r["sport_id"]:
            by_pid[r["mlbam_id"]].append((int(r["season"]), int(r["sport_id"])))

    hitters = sorted({r["mlbam_id"] for r in cw if r["mlbam_id"]} & set(by_pid.keys()))
    print(f"{len(hitters)} hitters to resolve")

    rows = []
    for i, pid in enumerate(hitters, 1):
        seasons = by_pid[pid]
        max_season = max(s for s, _ in seasons)
        sports_that_season = sorted({sp for s, sp in seasons if s == max_season})

        combined = {}
        for sport_id in sports_that_season:
            for pos, g in fielding_by_position(pid, max_season, sport_id).items():
                combined[pos] = combined.get(pos, 0) + g

        if combined:
            best_pos = max(combined, key=combined.get)
            rows.append({"mlbam_id": pid, "current_position": best_pos,
                        "current_position_games": combined[best_pos],
                        "current_position_season": max_season,
                        "all_positions_played": ";".join(
                            f"{p}:{g}" for p, g in
                            sorted(combined.items(), key=lambda x: -x[1]))})
        if i % 30 == 0 or i == len(hitters):
            print(f"  {i}/{len(hitters)}")

    config.DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    out = config.DATA_DERIVED / "current_position.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["mlbam_id", "current_position",
                           "current_position_games", "current_position_season",
                           "all_positions_played"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}, {len(hitters) - len(rows)} had no fielding data")


if __name__ == "__main__":
    main()
