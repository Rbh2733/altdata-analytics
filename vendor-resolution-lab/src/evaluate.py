"""Evaluation against ground truth.

Prices each pipeline stage separately: per-method precision, coverage,
false merges (a novel vendor forced onto a canonical name, the worst
failure mode in vendor matching), and new-vendor detection recall on the
seeded week-7 drift rows.
"""

import csv
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def load_labels():
    labels = {}
    with open(DATA / "labels.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels[row["raw_id"]] = row
    return labels


def evaluate(rows):
    labels = load_labels()
    per_method = defaultdict(lambda: {"n": 0, "correct": 0})
    false_merges = 0
    novel_total = 0
    novel_flagged = 0
    flagged_total = 0
    assigned = 0

    for r in rows:
        lab = labels[r["raw_id"]]
        is_novel = lab["in_canonical"] == "0"
        if is_novel:
            novel_total += 1

        final_vendor = r.get("final_vendor", "")
        method = r.get("final_method", r["method"])
        if final_vendor:
            assigned += 1
            per_method[method]["n"] += 1
            if final_vendor == lab["true_vendor"]:
                per_method[method]["correct"] += 1
            elif is_novel:
                false_merges += 1
        if r.get("new_vendor_flag") == 1:
            flagged_total += 1
            if is_novel:
                novel_flagged += 1

    metrics = {
        "rows": len(rows),
        "assigned": assigned,
        "coverage": round(assigned / len(rows), 4),
        "false_merges_of_novel_rows": false_merges,
        "novel_rows_total": novel_total,
        "novel_rows_flagged_new_vendor": novel_flagged,
        "new_vendor_flags_total": flagged_total,
        "novel_detection_recall": round(novel_flagged / novel_total, 4) if novel_total else None,
        "novel_detection_precision": round(novel_flagged / flagged_total, 4) if flagged_total else None,
        "per_method": {},
    }
    for m, d in sorted(per_method.items()):
        metrics["per_method"][m] = {
            "n": d["n"],
            "precision": round(d["correct"] / d["n"], 4) if d["n"] else None,
        }
    return metrics
