{{
    config(
        materialized='view'
    )
}}

/*
    Intermediate: Label catalog analysis
    
    Purpose: Aggregate track data to record label grain
    Grain: One row per label
    
    Use cases:
    - Label market share
    - Roster analysis
    - Content strategy comparison
*/

with tracks as (
    select * from {{ ref('stg_streaming_tracks') }}
),

label_aggregates as (
    select
        label,
        
        -- Catalog size
        count(distinct track_id) as catalog_size,
        count(distinct artist_name) as roster_size,
        count(distinct album_name) as album_count,
        
        -- Performance
        sum(stream_count) as total_streams,
        round(avg(popularity), 2) as avg_track_popularity,
        round(avg(stream_count), 0) as avg_streams_per_track,
        max(stream_count) as top_track_streams,
        
        -- Genre strategy
        mode(genre) as primary_genre,
        count(distinct genre) as genre_diversity,
        
        -- Content profile
        round(100.0 * sum(case when is_explicit then 1 else 0 end) / count(*), 1) as explicit_content_pct,
        round(avg(duration_minutes), 2) as avg_track_length_min,
        
        -- Geographic focus
        mode(country) as primary_market,
        count(distinct country) as market_reach,
        
        -- Temporal activity
        min(release_year) as earliest_release,
        max(release_year) as latest_release,
        count(distinct release_year) as active_years
        
    from tracks
    group by label
)

select * from label_aggregates
