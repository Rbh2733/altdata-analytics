{{
    config(
        materialized='view'
    )
}}

/*
    Intermediate: Artist-level metrics
    
    Purpose: Aggregate track data to artist grain
    Grain: One row per artist
    
    Key metrics:
    - Total tracks and streams
    - Popularity averages
    - Genre distribution
    - Label relationships
*/

with tracks as (
    select * from {{ ref('stg_streaming_tracks') }}
),

artist_aggregates as (
    select
        artist_name,
        
        -- Volume metrics
        count(distinct track_id) as total_tracks,
        count(distinct album_name) as total_albums,
        sum(stream_count) as total_streams,
        
        -- Performance metrics
        round(avg(popularity), 2) as avg_popularity,
        max(popularity) as max_popularity,
        round(avg(stream_count), 0) as avg_streams_per_track,
        
        -- Audio profile (averages)
        round(avg(danceability), 3) as avg_danceability,
        round(avg(energy), 3) as avg_energy,
        round(avg(tempo), 1) as avg_tempo,
        
        -- Content profile
        mode(genre) as primary_genre,
        mode(label) as primary_label,
        count(distinct genre) as genre_count,
        sum(case when is_explicit then 1 else 0 end) as explicit_tracks,
        
        -- Time range
        min(release_year) as first_release_year,
        max(release_year) as latest_release_year,
        max(release_year) - min(release_year) as career_span_years,
        
        -- Geographic reach
        count(distinct country) as country_count
        
    from tracks
    group by artist_name
)

select * from artist_aggregates
