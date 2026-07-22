"""All world parameters and planted-pathology specs.

This module is imported nowhere outside simulation/ (a test enforces it
with an AST walk). Everything the shop is supposed to discover rather
than be told lives here: plant magnitudes, archetype hazards, coverage
functions. config.py holds only the seed, calendar, and paths, which is
why it is safe for every layer to import.
"""

# ---------------------------------------------------------------------------
# 1. Population
# ---------------------------------------------------------------------------

SEGMENT_COUNTS = {
    "devtools": 90,
    "data_infrastructure": 85,
    "ai_applications": 95,
    "security": 70,
    "vertical_saas": 80,
    # Six-segment expansion (2026-07-22): AI infrastructure split out of the
    # generic AI bucket as its own archetype. Deliberately the smallest
    # segment: the infrastructure layer is more concentrated than the
    # application layer it serves.
    "ai_infrastructure": 60,
}

# Median initial ARR ($M), lognormal sigma (natural log), floor/cap ($M).
ARR_MEDIAN_M = 6.0
ARR_SIGMA = 1.1
ARR_FLOOR_M = 0.3
ARR_CAP_M = 400.0

# Revenue-per-employee ($) drawn once per segment, uniform low/high.
REV_PER_EMPLOYEE_RANGE = (180_000, 320_000)
HEADCOUNT_JITTER_SIGMA = 0.25  # per-vendor lognormal jitter on implied headcount

# ---------------------------------------------------------------------------
# 2. Archetypes and latent health
# ---------------------------------------------------------------------------

ARCHETYPE_MIX = {
    "steady_growth": 0.40,
    "acceleration": 0.20,
    "stall": 0.20,
    "decline": 0.12,
    "wind_down": 0.08,
}

# QoQ growth regimes (fractional, e.g. 0.04 = 4%), sampled uniform per vendor
# within the ranges below. "start"/"end" describe the regime before/after
# the (single) change point; wind_down gets a second, steeper change point.
ARCHETYPE_GROWTH = {
    "steady_growth": {"start": (0.04, 0.10), "end": None},
    "acceleration": {"start": (0.02, 0.06), "end": (0.12, 0.25)},
    "stall": {"start": (0.08, 0.18), "end": (-0.02, 0.02)},
    "decline": {"start": (0.00, 0.05), "end": (-0.12, -0.05)},
    "wind_down": {"start": (0.00, 0.05), "mid": (-0.12, -0.05), "end": (-0.35, -0.20)},
}

CHANGE_POINT_QUARTER_RANGE = (3, 9)  # uniform int, inclusive, 1-based quarter index
WIND_DOWN_SECOND_POINT_GAP = (2, 4)  # quarters after first change point

AR1_PHI = 0.5
AR1_INNOVATION_SIGMA_PP = 2.0  # percentage points of QoQ growth

INFLECTION_MIN_DELTA_PP = 8.0  # |regime delta| >= 8pp to emit a labeled inflection

# ---------------------------------------------------------------------------
# 3. Truth chain (hiring leads revenue by construction)
# ---------------------------------------------------------------------------

HIRING_ELASTICITY = 1.2
REPLACEMENT_CHURN_PER_QUARTER = 0.045
HEADCOUNT_DECLINE_LAG_QUARTERS = 1   # declines shrink headcount one quarter late
ARR_S_RAMP = (1.0 / 3.0, 2.0 / 3.0)  # fraction of regime delta realized at t+1, t+2

# ---------------------------------------------------------------------------
# 4. Outcome events (truth, judge-only)
# ---------------------------------------------------------------------------

FUNDING_HAZARD_BASE = 0.025
FUNDING_HAZARD_ACCELERATION = 0.12
FUNDING_COOLDOWN_QUARTERS = 4
FUNDING_RUNWAY_RESET_RANGE = (8, 14)  # quarters of runway granted at a round

SHUTDOWN_HAZARD_BASE = 0.001
SHUTDOWN_HAZARD_PER_NEG_QUARTER_PP = 0.04  # added per consecutive negative
                                            # quarter beyond the second
SHUTDOWN_RUNWAY_GATE_QUARTERS = 3
SHUTDOWN_WIND_DOWN_TERMINAL_HAZARD = 0.35  # steep terminal hazard, wind_down only

ACQUISITION_HAZARD_BASE = 0.008
ACQUISITION_HAZARD_ACCEL_MULT = 2.0
ACQUISITION_HAZARD_STALL_AFTER_GROWTH_MULT = 2.0

DISCLOSURE_RATE = 0.60          # share of acquisitions with a disclosed price
DISCLOSURE_LAG_QUARTERS = 1
MIN_DISCLOSURES = 6             # redraw seed if the frozen seed yields fewer

INITIAL_RUNWAY_RANGE = (6, 16)  # quarters, drawn at vendor creation

# ---------------------------------------------------------------------------
# 5. Exhaust: job postings
# ---------------------------------------------------------------------------

JOBS_FILL_TIME_DAYS = (30, 90)
# Logistic tracking-probability curve in log(headcount), fit so p(hc=40)=0.5
# and p(hc=200)=0.9; p(hc=15) then falls out at ~0.21, close to the ~0.25
# design target (the README reports the measured coverage this produces).
JOBS_TRACK_LOGISTIC_MIDPOINT_LOG_HC = 3.688879454113936   # ln(40)
JOBS_TRACK_LOGISTIC_SCALE = 0.732519
JOBS_RELIST_BACKGROUND_RATE = 0.03  # legitimate re-lists: same title, new id, next Q

JOB_FUNCTION_MIX = {
    "devtools": {"engineering": 0.55, "sales": 0.15, "support": 0.15, "other": 0.15},
    "data_infrastructure": {"engineering": 0.60, "sales": 0.12, "support": 0.13, "other": 0.15},
    "ai_applications": {"engineering": 0.50, "sales": 0.18, "support": 0.17, "other": 0.15},
    "security": {"engineering": 0.35, "sales": 0.30, "support": 0.20, "other": 0.15},
    "vertical_saas": {"engineering": 0.35, "sales": 0.25, "support": 0.25, "other": 0.15},
    # ai_infrastructure is the only segment whose postings draw on the
    # ml_infrastructure and research title categories: cluster/GPU
    # operations and applied research hiring is the visible face of a
    # capex-cycle build-out, while the sales and support motions stay
    # thin (enterprise contracts, no mass consumer support surface).
    "ai_infrastructure": {"engineering": 0.25, "ml_infrastructure": 0.30,
                           "research": 0.15, "sales": 0.10, "support": 0.05,
                           "other": 0.15},
}
JOB_AMBIGUOUS_TITLE_RATE = 0.08  # share of postings drawn from the ambiguous pool

# ---------------------------------------------------------------------------
# 6. Exhaust: web traffic
# ---------------------------------------------------------------------------

WEB_COVERAGE_RATE = 0.90               # missing 10% skews smallest
WEB_USAGE_EXPONENT = 0.9
WEB_LEVEL_BIAS_SIGMA = 0.5             # lognormal, constant per vendor forever
WEB_MONTHLY_NOISE_SIGMA = 0.18
WEB_SEASONAL_AMPLITUDE = 0.05

SEGMENT_TRAFFIC_CONSTANT = {
    "devtools": 900.0,
    "data_infrastructure": 500.0,
    "ai_applications": 1400.0,
    "security": 400.0,
    "vertical_saas": 700.0,
    "ai_infrastructure": 300.0,  # B2B, no consumer product surface
}

# Per-segment web-coverage and web-noise overrides (six-segment expansion).
# ai_infrastructure's product surface is an API and a cluster, not a
# website: the traffic panel misses roughly half the segment outright
# (extra missing probability on top of the size skew), and what traffic
# does exist (docs, careers, marketing) is only loosely coupled to actual
# usage, hence the roughly doubled monthly noise sigma. Segments not
# listed here keep the global behavior.
WEB_SEGMENT_MISSING_EXTRA = {
    "ai_infrastructure": 0.45,
}
WEB_SEGMENT_NOISE_SIGMA = {
    "ai_infrastructure": 0.35,
}

# ---------------------------------------------------------------------------
# 7. Exhaust: customer spend panel
# ---------------------------------------------------------------------------

SPEND_CHANNEL_PROB = {
    "devtools": 0.65,
    "ai_applications": 0.45,
    "vertical_saas": 0.35,
    "security": 0.15,
    "data_infrastructure": 0.12,
    # Below even data_infrastructure: AI infrastructure sells into capex
    # cycles through enterprise, invoice-billed contracts. A card-panel
    # rail almost never sees one of these vendors at all.
    "ai_infrastructure": 0.05,
}
SPEND_PANEL_SHARE_RANGE = (0.01, 0.03)     # per-vendor panelist thinning share
SPEND_GROWTH_NOISE_REL = (0.05, 0.08)      # relative error band on growth
SPEND_PUBLICATION_LAG_MONTHS = 1
SPEND_PRESENCE_MIN_TXN_TRAILING_2Q = 8
SPEND_DESCRIPTORS_PER_VENDOR = (1, 2)

SPEND_PANELIST_POOL_SIZE = 4000
SPEND_PANELISTS_PER_VENDOR_SCALE = 3000  # panelist_count = round(panel_share * scale)
SPEND_AVG_AMOUNT_MEDIAN = 180.0
SPEND_AVG_AMOUNT_SIGMA = 0.5
SPEND_AVG_AMOUNT_FLOOR = 15.0
SPEND_AVG_AMOUNT_CAP = 3000.0
SPEND_TXN_AMOUNT_JITTER_SIGMA = 0.4

# ---------------------------------------------------------------------------
# 8. Planted pathologies
# ---------------------------------------------------------------------------

PLANT_BOT_SPIKE = {
    "segment": "devtools",
    "quarter": "2024Q2",
    "weeks": 5,
    "multiplier": 6.0,
}

PLANT_REPOST_STORM = {
    "segment": "security",
    "quarters": ["2024Q3", "2024Q4"],
    "relist_period_days": (14, 21),
    "raw_multiplier": 5.0,
}

PLANT_DESCRIPTOR_FRAGMENTATION = {
    "segment": "vertical_saas",
    "quarter": "2025Q1",
    "fade_weeks": 3,
    "n_new_descriptors": 2,
}

PLANT_COVERAGE_CLIFF = {
    "segment": "ai_applications",
    "quarters": ["2025Q2", "2025Q3"],
}

# ---------------------------------------------------------------------------
# 9. Names
# ---------------------------------------------------------------------------

NAME_PREFIXES = [
    "Vector", "Nimbus", "Cascade", "Ledger", "Quartz", "Fable", "Beacon",
    "Anchor", "Delta", "Lumen", "Ridge", "Solace", "Trellis", "Wren",
    "Harbor", "Kestrel", "Meridian", "Pinecone", "Rivet", "Sable",
    "Thistle", "Vantage", "Amber", "Basalt", "Corbel", "Drift", "Ember",
    "Frost", "Glade", "Hollow", "Ivory", "Juniper", "Kite", "Loom",
    "Marrow", "Nettle", "Onyx", "Pallet", "Quill", "Rowan", "Slate",
    "Timbre", "Umber", "Verve", "Willow", "Xylo", "Yarrow", "Zephyr",
    "Argon", "Birch", "Cinder", "Dapple", "Elm", "Flint", "Gable",
    "Heron", "Iris", "Jasper", "Kelp", "Larch", "Moss", "North",
]

NAME_SUFFIXES = [
    "ly", "io", "hub", "base", "labs", "works", "stack", "path", "grid",
    "loop", "forge", "sync", "wave", "fold", "point", "trail", "span",
    "core", "field", "gate", "line", "mark", "node", "peak", "rise",
    "well", "yard", "zone", "bay", "cove", "deep", "edge", "flow",
]
