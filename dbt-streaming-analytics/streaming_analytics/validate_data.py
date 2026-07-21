"""Streaming-catalog analytics: data validation queries.

Runs analytical spot-checks against the DuckDB database that dbt builds.
Run from this directory, after `dbt build --profiles-dir .`:

    python validate_data.py
"""
import duckdb

conn = duckdb.connect('streaming.duckdb', read_only=True)

def run_query(title, sql):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    results = conn.execute(sql).fetchall()
    columns = [desc[0] for desc in conn.description]

    # Calculate column widths
    widths = [len(col) for col in columns]
    for row in results:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    # Print header
    header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    print(header)
    print("-" * len(header))

    # Print rows
    for row in results:
        print(" | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row)))

# ============================================================
# QUERY 1: Model Row Counts
# ============================================================
run_query("MODEL ROW COUNTS", """
SELECT 'stg_streaming_tracks' as model, count(*) as rows FROM main.stg_streaming_tracks
UNION ALL SELECT 'int_artist_metrics', count(*) FROM main.int_artist_metrics
UNION ALL SELECT 'int_genre_performance', count(*) FROM main.int_genre_performance
UNION ALL SELECT 'int_label_catalog', count(*) FROM main.int_label_catalog
UNION ALL SELECT 'dim_artists', count(*) FROM main.dim_artists
UNION ALL SELECT 'dim_genres', count(*) FROM main.dim_genres
UNION ALL SELECT 'fct_track_performance', count(*) FROM main.fct_track_performance
UNION ALL SELECT 'rpt_label_market_share', count(*) FROM main.rpt_label_market_share
ORDER BY rows DESC
""")

# ============================================================
# QUERY 2: Genre Market Share (Top Analysis)
# ============================================================
run_query("GENRE MARKET SHARE", """
SELECT
    genre,
    total_tracks,
    total_streams,
    stream_market_share_pct,
    stream_rank,
    market_position,
    audio_character
FROM main.dim_genres
ORDER BY stream_rank
""")

# ============================================================
# QUERY 3: Label Market Share & Efficiency
# ============================================================
run_query("LABEL COMPETITIVE ANALYSIS", """
SELECT
    label,
    competitive_tier,
    stream_market_share_pct,
    catalog_size,
    roster_size,
    efficiency_index,
    content_strategy
FROM main.rpt_label_market_share
ORDER BY stream_rank
LIMIT 10
""")

# ============================================================
# QUERY 4: Top Artists by Stream Tier
# ============================================================
run_query("ARTIST DISTRIBUTION BY TIER", """
SELECT
    stream_tier,
    count(*) as artist_count,
    round(100.0 * count(*) / sum(count(*)) over(), 2) as pct_of_artists,
    sum(total_streams) as tier_total_streams
FROM main.dim_artists
GROUP BY stream_tier
ORDER BY
    CASE stream_tier
        WHEN 'Platinum' THEN 1
        WHEN 'Gold' THEN 2
        WHEN 'Silver' THEN 3
        ELSE 4
    END
""")

# ============================================================
# QUERY 5: Track Performance Distribution
# ============================================================
run_query("TRACK PERFORMANCE TIERS", """
SELECT
    performance_tier,
    count(*) as track_count,
    round(avg(stream_count), 0) as avg_streams,
    round(avg(popularity), 1) as avg_popularity
FROM main.fct_track_performance
GROUP BY performance_tier
ORDER BY
    CASE performance_tier
        WHEN 'Viral' THEN 1
        WHEN 'Hit' THEN 2
        WHEN 'Moderate' THEN 3
        ELSE 4
    END
""")

# ============================================================
# QUERY 6: Year-over-Year Release Trends
# ============================================================
run_query("RELEASE VOLUME BY YEAR", """
SELECT
    release_year,
    count(*) as tracks_released,
    count(distinct artist_name) as unique_artists,
    round(avg(popularity), 1) as avg_popularity,
    sum(stream_count) as total_streams
FROM main.stg_streaming_tracks
GROUP BY release_year
ORDER BY release_year
""")

# ============================================================
# QUERY 7: Genre Audio Fingerprints
# ============================================================
run_query("GENRE AUDIO FINGERPRINTS", """
SELECT
    genre,
    round(avg_danceability, 2) as dance,
    round(avg_energy, 2) as energy,
    round(avg_tempo, 0) as tempo,
    round(avg_loudness, 1) as loud_db,
    audio_character
FROM main.dim_genres
ORDER BY avg_energy DESC
""")

# ============================================================
# QUERY 8: Top 10 Artists by Total Streams
# ============================================================
run_query("TOP 10 ARTISTS BY STREAMS", """
SELECT
    artist_name,
    stream_tier,
    total_streams,
    total_tracks,
    avg_popularity,
    primary_genre
FROM main.dim_artists
ORDER BY total_streams DESC
LIMIT 10
""")

# ============================================================
# QUERY 9: Explicit Content by Genre
# ============================================================
run_query("EXPLICIT CONTENT BY GENRE", """
SELECT
    genre,
    content_rating,
    round(explicit_pct, 1) as explicit_pct,
    total_tracks
FROM main.dim_genres
ORDER BY explicit_pct DESC
""")

# ============================================================
# QUERY 10: Cross-Layer Validation (Totals Match)
# ============================================================
run_query("CROSS-LAYER STREAM VALIDATION", """
SELECT
    'stg_streaming_tracks' as layer, sum(stream_count) as total_streams FROM main.stg_streaming_tracks
UNION ALL
SELECT 'int_artist_metrics', sum(total_streams) FROM main.int_artist_metrics
UNION ALL
SELECT 'int_genre_performance', sum(total_streams) FROM main.int_genre_performance
UNION ALL
SELECT 'int_label_catalog', sum(total_streams) FROM main.int_label_catalog
""")

print("\n" + "="*60)
print("  ALL QUERIES COMPLETE")
print("="*60)

conn.close()
