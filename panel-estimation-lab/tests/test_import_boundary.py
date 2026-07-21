"""The leakage boundary is the package layout; these tests are the fence
posts. estimation/ and sql/ may never import the fenced packages or name
a truth path; evaluation/ sees truth data but never the generator."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCED_FOR_ESTIMATION = {"simulation", "evaluation"}


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module.split(".")[0])
    return names


def _string_constants(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def test_estimation_and_sql_never_import_fenced_packages():
    for pkg in ("estimation", "sql"):
        for py in sorted((ROOT / pkg).glob("*.py")):
            bad = set(_imports(py)) & FENCED_FOR_ESTIMATION
            assert not bad, f"{pkg}/{py.name} imports fenced package(s): {bad}"


def test_estimation_has_no_truth_path_literals():
    for pkg in ("estimation", "sql"):
        for py in sorted((ROOT / pkg).glob("*.py")):
            for s in _string_constants(py):
                low = s.lower().replace("\\", "/")
                assert "data/truth" not in low, f"{pkg}/{py.name}: {s!r}"
                assert "truth_kpis" not in low, f"{pkg}/{py.name}: {s!r}"
                assert "planted_events" not in low, f"{pkg}/{py.name}: {s!r}"


def test_evaluation_never_imports_simulation():
    for py in sorted((ROOT / "evaluation").glob("*.py")):
        assert "simulation" not in _imports(py), f"evaluation/{py.name}"


def test_only_simulation_imports_params():
    for pkg in ("estimation", "evaluation", "sql"):
        for py in sorted((ROOT / pkg).glob("*.py")):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert "params" not in node.module, f"{pkg}/{py.name}"
                    assert not any(a.name == "params" for a in node.names), \
                        f"{pkg}/{py.name}"
