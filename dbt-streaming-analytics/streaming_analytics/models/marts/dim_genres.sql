{{
    config(
        materialized='table'
    )
}}

/*
    Dimension: Genres
    
    Grain: One row per genre
    Purpose: Genre profile with audio fingerprinting and market positioning
    
    Design notes:
    - Audio fingerprint columns enable "sound profile" analysis
    - Market share pre-calculated for common dashboard use
*/

with genre_metrics as (
    select * from {{ ref('int_genre_performance') }}
),

total_market as (
    select sum(total_streams) as market_total_streams
    from genre_metrics
),

genre_dimension as (
    select
        -- Surrogate key
        md5(g.genre) as genre_key,
        
        -- Natural key
        g.genre,
        
        -- Market position
        g.total_streams,
        round(100.0 * g.total_streams / nullif(t.market_total_streams, 0), 2) as stream_market_share_pct,
        rank() over (order by g.total_streams desc) as stream_rank,
        
        g.total_tracks,
        g.unique_artists,
        g.unique_albums,
        
        -- Performance profile
        g.avg_popularity,
        g.avg_streams_per_track,
        
        case
            when g.avg_popularity >= 55 then 'Mainstream'
            when g.avg_popularity >= 45 then 'Crossover'
            else 'Niche'
        end as market_position,
        
        -- Audio fingerprint (what makes this genre sound distinct)
        g.avg_danceability,
        g.avg_energy,
        g.avg_tempo,
        g.avg_loudness,
        g.avg_instrumentalness,
        
        -- Derived audio character
        case
            when g.avg_energy >= 0.7 and g.avg_tempo >= 120 then 'High Energy'
            when g.avg_danceability >= 0.7 then 'Dance-Friendly'
            when g.avg_instrumentalness >= 0.5 then 'Instrumental-Heavy'
            when g.avg_energy <= 0.4 then 'Chill/Ambient'
            else 'Balanced'
        end as audio_character,
        
        -- Content profile
        g.explicit_pct,
        case
            when g.explicit_pct >= 30 then 'Adult-Oriented'
            when g.explicit_pct >= 10 then 'Mixed'
            else 'Family-Friendly'
        end as content_rating,
        
        -- Industry structure
        g.dominant_label,
        g.label_diversity,
        case
            when g.label_diversity >= 8 then 'Fragmented'
            when g.label_diversity >= 5 then 'Competitive'
            else 'Concentrated'
        end as market_structure,
        
        -- Geographic profile
        g.country_reach,
        g.top_country
        
    from genre_metrics g
    cross join total_market t
)

select * from genre_dimension
