"""Biased panel sampler: recruitment skew, attrition, instrument coverage,
heterogeneous observability, plus the four planted feed pathologies.

The panel is a broken window onto the world. Everything here degrades or
distorts what the panel sees; nothing here changes the world itself.
"""

import numpy as np
import pandas as pd

import config
from simulation import params


# --------------------------------------------------------------- selection

def select_panelists(pop, rng):
    """Initial recruitment (skewed) plus the month-16 wave (differently
    skewed). Returns panelist frame indexed by panelist row order."""
    n = pop["n"]
    age, inc = pop["age_idx"], pop["inc_idx"]
    w = (np.array(params.RECRUIT_AGE_W)[age]
         * np.array(params.RECRUIT_INCOME_W)[inc])
    p_incl = config.PANEL_TARGET * w / w.sum()
    initial = rng.random(n) < p_incl

    wave_w = (np.array(params.WAVE_AGE_W)[age]
              * np.array(params.WAVE_INCOME_W)[inc])
    wave_w[initial] = 0.0
    wave_ids = rng.choice(n, size=params.WAVE_SIZE, replace=False,
                          p=wave_w / wave_w.sum())

    person = np.concatenate([np.flatnonzero(initial), np.sort(wave_ids)])
    joined = np.concatenate([
        np.ones(int(initial.sum()), dtype=np.int32),
        np.full(params.WAVE_SIZE, params.WAVE_MONTH, dtype=np.int32),
    ])
    order = np.lexsort((person, joined))
    person, joined = person[order], joined[order]
    pid = np.arange(1, len(person) + 1)

    # Attrition: monthly dropout hazard by age band from the join month.
    # left_month = first month the panelist no longer contributes; 0 = never.
    hazard = params.ATTRITION_BASE * np.array(params.ATTRITION_AGE_MULT)[age[person]]
    left = np.zeros(len(person), dtype=np.int32)
    alive = np.zeros(len(person), dtype=bool)
    for m in range(1, config.N_MONTHS + 1):
        alive |= joined == m
        drop = alive & (rng.random(len(person)) < hazard)
        left[drop & (left == 0)] = m + 1
        alive &= ~drop
    left[left > config.N_MONTHS] = 0  # dropping after the last month = never left

    return pd.DataFrame({
        "panelist_id": pid,
        "person": person,
        "age_idx": age[person],
        "inc_idx": inc[person],
        "reg_idx": pop["reg_idx"][person],
        "joined_month": joined,
        "left_month": left,
    })


def in_window(panel, months):
    """Bool matrix [P, len(months)]: panelist contributes in month."""
    j = panel["joined_month"].to_numpy()[:, None]
    l = panel["left_month"].to_numpy()[:, None]
    mm = np.asarray(months)[None, :]
    return (j <= mm) & ((l == 0) | (mm < l))


# ------------------------------------------------------------- instruments

def assign_instruments(panel, rng):
    """Holdings (1-3 of 4), usage mix, enrolled subset, capture factor,
    and per-subscription billing instrument."""
    p = len(panel)
    held = np.zeros((p, 4), dtype=bool)
    usage = np.zeros((p, 4))
    pop_w = params.INSTRUMENT_POPULARITY
    ks = rng.choice([1, 2, 3], size=p, p=params.HOLDING_COUNT_P)
    for i in range(p):
        idx = rng.choice(4, size=ks[i], replace=False, p=pop_w)
        held[i, idx] = True
        g = rng.gamma(params.USAGE_DIRICHLET_CONC, pop_w[idx])
        usage[i, idx] = g / g.sum()

    enroll_p = np.array([params.ENROLL_P_CARD] * 3 + [params.ENROLL_P_WALLET])
    enrolled = held & (rng.random((p, 4)) < enroll_p[None, :])
    none = ~enrolled.any(axis=1)
    top = np.argmax(np.where(held, usage, -1.0), axis=1)
    enrolled[np.flatnonzero(none), top[none]] = True

    capture = rng.beta(*params.CAPTURE_BETA, size=p)

    # Effective per-company instrument mix = usage * affinity, renormalized.
    mix = {}
    for co in params.COMPANIES + ["_noise"]:
        aff = np.array(params.COMPANY_INSTRUMENT_AFFINITY[co])
        m = usage * aff[None, :]
        mix[co] = m / m.sum(axis=1, keepdims=True)

    # Subscriptions bill one fixed instrument per panelist-service.
    billing = {}
    for co in params.SUB_COMPANIES:
        u = rng.random(p)
        cum = np.cumsum(mix[co], axis=1)
        billing[co] = (u[:, None] > cum).sum(axis=1).clip(0, 3)

    return {"held": held, "usage": usage, "enrolled": enrolled,
            "capture": capture, "mix": mix, "billing": billing}


def _draw_instrument(mix_rows, rng):
    u = rng.random(mix_rows.shape[0])
    cum = np.cumsum(mix_rows, axis=1)
    return (u[:, None] > cum).sum(axis=1).clip(0, 3)


# ----------------------------------------------------------- materialization

def _purchase_days(months, rng, vantry=False):
    days = np.array([config.days_in_month(m) for m in range(1, config.N_MONTHS + 1)])
    d = 1 + (rng.random(len(months)) * days[months - 1]).astype(np.int32)
    if vantry:
        promo = months == params.VANTRY_PROMO_MONTH
        to_day = promo & (rng.random(len(months)) < params.VANTRY_PROMO_DAY_SHARE)
        d[to_day] = params.VANTRY_PROMO_DAY
    return d


def build_raw_rows(pop, panel, inst, subs, ecom, pinefort_purchases, rng):
    """All panel-window rows before observation filters, as a DataFrame:
    prow (panel row index), month, day, company key, amount, instrument."""
    person_to_prow = np.full(pop["n"], -1, dtype=np.int64)
    person_to_prow[panel["person"].to_numpy()] = np.arange(len(panel))
    window = in_window(panel, np.arange(1, config.N_MONTHS + 1))

    frames = []

    # Subscription charges: one per active member-month, fixed billing day.
    for ci, co in enumerate(params.SUB_COMPANIES):
        act = subs[co]["active_during"][panel["person"].to_numpy()]  # [P, 36]
        obs = act & window
        prow, mm = np.nonzero(obs)
        month = (mm + 1).astype(np.int32)
        day = (1 + (panel["person"].to_numpy()[prow] * 7 + ci * 11) % 28).astype(np.int32)
        price = np.array([params.SUB_PRICE[co]] * config.N_MONTHS)
        if co == params.PRICE_EVENT_COMPANY:
            price[params.PRICE_EVENT_MONTH - 1:] = params.PRICE_EVENT_NEW_PRICE
        amount = price[mm]
        instr = inst["billing"][co][prow]
        frames.append(pd.DataFrame({
            "prow": prow, "month": month, "day": day, "company": co,
            "amount": amount, "instr": instr}))

    # Purchases: Vantry, Glimmerly, Pinefort member purchases.
    purchase_sets = [("Vantry", ecom["Vantry"]), ("Glimmerly", ecom["Glimmerly"]),
                     ("Pinefort", pinefort_purchases)]
    for co, blk in purchase_sets:
        prow = person_to_prow[blk["tx_person"]]
        month = blk["tx_month"].astype(np.int32)
        keep = window[prow, month - 1]
        prow, month = prow[keep], month[keep]
        amount = blk["tx_amount"][keep]
        day = _purchase_days(month, rng, vantry=(co == "Vantry"))
        instr = _draw_instrument(inst["mix"][co][prow], rng)
        frames.append(pd.DataFrame({
            "prow": prow, "month": month, "day": day, "company": co,
            "amount": amount, "instr": instr}))

    # Out-of-scope noise merchant.
    lam = np.where(window, params.NOISE_LAMBDA, 0.0)
    counts = rng.poisson(lam)
    prow, mm = np.nonzero(counts)
    reps = counts[prow, mm]
    prow = np.repeat(prow, reps)
    month = np.repeat(mm + 1, reps).astype(np.int32)
    amount = np.round(rng.lognormal(params.NOISE_AMOUNT_MU,
                                    params.NOISE_AMOUNT_SIGMA, len(prow)), 2)
    day = _purchase_days(month, rng)
    instr = _draw_instrument(inst["mix"]["_noise"][prow], rng)
    frames.append(pd.DataFrame({
        "prow": prow, "month": month, "day": day, "company": "_noise",
        "amount": amount, "instr": instr}))

    return pd.concat(frames, ignore_index=True)


# ------------------------------------------------ observation and pathologies

def observe(raw, inst, rng):
    """Instrument enrollment coverage plus per-panelist capture thinning."""
    enrolled = inst["enrolled"][raw["prow"].to_numpy(), raw["instr"].to_numpy()]
    raw = raw[enrolled]
    keep = rng.random(len(raw)) < inst["capture"][raw["prow"].to_numpy()]
    return raw[keep].reset_index(drop=True)


def _p4_suffix(i):
    a = "ABCDEFGHJKMNPQRSTUVWXYZ"
    return f"{a[(i * 7) % 23]}{(i * 31) % 10}"


def apply_pathologies(obs, panel):
    """P4 descriptor change, P3 supplier outage, P1 duplicated feed day.
    (P2, the recruitment wave, lives in panel composition itself.)
    Returns the final feed plus per-pathology bookkeeping for
    planted_events.csv."""
    df = obs.copy()
    df["panelist_id"] = panel["panelist_id"].to_numpy()[df["prow"].to_numpy()]
    df["date"] = [config.date_str(m, d) for m, d in zip(df["month"], df["day"])]
    df["instrument"] = np.array(params.INSTRUMENTS)[df["instr"].to_numpy()]
    df["merchant_descriptor"] = df["company"].map(
        {**params.BASE_DESCRIPTOR, "_noise": params.NOISE_DESCRIPTOR})

    # P4: descriptor change with per-row suffix noise.
    p4 = ((df["company"] == params.DESCRIPTOR_CHANGE_COMPANY)
          & (df["date"] >= params.DESCRIPTOR_CHANGE_DATE))
    idx = np.flatnonzero(p4.to_numpy())
    df.loc[df.index[idx], "merchant_descriptor"] = [
        f"{params.DESCRIPTOR_CHANGE_NEW} {_p4_suffix(int(i))}" for i in idx]

    # P3: supplier outage, card_B rows vanish for 12 days.
    out_mask = ((df["instrument"] == params.OUTAGE_INSTRUMENT)
                & (df["date"] >= params.OUTAGE_START)
                & (df["date"] <= params.OUTAGE_END))
    outage_removed = int(out_mask.sum())
    df = df[~out_mask].reset_index(drop=True)

    # P1: duplicated feed day. First guarantee no natural exact content
    # duplicates on the date (nudge amounts by one cent), then append two
    # extra copies of every row.
    key_cols = ["panelist_id", "date", "merchant_descriptor", "amount", "instrument"]
    for _ in range(6):
        sub = df[df["date"] == params.DUP_DATE]
        dup_rank = sub.groupby(key_cols).cumcount()
        if int(dup_rank.sum()) == 0:
            break
        df.loc[sub.index, "amount"] = (sub["amount"] + 0.01 * dup_rank).round(2)
    dup_rows = df[df["date"] == params.DUP_DATE]
    extra = pd.concat([dup_rows] * (params.DUP_COPIES - 1), ignore_index=True)
    dup_added = len(extra)
    df["copy"] = 0
    extra["copy"] = np.repeat(np.arange(1, params.DUP_COPIES), len(dup_rows))
    df = pd.concat([df, extra], ignore_index=True)

    df = df.sort_values(
        ["date", "panelist_id", "merchant_descriptor", "amount", "instrument", "copy"],
        kind="mergesort").reset_index(drop=True)
    df["txn_id"] = np.arange(1, len(df) + 1)

    events = pd.DataFrame([
        {"pathology": "duplicate_feed_day", "quarter": "2023Q3",
         "start_date": params.DUP_DATE, "end_date": params.DUP_DATE,
         "target": "extra_rows", "value": str(dup_added)},
        {"pathology": "recruitment_wave", "quarter": "2023Q2",
         "start_date": config.date_str(params.WAVE_MONTH, 1),
         "end_date": config.date_str(params.WAVE_MONTH,
                                     config.days_in_month(params.WAVE_MONTH)),
         "target": "new_panelists", "value": str(params.WAVE_SIZE)},
        {"pathology": "supplier_outage", "quarter": "2024Q1",
         "start_date": params.OUTAGE_START, "end_date": params.OUTAGE_END,
         "target": f"{params.OUTAGE_INSTRUMENT}_rows_removed",
         "value": str(outage_removed)},
        {"pathology": "descriptor_change", "quarter": "2024Q2",
         "start_date": params.DESCRIPTOR_CHANGE_DATE, "end_date": "2024-12-31",
         "target": params.DESCRIPTOR_CHANGE_COMPANY,
         "value": params.DESCRIPTOR_CHANGE_NEW},
    ])
    return df, events
