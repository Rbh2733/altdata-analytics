"""Runtime path guard on estimation/loader.py: rejects reads outside
data/exhaust/ and data/public/, including `..` traversal, and a
monkeypatched builtins.open during a full estimation run opens nothing
under data/truth/."""

import builtins
from pathlib import Path

import pytest

from estimation.loader import ShopData


def test_rejects_truth_path(built):
    sd = ShopData(built["root"])
    with pytest.raises(PermissionError):
        sd._read("data/truth/inflections.csv")


def test_rejects_dotdot_traversal(built):
    sd = ShopData(built["root"])
    with pytest.raises(PermissionError):
        sd._read("data/exhaust/../truth/inflections.csv")


def test_rejects_absolute_escape(built):
    sd = ShopData(built["root"])
    with pytest.raises(PermissionError):
        sd._read("../outside.csv")


def test_open_audit_full_estimation_run(built, monkeypatch):
    opened = []
    real_open = builtins.open

    def spy_open(file, *a, **kw):
        opened.append(str(file))
        return real_open(file, *a, **kw)

    monkeypatch.setattr(builtins, "open", spy_open)

    from estimation.loader import ShopData
    from estimation import coverage
    sd = ShopData(built["root"])
    coverage.build(sd, "2023Q4")  # small as_of window keeps this fast

    truth_dir = str((built["root"] / "data" / "truth").resolve())
    bad = [p for p in opened if p.startswith(truth_dir)]
    assert bad == [], f"estimation opened truth path(s): {bad}"
