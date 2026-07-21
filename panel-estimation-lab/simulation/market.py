"""Market simulation: adoption, churn, pricing, purchases for six services.

Runs a burn-in period so the world does not start empty, then simulates
months 1..36. Truth aggregates are exact sums over the full population;
per-transaction detail is retained only for the persons in `panel_mask`
(the world is never materialized at transaction grain for all 200,000
consumers, only aggregated).
"""

import numpy as np

import config
from simulation import params


def _sub_price(company, m):
    if company == params.PRICE_EVENT_COMPANY and m >= params.PRICE_EVENT_MONTH:
        return params.PRICE_EVENT_NEW_PRICE
    return params.SUB_PRICE[company]


def _tenure_mult(tenure):
    out = np.full(tenure.shape, params.TENURE_MULT_MID)
    out[tenure <= 2] = params.TENURE_MULT_EARLY
    out[tenure >= 12] = params.TENURE_MULT_LATE
    return out


def simulate_subscriptions(pop, rng):
    """Simulate the four subscription services. Returns per-company dict:
    active_during (bool [N, 36]), monthly adopt/churn counts, month-end
    active counts, baseline end-of-burn-in count, and monthly revenue."""
    n = pop["n"]
    age, inc = pop["age_idx"], pop["inc_idx"]
    frailty = pop["frailty"]
    out = {}
    for co in params.SUB_COMPANIES:
        adopt_cell = (np.array(params.SUB_ADOPT_AGE_MULT[co])[age]
                      * np.array(params.SUB_ADOPT_INCOME_MULT[co])[inc])
        churn_cell = np.array(params.SUB_CHURN_AGE_MULT[co])[age]
        base_a = params.SUB_BASE_ADOPT[co]
        base_c = params.SUB_BASE_CHURN[co]

        active = np.zeros(n, dtype=bool)
        tenure = np.zeros(n, dtype=np.int16)
        lapsed_at = np.full(n, -10_000, dtype=np.int32)  # month of last lapse

        active_during = np.zeros((n, config.N_MONTHS), dtype=bool)
        adopt_m = np.zeros(config.N_MONTHS, dtype=np.int64)
        churn_m = np.zeros(config.N_MONTHS, dtype=np.int64)
        end_m = np.zeros(config.N_MONTHS, dtype=np.int64)
        revenue_m = np.zeros(config.N_MONTHS)
        baseline_end = 0

        for m in range(1 - params.BURNIN_MONTHS, config.N_MONTHS + 1):
            trend = params.trend_value(params.SUB_TREND[co], m, config.N_MONTHS)
            winback = np.where(
                (m - lapsed_at) <= params.WINBACK_MONTHS, params.WINBACK_MULT, 1.0)
            h_a = np.clip(base_a * adopt_cell * frailty * trend * winback, 0.0, 0.5)
            adopt = (~active) & (rng.random(n) < h_a)
            active |= adopt
            tenure[adopt] = 1
            if 1 <= m:
                active_during[:, m - 1] = active
                adopt_m[m - 1] = int(adopt.sum())
                revenue_m[m - 1] = _sub_price(co, m) * int(active.sum())

            event = (params.PRICE_EVENT_CHURN_MULT
                     if (co == params.PRICE_EVENT_COMPANY
                         and m in params.PRICE_EVENT_CHURN_MONTHS) else 1.0)
            h_c = np.clip(base_c * churn_cell * _tenure_mult(tenure) * event, 0.0, 0.9)
            churn = active & (rng.random(n) < h_c)
            active &= ~churn
            lapsed_at[churn] = m
            tenure[active] += 1
            if 1 <= m:
                churn_m[m - 1] = int(churn.sum())
                end_m[m - 1] = int(active.sum())
            if m == 0:
                baseline_end = int(active.sum())

        out[co] = {
            "active_during": active_during,
            "adopt_m": adopt_m,
            "churn_m": churn_m,
            "end_m": end_m,
            "baseline_end": baseline_end,
            "revenue_m": revenue_m,
        }
    return out


def _ecom_gate(co, pop, rng):
    """Fixed per-person customer gate, demographically tilted."""
    age, inc = pop["age_idx"], pop["inc_idx"]
    p = (params.ECOM_GATE_BASE[co]
         * np.array(params.ECOM_AGE_MULT[co])[age]
         * np.array(params.ECOM_INCOME_MULT[co])[inc])
    return rng.random(pop["n"]) < np.clip(p, 0.0, 0.95)


def _ecom_lambda(co, pop, intensity, m):
    lam = (params.ECOM_BASE_LAMBDA[co]
           * pop["frailty"]
           * intensity
           * params.trend_value(params.ECOM_TREND[co], m, config.N_MONTHS))
    if co == "Vantry":
        if 1 <= m <= config.N_MONTHS and config.month_of_year(m) in (10, 11, 12):
            lam = lam * params.VANTRY_Q4_MULT
        if m == params.VANTRY_PROMO_MONTH:
            lam = lam * params.VANTRY_PROMO_LAMBDA_MULT
    if co == "Glimmerly" and 1 <= m <= config.N_MONTHS:
        lam = lam * params.GLIMMERLY_PROMO_MULT[m - 1]
    return np.clip(lam, 0.0, params.ECOM_LAMBDA_CAP)


def simulate_ecom(pop, panel_mask, rng):
    """Simulate Vantry and Glimmerly purchases plus Pinefort member
    purchases (membership activity passed in via pinefort_active_during).

    Returns per-company: monthly revenue, trailing-12-month active counts
    at each quarter end (plus baseline), quarterly add/churn counts, and
    panel-person transaction arrays (person index, month, amount).
    """
    n = pop["n"]
    hist_offset = params.ECOM_HISTORY_MONTHS - 1  # month m -> column m + offset
    out = {}
    for co in params.ECOM_COMPANIES:
        mu, sigma = params.ECOM_AMOUNT[co]
        bought = np.zeros((n, config.N_MONTHS + params.ECOM_HISTORY_MONTHS), dtype=bool)
        revenue_m = np.zeros(config.N_MONTHS)
        gate = _ecom_gate(co, pop, rng)
        intensity = gate * rng.gamma(params.ECOM_GAMMA_SHAPE,
                                     1.0 / params.ECOM_GAMMA_SHAPE, n)
        tx_person, tx_month, tx_amount = [], [], []
        for m in range(2 - params.ECOM_HISTORY_MONTHS, config.N_MONTHS + 1):
            lam = _ecom_lambda(co, pop, intensity, m)
            counts = rng.poisson(lam)
            bought[:, m + hist_offset] = counts > 0
            if m < 1:
                continue
            total = int(counts.sum())
            amounts = np.round(rng.lognormal(mu, sigma, total), 2)
            revenue_m[m - 1] = float(amounts.sum())
            person = np.repeat(np.arange(n), counts)
            sel = panel_mask[person]
            tx_person.append(person[sel])
            tx_month.append(np.full(int(sel.sum()), m, dtype=np.int16))
            tx_amount.append(amounts[sel])

        qe = [0] + [3 * (i + 1) for i in range(12)]  # month 0 baseline + quarter ends
        trailing = {}
        for e in qe:
            lo = e + hist_offset - (params.ECOM_HISTORY_MONTHS - 1)
            trailing[e] = bought[:, lo:e + hist_offset + 1].any(axis=1)
        actives_q = np.array([int(trailing[3 * (i + 1)].sum()) for i in range(12)])
        baseline = int(trailing[0].sum())
        adds_q, churn_q = np.zeros(12, dtype=np.int64), np.zeros(12, dtype=np.int64)
        for i in range(12):
            prev = trailing[3 * i] if i > 0 else trailing[0]
            cur = trailing[3 * (i + 1)]
            adds_q[i] = int((cur & ~prev).sum())
            churn_q[i] = int((prev & ~cur).sum())
        out[co] = {
            "revenue_m": revenue_m,
            "actives_q": actives_q,
            "baseline": baseline,
            "adds_q": adds_q,
            "churn_q": churn_q,
            "tx_person": np.concatenate(tx_person),
            "tx_month": np.concatenate(tx_month),
            "tx_amount": np.concatenate(tx_amount),
        }
    return out


def simulate_pinefort_purchases(pop, pinefort_active_during, panel_mask, rng):
    """Pinefort members purchase while their membership is active."""
    n = pop["n"]
    mu, sigma = params.PINEFORT_AMOUNT
    revenue_m = np.zeros(config.N_MONTHS)
    tx_person, tx_month, tx_amount = [], [], []
    lam_base = np.clip(params.PINEFORT_PURCHASE_LAMBDA * pop["frailty"],
                       0.0, params.ECOM_LAMBDA_CAP)
    for m in range(1, config.N_MONTHS + 1):
        lam = lam_base * pinefort_active_during[:, m - 1]
        counts = rng.poisson(lam)
        total = int(counts.sum())
        amounts = np.round(rng.lognormal(mu, sigma, total), 2)
        revenue_m[m - 1] = float(amounts.sum())
        person = np.repeat(np.arange(n), counts)
        sel = panel_mask[person]
        tx_person.append(person[sel])
        tx_month.append(np.full(int(sel.sum()), m, dtype=np.int16))
        tx_amount.append(amounts[sel])
    return {
        "revenue_m": revenue_m,
        "tx_person": np.concatenate(tx_person),
        "tx_month": np.concatenate(tx_month),
        "tx_amount": np.concatenate(tx_amount),
    }
