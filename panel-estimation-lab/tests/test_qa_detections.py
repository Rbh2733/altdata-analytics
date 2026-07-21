"""Every planted pathology is detected, dated, and sized by the QA layer,
and every correction does what it claims and nothing more. These tests
sit evaluation-side: they may read data/truth/planted_events.csv."""

import numpy as np
import pandas as pd


def _event(events, name):
    return events[events["pathology"] == name].iloc[0]


def test_duplicate_day_detected_and_dated(engines, events):
    bundle, _, _ = engines
    ev = _event(events, "duplicate_feed_day")
    detail = bundle["duplicates"]["detail"]
    assert len(detail) == 1
    d = detail[0]
    assert d["date"] == ev["start_date"]
    assert d["extra_copies"] == int(ev["value"])
    assert d["volume_z"] > 10


def test_dedupe_removes_only_planted_duplicates(engines, events):
    bundle, _, _ = engines
    ev = _event(events, "duplicate_feed_day")
    removed = bundle["rows_raw"] - bundle["rows_deduped"]
    assert removed == int(ev["value"])


def test_dedupe_is_idempotent(engines):
    from estimation import qa
    bundle, _, _ = engines
    flagged = bundle["duplicates"]["flagged_dates"]
    once = bundle["corrected"]
    twice = qa.dedupe(once, flagged)
    assert len(twice) == len(once)


def test_recruitment_wave_flagged_in_2023q2(engines, events):
    bundle, _, _ = engines
    ev = _event(events, "recruitment_wave")
    findings = bundle["wave"]["findings"]
    assert len(findings) == 1
    f = findings[0]
    assert f["month_label"] == ev["start_date"][:7]
    assert f["new_panelists"] == int(ev["value"])
    assert f["composition_l1"] > 0.06


def test_outage_detected_with_slice_and_window(engines, events):
    bundle, _, _ = engines
    ev = _event(events, "supplier_outage")
    windows = bundle["outages"]["windows"]
    assert len(windows) == 1
    w = windows[0]
    assert w["instrument"] == "card_B"
    assert w["start"] == ev["start_date"]
    assert w["end"] == ev["end_date"]
    assert w["days"] == 12


def test_outage_correction_self_test(engines):
    """Hold out a clean 12-day window, delete its card_B rows, reconstruct
    with the prior-eight-week share method, and compare to what was
    actually observed."""
    bundle, _, _ = engines
    txns = bundle["corrected"]
    txns = txns[txns["company"] != ""]
    start, end = "2023-05-08", "2023-05-19"
    pre_lo = "2023-03-13"  # eight weeks before the held-out window

    win = txns[(txns["date"] >= start) & (txns["date"] <= end)]
    pre = txns[(txns["date"] >= pre_lo) & (txns["date"] < start)]
    actual = win.groupby("company")["amount"].sum()
    observed = win[win["instrument"] != "card_B"].groupby("company")["amount"].sum()
    share = (pre[pre["instrument"] == "card_B"].groupby("company")["amount"].sum()
             / pre.groupby("company")["amount"].sum()).clip(0, 0.8)
    recon = observed / (1.0 - share)

    joined = pd.concat([actual, recon], axis=1, keys=["actual", "recon"]).dropna()
    big = joined[joined["actual"] > 50_000]
    rel = (big["recon"] - big["actual"]).abs() / big["actual"]
    assert (rel < 0.20).all(), f"per-company reconstruction off: {rel.to_dict()}"
    total_rel = abs(joined["recon"].sum() - joined["actual"].sum()) / joined["actual"].sum()
    assert total_rel < 0.08, f"total reconstruction off by {total_rel:.1%}"


def test_descriptor_change_matched_with_evidence(engines, events):
    bundle, _, _ = engines
    ev = _event(events, "descriptor_change")
    evidence = bundle["descriptor_changes"]["evidence"]
    assert len(evidence) == 1
    e = evidence[0]
    assert e["company"] == ev["target"]
    assert e["old_core"] == "BRAMBLEBOX"
    assert e["panelist_overlap"] > 0.3
    assert abs(e["median_amount_new"] - e["median_amount_old"]) < 0.01


def test_descriptor_bridge_recovers_bramblebox(estimates):
    est = estimates[(estimates["kpi"] == "revenue")
                    & (estimates["company"] == "Bramblebox")]

    def val(method, quarter):
        return float(est[(est["method"] == method)
                         & (est["quarter"] == quarter)]["estimate"].iloc[0])

    # uncorrected mapping loses essentially all volume in the first full
    # post-change quarter; the bridge restores continuity
    assert val("m2", "2024Q3") < 0.10 * val("m3", "2024Q3")
    ratio = val("m3", "2024Q3") / val("m3", "2024Q1")
    assert 0.6 < ratio < 2.5, f"bridged quarter not continuous: {ratio:.2f}"


def test_descriptor_map_does_not_over_merge_control(engines):
    bundle, _, _ = engines
    aliases = bundle["descriptor_changes"]["aliases"]
    assert "SNACKPOST MARKET" not in aliases
    corrected = bundle["corrected"]
    snack = corrected[corrected["core"] == "SNACKPOST MARKET"]
    assert len(snack) > 0
    assert (snack["company"] == "").all(), "control descriptor was merged"
