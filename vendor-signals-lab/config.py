"""Shared constants: seed, calendar, paths.

Nothing about the world's behavior, archetypes, or planted pathologies
lives here. Those parameters are in simulation/params.py, which only the
simulation package may import (a test enforces this). This module is
importable by every layer precisely because it contains nothing worth
leaking.
"""

from pathlib import Path

SEED = 11
ROBUSTNESS_SEED = 12

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
EXHAUST_DIR = DATA_DIR / "exhaust"
PUBLIC_DIR = DATA_DIR / "public"
TRUTH_DIR = DATA_DIR / "truth"
OUTPUT_DIR = ROOT / "outputs"

N_VENDORS = 420

# Calendar: 12 quarters, 2023Q1 .. 2025Q4, months as the underlying grain.
START_YEAR = 2023
QUARTERS = [f"{y}Q{q}" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)]
N_QUARTERS = len(QUARTERS)  # 12
WARMUP_QUARTERS = QUARTERS[:2]      # 2023Q1, 2023Q2
SCORED_QUARTERS = QUARTERS[2:]      # 2023Q3 .. 2025Q4 (10 quarters)

SEGMENTS = ["devtools", "data_infrastructure", "ai_applications",
            "security", "vertical_saas"]

_DAYS = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
         7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


def quarter_index(q: str) -> int:
    """0-based index into QUARTERS."""
    return QUARTERS.index(q)


def quarter_months(q: str) -> list:
    """Three 1-based (year, month) tuples for a quarter label."""
    i = quarter_index(q)
    year = START_YEAR + i // 4
    qn = i % 4  # 0..3
    first_month = qn * 3 + 1
    return [(year, first_month), (year, first_month + 1), (year, first_month + 2)]


def month_label(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def days_in_month(year: int, month: int) -> int:
    if month == 2 and year % 4 == 0:
        return 29
    return _DAYS[month]


def date_str(year: int, month: int, day: int) -> str:
    return f"{year}-{month:02d}-{day:02d}"


def quarter_of_date(year: int, month: int) -> str:
    i = (year - START_YEAR) * 4 + (month - 1) // 3
    if i < 0 or i >= N_QUARTERS:
        return None
    return QUARTERS[i]


def next_quarter(q: str, n: int = 1) -> str:
    i = quarter_index(q) + n
    if i < 0 or i >= N_QUARTERS:
        return None
    return QUARTERS[i]


def quarter_end_date(q: str) -> str:
    """Last calendar day of a quarter, as a sortable YYYY-MM-DD string."""
    months = quarter_months(q)
    year, month = months[-1]
    return date_str(year, month, days_in_month(year, month))


def quarter_start_date(q: str) -> str:
    year, month = quarter_months(q)[0]
    return date_str(year, month, 1)


def month_after(year: int, month: int):
    return (year + 1, 1) if month == 12 else (year, month + 1)


def spend_publish_date(year: int, month: int) -> str:
    """First calendar day a transaction dated in (year, month) becomes
    visible, given the one-month spend publication lag."""
    y2, m2 = month_after(year, month)
    return date_str(y2, m2, 1)
