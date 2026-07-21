"""Per-source clients. Each returns the source's native payload shape;
normalize.py owns the conversion to the canonical model."""

from .edgar import EdgarClient
from .fmp import FmpClient
from .polygon import PolygonClient

ALL_CLIENTS = [EdgarClient, FmpClient, PolygonClient]
