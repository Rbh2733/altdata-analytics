"""Precision/recall of the composite's accel/stall flags against truth
inflections, at k=1 and k=2 quarters, stratified by type and tier. A
flag matches a truth event of the same type within +/-k quarters,
greedy one-to-one in time order per vendor. Precision is stratified by
the tier at the flag's own quarter; recall by the tier at the event's
own quarter (the coverage_matrix tier for that vendor-quarter, whether
or not a flag exists there). Unlabeled sub-8pp change points draw no
truth row and so cannot be matched: any flag near one counts against
precision, deliberately.
"""

import pandas as pd

import config

K_VALUES = [1, 2]


def _greedy_match(flags: pd.DataFrame, events: pd.DataFrame, k: int):
    matched_flag_idx, matched_event_idx = set(), set()
    for vid in events["vendor_id"].unique():
        v_events = events[events["vendor_id"] == vid].sort_values("quarter")
        v_flags = flags[flags["vendor_id"] == vid].copy()
        used = set()
        for ei, erow in v_events.iterrows():
            e_idx = config.quarter_index(erow["quarter"])
            cands = v_flags[(v_flags["type"] == erow["type"]) & (~v_flags.index.isin(used))]
            if cands.empty:
                continue
            dist = cands["quarter"].map(lambda q: abs(config.quarter_index(q) - e_idx))
            cands = cands.assign(_dist=dist)
            cands = cands[cands["_dist"] <= k]
            if cands.empty:
                continue
            best = cands.sort_values(["_dist", "quarter"]).index[0]
            used.add(best)
            matched_flag_idx.add(best)
            matched_event_idx.add(ei)
    return matched_flag_idx, matched_event_idx


def build_flags_and_events(scored_df: pd.DataFrame, inflections_df: pd.DataFrame):
    flags = []
    for _, r in scored_df.iterrows():
        if r.get("accel_flag"):
            flags.append({"vendor_id": r["vendor_id"], "quarter": r["quarter"],
                          "type": "acceleration", "tier": r["tier"]})
        if r.get("stall_flag"):
            flags.append({"vendor_id": r["vendor_id"], "quarter": r["quarter"],
                          "type": "stall", "tier": r["tier"]})
    flags_df = pd.DataFrame(flags)

    tier_lookup = scored_df.set_index(["vendor_id", "quarter"])["tier"].to_dict()
    events = inflections_df.copy()
    events["tier"] = events.apply(
        lambda r: tier_lookup.get((r["vendor_id"], r["quarter"]), "C"), axis=1)
    return flags_df, events


def score(scored_df: pd.DataFrame, inflections_df: pd.DataFrame) -> pd.DataFrame:
    flags_df, events_df = build_flags_and_events(scored_df, inflections_df)
    rows = []
    for k in K_VALUES:
        matched_flag_idx, matched_event_idx = _greedy_match(flags_df, events_df, k)
        for etype in ("acceleration", "stall"):
            for tier in ("A", "B", "C"):
                f_cell = flags_df[(flags_df["type"] == etype) & (flags_df["tier"] == tier)] \
                    if not flags_df.empty else flags_df
                e_cell = events_df[(events_df["type"] == etype) & (events_df["tier"] == tier)]
                n_flags = len(f_cell)
                n_events = len(e_cell)
                n_matched_flags = sum(1 for i in f_cell.index if i in matched_flag_idx)
                n_matched_events = sum(1 for i in e_cell.index if i in matched_event_idx)
                precision = n_matched_flags / n_flags if n_flags else float("nan")
                recall = n_matched_events / n_events if n_events else float("nan")
                rows.append({"k": k, "type": etype, "tier": tier,
                             "n_flags": n_flags, "n_events": n_events,
                             "precision": precision, "recall": recall})
    return pd.DataFrame(rows)
