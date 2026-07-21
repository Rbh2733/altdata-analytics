"""Polygon.io client (experimental financials endpoint), key-gated.

Live mode calls the official endpoint:

    https://api.polygon.io/vX/reference/financials?ticker=...&timeframe=annual

The response nests each statement under results[].financials, with every
line item carrying an explicit value and unit; the normalizer walks that
structure. The key comes from POLYGON_API_KEY, and live mode refuses loudly
without it. Polygon labels this endpoint experimental (the vX prefix), which
is exactly the kind of shape-drift risk the README's limitations section
names.
"""

import os

import requests

from .base import BaseClient, MissingCredentialError, get_json

POLYGON_API_BASE = "https://api.polygon.io"
ANNUAL_LIMIT = 6


class PolygonClient(BaseClient):
    source_name = "polygon"

    def __init__(self, fixtures_dir=None, api_key=None):
        super().__init__(fixtures_dir)
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY") or ""
        self.session = requests.Session()

    def available_live(self) -> bool:
        return bool(self.api_key)

    def fetch(self, ticker: str) -> dict:
        if not self.api_key:
            raise MissingCredentialError(
                "POLYGON_API_KEY is not set; polygon live mode unavailable"
            )
        url = f"{POLYGON_API_BASE}/vX/reference/financials"
        params = {
            "ticker": ticker.upper(),
            "timeframe": "annual",
            "limit": ANNUAL_LIMIT,
            "apiKey": self.api_key,
        }
        return get_json(self.session, url, params=params)
