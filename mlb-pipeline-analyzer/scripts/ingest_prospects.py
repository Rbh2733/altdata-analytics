"""Flattens the three-cohort prospect-ranking workbook into one tidy CSV.

Source: data/raw/prospect_rankings_2022_2024.xlsx, three tabs (2022, 2023,
2024), 100 ranked prospects each, with a Current Level column reflecting
where each player sits TODAY rather than when they were ranked.

Cohorts are kept as separate rows rather than deduped to a unique-player
table, on purpose: 75 of the 300 rows are repeat appearances, and a
matcher that resolves the same person inconsistently across cohorts is
exhibiting a real defect worth being able to see. The measured shape of
the population: 212 unique names, 137 on exactly one list, 62 on two, 13
on all three.

Adapted from this repo's earlier baseball project. The current_* columns
are present-day snapshots and are NEVER used to select populations or
compute readiness, only as matcher tiebreakers. That rule is what the
earlier project's population leak taught.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import config

SOURCE = "prospect_rankings_2022_2024.xlsx"
FIELDS = ["cohort", "rank", "player", "position", "current_team",
          "current_level", "current_age", "bats", "throws"]


def main():
    src = config.DATA_RAW / SOURCE
    if not src.exists():
        raise SystemExit(f"missing {src}")

    xl = pd.ExcelFile(src)
    rows = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet, dtype=str, keep_default_na=False)
        for _, r in df.iterrows():
            rows.append({
                "cohort": sheet,
                "rank": r["Rank"],
                "player": r["Player"].strip(),
                "position": r["Position"].strip(),
                "current_team": r["Current Team"].strip(),
                "current_level": r["Current Level"].strip(),
                "current_age": r["Current Age"].strip(),
                "bats": r["Bats"].strip(),
                "throws": r["Throws"].strip(),
            })

    rows.sort(key=lambda r: (r["cohort"], int(r["rank"])))
    path = config.DATA_RAW / "prospect_rankings.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} ranking rows "
          f"({len(set(r['player'] for r in rows))} unique names) to {path}")


if __name__ == "__main__":
    main()
