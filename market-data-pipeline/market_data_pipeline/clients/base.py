"""Shared client plumbing: fixture loading and defensive HTTP.

Every client supports two modes. Fixture mode reads a committed JSON payload
from data/fixtures/<source>/<TICKER>.json, shaped like the source's real
response, so the whole pipeline runs with zero keys and zero network. Live
mode makes real HTTP calls against the source's official endpoints, gated on
whatever credential that source requires.
"""

import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = PROJECT_ROOT / "data" / "fixtures"

REQUEST_TIMEOUT = 15
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0  # seconds, doubled on each retry


class MissingCredentialError(RuntimeError):
    """Raised when live mode is requested without the credential it needs."""


def get_json(session, url, params=None):
    """GET with retries and backoff on 429 and 5xx. Raises on total failure.

    Discipline borrowed from production incident experience: rate-limit
    responses are retried with growing waits, hard client errors surface
    immediately, and nothing is swallowed silently.
    """
    last_status = None
    for attempt in range(RETRY_ATTEMPTS):
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 429 or response.status_code >= 500:
            last_status = response.status_code
            wait = RETRY_BACKOFF * (2 ** attempt)
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(
        f"request failed after {RETRY_ATTEMPTS} attempts "
        f"(last status {last_status}): {url}"
    )


class BaseClient:
    """Common fixture-mode behavior. Subclasses implement live fetching."""

    source_name = ""  # overridden

    def __init__(self, fixtures_dir=None):
        self.fixtures_dir = Path(fixtures_dir) if fixtures_dir else FIXTURES_DIR

    def fixture_path(self, ticker: str) -> Path:
        return self.fixtures_dir / self.source_name / f"{ticker.upper()}.json"

    def fixture_tickers(self) -> list:
        """Tickers with a committed fixture for this source, sorted."""
        d = self.fixtures_dir / self.source_name
        if not d.is_dir():
            return []
        return sorted(p.stem for p in d.glob("*.json"))

    def load_fixture(self, ticker: str) -> dict:
        path = self.fixture_path(ticker)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def available_live(self) -> bool:
        """Whether live mode can run (credential present). Overridden."""
        return False

    def fetch(self, ticker: str) -> dict:
        """Live fetch against the real API. Overridden."""
        raise NotImplementedError

    def get_payload(self, ticker: str, live: bool = False) -> dict:
        if live:
            return self.fetch(ticker)
        return self.load_fixture(ticker)
