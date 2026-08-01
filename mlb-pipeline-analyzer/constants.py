"""Every constant in the readiness chain, pinned with its provenance.

House rule: a number is either cited to a published source, derived live
from the data with the method stated, or labeled in-house with its
rationale. Nothing in this file is a silent guess. Full sourcing narrative:
the readiness-calculation spec that accompanies this project (private,
Career/mlb-pipeline-analyzer-readiness-calculation-2026-08-01.md).
"""

# --------------------------------------------------------------------------
# Level translation factors, run-denominated.
# Primary source: Clay Davenport's league difficulty ratings
# (claydavenport.com/archives/377), leagues collapsed to levels by simple
# average. Corroborated independently by Szymborski's canonical MLE method
# (AAA 0.82, Baseball Think Factory via the Internet Archive, lineage to
# Bill James' 1985 Abstract), Hall of Miller and Eric runs-created haircuts
# (AAA 0.800, AA 0.720), and Rosenblum's published worked example (0.825 at
# AAA in wOBA terms). Davenport's 2025 same-season AAA/MLB study (2021-2025
# data) confirms the AAA magnitude still holds.
# Short-season (sport 15) and Rookie/complex (sport 16) come from the same
# Davenport table (NY-Penn .406 / Northwest .387; GCL .338 / Arizona .333).
# Keyed by MLB Stats API sportId: 11 AAA, 12 AA, 13 High-A, 14 Single-A,
# 15 Short-season A (defunct after 2020), 16 Rookie/complex.
TRANSLATION_FACTORS = {
    11: 0.78,
    12: 0.68,
    13: 0.58,
    14: 0.49,
    15: 0.40,
    16: 0.34,
}

# Davenport's scale is NL = 1.000 with the AL at 1.107. Dividing the level
# factors by ~1.05 restates them against a blended-MLB baseline. Ships as a
# sensitivity column, never silently applied.
BLENDED_SCALE_DIVISOR = 1.05

# --------------------------------------------------------------------------
# Age credit, the Stoltz equivalence. Nathaniel Stoltz, "Quantifying Age
# Relative to Level" (Excessive Prospect Analysis, 2022), regressions of MLB
# attainment on age and same-season production, 2006-2016 minors data.
# Hitters: one year of age carries the predictive weight of ~25 wRC+ points
# (23.5 at Low-A, 25.5 at High-A, ~25 at Double-A). Pitchers: 1.00 FIP run
# per nine at A-ball, 0.50 at Double-A.
# Triple-A has NO published size anywhere in the research sweep, so it takes
# half the Double-A value, an IN-HOUSE taper justified by KATOH's published
# direction (the age effect shrinks as level rises) and Davenport's 2025 AAA
# age split (~3 EqA points per year, small but real). Short-season and
# Rookie take the Low-A value, in-house, same direction rationale.
AGE_WRC_POINTS_PER_YEAR = {
    11: 12.5,   # in-house taper: half of AA
    12: 25.0,   # Stoltz, Double-A
    13: 25.5,   # Stoltz, High-A
    14: 23.5,   # Stoltz, Low-A
    15: 23.5,   # in-house: Low-A value extended down
    16: 23.5,   # in-house: Low-A value extended down
}
AGE_FIP_RUNS_PER_YEAR = {
    11: 0.25,   # in-house taper: half of AA
    12: 0.50,   # Stoltz, Double-A
    13: 1.00,   # Stoltz, A-ball
    14: 1.00,   # Stoltz, A-ball
    15: 1.00,   # in-house: A-ball value extended down
    16: 1.00,   # in-house: A-ball value extended down
}
# Cap the credit at +/- 3 years to stay inside the source regressions'
# observed range.
AGE_CAP_YEARS = 3.0
# Age is measured at July 1 of the season, against the level's average age
# measured from that season's actual rosters.
AGE_REF_MONTH, AGE_REF_DAY = 7, 1

# --------------------------------------------------------------------------
# wOBA linear weights, FanGraphs 2023 season constants. Disclosed
# approximation: one MLB-season weight set applied across minor-league
# environments and seasons.
# CORRECTION 2026-08-01, found by adversarial review: the scale originally
# shipped as 1.157, which is the 2019 FanGraphs wOBAScale, under a comment
# claiming 2023. The 2023 value is 1.204 (FanGraphs Guts table, verified
# live). Fixed the same day, logged in the spec's correction log.
WOBA_WEIGHTS = {
    "bb": 0.696, "hbp": 0.726, "s1": 0.883,
    "s2": 1.244, "s3": 1.569, "hr": 2.004,
}
WOBA_SCALE = 1.204

# Stolen-base run values, standard published convention.
SB_RUNS = 0.20
CS_RUNS = -0.41

# --------------------------------------------------------------------------
# Replacement offset: 20.5 runs per 600 PA below average, the published
# FanGraphs unified-replacement convention for position players. Applied to
# pitchers per 600 batters faced as an IN-HOUSE symmetry choice, disclosed.
REPLACEMENT_RUNS_PER_600 = 20.5

# Positional adjustment, standard published convention, runs per 162 games.
# POSITION SOURCE (corrected 2026-08-01 after adversarial review): the
# adjustment uses the position printed on the player's earliest ranking-list
# row, NOT the API's current label. The API serves today's position even in
# historical payloads, so a post-debut conversion (MJ Melendez, a minors
# catcher relabeled DH today) would rewrite pre-debut stints retroactively.
# The list position is what the ranker saw, pre-debut by construction.
# The cost is coarse buckets: "INF" (average of 2B/3B/SS, in-house) and
# "OF" (average of LF/CF/RF, in-house). Unknown or utility positions get
# zero, disclosed rather than guessed.
POSITION_ADJ_PER_162 = {
    "C": 12.5, "SS": 7.5, "2B": 2.5, "3B": 2.5, "CF": 2.5,
    "INF": 4.2, "OF": -4.2, "LF": -7.5, "RF": -7.5, "1B": -12.5, "DH": -17.5,
}

RUNS_PER_WIN = 10.0

# --------------------------------------------------------------------------
# Sample minimums, house discipline: no reading on a handful of PA.
# A stint below the stint minimum contributes nothing and is reported as
# insufficient with its count. A season rate reading below the rate minimum
# is refused with its count.
MIN_STINT_PA = 40
MIN_STINT_BF = 60
MIN_RATE_PA = 100
MIN_RATE_BF = 100

MINOR_SPORT_IDS = [11, 12, 13, 14, 15, 16]
SPORT_LABELS = {1: "MLB", 11: "AAA", 12: "AA", 13: "A+", 14: "A",
                15: "SS-A", 16: "ROK"}
