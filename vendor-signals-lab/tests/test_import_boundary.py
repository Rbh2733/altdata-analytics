"""AST-walked import fence: estimation/ and sql/ never import simulation
or evaluation; evaluation/ never imports simulation; no string literal
under estimation/ or sql/ names a data/truth/ path segment;
simulation.params is imported nowhere outside simulation/."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _py_files(pkg):
    return sorted((ROOT / pkg).glob("*.py"))


def _imported_modules(tree):
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    return mods


def _docstring_nodes(tree):
    """Nodes that are docstrings (first statement of module/function/class
    bodies), which are prose, not path literals, and are exempt from the
    truth-path scan below."""
    nodes = set()
    candidates = [tree] + [n for n in ast.walk(tree)
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    for c in candidates:
        body = getattr(c, "body", [])
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            nodes.add(id(body[0].value))
    return nodes


def _string_literals(tree):
    doc_ids = _docstring_nodes(tree)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in doc_ids:
            out.append(node.value)
    return out


def test_estimation_never_imports_simulation_or_evaluation():
    for f in _py_files("estimation"):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        mods = _imported_modules(tree)
        assert "simulation" not in mods, f"{f} imports simulation"
        assert "evaluation" not in mods, f"{f} imports evaluation"


def test_sql_runner_never_imports_simulation_or_evaluation():
    for f in _py_files("sql"):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        mods = _imported_modules(tree)
        assert "simulation" not in mods, f"{f} imports simulation"
        assert "evaluation" not in mods, f"{f} imports evaluation"


def test_evaluation_never_imports_simulation():
    for f in _py_files("evaluation"):
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        mods = _imported_modules(tree)
        assert "simulation" not in mods, f"{f} imports simulation"


def test_no_truth_path_literals_in_estimation_or_sql():
    for pkg in ("estimation", "sql"):
        for f in _py_files(pkg):
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            for lit in _string_literals(tree):
                assert "truth" not in lit.replace("\\", "/").lower() or "truth_" not in lit, \
                    f"{f} contains a suspicious truth-path-like literal: {lit!r}"
                assert "data/truth" not in lit.replace("\\", "/"), \
                    f"{f} contains a data/truth path literal: {lit!r}"


def test_params_imported_only_by_simulation():
    for pkg in ("estimation", "evaluation", "sql", "."):
        base = ROOT if pkg == "." else ROOT / pkg
        files = base.glob("*.py") if pkg == "." else base.glob("*.py")
        for f in files:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "simulation" \
                        and any(a.name == "params" for a in node.names):
                    raise AssertionError(f"{f} imports simulation.params directly")
                if isinstance(node, ast.Import):
                    for a in node.names:
                        assert a.name != "simulation.params", f"{f} imports simulation.params"


def test_config_holds_no_leakable_parameters():
    text = (ROOT / "config.py").read_text(encoding="utf-8")
    for banned in ("ARCHETYPE_", "HAZARD", "PLANT_"):
        assert banned not in text, f"config.py appears to define world parameter {banned}"
