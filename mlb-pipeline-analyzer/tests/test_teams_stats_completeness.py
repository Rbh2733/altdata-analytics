"""Regression test for the Rookie-level team-stats truncation bug, found
2026-08-01. The MLB Stats API silently caps /v1/teams/stats at 50 rows
with no limit param, and Rookie ball genuinely fields 81-90 teams, so a
naive fetch built the hitting and pitching baselines from two different,
non-overlapping team populations (22-32 of 50 overlapping, confirmed
against live team IDs), corrupting every Rookie pitcher's readiness score
by a fixed amount regardless of his own performance.

No network calls: get_json is monkeypatched to return canned API-shaped
payloads, so this stays offline like the rest of the suite.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion import api


def _payload(total_splits, n_returned):
    return {"stats": [{
        "totalSplits": total_splits,
        "splits": [{"team": {"id": i}, "stat": {}} for i in range(n_returned)],
    }]}


def test_teams_stats_requests_a_wide_limit(monkeypatch):
    seen = {}

    def fake_get_json(path, params=None):
        seen["params"] = params
        return _payload(30, 30)

    monkeypatch.setattr(api, "get_json", fake_get_json)
    api.teams_stats(14, 2023, "hitting")
    assert seen["params"]["limit"] == 200


def test_teams_stats_returns_all_rows_when_under_the_limit(monkeypatch):
    monkeypatch.setattr(api, "get_json", lambda path, params=None: _payload(84, 84))
    rows = api.teams_stats(16, 2019, "hitting")
    assert len(rows) == 84


def test_teams_stats_fails_loud_never_silent_on_truncation(monkeypatch):
    """The exact shape of the real bug: the API says there are more teams
    than it actually returned. Must raise, never silently proceed with a
    partial, non-representative team population."""
    monkeypatch.setattr(api, "get_json", lambda path, params=None: _payload(90, 50))
    with pytest.raises(RuntimeError, match="90 teams but returned only 50"):
        api.teams_stats(16, 2015, "pitching")


def test_teams_stats_empty_response_returns_empty_list(monkeypatch):
    monkeypatch.setattr(api, "get_json", lambda path, params=None: {"stats": []})
    assert api.teams_stats(15, 2027, "hitting") == []
