"""Generator orchestrator: python -m simulation.generate

Simulates the world, samples the biased panel, injects the planted
pathologies, and writes every file under data/. Deterministic: a single
seed (config.SEED) threads through named substreams in fixed order.
"""

import numpy as np
import pandas as pd

import config
from simulation import market, panel, params, population, truth


def _write(df, path, formats=None):
    df = df.copy()
    for col, fmt in (formats or {}).items():
        df[col] = df[col].map(lambda x: format(x, fmt))
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, lineterminator="\n", encoding="utf-8")


def main(root=None, verbose=True):
    root = config.ROOT if root is None else root
    panel_dir = root / "data" / "panel"
    public_dir = root / "data" / "public"
    truth_dir = root / "data" / "truth"

    ss = np.random.SeedSequence(config.SEED)
    (s_pop, s_select, s_subs, s_ecom, s_pf, s_inst, s_rows, s_obs) = ss.spawn(8)

    pop = population.build_population(np.random.default_rng(s_pop))
    panelists = panel.select_panelists(pop, np.random.default_rng(s_select))
    panel_mask = np.zeros(pop["n"], dtype=bool)
    panel_mask[panelists["person"].to_numpy()] = True

    subs = market.simulate_subscriptions(pop, np.random.default_rng(s_subs))
    ecom = market.simulate_ecom(pop, panel_mask, np.random.default_rng(s_ecom))
    pf = market.simulate_pinefort_purchases(
        pop, subs["Pinefort"]["active_during"], panel_mask,
        np.random.default_rng(s_pf))

    truth_df = truth.build_truth(subs, ecom, pf)
    reported = truth.build_reported(truth_df)

    inst = panel.assign_instruments(panelists, np.random.default_rng(s_inst))
    raw = panel.build_raw_rows(pop, panelists, inst, subs, ecom, pf,
                               np.random.default_rng(s_rows))
    obs = panel.observe(raw, inst, np.random.default_rng(s_obs))
    feed, events = panel.apply_pathologies(obs, panelists)

    # ---- write panel files
    txns = feed[["txn_id", "panelist_id", "date", "merchant_descriptor",
                 "amount", "instrument"]]
    _write(txns, panel_dir / "panel_transactions.csv", formats={"amount": ".2f"})

    pl = panelists.copy()
    pl["age_band"] = [config.AGE_BANDS[i] for i in pl["age_idx"]]
    pl["income_band"] = [config.INCOME_BANDS[i] for i in pl["inc_idx"]]
    pl["region"] = [config.REGIONS[i] for i in pl["reg_idx"]]
    pl["left_month"] = pl["left_month"].map(lambda v: "" if v == 0 else str(v))
    _write(pl[["panelist_id", "age_band", "income_band", "region",
               "joined_month", "left_month"]], panel_dir / "panelists.csv")

    # ---- write public files
    ai_counts, reg_counts = population.census_tables(pop)
    rows = []
    for a in range(4):
        for i in range(3):
            rows.append({"margin": "age_income", "age_band": config.AGE_BANDS[a],
                         "income_band": config.INCOME_BANDS[i], "region": "",
                         "population": int(ai_counts[a * 3 + i])})
    for r in range(4):
        rows.append({"margin": "region", "age_band": "", "income_band": "",
                     "region": config.REGIONS[r], "population": int(reg_counts[r])})
    _write(pd.DataFrame(rows), public_dir / "census_margins.csv")

    comp = pd.DataFrame([
        {"company": co, "category": params.CATEGORY[co],
         "base_descriptor": params.BASE_DESCRIPTOR[co]}
        for co in params.COMPANIES])
    _write(comp, public_dir / "companies.csv")
    _write(reported, public_dir / "reported_actuals.csv", formats={"revenue": ".1f"})

    # ---- write truth files
    _write(truth_df, truth_dir / "truth_kpis.csv",
           formats={"revenue": ".2f", "churn_rate": ".6f", "arpu": ".4f",
                    "market_share": ".4f"})
    _write(events, truth_dir / "planted_events.csv")

    summary = {
        "panelists": len(panelists),
        "initial_panelists": int((panelists["joined_month"] == 1).sum()),
        "transactions": len(txns),
    }
    if verbose:
        print(f"      panel: {summary['panelists']} panelists "
              f"({summary['initial_panelists']} initial + wave), "
              f"{summary['transactions']} observed transactions")
    return summary


if __name__ == "__main__":
    main()
