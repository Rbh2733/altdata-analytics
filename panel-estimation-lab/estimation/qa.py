"""Panel QA: anomaly detection and feed corrections.

Everything here works from the panel alone. Thresholds are fixed in
advance and data-independent; findings are reported with numbers, not
adjectives. Detected pathologies:
- duplicated feed days (exact-content duplicate rate by date, plus a
  daily-volume z-score against a trailing window),
- recruitment waves (new-panelist share and composition distance),
- supplier outages (an instrument slice going to zero on days where it
  is otherwise never zero),
- merchant descriptor changes (a known merchant's volume collapses while
  a new descriptor appears whose cadence, amount distribution, and
  panelist overlap match the old one).

Corrections applied to the feed: dedupe on flagged days only, alias
resolution for matched descriptor changes. The outage is corrected at
aggregation time (estimation/methods.py) by scaling the affected slice;
the recruitment wave needs no row correction because quarterly
reweighting absorbs composition shifts (QA's job for the wave is
detection and narration only).
"""

import re

import numpy as np
import pandas as pd

import config

# Fixed detection thresholds (data-independent, chosen before any run).
DUP_RATE_FLAG = 0.20          # extra-copy share of a date's rows
VOLUME_Z_FLAG = 4.0           # daily volume z-score vs trailing window
TRAILING_DAYS = 28
WAVE_JOIN_SHARE_FLAG = 0.05   # monthly joins / prior active panel
WAVE_L1_FLAG = 0.06           # L1 distance of cell shares vs trailing 3-month mean
OUTAGE_MIN_DAILY = 30         # slice must normally exceed this to flag zeros
OUTAGE_MIN_RUN = 3            # consecutive zero days to call an outage
COLLAPSE_HISTORY_MONTHS = 6   # months of history before a collapse is judged
COLLAPSE_MIN_MONTHLY = 50     # mean monthly rows for a core to be tracked
COLLAPSE_DROP_RATIO = 0.25    # month volume vs trailing 3-month mean
ALIAS_MIN_VOLUME_RATIO = 0.30  # new core volume vs lost volume
ALIAS_AMOUNT_TOL = 0.25       # relative median-amount gap
ALIAS_OVERLAP_MIN = 0.30      # share of new-core panelists seen on old core
ALIAS_CADENCE_BAND = (0.5, 2.0)  # rows per panelist-month ratio band

CONTENT_COLS = ["panelist_id", "date", "merchant_descriptor", "amount", "instrument"]


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", s.upper())).strip()


def core(s: str) -> str:
    """Normalized descriptor with trailing digit-bearing tokens stripped
    (store numbers, date stamps, per-row suffix noise)."""
    toks = normalize(s).split(" ")
    while len(toks) > 1 and re.search(r"\d", toks[-1]):
        toks.pop()
    return " ".join(toks)


def prepare(txns: pd.DataFrame) -> pd.DataFrame:
    df = txns.copy()
    ym = df["date"].str.slice(0, 7)
    year = ym.str.slice(0, 4).astype(int)
    mon = ym.str.slice(5, 7).astype(int)
    df["month"] = (year - config.START_YEAR) * 12 + mon
    df["quarter"] = [config.quarter_of_month(m) for m in df["month"]]
    df["core"] = df["merchant_descriptor"].map(core)
    return df


# ------------------------------------------------------------- detections

def detect_duplicate_days(df: pd.DataFrame) -> dict:
    per_date = df.groupby("date").size()
    dup_extra = (df.groupby(CONTENT_COLS).size() - 1).clip(lower=0)
    extra_by_date = dup_extra[dup_extra > 0].reset_index().groupby("date")[0].sum() \
        if len(dup_extra[dup_extra > 0]) else pd.Series(dtype=int)
    rate = (extra_by_date / per_date).fillna(0.0) if len(extra_by_date) else pd.Series(dtype=float)
    flagged = sorted(rate[rate > DUP_RATE_FLAG].index.tolist())

    detail = []
    vols = per_date.sort_index()
    for d in flagged:
        i = vols.index.get_loc(d)
        window = vols.iloc[max(0, i - TRAILING_DAYS):i]
        mu, sd = float(window.mean()), float(window.std(ddof=0))
        z = (float(vols.loc[d]) - mu) / sd if sd > 0 else float("inf")
        detail.append({
            "date": d,
            "rows": int(vols.loc[d]),
            "extra_copies": int(extra_by_date.loc[d]),
            "dup_rate": round(float(rate.loc[d]), 4),
            "volume_z": round(z, 1),
        })
    return {"flagged_dates": flagged, "detail": detail}


def detect_recruitment_wave(panelists: pd.DataFrame) -> dict:
    p = panelists
    cells = (p["age_band"].map({b: i for i, b in enumerate(config.AGE_BANDS)}) * 3
             + p["income_band"].map({b: i for i, b in enumerate(config.INCOME_BANDS)}))
    findings = []
    for m in range(2, config.N_MONTHS + 1):
        active_prev = (p["joined_month"] < m) & ((p["left_month"] == 0) | (p["left_month"] > m - 1))
        active_now = (p["joined_month"] <= m) & ((p["left_month"] == 0) | (p["left_month"] > m))
        joins = int((p["joined_month"] == m).sum())
        share = joins / max(int(active_prev.sum()), 1)
        cur = np.bincount(cells[active_now], minlength=12) / max(int(active_now.sum()), 1)
        prev_shares = []
        for k in (1, 2, 3):
            mk = m - k
            if mk < 1:
                continue
            a = (p["joined_month"] <= mk) & ((p["left_month"] == 0) | (p["left_month"] > mk))
            prev_shares.append(np.bincount(cells[a], minlength=12) / max(int(a.sum()), 1))
        l1 = float(np.abs(cur - np.mean(prev_shares, axis=0)).sum()) if prev_shares else 0.0
        if share > WAVE_JOIN_SHARE_FLAG and l1 > WAVE_L1_FLAG:
            findings.append({"month": m, "month_label": config.month_label(m),
                             "new_panelists": joins,
                             "join_share": round(share, 4),
                             "composition_l1": round(l1, 4)})
    return {"findings": findings}


def detect_outages(df: pd.DataFrame) -> dict:
    all_dates = sorted(df["date"].unique())
    windows = []
    for instr in sorted(df["instrument"].unique()):
        counts = df[df["instrument"] == instr].groupby("date").size()
        counts = counts.reindex(all_dates, fill_value=0)
        vals = counts.to_numpy()
        run = []
        for i, d in enumerate(all_dates):
            trailing = vals[max(0, i - TRAILING_DAYS):i]
            normal = len(trailing) >= 7 and float(trailing[trailing > 0].mean()
                                                  if (trailing > 0).any() else 0) > OUTAGE_MIN_DAILY
            if vals[i] == 0 and normal:
                run.append(d)
            else:
                if len(run) >= OUTAGE_MIN_RUN:
                    windows.append({"instrument": instr, "start": run[0],
                                    "end": run[-1], "days": len(run)})
                run = []
        if len(run) >= OUTAGE_MIN_RUN:
            windows.append({"instrument": instr, "start": run[0],
                            "end": run[-1], "days": len(run)})
    return {"windows": windows}


def detect_descriptor_changes(df: pd.DataFrame, companies: pd.DataFrame) -> dict:
    """Volume-collapse plus new-core matching. Returns alias map
    {core -> company} and the evidence for each accepted match."""
    base_core = {core(r["base_descriptor"]): r["company"] for _, r in companies.iterrows()}
    vol = df.groupby(["core", "month"]).size().unstack(fill_value=0) \
        .reindex(columns=range(1, config.N_MONTHS + 1), fill_value=0)
    first_seen = {c: int(np.nonzero(vol.loc[c].to_numpy())[0][0]) + 1 for c in vol.index}

    aliases, evidence = {}, []
    for c in vol.index:
        if c not in base_core:
            continue
        v = vol.loc[c].to_numpy()
        for m in range(COLLAPSE_HISTORY_MONTHS + 1, config.N_MONTHS + 1):
            hist = v[:m - 1]
            if hist.mean() < COLLAPSE_MIN_MONTHLY:
                continue
            trail = v[m - 4:m - 1].mean()
            if trail > 0 and v[m - 1] < COLLAPSE_DROP_RATIO * trail:
                lost = trail - v[m - 1]
                for cand in vol.index:
                    if cand in base_core or cand in aliases:
                        continue
                    # a mid-month change surfaces the new core in the month
                    # before the old core's volume fully collapses
                    if first_seen[cand] not in (m - 1, m):
                        continue
                    cv = vol.loc[cand].to_numpy()
                    if cv[m - 1] < ALIAS_MIN_VOLUME_RATIO * lost:
                        continue
                    old_rows = df[(df["core"] == c) & (df["month"] < first_seen[cand])]
                    new_rows = df[(df["core"] == cand)
                                  & (df["month"].isin([m - 1, m, m + 1]))]
                    med_old = float(old_rows["amount"].median())
                    med_new = float(new_rows["amount"].median())
                    amount_gap = abs(med_new - med_old) / med_old
                    old_pan = set(old_rows[old_rows["month"] >= m - 6]["panelist_id"])
                    new_pan = set(new_rows["panelist_id"])
                    overlap = len(new_pan & old_pan) / max(len(new_pan), 1)
                    cad_old = len(old_rows[old_rows["month"] >= m - 6]) / max(
                        old_rows[old_rows["month"] >= m - 6]
                        .groupby("panelist_id")["month"].nunique().sum(), 1)
                    cad_new = len(new_rows) / max(
                        new_rows.groupby("panelist_id")["month"].nunique().sum(), 1)
                    cad_ratio = cad_new / cad_old if cad_old > 0 else 0.0
                    ok = (amount_gap <= ALIAS_AMOUNT_TOL
                          and overlap >= ALIAS_OVERLAP_MIN
                          and ALIAS_CADENCE_BAND[0] <= cad_ratio <= ALIAS_CADENCE_BAND[1])
                    if ok:
                        aliases[cand] = base_core[c]
                        evidence.append({
                            "old_core": c, "new_core": cand,
                            "company": base_core[c],
                            "collapse_month": config.month_label(m),
                            "old_trailing_monthly_rows": round(float(trail), 1),
                            "collapse_month_rows": int(v[m - 1]),
                            "new_core_rows_first_month": int(cv[m - 1]),
                            "median_amount_old": round(med_old, 2),
                            "median_amount_new": round(med_new, 2),
                            "panelist_overlap": round(overlap, 3),
                            "cadence_ratio": round(float(cad_ratio), 2),
                        })
                break  # judge each known core's first collapse only
    return {"aliases": aliases, "evidence": evidence}


# ------------------------------------------------------------- corrections

def dedupe(df: pd.DataFrame, flagged_dates) -> pd.DataFrame:
    """Keep one copy per exact-content group, on flagged dates only."""
    on = df["date"].isin(flagged_dates)
    kept = df[on].sort_values("txn_id").drop_duplicates(subset=CONTENT_COLS, keep="first")
    return pd.concat([df[~on], kept]).sort_values("txn_id").reset_index(drop=True)


def map_companies(df: pd.DataFrame, companies: pd.DataFrame, aliases=None) -> pd.DataFrame:
    """Attach a company column via normalized base descriptors plus any
    alias map. Unmapped rows keep company '' (out-of-scope spend)."""
    m = {core(r["base_descriptor"]): r["company"] for _, r in companies.iterrows()}
    if aliases:
        m.update(aliases)
    out = df.copy()
    out["company"] = out["core"].map(m).fillna("")
    return out


# ------------------------------------------------------------------ checks

def hard_checks(df: pd.DataFrame, panelists: pd.DataFrame, deduped: pd.DataFrame,
                flagged_dates) -> list:
    """Schema and sanity checks. Each returns (name, passed, note)."""
    checks = []
    checks.append(("schema_columns", list(df.columns[:6]) == [
        "txn_id", "panelist_id", "date", "merchant_descriptor", "amount",
        "instrument"], "expected column order"))
    checks.append(("txn_id_unique", df["txn_id"].is_unique,
                   f"{df['txn_id'].nunique()} unique of {len(df)}"))
    on_flagged = deduped[deduped["date"].isin(flagged_dates)]
    checks.append(("post_dedupe_content_unique_on_flagged_days",
                   not on_flagged.duplicated(subset=CONTENT_COLS).any(),
                   "no exact-content duplicates remain on flagged days"))
    checks.append(("amounts_positive_and_sane",
                   bool((df["amount"] > 0).all() and (df["amount"] < 10_000).all()),
                   f"min {df['amount'].min():.2f}, max {df['amount'].max():.2f}"))
    dates_ok = (df["date"].str.slice(0, 4).astype(int).between(2022, 2024)).all()
    checks.append(("dates_within_calendar", bool(dates_ok), "2022-01 .. 2024-12"))
    checks.append(("panelist_ids_known",
                   bool(df["panelist_id"].isin(set(panelists["panelist_id"])).all()),
                   "every transaction belongs to a known panelist"))
    return checks


def run_qa(txns_df, panelists, companies) -> dict:
    """Full QA pass: detect, correct, and return everything the engines
    and the report writer need. Inputs are the loaded panel and public
    frames (this module does no I/O of its own)."""
    txns = prepare(txns_df)

    dups = detect_duplicate_days(txns)
    wave = detect_recruitment_wave(panelists)
    outages = detect_outages(txns)

    deduped = dedupe(txns, dups["flagged_dates"])
    changes = detect_descriptor_changes(deduped, companies)
    corrected = map_companies(deduped, companies, changes["aliases"])
    raw_mapped = map_companies(txns, companies, aliases=None)

    checks = hard_checks(txns, panelists, deduped, dups["flagged_dates"])
    return {
        "raw": raw_mapped,
        "corrected": corrected,
        "panelists": panelists,
        "companies": companies,
        "duplicates": dups,
        "wave": wave,
        "outages": outages,
        "descriptor_changes": changes,
        "checks": checks,
        "rows_raw": len(txns),
        "rows_deduped": len(deduped),
    }


def write_qa_report(bundle, weight_diags, path):
    """qa_report.md: findings with numbers, all-clear checks, and
    weighting diagnostics. No wall clock, no absolute paths."""
    L = ["# Panel QA Report", "",
         "Generated by the estimation layer from data/panel/ and "
         "data/public/ only. Findings carry numbers, not adjectives.", ""]

    txn_n = bundle["rows_raw"]
    L += ["## Feed overview", "",
          f"- {txn_n} transaction rows, {bundle['panelists'].shape[0]} panelists, "
          f"calendar 2022-01 through 2024-12.",
          f"- {bundle['rows_deduped']} rows after duplicate-day correction "
          f"({txn_n - bundle['rows_deduped']} removed).", ""]

    L += ["## Findings", ""]
    d = bundle["duplicates"]
    if d["detail"]:
        for x in d["detail"]:
            L.append(f"1. Duplicated feed day: {x['date']} carries {x['rows']} rows, "
                     f"{x['extra_copies']} of them exact-content duplicate copies "
                     f"(duplicate rate {x['dup_rate']:.1%}); daily volume z-score "
                     f"{x['volume_z']} against the trailing {TRAILING_DAYS}-day mean. "
                     f"Correction: keep one copy per content group on this date only.")
    else:
        L.append("1. Duplicated feed days: none flagged.")
    w = bundle["wave"]["findings"]
    if w:
        for x in w:
            L.append(f"2. Recruitment wave: {x['new_panelists']} panelists joined in "
                     f"{x['month_label']} ({x['join_share']:.1%} of the prior active "
                     f"panel); age-income composition moved {x['composition_l1']:.3f} "
                     f"in L1 distance versus the trailing 3-month mean. No row "
                     f"correction; quarterly reweighting absorbs the shift.")
    else:
        L.append("2. Recruitment waves: none flagged.")
    o = bundle["outages"]["windows"]
    if o:
        for x in o:
            L.append(f"3. Supplier outage: instrument {x['instrument']} delivered "
                     f"zero rows for {x['days']} consecutive days, {x['start']} "
                     f"through {x['end']}, on a slice otherwise never at zero. "
                     f"Correction: scale the affected window's revenue using each "
                     f"company's {x['instrument']} share estimated from the prior "
                     f"eight weeks (assumes locally stable instrument mix).")
    else:
        L.append("3. Supplier outages: none flagged.")
    ev = bundle["descriptor_changes"]["evidence"]
    if ev:
        for x in ev:
            L.append(f"4. Descriptor change: '{x['old_core']}' collapsed in "
                     f"{x['collapse_month']} ({x['old_trailing_monthly_rows']} rows "
                     f"per month trailing, {x['collapse_month_rows']} that month) "
                     f"while new descriptor core '{x['new_core']}' appeared with "
                     f"{x['new_core_rows_first_month']} rows. Match evidence: "
                     f"median amount {x['median_amount_old']:.2f} vs "
                     f"{x['median_amount_new']:.2f}, panelist overlap "
                     f"{x['panelist_overlap']:.1%}, monthly cadence ratio "
                     f"{x['cadence_ratio']}. Mapped to {x['company']}.")
    else:
        L.append("4. Descriptor changes: none flagged.")
    L.append("")

    L += ["## Checks", "", "| check | status | note |", "|---|---|---|"]
    for name, ok, note in bundle["checks"]:
        L.append(f"| {name} | {'pass' if ok else 'FAIL'} | {note} |")
    L.append("")

    L += ["## Weighting diagnostics (corrected engine)", "",
          "| quarter | active panelists | rake iterations | raking groups "
          "| trimmed weights | weight sum |", "|---|---|---|---|---|---|"]
    for d2 in weight_diags:
        L.append(f"| {d2['quarter']} | {d2['active_panelists']} | "
                 f"{d2['iterations']} | {d2['collapsed_groups']}x4 | "
                 f"{d2['trimmed']} ({d2['trimmed_frac']:.2%}) | "
                 f"{d2['weight_sum']:.0f} |")
    L.append("")
    path.write_text("\n".join(L), encoding="utf-8", newline="\n")
