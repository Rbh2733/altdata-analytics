"""Shared constants: seed, calendar, paths, and scale.

Nothing about the world's behavior, biases, or pathologies lives here.
Those parameters are in simulation/params.py, which only the simulation
package may import (a test enforces this). This module is importable by
every layer precisely because it contains nothing worth leaking.
"""

from pathlib import Path

SEED = 11

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PANEL_DIR = DATA_DIR / "panel"
PUBLIC_DIR = DATA_DIR / "public"
TRUTH_DIR = DATA_DIR / "truth"
OUTPUT_DIR = ROOT / "outputs"

# Scale constants (how big, never how it behaves).
N_POP = 200_000
N_MONTHS = 36
PANEL_TARGET = 6_000
BOOTSTRAP_B = 400
CI_LEVEL = 0.90

# Calendar: months 1..36 map to 2022-01 .. 2024-12. Fictional calendar,
# no wall clock anywhere in the output path.
START_YEAR = 2022
QUARTERS = [f"{y}Q{q}" for y in (2022, 2023, 2024) for q in (1, 2, 3, 4)]
WARMUP_QUARTERS = QUARTERS[:4]
SCORED_QUARTERS = QUARTERS[4:]

AGE_BANDS = ["18-29", "30-44", "45-59", "60+"]
INCOME_BANDS = ["low", "mid", "high"]
REGIONS = ["north", "south", "east", "west"]

KPIS = ["revenue", "actives", "gross_adds", "churn_rate", "arpu", "market_share"]

_DAYS = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
         7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}


def month_year(m: int) -> int:
    return START_YEAR + (m - 1) // 12


def month_of_year(m: int) -> int:
    return (m - 1) % 12 + 1


def month_label(m: int) -> str:
    return f"{month_year(m)}-{month_of_year(m):02d}"


def days_in_month(m: int) -> int:
    y, mo = month_year(m), month_of_year(m)
    if mo == 2 and y % 4 == 0:
        return 29
    return _DAYS[mo]


def date_str(m: int, day: int) -> str:
    return f"{month_year(m)}-{month_of_year(m):02d}-{day:02d}"


def quarter_of_month(m: int) -> str:
    return QUARTERS[(m - 1) // 3]


def quarter_index(q: str) -> int:
    """0-based index into QUARTERS."""
    return QUARTERS.index(q)


def quarter_months(q: str) -> list:
    i = quarter_index(q)
    return [3 * i + 1, 3 * i + 2, 3 * i + 3]


def quarter_end_month(q: str) -> int:
    return 3 * (quarter_index(q) + 1)
