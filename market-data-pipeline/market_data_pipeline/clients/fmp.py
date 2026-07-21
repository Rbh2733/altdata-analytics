"""Financial Modeling Prep client (v3 statement endpoints), key-gated.

Live mode calls three official endpoints per ticker:

    /api/v3/income-statement/{ticker}?period=annual
    /api/v3/balance-sheet-statement/{ticker}?period=annual
    /api/v3/cash-flow-statement/{ticker}?period=annual

and bundles the three arrays into one payload dict, which is also the shape
the committed fixtures use. The key comes from FMP_API_KEY; without it, live
mode refuses loudly rather than degrading quietly. FMP reports values in raw
reported-currency units with fields like revenue, netIncome, epsdiluted,
totalAssets, and operatingCashFlow; the normalizer owns that mapping, and
the README owns the caveat that vendor response shapes drift over time.
"""

import os

import requests

from .base import BaseClient, MissingCredentialError, get_json

FMP_API_BASE = "https://financialmodelingprep.com/api/v3"
ANNUAL_LIMIT = 6  # fiscal years per statement request


class FmpClient(BaseClient):
    source_name = "fmp"

    def __init__(self, fixtures_dir=None, api_key=None):
        super().__init__(fixtures_dir)
        self.api_key = api_key or os.environ.get("FMP_API_KEY") or ""
        self.session = requests.Session()

    def available_live(self) -> bool:
        return bool(self.api_key)

    def _statement(self, kind: str, ticker: str) -> list:
        url = f"{FMP_API_BASE}/{kind}/{ticker.upper()}"
        params = {"period": "annual", "limit": ANNUAL_LIMIT, "apikey": self.api_key}
        data = get_json(self.session, url, params=params)
        return data if isinstance(data, list) else []

    def fetch(self, ticker: str) -> dict:
        if not self.api_key:
            raise MissingCredentialError(
                "FMP_API_KEY is not set; fmp live mode unavailable"
            )
        return {
            "symbol": ticker.upper(),
            "income_statement": self._statement("income-statement", ticker),
            "balance_sheet": self._statement("balance-sheet-statement", ticker),
            "cash_flow": self._statement("cash-flow-statement", ticker),
        }
