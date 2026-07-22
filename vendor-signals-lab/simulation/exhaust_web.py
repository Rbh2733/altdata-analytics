"""Web-traffic exhaust: monthly visit estimates, level bias, and the
bot-traffic-spike plant (P1).

Levels are off by 2-3x per vendor and never self-correct (the level bias
is drawn once and held constant); the shop is expected to consume this
source in log-differences only.
"""

import numpy as np

import config
from simulation import params
from simulation import exhaust_jobs as jobs_mod  # reuse _active_months


def _coverage_missing_prob(vendor, all_headcounts_sorted) -> float:
    """Missing-coverage probability skewed toward the smallest vendors;
    averages to roughly 1 - WEB_COVERAGE_RATE across the population."""
    hc = vendor["initial_headcount"]
    rank = np.searchsorted(all_headcounts_sorted, hc) / max(len(all_headcounts_sorted) - 1, 1)
    return float(0.20 * (1.0 - rank))


def build_web_traffic(vendors, trajectories_by_id, vendor_state, rng,
                       bot_spike_vendor_id=None):
    all_hc = np.array(sorted(v["initial_headcount"] for v in vendors))
    rows = []
    covered_rows = []
    plant = params.PLANT_BOT_SPIKE

    for v in vendors:
        vid = v["vendor_id"]
        seg = v["segment"]
        traj = trajectories_by_id[vid]
        miss_p = _coverage_missing_prob(v, all_hc)
        covered = bool(rng.random() >= miss_p)
        covered_rows.append({"vendor_id": vid, "covered": int(covered)})
        if not covered:
            continue

        level_bias = float(rng.lognormal(0.0, params.WEB_LEVEL_BIAS_SIGMA))
        seg_const = params.SEGMENT_TRAFFIC_CONSTANT[seg]

        for i in range(config.N_QUARTERS):
            t = i + 1
            q = config.QUARTERS[i]
            active_months = jobs_mod._active_months(vid, t, vendor_state)
            usage = traj["truth_usage"][i]
            base_visits = seg_const * (usage ** params.WEB_USAGE_EXPONENT) * level_bias

            for month in config.quarter_months(q):
                if month not in active_months:
                    continue
                seasonal = 1.0 + params.WEB_SEASONAL_AMPLITUDE * np.sin(
                    2 * np.pi * month[1] / 12.0)
                noise = float(rng.lognormal(0.0, params.WEB_MONTHLY_NOISE_SIGMA))
                visits = base_visits * seasonal * noise

                if (vid == bot_spike_vendor_id and q == plant["quarter"]
                        and month in config.quarter_months(plant["quarter"])[:2]):
                    idx_in_pair = config.quarter_months(plant["quarter"])[:2].index(month)
                    frac = [3.0 / 4.345, 2.0 / 4.345][idx_in_pair]
                    mult = 1.0 + frac * (plant["multiplier"] - 1.0)
                    visits *= mult

                rows.append({
                    "vendor_id": vid, "month": config.month_label(*month),
                    "estimated_visits": max(1, round(visits)),
                })

    return rows, covered_rows
