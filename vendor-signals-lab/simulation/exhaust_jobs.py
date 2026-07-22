"""Job-posting exhaust: requisitions, coverage skew, title bank, and the
repost-storm plant (P2).

No function column: inferring the function (engineering,
ml_infrastructure, research, sales, support, other) from the title text
is the tagger's job (estimation/tagger_mock.py, estimation/
tagger_claude.py). The ml_infrastructure and research banks only ever
surface through the ai_infrastructure segment's function mix; every
other segment's mix simply does not reference them.
"""

import numpy as np

import config
from simulation import params

TITLE_BANK = {
    "engineering": [
        "Software Engineer", "Senior Software Engineer", "Backend Engineer",
        "Platform Engineer", "Site Reliability Engineer", "Staff Engineer",
        "Engineering Manager", "Frontend Engineer", "Data Engineer",
        "Machine Learning Engineer", "Infrastructure Engineer",
        "Security Engineer", "QA Engineer",
    ],
    "sales": [
        "Account Executive", "Sales Development Representative",
        "Enterprise Account Executive", "Sales Engineer",
        "Regional Sales Manager", "Business Development Representative",
        "Sales Director", "Channel Partner Manager",
    ],
    "support": [
        "Customer Support Specialist", "Technical Support Engineer",
        "Support Team Lead", "Customer Success Manager",
        "Help Desk Analyst", "Implementation Specialist",
    ],
    "other": [
        "Product Manager", "Marketing Manager", "Recruiter",
        "Office Manager", "Financial Analyst", "Operations Manager",
        "General Counsel", "People Operations Partner", "Data Analyst",
    ],
    "ml_infrastructure": [
        "ML Infrastructure Engineer", "Machine Learning Infrastructure Engineer",
        "AI Infrastructure Engineer", "GPU Cluster Engineer",
        "Cluster Operations Engineer", "MLOps Engineer",
        "Distributed Training Engineer", "Inference Platform Engineer",
        "Datacenter Operations Engineer",
    ],
    "research": [
        "Research Scientist", "Applied Research Scientist",
        "AI Research Scientist", "Machine Learning Researcher",
        "Foundation Model Researcher",
    ],
}
# Deliberately ambiguous titles: plausible in more than one function bucket,
# so a keyword tagger's confusion matrix has real off-diagonal mass. The
# last two joined at the six-segment expansion: "ML Platform Engineer"
# carries none of the ml_infrastructure phrase anchors, and "Research
# Engineer" is neither a scientist nor a researcher by keyword, so both
# fall through to the generic engineer rule by construction.
AMBIGUOUS_TITLES = [
    "Solutions Engineer", "Developer Advocate",
    "Support Engineering Manager", "Customer Success Engineer",
    "ML Platform Engineer", "Research Engineer",
]

LOCATIONS = ["remote", "us", "eu", "apac"]


def _tracking_prob(headcount: float) -> float:
    x = (np.log(max(headcount, 1.0)) - params.JOBS_TRACK_LOGISTIC_MIDPOINT_LOG_HC)
    x = x / params.JOBS_TRACK_LOGISTIC_SCALE
    return 1.0 / (1.0 + np.exp(-x))


def _pick_title(segment: str, rng: np.random.Generator) -> str:
    if rng.random() < params.JOB_AMBIGUOUS_TITLE_RATE:
        return rng.choice(AMBIGUOUS_TITLES)
    mix = params.JOB_FUNCTION_MIX[segment]
    funcs = list(mix.keys())
    p = list(mix.values())
    func = rng.choice(funcs, p=p)
    return rng.choice(TITLE_BANK[func])


def _active_months(vendor_id, quarter_idx_1based, vendor_state):
    """Which (year, month) tuples in this quarter the vendor is still
    posting. Full quarter unless a shutdown or acquisition darkens it."""
    q = config.QUARTERS[quarter_idx_1based - 1]
    months = config.quarter_months(q)
    st = vendor_state[vendor_id]
    acq_qi = st["acquired_quarter_index"]
    if acq_qi is not None and quarter_idx_1based > acq_qi:
        return []
    sd_qi = st["shutdown_quarter_index"]
    if sd_qi is not None:
        if quarter_idx_1based > sd_qi:
            return []
        if quarter_idx_1based == sd_qi:
            sd_month = st["shutdown_month"]
            return [m for m in months if m <= sd_month]
    return months


def build_job_postings(vendors, trajectories_by_id, vendor_state, rng,
                        repost_storm_vendor_id=None):
    postings = []
    tracked_rows = []
    posting_seq = 0
    plant = params.PLANT_REPOST_STORM
    storm_quarters = set(plant["quarters"])

    for v in vendors:
        vid = v["vendor_id"]
        traj = trajectories_by_id[vid]
        tracked = bool(rng.random() < _tracking_prob(v["initial_headcount"]))
        # The repost-storm plant needs its vendor in the tracked set; the
        # override happens after the draw so the random stream is
        # identical either way. Disclosed in the README as a generator
        # convenience (the same pattern exhaust_spend.py uses for the
        # fragmentation vendor's channel membership).
        if vid == repost_storm_vendor_id:
            tracked = True
        tracked_rows.append({"vendor_id": vid, "tracked": int(tracked)})
        if not tracked:
            continue

        pending_relists = []  # (title, location, quarter_idx, day_offset_from_qstart)
        for i in range(config.N_QUARTERS):
            t = i + 1
            q = config.QUARTERS[i]
            active_months = _active_months(vid, t, vendor_state)
            if not active_months:
                pending_relists = []
                continue
            frac_active = len(active_months) / 3.0
            n_true = int(round(traj["requisitions_target"][i] * frac_active))

            this_quarter_titles = []
            for _ in range(n_true):
                title = _pick_title(v["segment"], rng)
                loc = rng.choice(LOCATIONS)
                this_quarter_titles.append((title, loc))

            # background legitimate re-lists carried over from last quarter
            for title, loc in pending_relists:
                posting_seq += 1
                month = active_months[int(rng.integers(0, len(active_months)))]
                day = int(rng.integers(1, config.days_in_month(*month) + 1))
                posted = config.date_str(month[0], month[1], day)
                closed = _maybe_close(posted, month, q, rng)
                postings.append({
                    "posting_id": f"P{posting_seq:07d}", "vendor_id": vid,
                    "title": title, "posted_date": posted,
                    "closed_date": closed, "location": loc,
                })
            pending_relists = []

            is_storm = (vid == repost_storm_vendor_id and q in storm_quarters)
            for title, loc in this_quarter_titles:
                posting_seq += 1
                month = active_months[int(rng.integers(0, len(active_months)))]
                day = int(rng.integers(1, config.days_in_month(*month) + 1))
                posted = config.date_str(month[0], month[1], day)
                closed = _maybe_close(posted, month, q, rng)
                postings.append({
                    "posting_id": f"P{posting_seq:07d}", "vendor_id": vid,
                    "title": title, "posted_date": posted,
                    "closed_date": closed, "location": loc,
                })

                if is_storm:
                    # relist the identical requisition every 14-21 days for
                    # the rest of the quarter: raw count ~5x true count.
                    n_extra = max(0, int(round(plant["raw_multiplier"])) - 1)
                    lo, hi = plant["relist_period_days"]
                    cursor_day = day
                    for _ in range(n_extra):
                        cursor_day += int(rng.integers(lo, hi + 1))
                        rel_month, rel_day = _advance(month, cursor_day, q)
                        if rel_month is None:
                            break
                        posting_seq += 1
                        r_posted = config.date_str(rel_month[0], rel_month[1], rel_day)
                        postings.append({
                            "posting_id": f"P{posting_seq:07d}", "vendor_id": vid,
                            "title": title, "posted_date": r_posted,
                            "closed_date": "", "location": loc,
                        })
                elif rng.random() < params.JOBS_RELIST_BACKGROUND_RATE:
                    pending_relists.append((title, loc))

    return postings, tracked_rows


def _advance(month, cursor_day, quarter):
    """Walk cursor_day (counted from the 1st of `month`) forward within
    the same quarter; returns (year, month) tuple and clamped day, or
    (None, None) if it overflows the quarter."""
    months = config.quarter_months(quarter)
    y, m = month
    running = cursor_day
    for cand in months:
        dim = config.days_in_month(*cand)
        if cand == month:
            if running <= dim:
                return cand, running
            running -= dim
            continue
        if cand[0] > y or (cand[0] == y and cand[1] > m):
            if running <= dim:
                return cand, running
            running -= dim
    return None, None


def _maybe_close(posted_date, month, quarter, rng):
    lo, hi = params.JOBS_FILL_TIME_DAYS
    fill = int(rng.integers(lo, hi + 1))
    y, mo, d = (int(x) for x in posted_date.split("-"))
    total_days = d + fill
    cur_y, cur_m = y, mo
    while total_days > config.days_in_month(cur_y, cur_m):
        total_days -= config.days_in_month(cur_y, cur_m)
        cur_m += 1
        if cur_m > 12:
            cur_m = 1
            cur_y += 1
    q_end = config.quarter_end_date(config.QUARTERS[-1])
    closed = config.date_str(cur_y, cur_m, total_days)
    return closed if closed <= q_end else ""
