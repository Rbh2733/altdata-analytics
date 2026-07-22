"""Orchestrates the world: builds vendors, trajectories, outcomes, and
the three exhaust streams, then writes everything under data/. Byte-
stable CSV writer (fixed column order, fixed float formatting, UTF-8,
``\\n`` line endings, no wall clock) so a rerun reproduces the tree
exactly.
"""

import csv
from pathlib import Path

import numpy as np

import config
from simulation import params, vendors as vendors_mod, trajectories as traj_mod
from simulation import outcomes as outcomes_mod
from simulation import exhaust_jobs, exhaust_web, exhaust_spend


def _write_csv(rows, fieldnames, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _pick_plant_vendor(segment, vendors, trajectories_by_id, affected_quarters,
                        rng, restrict_middle=False, vendor_state=None,
                        alive_through=None, min_window_reqs=None):
    """Plant-vendor selection with apparatus-validity gates (fifth
    disclosed fix, 2026-07-22): a plant is only a measurable experiment
    if its vendor is actually emitting in the plant window. alive_through
    skips vendors shut down on or before (or acquired strictly before)
    that quarter, since their exhaust is dark when the plant fires;
    min_window_reqs skips vendors whose organic requisition volume in the
    affected quarters is too small for a multiplied storm to surface at
    all. Neither gate consumes randomness, so they only reorder which
    candidate wins the same permutation."""
    candidates = [v for v in vendors if v["segment"] == segment]
    if restrict_middle:
        candidates = sorted(candidates, key=lambda v: v["initial_headcount"])
        n = len(candidates)
        candidates = candidates[n // 4: 3 * n // 4] or candidates
    ids = [v["vendor_id"] for v in candidates]
    order = rng.permutation(len(ids))
    for idx in order:
        vid = ids[idx]
        infl_quarters = {i["quarter"] for i in trajectories_by_id[vid]["inflections"]}
        if infl_quarters & set(affected_quarters):
            continue
        if alive_through is not None and vendor_state is not None:
            through = config.quarter_index(alive_through) + 1  # 1-based
            st = vendor_state[vid]
            sd = st["shutdown_quarter_index"]
            acq = st["acquired_quarter_index"]
            if sd is not None and sd <= through:
                continue  # shutdown truncates its own quarter's exhaust
            if acq is not None and acq < through:
                continue  # acquisition darkens exhaust the quarter after
        if min_window_reqs is not None:
            total = sum(trajectories_by_id[vid]["requisitions_target"][
                config.quarter_index(q)] for q in affected_quarters)
            if total < min_window_reqs:
                continue
        return vid
    return ids[0]


AMBIGUOUS_TRUE_FUNCTION = {
    "Solutions Engineer": "engineering",
    "Developer Advocate": "engineering",
    "Support Engineering Manager": "support",
    "Customer Success Engineer": "support",
    "ML Platform Engineer": "ml_infrastructure",
    "Research Engineer": "research",
}
MODIFIERS = ["", "Senior ", "Staff ", "Lead ", "Jr. ", "Principal ",
             "Associate ", "II"]


def _build_tagger_validation_set(rng: np.random.Generator):
    """30 template rows per title-bank function plus 30 ambiguous rows
    (210 total at six functions). The ambiguous rows are where the
    designed confusions live and get measured."""
    rows = []
    per_func = 30
    for func, bank in exhaust_jobs.TITLE_BANK.items():
        for i in range(per_func):
            base = bank[i % len(bank)]
            mod = MODIFIERS[i % len(MODIFIERS)]
            title = f"{mod}{base}" if not mod.endswith(" ") else f"{mod}{base}"
            if mod == "II":
                title = f"{base} II"
            rows.append({"title": title, "true_function": func})
    ambiguous_total = 30
    amb_titles = list(AMBIGUOUS_TRUE_FUNCTION.keys())
    for i in range(ambiguous_total):
        base = amb_titles[i % len(amb_titles)]
        mod = MODIFIERS[i % len(MODIFIERS)]
        title = f"{base} II" if mod == "II" else f"{mod}{base}"
        rows.append({"title": title, "true_function": AMBIGUOUS_TRUE_FUNCTION[base]})
    return rows


def main(root=None, verbose=True, seed=None):
    root = config.ROOT if root is None else Path(root)
    data_dir = root / "data"

    rng = np.random.default_rng(config.SEED if seed is None else seed)

    vendors = vendors_mod.build_vendors(rng)
    trajectories_by_id = {v["vendor_id"]: traj_mod.build_trajectory(v, rng)
                           for v in vendors}
    events, disclosures, vendor_state = outcomes_mod.generate_outcomes(
        vendors, trajectories_by_id, rng)

    bot_spike_vendor = _pick_plant_vendor(
        params.PLANT_BOT_SPIKE["segment"], vendors, trajectories_by_id,
        [params.PLANT_BOT_SPIKE["quarter"]], rng, restrict_middle=True,
        vendor_state=vendor_state,
        alive_through=params.PLANT_BOT_SPIKE["quarter"])
    # restrict_middle plus a minimal organic-volume gate for the storm
    # (fifth disclosed fix, 2026-07-22): the plant multiplies whatever
    # the vendor organically posts, so a near-zero-requisition vendor
    # storms invisibly. Same size rationale as the bot-spike restriction.
    repost_storm_vendor = _pick_plant_vendor(
        params.PLANT_REPOST_STORM["segment"], vendors, trajectories_by_id,
        params.PLANT_REPOST_STORM["quarters"], rng, restrict_middle=True,
        vendor_state=vendor_state,
        alive_through=params.PLANT_REPOST_STORM["quarters"][-1],
        min_window_reqs=10)
    # The migrated descriptors are the fragmentation vendor's permanent
    # state, so it must keep emitting through the end of the calendar for
    # the bridge to have anything to work with.
    fragmentation_vendor = _pick_plant_vendor(
        params.PLANT_DESCRIPTOR_FRAGMENTATION["segment"], vendors, trajectories_by_id,
        [params.PLANT_DESCRIPTOR_FRAGMENTATION["quarter"]], rng,
        vendor_state=vendor_state, alive_through=config.QUARTERS[-1])

    postings, tracked_rows = exhaust_jobs.build_job_postings(
        vendors, trajectories_by_id, vendor_state, rng,
        repost_storm_vendor_id=repost_storm_vendor)
    web_rows, covered_rows = exhaust_web.build_web_traffic(
        vendors, trajectories_by_id, vendor_state, rng,
        bot_spike_vendor_id=bot_spike_vendor)
    spend_rows, descriptor_map_rows, vendor_descriptors = exhaust_spend.build_spend_panel(
        vendors, trajectories_by_id, vendor_state, rng,
        fragmentation_vendor_id=fragmentation_vendor)

    tagger_val = _build_tagger_validation_set(rng)

    # ---- data/public
    _write_csv(
        [{"vendor_id": v["vendor_id"], "name": v["name"], "segment": v["segment"]}
         for v in vendors],
        ["vendor_id", "name", "segment"], data_dir / "public" / "vendor_directory.csv")

    _write_csv(descriptor_map_rows, ["vendor_id", "descriptor_string"],
               data_dir / "public" / "descriptor_map.csv")

    _write_csv(tagger_val, ["title", "true_function"],
               data_dir / "public" / "tagger_validation_set.csv")

    # ---- data/exhaust
    _write_csv(postings, ["posting_id", "vendor_id", "title", "posted_date",
                            "closed_date", "location"],
               data_dir / "exhaust" / "job_postings.csv")
    _write_csv(tracked_rows, ["vendor_id", "tracked"],
               data_dir / "exhaust" / "jobs_tracked_vendors.csv")
    _write_csv([{"vendor_id": r["vendor_id"], "month": r["month"],
                  "estimated_visits": r["estimated_visits"]} for r in web_rows],
               ["vendor_id", "month", "estimated_visits"],
               data_dir / "exhaust" / "web_traffic.csv")
    _write_csv(covered_rows, ["vendor_id", "covered"],
               data_dir / "exhaust" / "web_covered_vendors.csv")
    _write_csv([{"descriptor_string": r["descriptor_string"], "txn_date": r["txn_date"],
                  "amount": format(r["amount"], ".2f"), "panelist_id": r["panelist_id"]}
                 for r in spend_rows],
               ["descriptor_string", "txn_date", "amount", "panelist_id"],
               data_dir / "exhaust" / "spend_panel.csv")

    # ---- data/truth
    truth_fin_rows = []
    for v in vendors:
        vid = v["vendor_id"]
        traj = trajectories_by_id[vid]
        for i in range(config.N_QUARTERS):
            truth_fin_rows.append({
                "vendor_id": vid, "quarter": config.QUARTERS[i],
                "arr_m": format(traj["truth_arr"][i], ".6f"),
                "headcount": round(traj["truth_headcount"][i]),
                "growth": format(traj["truth_growth"][i], ".6f"),
            })
    _write_csv(truth_fin_rows, ["vendor_id", "quarter", "arr_m", "headcount", "growth"],
               data_dir / "truth" / "truth_financials.csv")

    infl_rows = []
    for v in vendors:
        vid = v["vendor_id"]
        for infl in trajectories_by_id[vid]["inflections"]:
            infl_rows.append({
                "vendor_id": vid, "quarter": infl["quarter"], "type": infl["type"],
                "delta_pp": format(infl["delta_pp"], ".4f"),
            })
    infl_rows.sort(key=lambda r: (r["vendor_id"], r["quarter"]))
    _write_csv(infl_rows, ["vendor_id", "quarter", "type", "delta_pp"],
               data_dir / "truth" / "inflections.csv")

    events_sorted = sorted(events, key=lambda e: (e["vendor_id"], e["quarter_index"], e["event_type"]))
    _write_csv([{"vendor_id": e["vendor_id"], "event_type": e["event_type"],
                  "quarter": e["quarter"]} for e in events_sorted],
               ["vendor_id", "event_type", "quarter"],
               data_dir / "truth" / "outcome_events.csv")

    disclosures_sorted = sorted(disclosures, key=lambda d: (d["vendor_id"], d["quarter"]))
    _write_csv([{"vendor_id": d["vendor_id"], "quarter": d["quarter"],
                  "disclosed_revenue_m": format(d["disclosed_revenue_m"], ".2f")}
                 for d in disclosures_sorted],
               ["vendor_id", "quarter", "disclosed_revenue_m"],
               data_dir / "truth" / "disclosed_revenues.csv")

    plant_rows = [
        {"pathology": "bot_traffic_spike", "vendor_id": bot_spike_vendor,
         "quarter": params.PLANT_BOT_SPIKE["quarter"],
         "detail": f"{params.PLANT_BOT_SPIKE['weeks']} weeks x{params.PLANT_BOT_SPIKE['multiplier']}"},
        {"pathology": "job_repost_storm", "vendor_id": repost_storm_vendor,
         "quarter": "|".join(params.PLANT_REPOST_STORM["quarters"]),
         "detail": f"raw_multiplier={params.PLANT_REPOST_STORM['raw_multiplier']}"},
        {"pathology": "descriptor_fragmentation", "vendor_id": fragmentation_vendor,
         "quarter": params.PLANT_DESCRIPTOR_FRAGMENTATION["quarter"],
         "detail": f"fade_weeks={params.PLANT_DESCRIPTOR_FRAGMENTATION['fade_weeks']}"},
        {"pathology": "coverage_cliff", "vendor_id": "ALL:" + params.PLANT_COVERAGE_CLIFF["segment"],
         "quarter": "|".join(params.PLANT_COVERAGE_CLIFF["quarters"]),
         "detail": f"segment={params.PLANT_COVERAGE_CLIFF['segment']}"},
    ]
    _write_csv(plant_rows, ["pathology", "vendor_id", "quarter", "detail"],
               data_dir / "truth" / "planted_pathologies.csv")

    return {
        "n_vendors": len(vendors),
        "n_postings": len(postings),
        "n_web_rows": len(web_rows),
        "n_spend_rows": len(spend_rows),
        "n_events": len(events),
        "n_disclosures": len(disclosures),
        "plant_vendors": {
            "bot_spike": bot_spike_vendor,
            "repost_storm": repost_storm_vendor,
            "fragmentation": fragmentation_vendor,
        },
    }


if __name__ == "__main__":
    summary = main()
    print(summary)
