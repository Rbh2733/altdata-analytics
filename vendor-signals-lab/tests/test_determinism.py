"""Determinism: two independent full runs (generate + estimate + score)
under the frozen seed produce byte-identical files everywhere, and no
wall-clock call exists anywhere in the four code layers."""

import re
from pathlib import Path

import pytest

import run_all

ROOT = Path(__file__).resolve().parent.parent
_WALLCLOCK_RE = re.compile(r"\b(datetime\.now|time\.time|date\.today|datetime\.today)\s*\(")


def _walk_py(pkgs):
    for pkg in pkgs:
        base = ROOT if pkg == "." else ROOT / pkg
        for f in sorted(base.glob("*.py")):
            yield f


def test_no_wallclock_calls_anywhere():
    offenders = []
    for f in _walk_py(["simulation", "estimation", "evaluation", "sql", "."]):
        if f.name.startswith("test_"):
            continue
        text = f.read_text(encoding="utf-8")
        for m in _WALLCLOCK_RE.finditer(text):
            offenders.append(f"{f}: {m.group(0)}")
    assert offenders == [], f"wall-clock calls found: {offenders}"


@pytest.mark.slow
def test_full_rerun_byte_identical(tmp_path_factory):
    r1 = tmp_path_factory.mktemp("run1")
    r2 = tmp_path_factory.mktemp("run2")
    (r1 / "outputs").mkdir()
    (r2 / "outputs").mkdir()
    run_all.main(root=r1, out_dir=r1 / "outputs", verbose=False)
    run_all.main(root=r2, out_dir=r2 / "outputs", verbose=False)

    files1 = sorted(p.relative_to(r1) for p in r1.rglob("*") if p.is_file())
    files2 = sorted(p.relative_to(r2) for p in r2.rglob("*") if p.is_file())
    assert files1 == files2

    mismatches = []
    for rel in files1:
        b1 = (r1 / rel).read_bytes()
        b2 = (r2 / rel).read_bytes()
        if b1 != b2:
            mismatches.append(str(rel))
    assert mismatches == [], f"non-deterministic output files: {mismatches}"
