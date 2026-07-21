"""The offline path must produce byte-identical outputs on every run,
and the committed outputs must match a fresh run exactly."""

import hashlib
from pathlib import Path

from market_data_pipeline.pipeline import OUTPUT_FILES, run

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _digests(out_dir):
    return {
        name: hashlib.sha256((Path(out_dir) / name).read_bytes()).hexdigest()
        for name in OUTPUT_FILES
    }


def test_offline_run_is_byte_identical(tmp_path):
    a = tmp_path / "run_a"
    b = tmp_path / "run_b"
    run(a, echo_sql=False)
    run(b, echo_sql=False)
    assert _digests(a) == _digests(b)


def test_committed_outputs_match_fresh_run(tmp_path):
    fresh = tmp_path / "fresh"
    run(fresh, echo_sql=False)
    committed = PROJECT_ROOT / "outputs"
    assert _digests(fresh) == _digests(committed)
