"""Outcome events (truth, judge-only): funding rounds, shutdowns,
acquisitions, and disclosed acquisition revenues. Also determines when a
vendor's exhaust goes dark (after shutdown, or the quarter after an
acquisition).

Boundary decision (stated again in the README): real funding
announcements are public and a real shop would consume them. Here every
outcome event lives in data/truth/ and only the evaluation layer reads
it, so outcome validation stays clean out-of-sample evidence. This costs
realism and buys inferential clarity.
"""

import numpy as np

import config
from simulation import params


def generate_outcomes(vendors: list, trajectories_by_id: dict,
                       rng: np.random.Generator):
    n = config.N_QUARTERS
    events = []
    vendor_state = {}

    for v in vendors:
        vid = v["vendor_id"]
        archetype = v["archetype"]
        traj = trajectories_by_id[vid]
        cps = traj["change_points"]

        runway = int(rng.integers(params.INITIAL_RUNWAY_RANGE[0],
                                   params.INITIAL_RUNWAY_RANGE[1] + 1))
        cooldown = 0
        consec_neg = 0
        alive = True
        shutdown_qi = None
        shutdown_month = None
        acquired_qi = None

        for i in range(n):
            if not alive:
                break
            t = i + 1
            g = traj["truth_growth"][i]
            consec_neg = consec_neg + 1 if g < 0 else 0

            in_acceleration = (archetype == "acceleration" and cps
                                and t > cps[0])
            in_stall_after_growth = (archetype == "stall" and cps
                                      and t > cps[0])

            # 1. funding
            if cooldown > 0:
                cooldown -= 1
                runway -= 1
            else:
                fhaz = (params.FUNDING_HAZARD_ACCELERATION if in_acceleration
                         else params.FUNDING_HAZARD_BASE)
                if rng.random() < fhaz:
                    events.append({"vendor_id": vid, "event_type": "funding",
                                    "quarter": config.QUARTERS[i], "quarter_index": t})
                    runway = int(rng.integers(params.FUNDING_RUNWAY_RESET_RANGE[0],
                                               params.FUNDING_RUNWAY_RESET_RANGE[1] + 1))
                    cooldown = params.FUNDING_COOLDOWN_QUARTERS
                else:
                    runway -= 1

            # 2. acquisition
            amult = 1.0
            if in_acceleration:
                amult *= params.ACQUISITION_HAZARD_ACCEL_MULT
            if in_stall_after_growth:
                amult *= params.ACQUISITION_HAZARD_STALL_AFTER_GROWTH_MULT
            ahaz = params.ACQUISITION_HAZARD_BASE * amult
            acquired_now = False
            if rng.random() < ahaz:
                events.append({"vendor_id": vid, "event_type": "acquisition",
                                "quarter": config.QUARTERS[i], "quarter_index": t})
                acquired_qi = t
                acquired_now = True
                alive = False

            # 3. shutdown (only if not acquired this quarter)
            if not acquired_now and runway < params.SHUTDOWN_RUNWAY_GATE_QUARTERS:
                terminal = (archetype == "wind_down" and len(cps) == 2
                            and t > cps[1])
                if terminal:
                    shaz = params.SHUTDOWN_WIND_DOWN_TERMINAL_HAZARD
                else:
                    extra = max(0, consec_neg - 2) * params.SHUTDOWN_HAZARD_PER_NEG_QUARTER_PP
                    shaz = params.SHUTDOWN_HAZARD_BASE + extra
                if rng.random() < shaz:
                    events.append({"vendor_id": vid, "event_type": "shutdown",
                                    "quarter": config.QUARTERS[i], "quarter_index": t})
                    shutdown_qi = t
                    shutdown_month = config.quarter_months(config.QUARTERS[i])[0]
                    alive = False

        vendor_state[vid] = {
            "acquired_quarter_index": acquired_qi,
            "shutdown_quarter_index": shutdown_qi,
            "shutdown_month": shutdown_month,  # (year, month) tuple or None
        }

    # Disclosed revenues: 60% of acquisitions, truth ARR at close rounded
    # to the nearest $1M (min $1M), dated one quarter after close.
    acquired_ids = sorted([vid for vid, st in vendor_state.items()
                            if st["acquired_quarter_index"] is not None])
    n_disclose = round(len(acquired_ids) * params.DISCLOSURE_RATE)
    disclosures = []
    if acquired_ids and n_disclose > 0:
        chosen = rng.choice(acquired_ids, size=min(n_disclose, len(acquired_ids)),
                              replace=False)
        for vid in sorted(chosen.tolist()):
            st = vendor_state[vid]
            qi = st["acquired_quarter_index"]
            disclosed_qi = qi + params.DISCLOSURE_LAG_QUARTERS
            if disclosed_qi > n:
                continue
            arr_at_close = trajectories_by_id[vid]["truth_arr"][qi - 1]
            disclosed_val = max(1.0, round(arr_at_close))
            disclosures.append({
                "vendor_id": vid,
                "quarter": config.QUARTERS[disclosed_qi - 1],
                "disclosed_revenue_m": disclosed_val,
            })

    return events, disclosures, vendor_state
