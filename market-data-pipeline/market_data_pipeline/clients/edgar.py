"""SEC EDGAR client: official companyfacts endpoint, polite by construction.

Live mode hits https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json,
which is free and keyless, but the SEC requires a descriptive User-Agent
identifying the caller, and caps automated traffic at 10 requests per
second. This client enforces both: the User-Agent comes from the
SEC_USER_AGENT environment variable (a placeholder default keeps offline
work running, with a warning if it leaks into live use), and every request
passes a minimum-interval rate limiter set below the SEC's cap.

Ticker-to-CIK resolution uses the SEC's own company_tickers.json mapping,
fetched once per client instance and cached.
"""

import os
import time

import requests

from .base import BaseClient, get_json

SEC_API_BASE = "https://data.sec.gov"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
PLACEHOLDER_USER_AGENT = "market-data-pipeline demo (contact@example.com)"
MIN_REQUEST_INTERVAL = 0.12  # seconds; comfortably under 10 req/s


class EdgarClient(BaseClient):
    source_name = "edgar"

    def __init__(self, fixtures_dir=None, user_agent=None):
        super().__init__(fixtures_dir)
        self.user_agent = (
            user_agent
            or os.environ.get("SEC_USER_AGENT")
            or PLACEHOLDER_USER_AGENT
        )
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        })
        self._cik_map = None
        self._last_request_time = 0.0

    def available_live(self) -> bool:
        # EDGAR is keyless; live mode always works, though a real contact
        # address in SEC_USER_AGENT is expected by the SEC's fair-access policy.
        return True

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get(self, url):
        self._rate_limit()
        return get_json(self.session, url)

    def ticker_to_cik(self, ticker: str) -> str:
        """Resolve a ticker to a zero-padded 10-digit CIK via the SEC mapping."""
        if self._cik_map is None:
            data = self._get(COMPANY_TICKERS_URL)
            self._cik_map = {
                row["ticker"].upper(): str(row["cik_str"]).zfill(10)
                for row in data.values()
            }
        ticker = ticker.upper()
        if ticker not in self._cik_map:
            raise KeyError(f"ticker {ticker} not found in SEC company_tickers.json")
        return self._cik_map[ticker]

    def fetch(self, ticker: str) -> dict:
        if self.user_agent == PLACEHOLDER_USER_AGENT:
            print(
                "WARNING: SEC_USER_AGENT is not set; using a placeholder. "
                "Set a real contact address before sustained live use."
            )
        cik = self.ticker_to_cik(ticker)
        return self._get(f"{SEC_API_BASE}/api/xbrl/companyfacts/CIK{cik}.json")
