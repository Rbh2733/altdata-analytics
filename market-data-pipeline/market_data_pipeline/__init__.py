"""market_data_pipeline: multi-source fundamentals with measured disagreement.

Ingest the same fundamental metrics from several sources, normalize to one
canonical model, quantify how much the sources disagree, then resolve each
group through an explicit source-reliability hierarchy. The disagreement
measurement is the product; the resolved table is the byproduct.
"""

__version__ = "1.0.0"
