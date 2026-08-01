"""Paths and API base for mlb-pipeline-analyzer.

Everything is Path(__file__)-relative so the project runs from any checkout
location. No absolute paths, no environment assumptions.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_RAW = ROOT / "data" / "raw"
DATA_CACHE = ROOT / "data" / "cache"
DATA_DERIVED = ROOT / "data" / "derived"
OUTPUTS = ROOT / "outputs"

MLB_STATS_API_BASE = "https://statsapi.mlb.com/api"
