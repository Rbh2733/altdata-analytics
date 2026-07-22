"""Customer spend panel exhaust: merchant descriptor strings, transaction
rows, and two plants: descriptor fragmentation (P3) and the coverage
cliff (P4).

Publication lag (one month) is not applied here; the generator just
stamps real transaction dates. The lag is enforced downstream, in
estimation/loader.py's as_of() view, which is where the temporal fence
actually lives.
"""

import numpy as np

import config
from simulation import params
from simulation import exhaust_jobs as jobs_mod


def _mangle(name: str, style: int) -> str:
    upper = name.upper()
    if style == 0:
        return upper
    if style == 1:
        return f"SQ *{upper}"
    if style == 2:
        return f"{upper} INC"
    if style == 3:
        return f"{upper[:10]}*SUB"
    return f"PYMT-{upper}"


def _assign_descriptors(vendor, rng):
    lo, hi = params.SPEND_DESCRIPTORS_PER_VENDOR
    n = int(rng.integers(lo, hi + 1))
    styles = rng.choice([0, 1, 2, 3, 4], size=n, replace=False)
    return [_mangle(vendor["name"], int(s)) for s in styles]


def build_spend_panel(vendors, trajectories_by_id, vendor_state, rng,
                       fragmentation_vendor_id=None):
    plant_frag = params.PLANT_DESCRIPTOR_FRAGMENTATION
    plant_cliff = params.PLANT_COVERAGE_CLIFF
    cliff_quarters = set(plant_cliff["quarters"])
    cliff_segment = plant_cliff["segment"]

    panel_pool = np.array([f"PAN{i:05d}" for i in range(params.SPEND_PANELIST_POOL_SIZE)])

    txn_rows = []
    descriptor_map_rows = []  # public: initial descriptors only
    vendor_descriptors = {}   # vendor_id -> list of {descriptor, era}
    txn_seq = 0

    for v in vendors:
        vid = v["vendor_id"]
        seg = v["segment"]
        p_channel = params.SPEND_CHANNEL_PROB[seg]
        in_channel = bool(rng.random() < p_channel)
        # The fragmentation plant needs its vendor in-channel; forcing it
        # here (rather than redrawing the world) is disclosed in the
        # README as a generator convenience.
        if vid == fragmentation_vendor_id:
            in_channel = True
        if not in_channel:
            continue

        traj = trajectories_by_id[vid]
        panel_share = float(rng.uniform(*params.SPEND_PANEL_SHARE_RANGE))
        rel_noise = float(rng.uniform(*params.SPEND_GROWTH_NOISE_REL))

        # Design intent: the row budget must not scale with vendor ARR (a
        # $400M vendor is not 65x more spend-panel transactions than a
        # $6M vendor, it just has bigger average deal sizes). So a target
        # transaction count is drawn independent of size, and the average
        # transaction amount is *solved for* from that target against the
        # vendor's initial quarterly revenue, then held fixed. Quarter to
        # quarter, transaction counts move with revenue growth relative to
        # that baseline, amounts stay put.
        target_txn_per_q = float(np.clip(
            rng.lognormal(np.log(55.0), 0.5), 9.0, 180.0))
        initial_quarterly_rev_m = v["initial_arr_m"] / 4.0
        avg_amount = float(np.clip(
            (initial_quarterly_rev_m * 1_000_000 * panel_share) / target_txn_per_q,
            params.SPEND_AVG_AMOUNT_FLOOR, params.SPEND_AVG_AMOUNT_CAP))

        n_panelists = max(15, round(panel_share * params.SPEND_PANELISTS_PER_VENDOR_SCALE))
        n_panelists = min(n_panelists, len(panel_pool))
        my_panelists = rng.choice(panel_pool, size=n_panelists, replace=False)

        initial_descs = _assign_descriptors(v, rng)
        for d in initial_descs:
            descriptor_map_rows.append({"vendor_id": vid, "descriptor_string": d})

        is_frag_vendor = (vid == fragmentation_vendor_id)
        new_descs = []
        if is_frag_vendor:
            used_styles = set()
            for d in initial_descs:
                for s in range(5):
                    if _mangle(v["name"], s) == d:
                        used_styles.add(s)
            remaining = [s for s in range(5) if s not in used_styles]
            for s in remaining[:plant_frag["n_new_descriptors"]]:
                new_descs.append(_mangle(v["name"], s))
            if len(new_descs) < plant_frag["n_new_descriptors"]:
                new_descs.append(f"{v['name'].upper()}-NEW")

        for i in range(config.N_QUARTERS):
            t = i + 1
            q = config.QUARTERS[i]
            if seg == cliff_segment and q in cliff_quarters:
                continue
            active_months = jobs_mod._active_months(vid, t, vendor_state)
            if not active_months:
                continue

            quarterly_rev_m = traj["truth_arr"][i] / 4.0
            growth_ratio = quarterly_rev_m / max(initial_quarterly_rev_m, 1e-6)
            noise_factor = float(rng.lognormal(0.0, rel_noise))
            n_txn = max(0, int(round(target_txn_per_q * growth_ratio * noise_factor)))
            n_txn = min(n_txn, 600)  # safety cap: no single vendor-quarter dominates the budget
            if len(active_months) < 3:
                n_txn = int(round(n_txn * len(active_months) / 3.0))
            if n_txn == 0:
                continue

            q_start_day = 1
            days_span = sum(config.days_in_month(*m) for m in active_months)

            for _ in range(n_txn):
                offset = int(rng.integers(0, days_span))
                month, day = _offset_to_date(active_months, offset)
                date_s = config.date_str(month[0], month[1], day)

                if is_frag_vendor and q == plant_frag["quarter"]:
                    day_of_q = _day_index_in_quarter(active_months, month, day)
                    fade_days = plant_frag["fade_weeks"] * 7
                    if day_of_q < fade_days:
                        p_old = 1.0 - (day_of_q / fade_days)
                    else:
                        p_old = 0.0
                    if rng.random() < p_old:
                        desc = initial_descs[0]
                    else:
                        desc = new_descs[int(rng.integers(0, len(new_descs)))]
                elif is_frag_vendor and config.quarter_index(q) > config.quarter_index(plant_frag["quarter"]):
                    desc = new_descs[int(rng.integers(0, len(new_descs)))]
                else:
                    weights = [0.75, 0.25][:len(initial_descs)]
                    weights = np.array(weights) / sum(weights)
                    desc = str(rng.choice(initial_descs, p=weights))

                amount = float(np.clip(
                    rng.lognormal(np.log(avg_amount), params.SPEND_TXN_AMOUNT_JITTER_SIGMA),
                    5.0, avg_amount * 20))
                panelist = str(rng.choice(my_panelists))
                txn_seq += 1
                txn_rows.append({
                    "descriptor_string": desc, "txn_date": date_s,
                    "amount": round(amount, 2), "panelist_id": panelist,
                })

        vendor_descriptors[vid] = {"initial": initial_descs, "new": new_descs}

    return txn_rows, descriptor_map_rows, vendor_descriptors


def _offset_to_date(active_months, offset):
    running = offset
    for m in active_months:
        dim = config.days_in_month(*m)
        if running < dim:
            return m, running + 1
        running -= dim
    return active_months[-1], config.days_in_month(*active_months[-1])


def _day_index_in_quarter(active_months, month, day):
    idx = 0
    for m in active_months:
        if m == month:
            return idx + day - 1
        idx += config.days_in_month(*m)
    return idx
