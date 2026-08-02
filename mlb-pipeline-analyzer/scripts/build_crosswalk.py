"""Resolves every ranking row to an MLBAM player id and writes the
crosswalk plus per-stage metrics.

Precision is reported per stage, never blended: an exact match, a
tiebroken match, and a fuzzy match earn different confidence and the
metrics file keeps them separate so nobody averages away where the errors
live. Same discipline as this repo's earlier baseball project.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from matching.resolve_prospect import resolve_all

FIELDS = ["cohort", "rank", "player", "position", "current_level",
          "method", "score", "matched_on", "disambiguated_by",
          "mlbam_id", "matched_name", "mlb_debut_date"]


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def apply_overrides(rows, universe):
    """Fill declined rows from the curated override table, visibly.

    Overrides exist only for genuine name collisions the automatic
    tiebreakers correctly refuse to guess on. Each carries a written reason
    and the rows it fills are labeled method=manual_override so the metrics
    never fold them into accuracy the matcher did not earn.
    """
    path = config.DATA_RAW / "manual_overrides.csv"
    if not path.exists():
        return rows
    by_id = {u["mlbam_id"]: u for u in universe}
    overrides = {(o["cohort"], o["rank"], o["player"]): o for o in read_csv(path)}
    for r in rows:
        key = (r["cohort"], r["rank"], r["player"])
        if not r["mlbam_id"] and key in overrides:
            o = overrides[key]
            u = by_id.get(o["mlbam_id"], {})
            r["mlbam_id"] = o["mlbam_id"]
            r["matched_name"] = u.get("full_name", "")
            r["mlb_debut_date"] = u.get("mlb_debut_date", "")
            r["method"] = "manual_override"
            r["disambiguated_by"] = "curated"
    return rows


def main():
    rankings = read_csv(config.DATA_RAW / "prospect_rankings.csv")
    universe = read_csv(config.DATA_RAW / "player_universe.csv")

    rows = apply_overrides(resolve_all(rankings, universe), universe)

    config.DATA_DERIVED.mkdir(parents=True, exist_ok=True)
    out = config.DATA_DERIVED / "crosswalk.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in FIELDS})

    by_stage = Counter(r["method"] for r in rows)
    matched = [r for r in rows if r["mlbam_id"]]
    unique_ids = {r["mlbam_id"] for r in matched}
    debuted = {r["mlbam_id"] for r in matched if r["mlb_debut_date"]}
    metrics = {
        "ranking_rows": len(rows),
        "matched_rows": len(matched),
        "coverage_pct": round(100 * len(matched) / len(rows), 1),
        "by_stage": dict(by_stage),
        "unique_matched_players": len(unique_ids),
        "unique_debuted": len(debuted),
        "unique_never_debuted": len(unique_ids) - len(debuted),
    }
    mpath = config.DATA_DERIVED / "crosswalk_metrics.json"
    mpath.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    unmatched = [r for r in rows if not r["mlbam_id"]]
    if unmatched:
        print("\nunmatched rows:")
        for r in unmatched:
            print(f"  {r['cohort']} #{r['rank']} {r['player']} "
                  f"({r['method']}/{r['disambiguated_by']})")


if __name__ == "__main__":
    main()
