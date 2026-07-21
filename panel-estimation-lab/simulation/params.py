"""Every behavioral, bias, and pathology parameter of the synthetic world.

Only the simulation package imports this module (a test enforces it).
The estimation layer never sees these values; it sees only the panel and
the published public facts. All parameters here were frozen before any
estimator was scored, per the honesty protocol described in the README.
"""

import numpy as np

# ---------------------------------------------------------------- population

# Age x income joint probabilities (rows: 18-29, 30-44, 45-59, 60+;
# cols: low, mid, high). Age mass sits in 30-59, income is a pyramid,
# and age and income are deliberately not independent.
AGE_INCOME_P = np.array([
    [0.13, 0.07, 0.02],
    [0.12, 0.13, 0.07],
    [0.09, 0.12, 0.07],
    [0.08, 0.06, 0.04],
])
REGION_P = np.array([0.30, 0.28, 0.22, 0.20])  # north, south, east, west

FRAILTY_SIGMA = 0.5  # per-person lognormal frailty, shared across services

# Burn-in months simulated before month 1 so the world does not start
# empty: subscriptions have a base, and trailing-12-month purchase
# windows are complete at month 1. Burn-in generates no revenue rows.
BURNIN_MONTHS = 18
ECOM_HISTORY_MONTHS = 12  # purchase-history depth kept during burn-in

# ---------------------------------------------------------------- companies

COMPANIES = ["Streambird", "Aurelo", "Bramblebox", "Pinefort", "Vantry", "Glimmerly"]
SUB_COMPANIES = ["Streambird", "Aurelo", "Bramblebox", "Pinefort"]
ECOM_COMPANIES = ["Vantry", "Glimmerly"]

CATEGORY = {
    "Streambird": "video_streaming",
    "Aurelo": "music_streaming",
    "Bramblebox": "meal_kits",
    "Pinefort": "retail_membership",
    "Vantry": "marketplace",
    "Glimmerly": "fashion_ecom",
}

BASE_DESCRIPTOR = {
    "Streambird": "STREAMBIRD.COM",
    "Aurelo": "AURELO MUSIC",
    "Bramblebox": "BRAMBLEBOX",
    "Pinefort": "PINEFORT CLUB",
    "Vantry": "VANTRY MKTPLC",
    "Glimmerly": "GLIMMERLY",
}

# Out-of-scope merchant: real panels contain spend the shop does not
# cover. It also serves as the control descriptor that the alias
# detector must NOT merge onto any covered company.
NOISE_DESCRIPTOR = "SNACKPOST MARKET"
NOISE_LAMBDA = 0.32            # purchases per panelist-month
NOISE_AMOUNT_MU = 2.75         # lognormal, mean about 18
NOISE_AMOUNT_SIGMA = 0.55

# ------------------------------------------------------- subscription model

SUB_PRICE = {
    "Streambird": 11.99,   # rises to 13.99 at PRICE_EVENT_MONTH
    "Aurelo": 10.99,
    "Bramblebox": 59.99,
    "Pinefort": 14.99,
}
PRICE_EVENT_COMPANY = "Streambird"
PRICE_EVENT_MONTH = 31         # 2024-07, start of 2024Q3
PRICE_EVENT_NEW_PRICE = 13.99
PRICE_EVENT_CHURN_MULT = 1.6   # churn hazard multiplier, months 31-32
PRICE_EVENT_CHURN_MONTHS = (31, 32)

# Monthly adoption hazard for a non-customer:
#   h_a = SUB_BASE_ADOPT * age_mult * income_mult * frailty * trend(m)
# Base rates were tuned (before the freeze) so month-36 penetration lands
# near: Streambird 22%, Aurelo 15%, Bramblebox 6%, Pinefort 12%.
SUB_BASE_ADOPT = {
    "Streambird": 0.0085,
    "Aurelo": 0.0063,
    "Bramblebox": 0.0038,
    "Pinefort": 0.0031,
}

# Demographic signatures (age order 18-29, 30-44, 45-59, 60+; income order
# low, mid, high). These are what make composition bias bite differently
# by company.
SUB_ADOPT_AGE_MULT = {
    "Streambird": [1.25, 1.15, 0.95, 0.65],
    "Aurelo": [1.90, 1.20, 0.60, 0.30],
    "Bramblebox": [1.60, 1.40, 0.70, 0.30],
    "Pinefort": [0.60, 1.30, 1.30, 0.80],
}
SUB_ADOPT_INCOME_MULT = {
    "Streambird": [0.85, 1.05, 1.25],
    "Aurelo": [0.95, 1.00, 1.15],
    "Bramblebox": [0.45, 1.00, 2.10],
    "Pinefort": [0.70, 1.30, 1.10],
}

# Adoption trend over months 1..36 (linear ramp endpoints; burn-in months
# use the month-1 value).
SUB_TREND = {
    "Streambird": (1.00, 1.30),   # steady grower
    "Aurelo": (1.00, 0.70),       # mature, slowly fading adoption
    "Bramblebox": (0.60, 2.20),   # fast grower
    "Pinefort": (1.00, 1.05),     # steady
}

# Monthly churn hazard per subscriber:
#   h_c = SUB_BASE_CHURN * churn_age_mult * tenure_mult * event_mult
SUB_BASE_CHURN = {
    "Streambird": 0.030,
    "Aurelo": 0.025,
    "Bramblebox": 0.090,
    "Pinefort": 0.015,
}
SUB_CHURN_AGE_MULT = {
    "Streambird": [1.20, 1.00, 0.90, 0.95],
    "Aurelo": [1.25, 1.00, 0.85, 0.90],
    "Bramblebox": [1.15, 1.00, 0.95, 1.00],
    "Pinefort": [1.20, 0.95, 0.90, 1.00],
}
# Tenure multiplier: months 1-2 fragile, settling to loyal by month 12+.
TENURE_MULT_EARLY = 1.5    # tenure 1-2
TENURE_MULT_MID = 1.0      # tenure 3-11
TENURE_MULT_LATE = 0.7     # tenure 12+

# Lapsed customers carry a winback adoption multiplier for 6 months.
WINBACK_MULT = 2.0
WINBACK_MONTHS = 6

# ---------------------------------------------------------- e-commerce model

# Not everyone shops a given marketplace. A fixed per-person gate (drawn
# once, demographically tilted) marks who is a potential customer; only
# gated persons purchase. Monthly purchase count for gated persons is
# Poisson(lambda), lambda = base * frailty * trend * seasonal. The
# demographic signature lives in the gate, which is what makes
# penetration-by-segment analysis non-trivial.
ECOM_LAMBDA_CAP = 12.0

ECOM_GATE_BASE = {
    "Vantry": 0.38,
    "Glimmerly": 0.20,
}
ECOM_BASE_LAMBDA = {
    "Vantry": 1.55,
    "Glimmerly": 1.20,
}
# Per-person purchase-intensity factor among gated customers,
# Gamma(shape, scale=1/shape), mean 1. The low-intensity tail is what
# gives the trailing-12-month active definition real turnover; without
# it, habitual buyers saturate the window and churn collapses to zero.
ECOM_GAMMA_SHAPE = 0.7
ECOM_AGE_MULT = {
    "Vantry": [1.15, 1.20, 1.00, 0.60],
    "Glimmerly": [1.80, 1.30, 0.60, 0.25],
}
ECOM_INCOME_MULT = {
    "Vantry": [0.80, 1.05, 1.40],
    "Glimmerly": [0.70, 1.05, 1.75],
}
ECOM_TREND = {
    "Vantry": (0.85, 1.35),      # grower
    "Glimmerly": (1.00, 1.00),   # flat trend; promos do the moving
}
# Vantry Q4 seasonality: lambda multiplier in months 10, 11, 12 of each year.
VANTRY_Q4_MULT = 1.5
# Vantry promo day: extra lambda in 2023-08 (month 20), with purchase dates
# concentrated on day 14. This is the high-volume day the duplicated-feed
# pathology lands on.
VANTRY_PROMO_MONTH = 20
VANTRY_PROMO_LAMBDA_MULT = 1.30
VANTRY_PROMO_DAY = 14
VANTRY_PROMO_DAY_SHARE = 0.30  # share of that month's purchases on the promo day

# Glimmerly monthly promo multipliers, months 1..36. Drawn once during
# design and committed as literals so the world is fully frozen.
GLIMMERLY_PROMO_MULT = [
    1.05, 0.88, 1.32, 0.95, 1.10, 0.82, 1.45, 1.02, 0.90, 1.25, 1.60, 1.15,
    0.85, 1.08, 1.38, 0.92, 1.20, 0.86, 1.52, 1.00, 0.94, 1.30, 1.72, 1.18,
    0.88, 1.12, 1.42, 0.96, 1.24, 0.90, 1.58, 1.04, 0.98, 1.36, 1.80, 1.22,
]

# Basket amounts, lognormal(mu, sigma), rounded to cents.
ECOM_AMOUNT = {
    "Vantry": (3.21, 0.80),      # mean about 34
    "Glimmerly": (3.815, 0.70),  # mean about 58
}

# Pinefort members also purchase (counts toward Pinefort revenue; Pinefort
# actives remain membership counts).
PINEFORT_PURCHASE_LAMBDA = 2.6
PINEFORT_AMOUNT = (3.63, 0.60)   # mean about 45

# ------------------------------------------------------------- panel biases

# Recruitment skew: inclusion probability proportional to a cell weight.
# Young high-income recruits at roughly 3.3x the rate of 60+ low-income.
RECRUIT_AGE_W = [1.40, 1.15, 0.85, 0.65]
RECRUIT_INCOME_W = [0.85, 1.00, 1.30]

# Monthly attrition hazard by age band, young faster. Average is near 1.0%
# per month, thinning the panel roughly 30% over 36 months absent
# recruitment. (The design intent named both a 2-4% hazard and a 30%
# thinning target, which are mutually inconsistent; the thinning target
# won because it drives the story numbers.)
ATTRITION_BASE = 0.010
ATTRITION_AGE_MULT = [1.35, 1.10, 0.85, 0.70]

# Payment instruments.
INSTRUMENTS = ["card_A", "card_B", "card_C", "wallet_W"]
INSTRUMENT_POPULARITY = np.array([0.34, 0.30, 0.21, 0.15])
HOLDING_COUNT_P = [0.30, 0.45, 0.25]  # P(hold 1 / 2 / 3 instruments)
USAGE_DIRICHLET_CONC = 2.0

# Per-company instrument affinity (multiplies a person's usage mix, then
# renormalized over the instruments the person holds). Glimmerly skews
# hard toward wallet_W.
COMPANY_INSTRUMENT_AFFINITY = {
    "Streambird": [1.0, 1.0, 1.0, 0.35],
    "Aurelo": [1.0, 1.0, 1.0, 0.35],
    "Bramblebox": [1.0, 1.0, 1.0, 0.35],
    "Pinefort": [1.0, 1.0, 1.0, 0.50],
    "Vantry": [1.0, 1.0, 1.0, 1.30],
    "Glimmerly": [0.60, 0.60, 0.60, 4.00],
    "_noise": [1.0, 1.0, 1.0, 1.0],
}

# Panel enrollment of held instruments. Cards enroll at 0.80, the wallet
# at 0.40 (linking a wallet is harder in-world), minimum one enrolled.
# The design intent named a uniform 0.75 and also required wallet_W to
# be the worst-covered slice; a uniform rate cannot produce that, so the
# differential rates below (weighted average near 0.75) implement the
# mechanism that rung 4 is built around.
ENROLL_P_CARD = 0.80
ENROLL_P_WALLET = 0.40

# Heterogeneous observability: per-panelist capture factor.
CAPTURE_BETA = (8.0, 2.0)

# ------------------------------------------------------- planted pathologies

# P1: duplicated feed day. Every panel row dated DUP_DATE appears 3x total.
DUP_DATE = "2023-08-14"
DUP_COPIES = 3

# P2: recruitment wave at month 16 (2023-04), skewed young low-income.
WAVE_MONTH = 16
WAVE_SIZE = 1_500
WAVE_AGE_W = [3.0, 1.5, 0.6, 0.3]
WAVE_INCOME_W = [2.2, 1.0, 0.4]

# P3: supplier outage. card_B rows vanish for 12 consecutive days.
OUTAGE_INSTRUMENT = "card_B"
OUTAGE_START = "2024-02-05"
OUTAGE_END = "2024-02-16"

# P4: merchant descriptor change. Bramblebox's descriptor changes on
# 2024-05-20; the new raw form carries per-row suffix noise.
DESCRIPTOR_CHANGE_COMPANY = "Bramblebox"
DESCRIPTOR_CHANGE_DATE = "2024-05-20"
DESCRIPTOR_CHANGE_NEW = "BRMB*BOX 0520"


def trend_value(endpoints, m, n_months):
    """Linear ramp between endpoints over months 1..n_months; months
    before 1 (burn-in) clamp to the month-1 value."""
    lo, hi = endpoints
    t = min(max(m, 1), n_months)
    return lo + (hi - lo) * (t - 1) / (n_months - 1)
