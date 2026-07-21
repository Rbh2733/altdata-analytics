{{
    config(
        materialized='view'
    )
}}

/*
    Intermediate: Genre-level performance metrics
    
    Purpose: Aggregate track data to genre grain
    Grain: One row per genre
    
    Use cases:
    - Genre market share analysis
    - Audio feature profiling by genre
    - Trend analysis over time
*/

with tracks as (
    select * from {{ ref('stg_streaming_tracks') }}
),

genre_aggregates as (
    select
        genre,
        
        -- Volume metrics
        count(distinct track_id) as total_tracks,
        count(distinct artist_name) as unique_artists,
        count(distinct album_name) as unique_albums,
        sum(stream_count) as total_streams,
        
        -- Market share (calculated in mart layer)
        
        -- Performance metrics
        round(avg(popularity), 2) as avg_popularity,
        round(avg(stream_count), 0) as avg_streams_per_track,
        
        -- Audio fingerprint (what makes this genre distinct)
        round(avg(danceability), 3) as avg_danceability,
        round(avg(energy), 3) as avg_energy,
        round(avg(tempo), 1) as avg_tempo,
        round(avg(loudness), 2) as avg_loudness,
        round(avg(instrumentalness), 3) as avg_instrumentalness,
        
        -- Content profile
        round(100.0 * sum(case when is_explicit then 1 else 0 end) / count(*), 1) as explicit_pct,
        
        -- Label distribution
        mode(label) as dominant_label,
        count(distinct label) as label_diversity,
        
        -- Geographic distribution
        count(distinct country) as country_reach,
        mode(country) as top_country
        
    from tracks
    group by genre
)

select * from genre_aggregates
