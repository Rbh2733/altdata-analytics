"""QA expectations and drift monitoring over the resolved output.

The checks mirror what a production vendor pipeline needs before anything
ships downstream: key uniqueness, referential integrity against the vendor
master, value sanity, and a weekly coverage monitor that flags the seeded
week-7 drift instead of letting the match rate degrade silently.
"""

import re
from collections import Counter, defaultdict

DRIFT_DROP_PP = 0.03  # flag a week whose auto-match rate drops 3pp or more vs trailing mean
LEAD_TOKEN = re.compile(r"^[A-Z0-9]+")


def run_qa(rows, vendors):
    checks = []
    ids = [r["raw_id"] for r in rows]
    checks.append(("raw_id uniqueness", len(ids) == len(set(ids)),
                   f"{len(ids)} rows, {len(set(ids))} distinct ids"))

    canon = {v["vendor"] for v in vendors}
    bad_ref = [r for r in rows if r.get("final_vendor") and r["final_vendor"] not in canon]
    checks.append(("referential integrity (assigned vendor exists in master)",
                   not bad_ref, f"{len(bad_ref)} violations"))

    bad_amt = [r for r in rows if float(r["amount"]) <= 0]
    checks.append(("amount sanity (all positive)", not bad_amt, f"{len(bad_amt)} violations"))

    empty_core = [r for r in rows if not r["core"]]
    checks.append(("normalization non-empty", not empty_core, f"{len(empty_core)} empty cores"))

    weekly = defaultdict(lambda: {"n": 0, "auto": 0})
    for r in rows:
        w = int(r["week"])
        weekly[w]["n"] += 1
        if r["method"] in ("exact", "fuzzy_auto"):
            weekly[w]["auto"] += 1
    rates = {w: d["auto"] / d["n"] for w, d in sorted(weekly.items())}

    drift_flags = []
    weeks = sorted(rates)
    for i, w in enumerate(weeks):
        if i < 3:
            continue
        trailing = sum(rates[weeks[j]] for j in range(i - 3, i)) / 3
        if rates[w] <= trailing - DRIFT_DROP_PP:
            # attribution: what leads the strings the resolver could NOT
            # auto-match this week; a new processor format surfaces here
            # from the data itself, with no prior knowledge of it
            tokens = Counter()
            for r in rows:
                if int(r["week"]) == w and r["method"] not in ("exact", "fuzzy_auto"):
                    m = LEAD_TOKEN.match(r["raw_string"].upper())
                    if m:
                        tokens[m.group()] += 1
            drift_flags.append((w, rates[w], trailing, tokens.most_common(3)))

    return checks, rates, drift_flags


def render_report(checks, rates, drift_flags, metrics) -> str:
    lines = ["# QA Report", ""]
    lines.append("## Expectations")
    lines.append("")
    lines.append("| Check | Result | Detail |")
    lines.append("|---|---|---|")
    for name, ok, detail in checks:
        lines.append(f"| {name} | {'PASS' if ok else 'FAIL'} | {detail} |")
    lines.append("")
    lines.append("## Weekly auto-match rate (exact + fuzzy_auto)")
    lines.append("")
    lines.append("| Week | Auto-match rate |")
    lines.append("|---|---|")
    for w, rate in rates.items():
        lines.append(f"| {w} | {rate:.1%} |")
    lines.append("")
    if drift_flags:
        lines.append("## Drift alerts")
        lines.append("")
        for w, rate, trailing, top_tokens in drift_flags:
            toks = ", ".join(f"{t} ({n} rows)" for t, n in top_tokens)
            lines.append(
                f"- Week {w}: auto-match rate {rate:.1%} vs trailing-3-week mean "
                f"{trailing:.1%}. Degraded beyond the {DRIFT_DROP_PP * 100:.0f}pp "
                f"threshold. Most common leading tokens among non-auto-matched "
                f"strings this week: {toks}. Investigate new processor formats "
                f"and new-vendor candidates before this feeds anything downstream."
            )
    else:
        lines.append("## Drift alerts")
        lines.append("")
        lines.append("- None.")
    lines.append("")
    lines.append("## Headline metrics")
    lines.append("")
    lines.append(f"- Coverage: {metrics['coverage']:.1%} of rows assigned a canonical vendor")
    for m, d in metrics["per_method"].items():
        p = f"{d['precision']:.2%}" if d["precision"] is not None else "n/a"
        lines.append(f"- {m}: n={d['n']}, precision {p}")
    lines.append(f"- False merges of novel-vendor rows: {metrics['false_merges_of_novel_rows']}")
    lines.append(
        f"- Novel-vendor detection: {metrics['novel_rows_flagged_new_vendor']} of "
        f"{metrics['novel_rows_total']} novel rows flagged "
        f"({metrics['novel_detection_recall']:.1%} recall); "
        f"{metrics['novel_rows_flagged_new_vendor']} of {metrics['new_vendor_flags_total']} "
        f"flags are truly novel ({metrics['novel_detection_precision']:.1%} precision)"
    )
    lines.append("")
    return "\n".join(lines)
