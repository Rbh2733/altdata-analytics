"""Temporal fence: reported actuals are usable only for quarters strictly
before the one being estimated, and the future is not merely unused, it
is unnecessary (deleting it changes nothing)."""

import shutil

import config


def test_reported_before_excludes_target_and_future(shop):
    for q in ("2022Q2", "2023Q1", "2024Q3"):
        rep = shop.reported_before(q)
        assert len(rep) > 0
        assert (rep["quarter"] < q).all()
        assert q not in set(rep["quarter"])


def test_m4_unchanged_when_future_reported_rows_deleted(root, tmp_path):
    from estimation import loader, methods

    target = "2024Q2"
    trunc = tmp_path / "trunc"
    for sub in ("panel", "public"):
        shutil.copytree(root / "data" / sub, trunc / "data" / sub)
    rep_path = trunc / "data" / "public" / "reported_actuals.csv"
    lines = rep_path.read_text(encoding="utf-8").splitlines()
    kept = [lines[0]] + [ln for ln in lines[1:] if ln.split(",")[1] < target]
    rep_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    def m4_for(r):
        shop = loader.ShopData(r)
        panel = {"transactions": shop.panel_transactions(),
                 "panelists": shop.panelists()}
        public = {"census_margins": shop.census_margins(),
                  "companies": shop.companies(),
                  "reported_before": shop.reported_before}
        return methods.m4_calibrated(target, panel, public)

    full = m4_for(root).sort_values(["company", "kpi"]).reset_index(drop=True)
    cut = m4_for(trunc).sort_values(["company", "kpi"]).reset_index(drop=True)
    assert (full["estimate"] == cut["estimate"]).all(), \
        "m4 for the target quarter changed when future reported rows vanished"
