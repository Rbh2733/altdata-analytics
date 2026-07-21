/*
    Test: Total streams consistency across layers
    
    Business rule: The sum of streams at the track level (staging)
    should equal the sum at the artist level (intermediate) which
    should equal the sum at the label level (intermediate).
    
    Discrepancies indicate aggregation errors or data loss between layers.
    
    Returns: A row if layer totals don't match (should be zero rows)
*/

with staging_total as (
    select sum(stream_count) as total_streams
    from {{ ref('stg_streaming_tracks') }}
),

artist_total as (
    select sum(total_streams) as total_streams
    from {{ ref('int_artist_metrics') }}
),

label_total as (
    select sum(total_streams) as total_streams
    from {{ ref('int_label_catalog') }}
),

genre_total as (
    select sum(total_streams) as total_streams
    from {{ ref('int_genre_performance') }}
)

select
    'staging_vs_artist' as comparison,
    s.total_streams as staging_streams,
    a.total_streams as aggregated_streams,
    s.total_streams - a.total_streams as difference
from staging_total s
cross join artist_total a
where s.total_streams != a.total_streams

union all

select
    'staging_vs_label' as comparison,
    s.total_streams as staging_streams,
    l.total_streams as aggregated_streams,
    s.total_streams - l.total_streams as difference
from staging_total s
cross join label_total l
where s.total_streams != l.total_streams

union all

select
    'staging_vs_genre' as comparison,
    s.total_streams as staging_streams,
    g.total_streams as aggregated_streams,
    s.total_streams - g.total_streams as difference
from staging_total s
cross join genre_total g
where s.total_streams != g.total_streams
