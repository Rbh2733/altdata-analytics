"""Mock tagger is deterministic and matches the committed accuracy;
every row is tagged exactly once; the live adapter fails loudly without
a key, and fails loudly if a batch drops a row."""

import json
import os
import re

import pandas as pd
import pytest

from estimation import tagger_mock


def test_mock_tagger_deterministic():
    titles = ["Sales Engineer", "Customer Success Engineer", "Backend Engineer"] * 5
    a = tagger_mock.tag_titles(titles)
    b = tagger_mock.tag_titles(titles)
    assert a == b


def test_mock_tagger_every_row_tagged_once():
    titles = [f"Title {i}" for i in range(37)]
    out = tagger_mock.tag_titles(titles)
    assert len(out) == len(titles)
    assert all(f in tagger_mock.FUNCTIONS for f in out)


def test_mock_tagger_accuracy_matches_committed(built):
    with open(built["out"] / "tagger_report.md", encoding="utf-8") as fh:
        text = fh.read()
    val = pd.read_csv(built["root"] / "data" / "public" / "tagger_validation_set.csv")
    preds = tagger_mock.tag_titles(val["title"])
    acc = (pd.Series(preds) == val["true_function"]).mean()
    m = re.search(r"Accuracy on (\d+) hand-labeled titles: ([\d.]+)%", text)
    assert m is not None
    assert int(m.group(1)) == len(val)
    reported = float(m.group(2))
    assert abs(100 * acc - reported) < 0.05
    assert acc >= 0.90


def test_live_adapter_fails_loudly_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from estimation import tagger_claude
    with pytest.raises(RuntimeError):
        tagger_claude.tag_titles(["Software Engineer"])


def test_live_adapter_fails_loudly_on_dropped_row(monkeypatch):
    from estimation import tagger_claude

    class FakeContentBlock:
        def __init__(self, text):
            self.text = text

    class FakeResponse:
        def __init__(self, text):
            self.content = [FakeContentBlock(text)]

    class FakeMessages:
        def create(self, **kwargs):
            # drop row id 1 from the response on purpose
            return FakeResponse(json.dumps([{"id": 0, "function": "engineering"}]))

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr(tagger_claude, "_get_client", lambda: FakeClient())
    with pytest.raises(RuntimeError):
        tagger_claude.tag_titles(["Software Engineer", "Account Executive"])
