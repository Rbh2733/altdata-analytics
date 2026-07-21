{{
    config(
        materialized='table'
    )
}}

/*
    Dimension: Artists
    
    Grain: One row per unique artist
    Purpose: Comprehensive artist profile for analytical joins
    
    Design notes:
    - Materialized as table for query performance (dimension lookups are frequent)
    - Includes derived tiers/segments for filtering without recalculation
    - Surrogate key (artist_key) for stable joins if source names change
*/

with artist_metrics as (
    select * from {{ ref('int_artist_metrics') }}
),

artist_dimension as (
    select
        -- Surrogate key (hash for stability)
        md5(artist_name) as artist_key,
        
        -- Natural key
        artist_name,
        
        -- Categorical attributes
        primary_genre,
        primary_label,
        
        -- Derived segments (pre-calculated for filtering)
        case
            when total_streams >= 1000000 then 'Platinum'
            when total_streams >= 100000 then 'Gold'
            when total_streams >= 10000 then 'Silver'
            else 'Bronze'
        end as stream_tier,
        
        case
            when avg_popularity >= 70 then 'High'
            when avg_popularity >= 40 then 'Medium'
            else 'Low'
        end as popularity_tier,
        
        case
            when career_span_years >= 5 then 'Established'
            when career_span_years >= 2 then 'Growing'
            else 'Emerging'
        end as career_stage,
        
        -- Volume metrics
        total_tracks,
        total_albums,
        total_streams,
        avg_streams_per_track,
        
        -- Performance metrics
        avg_popularity,
        max_popularity,
        
        -- Audio signature
        avg_danceability,
        avg_energy,
        avg_tempo,
        
        -- Content profile
        genre_count,
        explicit_tracks,
        round(100.0 * explicit_tracks / nullif(total_tracks, 0), 1) as explicit_pct,
        
        -- Career timeline
        first_release_year,
        latest_release_year,
        career_span_years,
        
        -- Geographic reach
        country_count,
        case
            when country_count >= 8 then 'Global'
            when country_count >= 4 then 'Regional'
            else 'Local'
        end as geographic_reach
        
    from artist_metrics
)

select * from artist_dimension
