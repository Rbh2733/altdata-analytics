"""Sole I/O gateway for the estimation layer.

Two guards live here:
- Path guard: every file read resolves the requested path and raises
  PermissionError unless it sits under data/panel/ or data/public/.
- Temporal guard: reported actuals are only reachable through
  reported_before(quarter), which returns strictly earlier quarters.
  There is no accessor for the full reported file.
"""

import builtins
from pathlib import Path

import pandas as pd

import config


class ShopData:
    """All estimation-side file access goes through this class."""

    def __init__(self, root=None):
        self.root = (config.ROOT if root is None else Path(root)).resolve()
        self._allowed = [self.root / "data" / "panel",
                         self.root / "data" / "public"]
        self._cache = {}

    def _read(self, relpath: str) -> pd.DataFrame:
        path = (self.root / relpath).resolve()
        allowed = False
        for a in self._allowed:
            try:
                path.relative_to(a)
                allowed = True
                break
            except ValueError:
                continue
        if not allowed:
            raise PermissionError(
                f"estimation layer may not read {relpath}; only data/panel/ "
                f"and data/public/ are readable from this side of the fence")
        if relpath not in self._cache:
            # builtins.open explicitly, so a monkeypatched open() sees every
            # file this layer touches (test_no_truth_io relies on it).
            with builtins.open(path, "r", encoding="utf-8", newline="") as fh:
                self._cache[relpath] = pd.read_csv(fh, keep_default_na=False,
                                                   na_values=[])
        return self._cache[relpath].copy()

    # ---- panel
    def panel_transactions(self) -> pd.DataFrame:
        df = self._read("data/panel/panel_transactions.csv")
        df["amount"] = df["amount"].astype(float)
        return df

    def panelists(self) -> pd.DataFrame:
        df = self._read("data/panel/panelists.csv")
        df["left_month"] = df["left_month"].replace("", "0").astype(int)
        df["joined_month"] = df["joined_month"].astype(int)
        return df

    # ---- public
    def census_margins(self) -> pd.DataFrame:
        df = self._read("data/public/census_margins.csv")
        df["population"] = df["population"].astype(int)
        return df

    def companies(self) -> pd.DataFrame:
        return self._read("data/public/companies.csv")

    def population_total(self) -> int:
        c = self.census_margins()
        return int(c.loc[c["margin"] == "region", "population"].sum())

    def reported_before(self, quarter: str) -> pd.DataFrame:
        """Reported actuals for quarters strictly earlier than `quarter`.
        Quarter labels are fixed-width (YYYYQn), so lexicographic order is
        chronological order."""
        df = self._read("data/public/reported_actuals.csv")
        df["revenue"] = df["revenue"].astype(float)
        df["actives"] = df["actives"].astype(int)
        return df[df["quarter"] < quarter].reset_index(drop=True)
