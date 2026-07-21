{{
    config(
        materialized='table'
    )
}}

/*
    Fact: Track Performance
    
    Grain: One row per track (track_id)
    Purpose: Central fact table for track-level analysis
    
    Design notes:
    - Includes dimension keys for star schema joins
    - Preserves all measures at atomic grain
    - Derived metrics pre-calculated for dashboard performance
    - This is the "widest" table; use it for ad-hoc exploration
*/

with tracks as (
    select * from {{ ref('stg_streaming_tracks') }}
),

-- Get dimension keys for joining
artist_dim as (
    select artist_key, artist_name 
    from {{ ref('dim_artists') }}
),

genre_dim as (
    select genre_key, genre 
    from {{ ref('dim_genres') }}
),

fact_tracks as (
    select
        -- Primary key
        t.track_id,
        
        -- Dimension foreign keys (for star schema joins)
        a.artist_key,
        g.genre_key,
        md5(t.label) as label_key,
        md5(t.country) as country_key,
        
        -- Degenerate dimensions (low cardinality, kept in fact)
        t.track_name,
        t.album_name,
        t.artist_name,
        t.genre,
        t.label,
        t.country,
        
        -- Time dimension
        t.release_date,
        t.release_year,
        
        -- Core measures
        t.stream_count,
        t.popularity,
        
        -- Duration measures
        t.duration_ms,
        t.duration_seconds,
        t.duration_minutes,
        
        -- Audio feature measures
        t.danceability,
        t.energy,
        t.musical_key,
        t.loudness,
        t.musical_mode,
        t.instrumentalness,
        t.tempo,
        
        -- Flags
        t.is_explicit,
        
        -- Derived performance metrics
        case
            when t.stream_count >= 100000 then 'Viral'
            when t.stream_count >= 10000 then 'Hit'
            when t.stream_count >= 1000 then 'Moderate'
            else 'Emerging'
        end as performance_tier,
        
        case
            when t.popularity >= 70 then 'Top Tier'
            when t.popularity >= 50 then 'Popular'
            when t.popularity >= 30 then 'Moderate'
            else 'Deep Cut'
        end as popularity_band,
        
        -- Audio character flags (for filtering)
        case when t.danceability >= 0.7 then true else false end as is_danceable,
        case when t.energy >= 0.7 then true else false end as is_high_energy,
        case when t.instrumentalness >= 0.5 then true else false end as is_instrumental,
        case when t.tempo >= 120 then true else false end as is_uptempo
        
    from tracks t
    left join artist_dim a on t.artist_name = a.artist_name
    left join genre_dim g on t.genre = g.genre
)

select * from fact_tracks
