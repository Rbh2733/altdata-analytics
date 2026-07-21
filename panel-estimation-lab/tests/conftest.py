"""Shared fixtures. Committed data is the fast path; the two session-
scoped regeneration fixtures are the only expensive work in the suite."""

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def shop():
    from estimation import loader
    return loader.ShopData(ROOT)


@pytest.fixture(scope="session")
def engines(shop):
    """(bundle, raw_engine, cor_engine) built once from committed data."""
    import config
    from estimation import methods
    reported = shop.reported_before(config.QUARTERS[-1])
    return methods.build_engines(
        shop.panel_transactions(), shop.panelists(), shop.companies(),
        shop.census_margins(), reported)


@pytest.fixture(scope="session")
def truth():
    return pd.read_csv(ROOT / "data" / "truth" / "truth_kpis.csv")


@pytest.fixture(scope="session")
def events():
    return pd.read_csv(ROOT / "data" / "truth" / "planted_events.csv")


@pytest.fixture(scope="session")
def estimates():
    return pd.read_csv(ROOT / "outputs" / "estimates.csv")


@pytest.fixture(scope="session")
def metrics():
    import json
    return json.loads((ROOT / "outputs" / "metrics.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def regen_data_root(tmp_path_factory):
    """Regenerate the world into tmp (first of the at-most-two regens)."""
    import run_all
    out = tmp_path_factory.mktemp("regen")
    run_all.run_generation(root=out, verbose=False)
    return out


@pytest.fixture(scope="session")
def regen_out_dir(tmp_path_factory):
    """Re-run estimation plus evaluation from committed data into tmp
    (the second regen; full bootstrap included)."""
    import run_all
    out = tmp_path_factory.mktemp("outs")
    b = run_all.run_estimation(root=ROOT, out_dir=out, verbose=False)
    run_all.run_evaluation(b, root=ROOT, out_dir=out, verbose=False)
    return out
