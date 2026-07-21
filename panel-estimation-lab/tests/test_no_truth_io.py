"""Runtime leakage guards: the path gate rejects truth reads, and a full
rung-4 estimation run, audited file-by-file, opens nothing under
data/truth/."""

import builtins

import numpy as np
import pytest


def test_loader_rejects_truth_paths(root):
    from estimation import loader
    shop = loader.ShopData(root)
    for rel in ("data/truth/truth_kpis.csv",
                "data/truth/planted_events.csv",
                "data/panel/../truth/truth_kpis.csv"):
        with pytest.raises(PermissionError):
            shop._read(rel)


def test_full_estimation_run_opens_no_truth_files(root, monkeypatch):
    import config
    from estimation import loader, methods

    opened = []
    real_open = builtins.open

    def audited_open(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", audited_open)
    shop = loader.ShopData(root)  # fresh instance: no warm cache
    reported = shop.reported_before(config.QUARTERS[-1])
    _, raw, cor = methods.build_engines(
        shop.panel_transactions(), shop.panelists(), shop.companies(),
        shop.census_margins(), reported)
    cor.m4(np.ones(cor.P))
    monkeypatch.undo()

    assert opened, "the audit hook saw no file opens at all"
    for p in opened:
        norm = p.replace("\\", "/").lower()
        assert "data/truth" not in norm, f"estimation opened a truth file: {p}"
