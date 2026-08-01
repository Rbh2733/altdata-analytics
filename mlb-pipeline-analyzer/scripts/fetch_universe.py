"""Downloads a multi-season player universe and writes data/raw/player_universe.csv.

Adapted from this repo's earlier baseball project with one deliberate
change: the union spans seasons 2021 through 2026 instead of 2026 alone.
The earlier project's universe was appearance-based for a single season,
which made players who were rostered but injured, or who had left
affiliated ball, invisible (its own scoreboard documented Triston Casas,
an established MLB player, unmatched for exactly this reason). A
multi-season union closes most of that hole for zero methodology cost,
six bulk calls per season.

Bulk rather than per-name search, same reasons as before, all verified
live: fewer calls, offline tests, and MLB's own search endpoint cannot
find players indexed under use-names ("Leodalis De Vries" returns zero
results).

The level column is the highest level seen in the most recent season the
player appeared, used only as a matcher tiebreaker, never for population
selection or readiness computation.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from ingestion import api

SEASONS = [2026, 2025, 2024, 2023, 2022, 2021]   # newest first, first write wins

# Highest level first within a season. sportId codes verified live.
LEVELS = {1: "MLB", 11: "AAA", 12: "AA", 13: "A+", 14: "A", 16: "ROK"}

FIELDS = [
    "mlbam_id", "level", "full_name", "first_name", "last_name",
    "use_name", "use_last_name", "full_fml_name", "middle_name",
    "name_slug", "birth_date", "primary_position", "mlb_debut_date",
    "first_seen_season",
]


def slim(person: dict, level: str, season: int) -> dict:
    return {
        "mlbam_id": person.get("id", ""),
        "level": level,
        "full_name": person.get("fullName", ""),
        "first_name": person.get("firstName", ""),
        "last_name": person.get("lastName", ""),
        "use_name": person.get("useName", ""),
        "use_last_name": person.get("useLastName", ""),
        "full_fml_name": person.get("fullFMLName", ""),
        "middle_name": person.get("middleName", ""),
        "name_slug": person.get("nameSlug", ""),
        "birth_date": person.get("birthDate", ""),
        "primary_position": person.get("primaryPosition", {}).get("abbreviation", ""),
        "mlb_debut_date": person.get("mlbDebutDate", ""),
        "first_seen_season": season,
    }


def main():
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)

    by_id = {}
    for season in SEASONS:
        for sport_id, level in LEVELS.items():
            people = api.sports_players(sport_id, season)
            new = 0
            for person in people:
                pid = person.get("id")
                if pid and pid not in by_id:
                    by_id[pid] = slim(person, level, season)
                    new += 1
                elif pid and not by_id[pid].get("mlb_debut_date") and person.get("mlbDebutDate"):
                    by_id[pid]["mlb_debut_date"] = person.get("mlbDebutDate")
            print(f"  {season} sportId {sport_id:>2} ({level:>3}): "
                  f"{len(people):>5} returned, {new:>5} new")

    path = config.DATA_RAW / "player_universe.csv"
    rows = [by_id[k] for k in sorted(by_id)]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    debuted = sum(1 for r in rows if r["mlb_debut_date"])
    print(f"\nwrote {len(rows)} unique players to {path}")
    print(f"  {debuted} have an MLB debut date, {len(rows) - debuted} have not debuted")


if __name__ == "__main__":
    main()
