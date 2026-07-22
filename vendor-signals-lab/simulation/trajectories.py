"""Latent health paths: truth ARR, headcount, usage index, and the truth
inflection labels the judge grades against.

Design intent: the archetype definitions constrain only the start and
end growth rates around a regime change, not the exact mechanics of the
"S-ramp" between them, so the staggered lag below is the concrete
implementation chosen. Each archetype has a
piecewise-constant growth *plan* that changes at one or two change-point
quarters. The plan takes effect immediately (quarter t0 = change_point+1)
for hiring. Web usage catches up fully one quarter later (t0+1). ARR
realizes the new rate gradually: 0% of the delta at t0, one third at
t0+1, the full new rate from t0+2 onward. This is what "jobs leads
revenue by ~2 quarters, web by ~1" means operationally, and it is a
property of this generator, not a law the evaluation layer is told about.
"""

import numpy as np

import config
from simulation import params


def _regime_plan(archetype, rng):
    """Returns (plan[1..12] as a length-12 list, change points, regime
    values) for one vendor."""
    spec = params.ARCHETYPE_GROWTH[archetype]
    lo, hi = spec["start"]
    start_growth = float(rng.uniform(lo, hi))
    n = config.N_QUARTERS

    if archetype == "steady_growth":
        plan = [start_growth] * n
        return plan, [], {"start": start_growth}

    cp1 = int(rng.integers(params.CHANGE_POINT_QUARTER_RANGE[0],
                            params.CHANGE_POINT_QUARTER_RANGE[1] + 1))

    if archetype == "wind_down":
        mlo, mhi = spec["mid"]
        elo, ehi = spec["end"]
        mid_growth = float(rng.uniform(mlo, mhi))
        end_growth = float(rng.uniform(elo, ehi))
        gap = int(rng.integers(params.WIND_DOWN_SECOND_POINT_GAP[0],
                                params.WIND_DOWN_SECOND_POINT_GAP[1] + 1))
        cp2 = cp1 + gap
        plan = []
        for t in range(1, n + 1):
            if t <= cp1:
                plan.append(start_growth)
            elif t <= cp2:
                plan.append(mid_growth)
            else:
                plan.append(end_growth)
        cps = [cp1] if cp2 > n else [cp1, cp2]
        return plan, cps, {"start": start_growth, "mid": mid_growth, "end": end_growth}

    elo, ehi = spec["end"]
    end_growth = float(rng.uniform(elo, ehi))
    plan = [start_growth if t <= cp1 else end_growth for t in range(1, n + 1)]
    return plan, [cp1], {"start": start_growth, "end": end_growth}


def _ramp(plan, ramp_len2=True):
    """Smooth a piecewise-constant plan into the growth actually realized
    downstream. ramp_len2=True gives the 2-quarter ARR ramp (0%, 1/3,
    100%); False gives the 1-quarter web ramp (0%, 100%)."""
    n = len(plan)
    out = list(plan)
    for idx in range(1, n):
        if plan[idx] != plan[idx - 1]:
            old, new = plan[idx - 1], plan[idx]
            out[idx] = old
            if ramp_len2:
                if idx + 1 < n:
                    out[idx + 1] = old + (new - old) / 3.0
                if idx + 2 < n:
                    out[idx + 2] = new
            else:
                if idx + 1 < n:
                    out[idx + 1] = new
    return out


def build_trajectory(vendor: dict, rng: np.random.Generator) -> dict:
    archetype = vendor["archetype"]
    n = config.N_QUARTERS
    plan, change_points, regime_values = _regime_plan(archetype, rng)

    # AR(1) disturbance on ARR growth only.
    phi = params.AR1_PHI
    sigma = params.AR1_INNOVATION_SIGMA_PP / 100.0
    disturbance = [0.0] * n
    prev = 0.0
    for i in range(n):
        prev = phi * prev + float(rng.normal(0.0, sigma))
        disturbance[i] = prev

    arr_ramp = _ramp(plan, ramp_len2=True)
    usage_ramp = _ramp(plan, ramp_len2=False)

    arr = [0.0] * n
    truth_growth = [0.0] * n
    prev_arr = vendor["initial_arr_m"]
    for i in range(n):
        g = arr_ramp[i] + disturbance[i]
        truth_growth[i] = g
        cur = max(prev_arr * (1.0 + g), 0.01)
        arr[i] = cur
        prev_arr = cur

    usage = [0.0] * n
    prev_usage = 1.0
    for i in range(n):
        cur = max(prev_usage * (1.0 + usage_ramp[i]), 1e-6)
        usage[i] = cur
        prev_usage = cur

    headcount = [0] * n
    requisitions_target = [0.0] * n
    prev_hc = float(vendor["initial_headcount"])
    for i in range(n):
        t = i + 1
        plan_g = plan[i]
        if plan_g >= 0:
            hc_g = plan_g
            planned_hires = prev_hc * plan_g * params.HIRING_ELASTICITY
            replacement = prev_hc * params.REPLACEMENT_CHURN_PER_QUARTER
        else:
            prior_plan_g = plan[i - 1] if i > 0 else 0.0
            hc_g = min(0.0, prior_plan_g)
            planned_hires = 0.0
            replacement = 0.0
        requisitions_target[i] = max(planned_hires + replacement, 0.0)
        cur_hc = max(prev_hc * (1.0 + hc_g), 1.0)
        headcount[i] = cur_hc
        prev_hc = cur_hc

    # Truth inflection labels: one row per change point with |delta| >= 8pp.
    inflections = []
    for cp in change_points:
        t0 = cp + 1
        if t0 > n:
            continue
        old_g = plan[cp - 1]
        new_g = plan[t0 - 1] if t0 - 1 < n else plan[-1]
        delta_pp = (new_g - old_g) * 100.0
        if abs(delta_pp) >= params.INFLECTION_MIN_DELTA_PP:
            label = "acceleration" if delta_pp > 0 else "stall"
            inflections.append({
                "quarter_index": t0,  # 1-based
                "quarter": config.QUARTERS[t0 - 1],
                "type": label,
                "delta_pp": delta_pp,
            })

    return {
        "vendor_id": vendor["vendor_id"],
        "archetype": archetype,
        "plan": plan,
        "regime_values": regime_values,
        "change_points": change_points,
        "truth_growth": truth_growth,
        "truth_arr": arr,
        "truth_usage": usage,
        "truth_headcount": headcount,
        "requisitions_target": requisitions_target,
        "inflections": inflections,
    }
