# Fixtures: synthetic, fictional, deliberately messy

Everything under this directory is synthetic. The ten companies are
fictional, their tickers are invented, and every value and date was
hand-set in `scripts/generate_fixtures.py`; any resemblance to a real
company, ticker, or figure is coincidental. No fixture value was taken
from a real filing or a real vendor response.

Each subdirectory holds one payload per company, shaped like the real
source's response format so the normalizers exercise the same parsing they
would use live:

- `edgar/` mirrors the SEC companyfacts JSON (us-gaap tags, unit lists,
  per-filing facts with form, fp, fy, and filed fields).
- `fmp/` mirrors Financial Modeling Prep's v3 statement arrays, bundled
  into one object per company the same way the live client bundles its
  three endpoint calls.
- `polygon/` mirrors Polygon's vX financials response (results list with
  nested statements; every line item carries a value and unit).

## The roster

| Ticker | Company | Fiscal year end |
|---|---|---|
| ARBL | Arborlight Therapeutics, Inc. | Dec 31 |
| CNDP | Cinderpath Media Group, Inc. | Dec 31 |
| HLGR | Halcyon Grid Energy, Inc. | Dec 31 |
| MRHW | Mirevale Homewares, Inc. | Dec 31 |
| NMBW | Nimbusware Cloud Corp. | Jan 31 |
| ONFD | Orrington Foods Company | Dec 31 |
| PLXF | Parallax Freight Systems, Inc. | Dec 31 |
| QNTB | Quantelle Biosciences, Inc. | Dec 31 |
| TSSL | Tessellate Systems, Inc. | Dec 31 |
| VLTX | Veltrix Instruments, Inc. | Dec 31 |

## Planted data-quality cases

The mess is deliberate and labeled; each case models a failure mode real
multi-source fundamental feeds produce, and tests assert that each one
surfaces in the disagreement report:

1. **Dropped scale factor.** ONFD FY2025 revenue arrives from fmp 1000x
   low: a thousands-scaled figure passed through as raw dollars.
2. **Fiscal-versus-calendar windows.** NMBW's fiscal year ends January 31;
   fmp maps its labels to calendar years, so every NMBW group pairs one
   label with two different window end dates.
3. **Restatement lag.** QNTB's FY2024 revenue was restated in the FY2025
   10-K. EDGAR and polygon carry the restated figure; fmp still carries
   the pre-restatement value.
4. **Coverage holes.** CNDP FY2025 operating cash flow exists only in
   EDGAR; HLGR FY2025 diluted eps is missing from fmp; TSSL FY2024 revenue
   is absent from EDGAR (filed under a tag the parser does not map).
5. **Collection noise.** Sub-2-percent divergences on MRHW net income,
   TSSL revenue, and PLXF operating cash flow; plus one sub-0.1-percent
   difference on ARBL total assets that stays inside the agreement band.

Regenerate with `python scripts/generate_fixtures.py` (no randomness, no
wall clock; output is identical on every run).
