"""
generate_sample_data.py
-----------------------
Synthesizes three DISPARATE raw sources that mirror a real cross-screen
measurement panel, modeled on the Samba TV JD's own example:

  1. ad_exposure.csv   - "ad exposure files from a publisher"
  2. conversions.csv   - "conversion data from a measurement partner"
  3. panel.csv         - "panel weights from the Samba measurement panel"

The data is intentionally MESSY on purpose, so the notebook's Shape step
has something real to clean:
  - household_id key arrives in inconsistent case + stray whitespace across sources
  - nulls in segment and device fields
  - a few duplicate exposure rows (double-logged impressions)

Causal signal baked in (so the drivers analysis has something true to find):
  - Conversion probability rises with exposure frequency, but with diminishing
    returns past ~4 exposures (frequency saturation).
  - "Streaming-heavy" viewers convert better than "Linear-heavy" at equal frequency.
  - One segment ("Cordcutter_HHI_High") is the strongest converter.

Deterministic via SEED so the proof reproduces identically every run.
"""

import csv
import random
from pathlib import Path

SEED = 42
N_HOUSEHOLDS = 4000
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

random.seed(SEED)

SEGMENTS = [
    "Cordcutter_HHI_High",
    "Cordcutter_HHI_Mid",
    "Bundler_HHI_High",
    "Bundler_HHI_Mid",
    "Linear_Loyalist",
]
SEGMENT_BASE_RATE = {
    "Cordcutter_HHI_High": 0.060,
    "Cordcutter_HHI_Mid": 0.040,
    "Bundler_HHI_High": 0.035,
    "Bundler_HHI_Mid": 0.025,
    "Linear_Loyalist": 0.018,
}
VIEWING = ["Streaming-heavy", "Balanced", "Linear-heavy"]
VIEWING_MULT = {"Streaming-heavy": 1.45, "Balanced": 1.0, "Linear-heavy": 0.7}
DEVICES = ["CTV", "Mobile", "Desktop", "Tablet"]


def messy_key(hid: int) -> str:
    """Return the household id in a deliberately inconsistent surface form."""
    base = f"HH{hid:06d}"
    r = random.random()
    if r < 0.18:
        return base.lower()                 # case drift
    if r < 0.30:
        return f"  {base} "                  # whitespace drift
    return base


# ---- Build the panel universe (the source of truth for who's who) ----
panel_rows = []
hh_segment = {}
hh_viewing = {}
for hid in range(1, N_HOUSEHOLDS + 1):
    seg = random.choice(SEGMENTS)
    view = random.choices(VIEWING, weights=[3, 4, 3])[0]
    hh_segment[hid] = seg
    hh_viewing[hid] = view
    # Panel weight: inverse-propensity style, heavier for under-sampled cells.
    weight = round(random.uniform(0.5, 3.5), 3)
    # ~4% of panel segment labels are missing (real panels have gaps)
    seg_out = "" if random.random() < 0.04 else seg
    panel_rows.append({
        "household_id": f"HH{hid:06d}",   # panel stores the CLEAN canonical key
        "segment": seg_out,
        "viewing_profile": view,
        "panel_weight": weight,
    })

with open(OUT / "panel.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["household_id", "segment", "viewing_profile", "panel_weight"])
    w.writeheader()
    w.writerows(panel_rows)

# ---- Build ad exposure log (publisher-side; messy key, duplicates, nulls) ----
exposure_rows = []
hh_freq = {}
for hid in range(1, N_HOUSEHOLDS + 1):
    # 22% of panel households were never exposed (no row at all)
    if random.random() < 0.22:
        hh_freq[hid] = 0
        continue
    freq = random.choices(range(1, 13), weights=[20, 17, 14, 11, 9, 7, 5, 4, 3, 2, 1, 1])[0]
    hh_freq[hid] = freq
    device = random.choice(DEVICES)
    device_out = "" if random.random() < 0.05 else device   # 5% null device
    exposure_rows.append({
        "household_id": messy_key(hid),
        "campaign_id": "CMP_2026_Q2_AUTO",
        "exposure_frequency": freq,
        "primary_device": device_out,
    })
    # ~3% double-logged impressions (exact duplicate row)
    if random.random() < 0.03:
        exposure_rows.append(dict(exposure_rows[-1]))

random.shuffle(exposure_rows)
with open(OUT / "ad_exposure.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["household_id", "campaign_id", "exposure_frequency", "primary_device"])
    w.writeheader()
    w.writerows(exposure_rows)

# ---- Build conversion events (measurement-partner side; messy key) ----
conversion_rows = []
for hid in range(1, N_HOUSEHOLDS + 1):
    seg = hh_segment[hid]
    view = hh_viewing[hid]
    freq = hh_freq[hid]
    # Saturating response curve: marginal lift per exposure decays.
    # effective exposure pressure ~ log-shaped
    if freq <= 0:
        pressure = 0.0
    else:
        pressure = (1 - 0.78 ** freq)        # 0 -> ~1 as freq grows, diminishing
    p = SEGMENT_BASE_RATE[seg] + 0.22 * pressure * VIEWING_MULT[view]
    p = min(p, 0.97)
    converted = 1 if random.random() < p else 0
    if converted:
        conversion_rows.append({
            "household_id": messy_key(hid),
            "conversion_event": "purchase",
            "conversion_value_usd": round(random.uniform(18, 240), 2),
        })

random.shuffle(conversion_rows)
with open(OUT / "conversions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["household_id", "conversion_event", "conversion_value_usd"])
    w.writeheader()
    w.writerows(conversion_rows)

print(f"panel.csv        rows: {len(panel_rows)}")
print(f"ad_exposure.csv  rows: {len(exposure_rows)} (incl. duplicates)")
print(f"conversions.csv  rows: {len(conversion_rows)}")
print(f"overall raw conversion rate: {len(conversion_rows)/N_HOUSEHOLDS:.3f}")
