"""End-to-end lab run: generate, resolve, tag the tail, evaluate, QA.

Usage:
  python run_all.py                 deterministic run (mock tagger)
  python run_all.py --tagger claude live LLM tagger (needs anthropic + API key)

Outputs land in outputs/: resolved.csv, metrics.json, qa_report.md,
resolved_sample.csv. The data/ inputs regenerate deterministically on every
run, so the whole repository is reproducible from a clean checkout.
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import evaluate  # noqa: E402
import qa_checks  # noqa: E402
import resolve  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tagger", choices=["mock", "claude"], default="mock")
    args = ap.parse_args()

    print("[1/5] generating deterministic synthetic data")
    subprocess.run([sys.executable, str(ROOT / "src" / "generate_data.py")], check=True)

    print("[2/5] resolving raw strings against the vendor master")
    rows = resolve.run()
    vendors = resolve.load_vendors()

    tail = [r for r in rows if r["method"] in ("review", "unmatched")]
    print(f"[3/5] tagging the tail ({len(tail)} rows) with the {args.tagger} tagger")
    if args.tagger == "claude":
        import tagger_claude as tagger
    else:
        import tagger_mock as tagger
    tags = {t["raw_id"]: t for t in tagger.tag(tail, vendors)}

    cat_by_vendor = {v["vendor"]: v["category"] for v in vendors}
    dropped = 0
    for r in rows:
        if r["method"] not in ("review", "unmatched"):
            # settled by the resolver; never depends on the tagger returning
            r["final_vendor"] = r["vendor"]
            r["final_method"] = r["method"]
            r["new_vendor_flag"] = 0
            r["tagger_confidence"] = ""
            continue
        t = tags.get(r["raw_id"])
        if t is None:
            # the tagger failed to return this row; make the gap visible
            # instead of silently accepting the resolver's unconfirmed guess
            dropped += 1
            r["final_vendor"] = ""
            r["final_method"] = "tagger_dropped"
            r["new_vendor_flag"] = 0
            r["tagger_confidence"] = ""
            continue
        r["tagger_confidence"] = t["confidence"]
        if t["vendor_guess"]:
            r["new_vendor_flag"] = t["new_vendor_flag"]
            r["final_vendor"] = t["vendor_guess"]
            r["category"] = cat_by_vendor.get(t["vendor_guess"], t["category_guess"])
            r["final_method"] = "tagger_review" if r["method"] == "review" else "tagger_tail"
        elif r["method"] == "review":
            # tagger abstained but the resolver holds a >= REVIEW_T candidate;
            # keep it under its own label rather than erasing it, since the
            # abstaining mock judges with a strictly weaker signal
            r["new_vendor_flag"] = 0
            r["final_vendor"] = r["vendor"]
            r["final_method"] = "review_unconfirmed"
        else:
            r["new_vendor_flag"] = t["new_vendor_flag"]
            r["final_vendor"] = ""
            r["category"] = t["category_guess"]
            r["final_method"] = "new_vendor_candidate"
    if dropped:
        print(f"WARNING: tagger failed to return {dropped} rows (method tagger_dropped)")

    print("[4/5] evaluating against ground truth")
    metrics = evaluate.evaluate(rows)
    metrics["tagger"] = args.tagger

    print("[5/5] running QA expectations and drift monitor")
    checks, rates, drift_flags = qa_checks.run_qa(rows, vendors)
    report = qa_checks.render_report(checks, rates, drift_flags, metrics)

    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    fields = ["raw_id", "week", "raw_string", "amount", "core", "method", "score",
              "vendor", "final_vendor", "final_method", "category",
              "new_vendor_flag", "tagger_confidence"]
    with open(out / "resolved.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in fields} for r in rows)

    # stratified sample: up to 30 rows per final_method, seeded, so the
    # committed sample shows every pipeline stage rather than 200 easy rows
    import random
    sampler = random.Random(7)
    by_method = {}
    for r in rows:
        by_method.setdefault(r["final_method"], []).append(r)
    sample = []
    for m in sorted(by_method):
        grp = by_method[m]
        sample.extend(grp if len(grp) <= 30 else sampler.sample(grp, 30))
    sample.sort(key=lambda r: int(r["raw_id"]))
    with open(out / "resolved_sample.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in fields} for r in sample)
    with open(out / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    (out / "qa_report.md").write_text(report, encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    if any(not ok for _, ok, _ in checks):
        print("QA FAILURES present, see outputs/qa_report.md")
        sys.exit(1)
    print("done. outputs/: resolved.csv, resolved_sample.csv, metrics.json, qa_report.md")


if __name__ == "__main__":
    main()
