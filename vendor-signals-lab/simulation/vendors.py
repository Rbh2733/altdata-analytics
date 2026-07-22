"""Vendor directory: names, segments, sizes, archetype assignment."""

import numpy as np

import config
from simulation import params


def _make_name(rng: np.random.Generator, used: set) -> str:
    for _ in range(200):
        name = rng.choice(params.NAME_PREFIXES) + rng.choice(params.NAME_SUFFIXES)
        if name not in used:
            used.add(name)
            return name
    raise RuntimeError("name space exhausted")


def build_vendors(rng: np.random.Generator) -> list:
    """Returns a list of vendor dicts: vendor_id, name, segment, archetype,
    initial_arr_m, initial_headcount, rev_per_employee."""
    vendors = []
    used_names = set()
    vendor_idx = 0

    # revenue-per-employee drawn once per segment
    rev_per_emp = {}
    for seg in config.SEGMENTS:
        lo, hi = params.REV_PER_EMPLOYEE_RANGE
        rev_per_emp[seg] = rng.uniform(lo, hi)

    archetypes = list(params.ARCHETYPE_MIX.keys())
    archetype_p = list(params.ARCHETYPE_MIX.values())

    for seg in config.SEGMENTS:
        n = params.SEGMENT_COUNTS[seg]
        for _ in range(n):
            vendor_idx += 1
            vendor_id = f"V{vendor_idx:04d}"
            name = _make_name(rng, used_names)
            archetype = rng.choice(archetypes, p=archetype_p)

            arr_m = float(np.clip(
                rng.lognormal(np.log(params.ARR_MEDIAN_M), params.ARR_SIGMA),
                params.ARR_FLOOR_M, params.ARR_CAP_M))
            implied_hc = (arr_m * 1_000_000) / rev_per_emp[seg]
            jitter = rng.lognormal(0.0, params.HEADCOUNT_JITTER_SIGMA)
            headcount = max(2, round(implied_hc * jitter))

            vendors.append({
                "vendor_id": vendor_id,
                "name": name,
                "segment": seg,
                "archetype": archetype,
                "initial_arr_m": arr_m,
                "initial_headcount": headcount,
                "rev_per_employee": rev_per_emp[seg],
            })
    return vendors
