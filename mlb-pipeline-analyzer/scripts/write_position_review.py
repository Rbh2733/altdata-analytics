"""Writes outputs/position_review_needed.csv, every multi-position player
whose real current position matched none of his originally listed
positions, for Reid to review by hand per his 2026-08-01 ruling. These
players keep the old first-listed-token default for scoring until
reviewed, they are never silently resolved.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    summary = read_csv(config.OUTPUTS / "readiness_summary.csv")
    current = {r["mlbam_id"]: r for r in read_csv(config.DATA_DERIVED / "current_position.csv")}

    flagged = [s for s in summary if s["position_resolution"] in
              ("flagged_no_match", "flagged_no_data")]

    rows = []
    for s in flagged:
        c = current.get(s["mlbam_id"], {})
        rows.append({
            "player": s["player"],
            "listed_positions": s["position"],
            "currently_scored_as": s["position_used_for_scoring"],
            "real_current_position": c.get("current_position", ""),
            "games_at_that_position": c.get("current_position_games", ""),
            "season_measured": c.get("current_position_season", ""),
            "all_positions_played": c.get("all_positions_played", ""),
            "reason": s["position_resolution"],
        })
    rows.sort(key=lambda r: r["player"])

    out = config.OUTPUTS / "position_review_needed.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else
                           ["player", "listed_positions", "currently_scored_as",
                            "real_current_position", "games_at_that_position",
                            "season_measured", "all_positions_played", "reason"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} flagged players to {out}")


if __name__ == "__main__":
    main()
