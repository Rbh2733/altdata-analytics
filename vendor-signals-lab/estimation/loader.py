"""Sole I/O gateway for the estimation layer.

Two guards live here:
- Path guard: every file read resolves the requested path and raises
  PermissionError unless it sits under data/exhaust/ or data/public/.
- Temporal guard: as_of(quarter) returns exhaust dated inside or before
  that quarter, with the spend publication lag applied. There is no
  accessor for data/truth/ anywhere in this module.
"""

import builtins
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import config


class ShopData:
    """All estimation-side file access goes through this class."""

    def __init__(self, root=None):
        self.root = (config.ROOT if root is None else Path(root)).resolve()
        self._allowed = [self.root / "data" / "exhaust",
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
                f"estimation layer may not read {relpath}; only data/exhaust/ "
                f"and data/public/ are readable from this side of the fence")
        if relpath not in self._cache:
            # builtins.open explicitly, so a monkeypatched open() sees every
            # file this layer touches (test_no_truth_io relies on it).
            with builtins.open(path, "r", encoding="utf-8", newline="") as fh:
                self._cache[relpath] = pd.read_csv(fh, keep_default_na=False,
                                                    na_values=[])
        return self._cache[relpath].copy()

    # ---- exhaust
    def job_postings(self) -> pd.DataFrame:
        return self._read("data/exhaust/job_postings.csv")

    def jobs_tracked_vendors(self) -> pd.DataFrame:
        df = self._read("data/exhaust/jobs_tracked_vendors.csv")
        df["tracked"] = df["tracked"].astype(int)
        return df

    def web_traffic(self) -> pd.DataFrame:
        df = self._read("data/exhaust/web_traffic.csv")
        df["estimated_visits"] = df["estimated_visits"].astype(float)
        return df

    def web_covered_vendors(self) -> pd.DataFrame:
        df = self._read("data/exhaust/web_covered_vendors.csv")
        df["covered"] = df["covered"].astype(int)
        return df

    def spend_panel(self) -> pd.DataFrame:
        df = self._read("data/exhaust/spend_panel.csv")
        df["amount"] = df["amount"].astype(float)
        return df

    # ---- public
    def vendor_directory(self) -> pd.DataFrame:
        return self._read("data/public/vendor_directory.csv")

    def descriptor_map(self) -> pd.DataFrame:
        return self._read("data/public/descriptor_map.csv")

    def tagger_validation_set(self) -> pd.DataFrame:
        return self._read("data/public/tagger_validation_set.csv")

    # ---- temporal guard
    def as_of(self, quarter: str) -> SimpleNamespace:
        """Exhaust dated inside or before `quarter`. Spend carries an
        additional one-month publication lag: a transaction is included
        only if its publish date (the 1st of the following month) falls
        on or before quarter's last calendar day."""
        q_end = config.quarter_end_date(quarter)

        jobs = self.job_postings()
        jobs = jobs[jobs["posted_date"] <= q_end].reset_index(drop=True)

        web = self.web_traffic()
        web_end_label = config.month_label(*config.quarter_months(quarter)[-1])
        web = web[web["month"] <= web_end_label].reset_index(drop=True)

        spend = self.spend_panel()
        pub = spend["txn_date"].str.slice(0, 7).apply(
            lambda ym: config.spend_publish_date(int(ym[:4]), int(ym[5:7])))
        spend = spend[pub <= q_end].reset_index(drop=True)

        return SimpleNamespace(quarter=quarter, jobs=jobs, web=web, spend=spend)
