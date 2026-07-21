"""Regenerate the committed synthetic fixtures under data/fixtures/.

Every company, value, and date here is fictional and hand-constant: no
randomness, no wall clock, so the fixtures are identical on every run and
the offline pipeline is deterministic end to end. The mess is deliberate
and labeled: each planted case below models a data-quality failure that
real multi-source fundamental feeds produce, and each one must surface in
the disagreement report (tests assert that they do).

Planted cases:
1. ONFD FY2025 revenue, fmp: value delivered 1000x low (a thousands-scaled
   figure passed through as raw dollars). Surfaces as unit_scale_mismatch.
2. NMBW (fiscal year ends January 31): fmp maps fiscal labels to calendar
   years, so every NMBW metric pairs the same label with a window ending a
   month earlier than the filing's. Surfaces as period_misalignment.
3. QNTB FY2024 revenue restated in the FY2025 10-K (gross-versus-net
   presentation change; earnings unchanged). EDGAR and polygon carry the
   restated figure; fmp still carries the pre-restatement value. Surfaces
   as material_divergence.
4. Missing coverage: CNDP FY2025 operating cash flow exists only in EDGAR
   (single_source); HLGR FY2025 diluted eps is absent from fmp; TSSL FY2024
   revenue is absent from EDGAR (unmapped filer tag), leaving that group
   with no regulatory anchor.
5. Small genuine divergences (vendor rounding or collection noise):
   MRHW FY2025 net income, TSSL FY2025 revenue, PLXF FY2025 operating cash
   flow. Surface as minor_divergence. ARBL FY2025 total assets differ by
   under 0.1 percent across sources and stay inside the agreement band, so
   the tolerance is demonstrated in both directions.

Run: python scripts/generate_fixtures.py
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PROJECT_ROOT / "data" / "fixtures"

# ticker, name, cik, jan_fye, shares, rev_fy2025, growth, net_margin,
# asset_mult, ocf_margin
COMPANIES = [
    ("ARBL", "Arborlight Therapeutics, Inc.", 9990001, False, 132_000_000,
     2_054_900_000, 0.09, 0.17, 2.0, 0.24),
    ("CNDP", "Cinderpath Media Group, Inc.", 9990002, False, 88_000_000,
     1_183_500_000, 0.02, 0.04, 1.5, 0.13),
    ("HLGR", "Halcyon Grid Energy, Inc.", 9990003, False, 210_000_000,
     3_612_800_000, 0.04, 0.09, 2.8, 0.22),
    ("MRHW", "Mirevale Homewares, Inc.", 9990004, False, 54_000_000,
     986_700_000, 0.05, 0.07, 1.1, 0.11),
    ("NMBW", "Nimbusware Cloud Corp.", 9990005, True, 118_000_000,
     754_900_000, 0.24, 0.08, 1.9, 0.21),
    ("ONFD", "Orrington Foods Company", 9990006, False, 141_000_000,
     2_847_300_000, 0.03, 0.065, 1.2, 0.10),
    ("PLXF", "Parallax Freight Systems, Inc.", 9990007, False, 164_000_000,
     5_238_100_000, 0.06, 0.05, 1.4, 0.09),
    ("QNTB", "Quantelle Biosciences, Inc.", 9990008, False, 76_000_000,
     1_731_600_000, None, 0.14, 2.2, 0.18),  # FY2024 set explicitly below
    ("TSSL", "Tessellate Systems, Inc.", 9990009, False, 47_000_000,
     612_300_000, 0.31, -0.03, 1.3, 0.06),
    ("VLTX", "Veltrix Instruments, Inc.", 9990010, False, 92_000_000,
     1_920_400_000, 0.07, 0.11, 1.6, 0.15),
]

QNTB_FY2024_REVENUE_RESTATED = 1_412_400_000
QNTB_FY2024_REVENUE_ORIGINAL = 1_538_200_000  # pre-restatement, fmp still has it
NMBW_CALENDAR_WINDOW_FACTOR = 0.984  # fmp's calendar window vs the fiscal window

PERIODS = ["FY2024", "FY2025"]


def r100k(v: float) -> int:
    return int(round(v / 100_000.0) * 100_000)


def windows(jan_fye: bool, fy: int):
    """(start, end) of the fiscal window labeled FY<fy>."""
    if jan_fye:
        return (f"{fy}-02-01", f"{fy + 1}-01-31")
    return (f"{fy}-01-01", f"{fy}-12-31")


def filed_date(jan_fye: bool, fy: int, idx: int) -> str:
    """10-K filing date for fiscal year fy (staggered per company)."""
    if jan_fye:
        return f"{fy + 1}-03-{20 + (idx % 5):02d}"
    return f"{fy + 1}-02-{9 + (idx % 9):02d}"


def base_metrics(company, period):
    """Canonical true values for one company and period."""
    (ticker, _name, _cik, jan_fye, shares, rev25, growth, nm, am, om) = company
    if ticker == "QNTB":
        rev = rev25 if period == "FY2025" else QNTB_FY2024_REVENUE_RESTATED
    else:
        rev = rev25 if period == "FY2025" else r100k(rev25 / (1.0 + growth))
    ni = r100k(rev * nm)
    return {
        "revenue": rev,
        "net_income": ni,
        "eps_diluted": round(ni / shares, 2),
        "total_assets": r100k(rev * am),
        "operating_cash_flow": r100k(rev * om),
    }


def accn(cik: int, fy: int, seq: int) -> str:
    return f"{cik:010d}-{(fy + 1) % 100:02d}-{seq:06d}"


# ---------------------------------------------------------------------------
# EDGAR fixtures
# ---------------------------------------------------------------------------

EDGAR_METRIC_TAGS = {
    "net_income": ("NetIncomeLoss", "USD", False),
    "eps_diluted": ("EarningsPerShareDiluted", "USD/shares", False),
    "total_assets": ("Assets", "USD", True),  # instant fact
    "operating_cash_flow": ("NetCashProvidedByUsedInOperatingActivities",
                            "USD", False),
}


def edgar_fact(company, fy, value, instant, idx, fy_override=None,
               filed_override=None):
    (_t, _n, cik, jan_fye, *_rest) = company
    start, end = windows(jan_fye, fy)
    fact = {} if instant else {"start": start}
    fact["end"] = end
    fact["val"] = value
    fact["accn"] = accn(cik, fy_override if fy_override else fy, idx)
    fact["fy"] = fy_override if fy_override else fy
    fact["fp"] = "FY"
    fact["form"] = "10-K"
    fact["filed"] = filed_override or filed_date(jan_fye, fy, idx)
    return fact


def build_edgar(company, idx):
    (ticker, name, cik, jan_fye, *_rest) = company
    revenue_tag = ("RevenueFromContractWithCustomerExcludingAssessedTax"
                   if ticker == "ARBL" else "Revenues")
    gaap = {}

    # Revenue facts, with the QNTB restatement and the TSSL tag gap.
    rev_facts = []
    for fy in (2024, 2025):
        base = base_metrics(company, f"FY{fy}")
        if ticker == "QNTB" and fy == 2024:
            # Original figure from the FY2024 10-K...
            rev_facts.append(edgar_fact(
                company, 2024, QNTB_FY2024_REVENUE_ORIGINAL, False, idx))
            # ...superseded by the restated comparative in the FY2025 10-K.
            rev_facts.append(edgar_fact(
                company, 2024, QNTB_FY2024_REVENUE_RESTATED, False, idx,
                fy_override=2025,
                filed_override=filed_date(jan_fye, 2025, idx)))
            continue
        if ticker == "TSSL" and fy == 2024:
            continue  # filed under a tag the parser does not map
        rev_facts.append(edgar_fact(company, fy, base["revenue"], False, idx))
    if ticker == "VLTX":
        # One quarterly fact, present to prove the annual filter works.
        rev_facts.append({
            "start": "2025-07-01", "end": "2025-09-30", "val": 489_600_000,
            "accn": accn(cik, 2025, 900), "fy": 2025, "fp": "Q3",
            "form": "10-Q", "filed": "2025-10-28",
        })
    gaap[revenue_tag] = {
        "label": "Revenues",
        "description": "Total revenue recognized during the period.",
        "units": {"USD": rev_facts},
    }

    for metric, (tag, unit, instant) in EDGAR_METRIC_TAGS.items():
        facts = []
        for fy in (2024, 2025):
            base = base_metrics(company, f"FY{fy}")
            facts.append(edgar_fact(company, fy, base[metric], instant, idx))
        gaap[tag] = {
            "label": tag,
            "description": f"Synthetic fixture facts for {tag}.",
            "units": {unit: facts},
        }

    return {"cik": cik, "entityName": name, "facts": {"us-gaap": gaap}}


# ---------------------------------------------------------------------------
# FMP fixtures
# ---------------------------------------------------------------------------


def fmp_windows(company, fy):
    """fmp's window for the label FY<fy>: calendar year for NMBW (the planted
    misalignment), the true fiscal window for everyone else."""
    (ticker, _n, _cik, jan_fye, *_rest) = company
    if ticker == "NMBW":
        return (f"{fy}-01-01", f"{fy}-12-31")
    return windows(jan_fye, fy)


def fmp_values(company, period):
    """fmp's reported values, including every fmp-side planted case."""
    (ticker, _n, _cik, _j, shares, *_rest) = company
    vals = dict(base_metrics(company, period))
    if ticker == "NMBW":
        # Calendar-window collection: every flow metric shifts with the window.
        for k in ("revenue", "net_income", "total_assets", "operating_cash_flow"):
            vals[k] = r100k(vals[k] * NMBW_CALENDAR_WINDOW_FACTOR)
        vals["eps_diluted"] = round(vals["net_income"] / shares, 2)
    if ticker == "ONFD" and period == "FY2025":
        vals["revenue"] = vals["revenue"] // 1000  # dropped thousands scale
    if ticker == "QNTB" and period == "FY2024":
        vals["revenue"] = QNTB_FY2024_REVENUE_ORIGINAL  # stale pre-restatement
    if ticker == "HLGR" and period == "FY2025":
        vals["eps_diluted"] = None
    if ticker == "CNDP" and period == "FY2025":
        vals["operating_cash_flow"] = None
    if ticker == "MRHW" and period == "FY2025":
        vals["net_income"] = 69_400_000  # collection noise vs 69,100,000 filed
    if ticker == "PLXF" and period == "FY2025":
        vals["operating_cash_flow"] = 476_600_000  # vs 471,400,000 filed
    return vals


def build_fmp(company, idx):
    (ticker, _name, cik, jan_fye, *_rest) = company
    income, balance, cash = [], [], []
    for fy in (2025, 2024):  # newest first, matching the live API
        vals = fmp_values(company, f"FY{fy}")
        _start, end = fmp_windows(company, fy)
        filed = filed_date(jan_fye, fy, idx)
        common = {
            "date": end,
            "symbol": ticker,
            "reportedCurrency": "USD",
            "cik": f"{cik:010d}",
            "fillingDate": filed,
            "acceptedDate": f"{filed} 16:30:12",
            "calendarYear": str(fy),
            "period": "FY",
        }
        income.append({**common, "revenue": vals["revenue"],
                       "netIncome": vals["net_income"],
                       "epsdiluted": vals["eps_diluted"]})
        balance.append({**common, "totalAssets": vals["total_assets"]})
        cash.append({**common,
                     "operatingCashFlow": vals["operating_cash_flow"]})
    return {
        "symbol": ticker,
        "income_statement": income,
        "balance_sheet": balance,
        "cash_flow": cash,
    }


# ---------------------------------------------------------------------------
# Polygon fixtures
# ---------------------------------------------------------------------------


def polygon_values(company, period):
    """polygon's reported values, including every polygon-side planted case."""
    ticker = company[0]
    vals = dict(base_metrics(company, period))
    if ticker == "QNTB" and period == "FY2024":
        vals["revenue"] = QNTB_FY2024_REVENUE_RESTATED  # vendor caught the update
    if ticker == "MRHW" and period == "FY2025":
        vals["net_income"] = 68_900_000
    if ticker == "TSSL" and period == "FY2025":
        vals["revenue"] = 607_400_000  # vs 612,300,000 filed
    if ticker == "ARBL" and period == "FY2025":
        vals["total_assets"] = 4_105_700_000  # 0.1 percent off; stays agreement
    if ticker == "CNDP" and period == "FY2025":
        vals["operating_cash_flow"] = None  # statement section missing
    return vals


def _pg_item(value, unit, label, order):
    return {"value": value, "unit": unit, "label": label, "order": order}


def build_polygon(company, idx):
    (ticker, name, cik, jan_fye, *_rest) = company
    results = []
    for fy in (2025, 2024):  # newest first
        vals = polygon_values(company, f"FY{fy}")
        start, end = windows(jan_fye, fy)
        financials = {
            "income_statement": {
                "revenues": _pg_item(vals["revenue"], "USD", "Revenues", 100),
                "net_income_loss": _pg_item(
                    vals["net_income"], "USD", "Net Income/Loss", 3200),
                "diluted_earnings_per_share": _pg_item(
                    vals["eps_diluted"], "USD / shares",
                    "Diluted Earnings Per Share", 4300),
            },
            "balance_sheet": {
                "assets": _pg_item(vals["total_assets"], "USD", "Assets", 100),
            },
            "cash_flow_statement": {
                "net_cash_flow_from_operating_activities": _pg_item(
                    vals["operating_cash_flow"], "USD",
                    "Net Cash Flow From Operating Activities", 100),
            },
        }
        if vals["operating_cash_flow"] is None:
            del financials["cash_flow_statement"]
        results.append({
            "start_date": start,
            "end_date": end,
            "timeframe": "annual",
            "fiscal_period": "FY",
            "fiscal_year": str(fy),
            "cik": f"{cik:010d}",
            "company_name": name,
            "filing_date": filed_date(jan_fye, fy, idx),
            "financials": financials,
        })
    return {"status": "OK", "request_id": "synthetic-fixture", "results": results}


# ---------------------------------------------------------------------------


def write(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def main():
    builders = {"edgar": build_edgar, "fmp": build_fmp, "polygon": build_polygon}
    count = 0
    for source, build in builders.items():
        for idx, company in enumerate(COMPANIES):
            write(FIXTURES / source / f"{company[0]}.json", build(company, idx))
            count += 1
    print(f"wrote {count} fixture files under data/fixtures/ "
          f"({len(COMPANIES)} companies x {len(builders)} sources)")


if __name__ == "__main__":
    main()
