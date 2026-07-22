"""Four anomaly detectors plus generic sanity checks. Thresholds are
frozen here, data-independent, and never reference plant parameters
(which live behind the import fence in simulation/params.py). Every
function accepts whatever data slice it is given (full history for the
committed QA report, or a single quarter's as_of() slice inside feature
building), so the same rule fires identically in both places, which is
what keeps the delete-the-future test honest for QA-derived corrections.
"""

import re
from datetime import date

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Frozen thresholds
# ---------------------------------------------------------------------------

BOT_SPIKE_Z_THRESHOLD = 4.0
BOT_SPIKE_TRAILING_MONTHS = 6
BOT_SPIKE_COROBORATION_GROWTH = 0.35    # |log growth| below this = "no move"

REPOST_STORM_FINGERPRINT_RATIO = 0.4
REPOST_STORM_MIN_RAW = 10               # ignore tiny vendor-quarters
RELIST_COLLAPSE_WINDOW_DAYS = 45

FRAG_PANELIST_OVERLAP_MIN = 0.5
FRAG_AMOUNT_RATIO_MIN = 0.6
FRAG_CADENCE_RATIO_RANGE = (0.8, 1.25)
FRAG_FADE_RATIO_MAX = 0.7               # candidate vendor must show some decline

CLIFF_DROP_FRACTION = 0.5
CLIFF_TRAILING_QUARTERS = 4

SPEND_PRESENCE_MIN_TXN_TRAILING_2Q = 8

_PUNCT_RE = re.compile(r"[^a-z0-9 ]")


def normalize_title(title: str) -> str:
    t = title.lower()
    t = _PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def fingerprint(title: str, location: str) -> str:
    return f"{normalize_title(title)}|{location}"


# ---------------------------------------------------------------------------
# P2: job repost storm
# ---------------------------------------------------------------------------

def _quarter_of_date(date_str: str) -> str:
    import config
    y, m = int(date_str[:4]), int(date_str[5:7])
    return config.quarter_of_date(y, m)


def repost_storm_ratios(jobs_df: pd.DataFrame) -> pd.DataFrame:
    """Unique-fingerprint / raw-posting ratio per vendor-quarter."""
    if jobs_df.empty:
        return pd.DataFrame(columns=["vendor_id", "quarter", "raw", "unique", "ratio"])
    df = jobs_df.copy()
    df["quarter"] = df["posted_date"].map(_quarter_of_date)
    df["fp"] = [fingerprint(t, l) for t, l in zip(df["title"], df["location"])]
    g = df.groupby(["vendor_id", "quarter"])
    out = g.agg(raw=("fp", "size"), unique=("fp", "nunique")).reset_index()
    out["ratio"] = out["unique"] / out["raw"]
    return out


def detect_repost_storm(jobs_df: pd.DataFrame) -> pd.DataFrame:
    ratios = repost_storm_ratios(jobs_df)
    flagged = ratios[(ratios["raw"] >= REPOST_STORM_MIN_RAW)
                      & (ratios["ratio"] < REPOST_STORM_FINGERPRINT_RATIO)]
    return flagged.reset_index(drop=True)


def dedupe_jobs(jobs_df: pd.DataFrame,
                 window_days: int = RELIST_COLLAPSE_WINDOW_DAYS) -> pd.DataFrame:
    """Collapse near-duplicate postings (same normalized title+location for
    the same vendor) into one row per requisition when the re-post lands
    within `window_days` of the previous one in the same fingerprint
    group. Returns the deduped postings (one row per surviving
    requisition, posted_date = first-seen date of that requisition)."""
    if jobs_df.empty:
        return jobs_df.copy()
    df = jobs_df.copy()
    df["fp"] = [fingerprint(t, l) for t, l in zip(df["title"], df["location"])]
    df = df.sort_values(["vendor_id", "fp", "posted_date"])
    # Single forward pass with itertuples (not groupby+iterrows, which is
    # the classic pandas slow path): track the last kept date per
    # (vendor, fingerprint) key by hand.
    last_kept = {}
    keep_mask = []
    collapsed_legit = 0
    for row in df.itertuples(index=False):
        key = (row.vendor_id, row.fp)
        d = date.fromisoformat(row.posted_date)
        prev = last_kept.get(key)
        if prev is None or (d - prev).days > window_days:
            keep_mask.append(True)
            last_kept[key] = d
        else:
            # this collapse might be eating a legitimate background
            # re-list rather than a storm duplicate; counted, not hidden.
            keep_mask.append(False)
            collapsed_legit += 1
    result = df[keep_mask].drop(columns=["fp"]).reset_index(drop=True)
    result.attrs["collapsed_count"] = collapsed_legit
    return result


# ---------------------------------------------------------------------------
# P1: bot traffic spike
# ---------------------------------------------------------------------------

def bot_spike_flags(web_df: pd.DataFrame) -> pd.DataFrame:
    """Rule: within-vendor monthly log-RETURN z > 4 vs the trailing 6
    months of returns (not levels: a return-based z-score has a much
    more stable variance under a slowly-trending series than a
    level-based one would, since it does not conflate "the vendor is
    growing" with "the vendor just had one weird month")."""
    if web_df.empty:
        return pd.DataFrame(columns=["vendor_id", "month", "z", "log_return"])
    df = web_df.sort_values(["vendor_id", "month"]).copy()
    df["log_visits"] = np.log(df["estimated_visits"].clip(lower=1))
    rows = []
    for vid, grp in df.groupby("vendor_id", sort=False):
        grp = grp.reset_index(drop=True)
        lv = grp["log_visits"].values
        if len(lv) < 2:
            continue
        ret = np.diff(lv)  # ret[i] = lv[i+1]-lv[i], aligned to month i+1
        for i in range(1, len(ret) + 1):
            lo = max(0, i - 1 - BOT_SPIKE_TRAILING_MONTHS)
            trailing = ret[lo:i - 1]
            if len(trailing) < BOT_SPIKE_TRAILING_MONTHS:
                continue  # need a full trailing window of returns
            mu, sd = trailing.mean(), trailing.std(ddof=0)
            sd = max(sd, 0.10)  # floor near the known monthly noise sigma
                                 # so a lucky flat trailing window cannot
                                 # manufacture a spurious spike
            z = (ret[i - 1] - mu) / sd
            if z > BOT_SPIKE_Z_THRESHOLD:
                rows.append({"vendor_id": vid, "month": grp.loc[i, "month"],
                              "z": z, "log_return": ret[i - 1]})
    return pd.DataFrame(rows)


def _quarter_growth_jobs(jobs_df, vendor_id, quarter):
    import config
    ratios = repost_storm_ratios(jobs_df[jobs_df["vendor_id"] == vendor_id])
    idx = config.quarter_index(quarter)
    prior = config.QUARTERS[idx - 1] if idx > 0 else None
    cur_row = ratios[ratios["quarter"] == quarter]
    prior_row = ratios[ratios["quarter"] == prior] if prior else ratios.iloc[0:0]
    cur = cur_row["raw"].sum() if len(cur_row) else 0
    prior_v = prior_row["raw"].sum() if len(prior_row) else 0
    if cur == 0 or prior_v == 0:
        return 0.0
    return float(np.log(cur) - np.log(prior_v))


def _quarter_growth_spend(spend_resolved, vendor_id, quarter):
    import config
    df = spend_resolved[spend_resolved["vendor_id"] == vendor_id].copy()
    if df.empty:
        return 0.0
    df["quarter"] = df["txn_date"].map(_quarter_of_date)
    idx = config.quarter_index(quarter)
    prior = config.QUARTERS[idx - 1] if idx > 0 else None
    cur = df.loc[df["quarter"] == quarter, "amount"].sum()
    prior_v = df.loc[df["quarter"] == prior, "amount"].sum() if prior else 0
    if cur <= 0 or prior_v <= 0:
        return 0.0
    return float(np.log(cur) - np.log(prior_v))


def detect_bot_spikes(web_df: pd.DataFrame, jobs_df: pd.DataFrame = None,
                       spend_resolved: pd.DataFrame = None) -> pd.DataFrame:
    """z>4 candidates, kept only where neither other source corroborates
    a real move that quarter."""
    import config
    cands = bot_spike_flags(web_df)
    if cands.empty:
        return cands
    cands = cands.copy()
    cands["quarter"] = cands["month"].map(
        lambda m: config.quarter_of_date(int(m[:4]), int(m[5:7])))
    keep = []
    for _, row in cands.iterrows():
        jg = (_quarter_growth_jobs(jobs_df, row["vendor_id"], row["quarter"])
              if jobs_df is not None else 0.0)
        sg = (_quarter_growth_spend(spend_resolved, row["vendor_id"], row["quarter"])
              if spend_resolved is not None else 0.0)
        no_corroboration = (abs(jg) < BOT_SPIKE_COROBORATION_GROWTH
                             and abs(sg) < BOT_SPIKE_COROBORATION_GROWTH)
        if no_corroboration:
            keep.append(True)
        else:
            keep.append(False)
    cands["corrected"] = keep
    return cands[cands["corrected"]].drop(columns=["corrected"]).reset_index(drop=True)


def winsorize_web(web_df: pd.DataFrame, spike_rows: pd.DataFrame) -> pd.DataFrame:
    if web_df.empty or spike_rows.empty:
        return web_df.copy()
    df = web_df.sort_values(["vendor_id", "month"]).copy()
    df["corrected"] = False
    flagged_keys = set(zip(spike_rows["vendor_id"], spike_rows["month"]))
    for vid, grp in df.groupby("vendor_id", sort=False):
        idxs = grp.index.tolist()
        visits = grp["estimated_visits"].values.astype(float)
        for pos, idx in enumerate(idxs):
            key = (vid, df.loc[idx, "month"])
            if key in flagged_keys:
                lo = max(0, pos - BOT_SPIKE_TRAILING_MONTHS)
                trailing = visits[lo:pos]
                if len(trailing) > 0:
                    median = float(np.median(trailing))
                    df.loc[idx, "estimated_visits"] = median
                    df.loc[idx, "corrected"] = True
    return df


# ---------------------------------------------------------------------------
# P3: descriptor fragmentation
# ---------------------------------------------------------------------------

def _avg_cadence_days(txn_df: pd.DataFrame):
    if len(txn_df) < 2:
        return None
    dates = sorted(date.fromisoformat(d) for d in txn_df["txn_date"])
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]
    return float(np.mean(gaps)) if gaps else None


def find_unresolved_descriptors(spend_df: pd.DataFrame, descriptor_map_df: pd.DataFrame):
    known = set(descriptor_map_df["descriptor_string"])
    return sorted(set(spend_df["descriptor_string"]) - known)


def detect_descriptor_fragmentation(spend_df: pd.DataFrame, descriptor_map_df: pd.DataFrame):
    """Returns (bridge_map: {new_descriptor: vendor_id}, evidence: list[dict])."""
    unresolved = find_unresolved_descriptors(spend_df, descriptor_map_df)
    evidence = []
    bridge_map = {}
    if not unresolved:
        return bridge_map, evidence

    known_by_vendor = descriptor_map_df.groupby("vendor_id")["descriptor_string"].apply(list).to_dict()

    for vendor_id, descs in known_by_vendor.items():
        known_txn = spend_df[spend_df["descriptor_string"].isin(descs)]
        if known_txn.empty:
            continue
        known_txn = known_txn.copy()
        known_txn["month"] = known_txn["txn_date"].str.slice(0, 7)
        monthly = known_txn.groupby("month").size()
        if len(monthly) < 2:
            continue
        recent = monthly.iloc[-1]
        trailing_avg = monthly.iloc[:-1].mean() if len(monthly) > 1 else recent
        faded = trailing_avg > 0 and (recent / trailing_avg) <= FRAG_FADE_RATIO_MAX
        if not faded:
            continue

        known_panelists = set(known_txn["panelist_id"])
        known_amount_med = known_txn["amount"].median()
        known_cadence = _avg_cadence_days(known_txn)
        if known_cadence is None or known_cadence <= 0:
            continue

        for ud in unresolved:
            if ud in bridge_map:
                continue
            cand = spend_df[spend_df["descriptor_string"] == ud]
            if cand.empty:
                continue
            cand_panelists = set(cand["panelist_id"])
            overlap = (len(known_panelists & cand_panelists) / max(1, len(cand_panelists)))
            cand_amount_med = cand["amount"].median()
            amount_ratio = (min(known_amount_med, cand_amount_med)
                             / max(known_amount_med, cand_amount_med)
                             if max(known_amount_med, cand_amount_med) > 0 else 0)
            cand_cadence = _avg_cadence_days(cand)
            cadence_ratio = (cand_cadence / known_cadence) if cand_cadence else None

            passes = (overlap > FRAG_PANELIST_OVERLAP_MIN
                      and amount_ratio >= FRAG_AMOUNT_RATIO_MIN
                      and cadence_ratio is not None
                      and FRAG_CADENCE_RATIO_RANGE[0] <= cadence_ratio <= FRAG_CADENCE_RATIO_RANGE[1])
            if passes:
                bridge_map[ud] = vendor_id
                evidence.append({
                    "vendor_id": vendor_id, "new_descriptor": ud,
                    "panelist_overlap": overlap, "amount_ratio": amount_ratio,
                    "cadence_ratio": cadence_ratio,
                })
    return bridge_map, evidence


def resolve_spend(spend_df: pd.DataFrame, descriptor_map_df: pd.DataFrame,
                   bridge_map: dict) -> pd.DataFrame:
    """Adds a vendor_id column; rows whose descriptor cannot be resolved
    (not in descriptor_map and not bridged) are dropped."""
    known_map = dict(zip(descriptor_map_df["descriptor_string"], descriptor_map_df["vendor_id"]))
    full_map = {**known_map, **bridge_map}
    df = spend_df.copy()
    df["vendor_id"] = df["descriptor_string"].map(full_map)
    df["descriptor_fragmented"] = df["descriptor_string"].isin(bridge_map)
    return df[df["vendor_id"].notna()].reset_index(drop=True)


# ---------------------------------------------------------------------------
# P4: coverage cliff
# ---------------------------------------------------------------------------

def detect_coverage_cliff(spend_resolved: pd.DataFrame, vendor_directory: pd.DataFrame):
    """Bounded to the horizon actually present in `spend_resolved`: a
    caller handing in an as_of()-limited slice must not get spurious
    'cliff' rows for quarters beyond that slice's own last dated
    transaction. This makes the rule caller-agnostic: it can be handed a
    slice narrower than the full history (as features_spend.compute does,
    one quarter at a time) without a defensive downstream truncation.
    """
    import config
    df = spend_resolved.merge(vendor_directory[["vendor_id", "segment"]], on="vendor_id", how="left")
    if df.empty:
        return pd.DataFrame(columns=["segment", "quarter", "n_covered", "trailing_mean"])
    df["quarter"] = df["txn_date"].map(_quarter_of_date)
    counts = df.groupby(["segment", "quarter"])["vendor_id"].nunique().reset_index(name="n_covered")
    horizon_idx = max(config.quarter_index(q) for q in counts["quarter"].unique())
    flags = []
    for seg in sorted(counts["segment"].unique()):
        seg_counts = counts[counts["segment"] == seg].set_index("quarter")["n_covered"]
        for q in config.QUARTERS[:horizon_idx + 1]:
            n = int(seg_counts.get(q, 0))
            idx = config.quarter_index(q)
            trailing = [seg_counts.get(config.QUARTERS[i], 0)
                        for i in range(max(0, idx - CLIFF_TRAILING_QUARTERS), idx)]
            trailing_mean = float(np.mean(trailing)) if trailing else 0.0
            if trailing_mean > 0 and n < (1 - CLIFF_DROP_FRACTION) * trailing_mean:
                flags.append({"segment": seg, "quarter": q, "n_covered": n,
                               "trailing_mean": trailing_mean})
    return pd.DataFrame(flags)


# ---------------------------------------------------------------------------
# Spend presence rule
# ---------------------------------------------------------------------------

def spend_presence(spend_resolved: pd.DataFrame, vendor_id: str, quarter: str) -> str:
    """'present' | 'thin' | 'absent' for one vendor-quarter, based on
    trailing-2-quarter transaction count (>= 8 required for presence)."""
    import config
    idx = config.quarter_index(quarter)
    window = [config.QUARTERS[i] for i in range(max(0, idx - 1), idx + 1)]
    df = spend_resolved[spend_resolved["vendor_id"] == vendor_id].copy()
    if df.empty:
        return "absent"
    df["quarter"] = df["txn_date"].map(_quarter_of_date)
    n = int(df[df["quarter"].isin(window)].shape[0])
    if n >= SPEND_PRESENCE_MIN_TXN_TRAILING_2Q:
        return "present"
    if n > 0:
        return "thin"
    return "absent"
