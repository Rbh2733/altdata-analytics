"""The methods ladder.

Four estimators share one interface: estimate(quarter, panel, public)
returns a DataFrame[company, kpi, estimate] for that quarter.

- m1_naive: raw-descriptor totals scaled by population over INITIAL
  panel size. The static denominator is a deliberate, classic mistake:
  attrition drags it down slowly and the recruitment wave jumps it.
- m2_weighted: quarterly raking of the active panel to the published
  census margins. Fixes composition (and, silently, the denominator).
- m3_weighted_qa: m2 plus QA corrections (dedupe, descriptor aliasing,
  outage slice reconstruction) and subscription spell logic with a
  one-month gap tolerance.
- m4_calibrated: m3 plus ratio calibration to previously reported
  quarters (estimation/calibrate.py).

Internally everything runs through Engine, which precomputes panelist-
level aggregates once and evaluates any method under any panelist
multiplicity vector; the bootstrap reuses the same code path, so point
estimates and replicates can never diverge.
"""

import numpy as np
import pandas as pd

import config
from estimation import calibrate, qa, weights

SUB_CATEGORIES = {"video_streaming", "music_streaming", "meal_kits",
                  "retail_membership"}


def gap_fill(pres):
    """One-month gap tolerance on monthly presence [..., months]: a single
    missing month between two observed months does not end a spell; two
    consecutive missing months do. Edges are never filled."""
    prev = np.zeros_like(pres)
    prev[..., 1:] = pres[..., :-1]
    nxt = np.zeros_like(pres)
    nxt[..., :-1] = pres[..., 1:]
    return pres | (prev & nxt)

KPIS = config.KPIS
NQ = 12
NM = config.N_MONTHS


class Engine:
    def __init__(self, bundle, census, reported, corrected):
        """bundle: qa.run_qa output. census: census_margins frame.
        reported: reported actuals for quarters before 2024Q4 (the last
        quarter's own report is never needed: calibration for quarter q
        looks only at j < q, and 2024Q4 is the final quarter)."""
        self.corrected = corrected
        txns = bundle["corrected" if corrected else "raw"]
        panelists = bundle["panelists"].sort_values("panelist_id").reset_index(drop=True)
        self.companies = bundle["companies"]["company"].tolist()
        cats = dict(zip(bundle["companies"]["company"], bundle["companies"]["category"]))
        self.sub_idx = [i for i, c in enumerate(self.companies)
                        if cats[c] in SUB_CATEGORIES]
        self.ecom_idx = [i for i, c in enumerate(self.companies)
                         if cats[c] not in SUB_CATEGORIES]
        C = len(self.companies)
        self.C = C

        # ---- panelist frame
        P = len(panelists)
        self.P = P
        pid_to_row = {pid: i for i, pid in enumerate(panelists["panelist_id"])}
        self.ai = (panelists["age_band"].map(
            {b: i for i, b in enumerate(config.AGE_BANDS)}) * 3
            + panelists["income_band"].map(
                {b: i for i, b in enumerate(config.INCOME_BANDS)})).to_numpy()
        self.reg = panelists["region"].map(
            {r: i for i, r in enumerate(config.REGIONS)}).to_numpy()
        joined = panelists["joined_month"].to_numpy()
        left = panelists["left_month"].to_numpy()
        self.joined = joined

        # ---- census margins
        ai_rows = census[census["margin"] == "age_income"]
        m = np.zeros(12)
        for _, r in ai_rows.iterrows():
            a = config.AGE_BANDS.index(r["age_band"])
            i = config.INCOME_BANDS.index(r["income_band"])
            m[a * 3 + i] = r["population"]
        self.ai_margin = m
        reg_rows = census[census["margin"] == "region"]
        self.reg_margin = np.array([
            float(reg_rows.loc[reg_rows["region"] == r, "population"].iloc[0])
            for r in config.REGIONS])
        self.n_pop = float(self.reg_margin.sum())

        # ---- transaction-level aggregates
        prow = txns["panelist_id"].map(pid_to_row).to_numpy()
        cidx = txns["company"].map(
            {c: i for i, c in enumerate(self.companies)}).fillna(-1).astype(int).to_numpy()
        month = txns["month"].to_numpy()
        qidx = (month - 1) // 3
        amount = txns["amount"].to_numpy()

        self.rev = np.zeros((P, C, NQ))
        mapped = cidx >= 0
        np.add.at(self.rev, (prow[mapped], cidx[mapped], qidx[mapped]), amount[mapped])

        pres = np.zeros((P, C, NM), dtype=bool)
        pres[prow[mapped], cidx[mapped], month[mapped] - 1] = True
        self.pres = pres

        present_any = np.zeros((P, NQ), dtype=bool)
        present_any[prow, qidx] = True
        month_ends = np.array([3 * (q + 1) for q in range(NQ)])
        self.in_panel_end = ((joined[:, None] <= month_ends[None, :])
                             & ((left[:, None] == 0) | (left[:, None] > month_ends[None, :])))
        act = present_any.copy()
        act[:, 1:] |= present_any[:, :-1]
        self.active_q = act & self.in_panel_end

        # ---- naive (m1/m2) definitions
        self.last_charge = pres[:, :, 2::3]                      # [P, C, 12]
        first_month = np.where(pres.any(axis=2), pres.argmax(axis=2), -1)  # 0-based
        self.first_adds = np.zeros((P, C, NQ))
        ok = first_month >= 1                                    # month 1 is censored
        pp, cc = np.nonzero(ok)
        np.add.at(self.first_adds, (pp, cc, first_month[ok] // 3), 1.0)

        # ---- trailing-12-month e-commerce actives
        self.trail = np.zeros((P, C, NQ), dtype=bool)
        for q in range(NQ):
            lo = max(0, 3 * (q + 1) - 12)
            self.trail[:, :, q] = pres[:, :, lo:3 * (q + 1)].any(axis=2)

        # ---- spell logic (used by the corrected engine only)
        filled = gap_fill(pres)
        f_prev = np.zeros_like(filled)
        f_prev[:, :, 1:] = filled[:, :, :-1]
        f_next = np.zeros_like(filled)
        f_next[:, :, :-1] = filled[:, :, 1:]
        self.spell_active = filled[:, :, 2::3]                   # active at quarter end
        starts = filled & ~f_prev
        ends = filled & ~f_next
        self.spell_adds = np.zeros((P, C, NQ))
        pp, cc, mm = np.nonzero(starts)
        keep = (mm >= 1) & (joined[pp] <= mm)                    # censor month 1 and join months
        np.add.at(self.spell_adds, (pp[keep], cc[keep], mm[keep] // 3), 1.0)
        self.spell_ends = np.zeros((P, C, NQ))
        pp, cc, mm = np.nonzero(ends)
        e1 = mm + 1                                              # 1-based last paid month
        keep = (e1 < NM) & ((left[pp] == 0) | (left[pp] > e1 + 2))
        np.add.at(self.spell_ends, (pp[keep], cc[keep], mm[keep] // 3), 1.0)

        # ---- outage windows (corrected engine): observed window revenue
        # and pre-window slice shares for reconstruction
        self.outage = []
        if corrected:
            for w in bundle["outages"]["windows"]:
                q = (int(w["start"][5:7]) + (int(w["start"][0:4])
                                             - config.START_YEAR) * 12 - 1) // 3
                in_win = (txns["date"] >= w["start"]) & (txns["date"] <= w["end"])
                start_m = int(w["start"][5:7]) + (int(w["start"][0:4])
                                                  - config.START_YEAR) * 12
                pre_lo = config.date_str(max(1, start_m - 2), 1)
                pre = (txns["date"] >= pre_lo) & (txns["date"] < w["start"])
                rev_win = np.zeros((P, C))
                sel = in_win.to_numpy() & mapped
                np.add.at(rev_win, (prow[sel], cidx[sel]), amount[sel])
                rev_pre_all = np.zeros((P, C))
                sel = pre.to_numpy() & mapped
                np.add.at(rev_pre_all, (prow[sel], cidx[sel]), amount[sel])
                rev_pre_slice = np.zeros((P, C))
                sel = (pre & (txns["instrument"] == w["instrument"])).to_numpy() & mapped
                np.add.at(rev_pre_slice, (prow[sel], cidx[sel]), amount[sel])
                self.outage.append({"q": q, "rev_win": rev_win,
                                    "rev_pre_all": rev_pre_all,
                                    "rev_pre_slice": rev_pre_slice})

        # ---- reported actuals (through the temporal fence), for m4
        self.rep_rev = np.full((C, NQ), np.nan)
        self.rep_act = np.full((C, NQ), np.nan)
        for _, r in reported.iterrows():
            ci = self.companies.index(r["company"])
            qi = config.quarter_index(r["quarter"])
            self.rep_rev[ci, qi] = r["revenue"]
            self.rep_act[ci, qi] = r["actives"]

        self._weight_cache = {}

    # ------------------------------------------------------------ weights

    def raked_weights(self, mult):
        """Per-quarter raked weight matrix [P, 12] plus diagnostics."""
        key = mult.tobytes()
        if key in self._weight_cache:
            return self._weight_cache[key]
        W = np.zeros((self.P, NQ))
        diags = []
        for q in range(NQ):
            w, d = weights.rake_weights(self.ai, self.reg,
                                        mult * self.active_q[:, q],
                                        self.ai_margin, self.reg_margin)
            W[:, q] = w
            d["quarter"] = config.QUARTERS[q]
            diags.append(d)
        if len(self._weight_cache) < 2:  # cache point-estimate weights only
            self._weight_cache[key] = (W, diags)
        return W, diags

    # ------------------------------------------------------------ methods

    def _core(self, W, use_spells, outage_fix):
        """KPI grids [C, 12] under weight matrix W (already includes any
        multiplicity)."""
        rev = np.einsum("pq,pcq->cq", W, self.rev)
        if outage_fix:
            for o in self.outage:
                q = o["q"]
                wq = W[:, q]
                pre_all = wq @ o["rev_pre_all"]
                pre_slice = wq @ o["rev_pre_slice"]
                with np.errstate(divide="ignore", invalid="ignore"):
                    share = np.where(pre_all > 0, pre_slice / pre_all, 0.0)
                share = np.clip(share, 0.0, 0.8)
                rev[:, q] += (wq @ o["rev_win"]) * share / (1.0 - share)

        actives = np.zeros((self.C, NQ))
        adds = np.zeros((self.C, NQ))
        churn = np.zeros((self.C, NQ))
        sub_active = self.spell_active if use_spells else self.last_charge
        sub_adds = self.spell_adds if use_spells else self.first_adds
        s = self.sub_idx
        actives[s, :] = np.einsum("pq,pcq->cq", W, sub_active[:, s, :].astype(float))
        adds[s, :] = np.einsum("pq,pcq->cq", W, sub_adds[:, s, :])
        if use_spells:
            num = np.einsum("pq,pcq->cq", W, self.spell_ends[:, s, :])
            den = np.zeros((len(s), NQ))
            den[:, 1:] = np.einsum("pq,pcq->cq", W[:, 1:],
                                   self.spell_active[:, s, :-1].astype(float))
        else:
            lost = np.zeros((self.P, len(s), NQ))
            prev = self.last_charge[:, s, :-1]
            cur = self.last_charge[:, s, 1:]
            lost[:, :, 1:] = (prev & ~cur).astype(float)
            lost *= self.in_panel_end[:, None, :]
            num = np.einsum("pq,pcq->cq", W, lost)
            den = np.zeros((len(s), NQ))
            den[:, 1:] = np.einsum(
                "pq,pcq->cq", W[:, 1:],
                (self.last_charge[:, s, :-1] & self.in_panel_end[:, None, 1:]).astype(float))
        with np.errstate(divide="ignore", invalid="ignore"):
            churn[s, :] = np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)

        e = self.ecom_idx
        tr = self.trail[:, e, :].astype(float)
        actives[e, :] = np.einsum("pq,pcq->cq", W, tr)
        newly = np.zeros_like(tr)
        newly[:, :, 1:] = (self.trail[:, e, 1:] & ~self.trail[:, e, :-1]).astype(float)
        adds[e, :] = np.einsum("pq,pcq->cq", W, newly)
        gone = np.zeros_like(tr)
        gone[:, :, 1:] = (self.trail[:, e, :-1] & ~self.trail[:, e, 1:]).astype(float)
        num = np.einsum("pq,pcq->cq", W, gone)
        den = np.zeros((len(e), NQ))
        den[:, 1:] = np.einsum("pq,pcq->cq", W[:, 1:], tr[:, :, :-1])
        with np.errstate(divide="ignore", invalid="ignore"):
            churn[e, :] = np.where(den > 0, num / np.where(den > 0, den, 1.0), 0.0)

        with np.errstate(divide="ignore", invalid="ignore"):
            arpu = np.where(actives > 0, rev / np.where(actives > 0, actives, 1.0), 0.0)
        total = rev.sum(axis=0)
        share = 100.0 * rev / np.where(total > 0, total, 1.0)[None, :]
        return {"revenue": rev, "actives": actives, "gross_adds": adds,
                "churn_rate": churn, "arpu": arpu, "market_share": share}

    def m1(self, mult):
        initial = float(mult[self.joined == 1].sum())
        scale = self.n_pop / initial
        W = np.tile((mult * scale)[:, None], (1, NQ))
        return self._core(W, use_spells=False, outage_fix=False)

    def m2(self, mult):
        W, _ = self.raked_weights(mult)
        return self._core(mult[:, None] * W, use_spells=False, outage_fix=False)

    def m3(self, mult):
        W, _ = self.raked_weights(mult)
        return self._core(mult[:, None] * W, use_spells=True, outage_fix=True)

    def m4(self, mult, m3_est=None):
        est = m3_est if m3_est is not None else self.m3(mult)
        f_rev = calibrate.factor_grid(self.rep_rev, est["revenue"])
        f_act = calibrate.factor_grid(self.rep_act, est["actives"])
        rev = est["revenue"] * f_rev
        act = est["actives"] * f_act
        adds = est["gross_adds"] * f_act
        with np.errstate(divide="ignore", invalid="ignore"):
            arpu = np.where(act > 0, rev / np.where(act > 0, act, 1.0), 0.0)
        total = rev.sum(axis=0)
        share = 100.0 * rev / np.where(total > 0, total, 1.0)[None, :]
        return {"revenue": rev, "actives": act, "gross_adds": adds,
                "churn_rate": est["churn_rate"], "arpu": arpu,
                "market_share": share}

    def all_methods(self, mult=None):
        mult = np.ones(self.P) if mult is None else mult
        return {"m1": self.m1(mult), "m2": self.m2(mult), "m3": self.m3(mult)}


# --------------------------------------------------------- public interface

_CACHE = {}


def build_engines(txns, panelists, companies, census, reported):
    bundle = qa.run_qa(txns, panelists, companies)
    raw = Engine(bundle, census, reported, corrected=False)
    cor = Engine(bundle, census, reported, corrected=True)
    return bundle, raw, cor


def _engines_for(panel, public):
    key = id(panel["transactions"])
    if key not in _CACHE:
        reported = public["reported_before"](config.QUARTERS[-1])
        _CACHE[key] = build_engines(
            panel["transactions"], panel["panelists"], public["companies"],
            public["census_margins"], reported)
        while len(_CACHE) > 2:
            _CACHE.pop(next(iter(_CACHE)))
    return _CACHE[key]


def _frame(grids, engine, quarter):
    qi = config.quarter_index(quarter)
    rows = [{"company": co, "kpi": k, "estimate": float(grids[k][ci, qi])}
            for ci, co in enumerate(engine.companies) for k in KPIS]
    return pd.DataFrame(rows)


def m1_naive(quarter, panel, public):
    _, raw, _ = _engines_for(panel, public)
    return _frame(raw.m1(np.ones(raw.P)), raw, quarter)


def m2_weighted(quarter, panel, public):
    _, raw, _ = _engines_for(panel, public)
    return _frame(raw.m2(np.ones(raw.P)), raw, quarter)


def m3_weighted_qa(quarter, panel, public):
    _, _, cor = _engines_for(panel, public)
    return _frame(cor.m3(np.ones(cor.P)), cor, quarter)


def m4_calibrated(quarter, panel, public):
    _, _, cor = _engines_for(panel, public)
    return _frame(cor.m4(np.ones(cor.P)), cor, quarter)
