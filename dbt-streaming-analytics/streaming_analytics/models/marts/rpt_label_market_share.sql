{{
    config(
        materialized='table'
    )
}}

/*
    Report: Label Market Share Analysis
    
    Grain: One row per label
    Purpose: Pre-aggregated executive dashboard for label performance
    
    Design notes:
    - Designed for direct BI consumption (no joins required)
    - Includes competitive positioning metrics
    - Year-over-year calculations where data permits
    
    Business questions answered:
    - Which labels dominate market share?
    - How does catalog size relate to streaming performance?
    - What's the content strategy of each label?
*/

with label_metrics as (
    select * from {{ ref('int_label_catalog') }}
),

total_market as (
    select 
        sum(total_streams) as market_total_streams,
        sum(catalog_size) as market_total_tracks
    from label_metrics
),

label_report as (
    select
        -- Label identity
        l.label,
        
        -- Market share metrics
        l.total_streams,
        round(100.0 * l.total_streams / nullif(t.market_total_streams, 0), 2) as stream_market_share_pct,
        rank() over (order by l.total_streams desc) as stream_rank,
        
        l.catalog_size,
        round(100.0 * l.catalog_size / nullif(t.market_total_tracks, 0), 2) as catalog_market_share_pct,
        rank() over (order by l.catalog_size desc) as catalog_rank,
        
        -- Roster analysis
        l.roster_size,
        l.album_count,
        round(l.catalog_size::float / nullif(l.roster_size, 0), 1) as tracks_per_artist,
        round(l.album_count::float / nullif(l.roster_size, 0), 1) as albums_per_artist,
        
        -- Performance efficiency
        l.avg_track_popularity,
        l.avg_streams_per_track,
        l.top_track_streams,
        round(l.total_streams::float / nullif(l.roster_size, 0), 0) as streams_per_artist,
        
        -- Efficiency ratio: Are they getting more streams per track than average?
        round(
            (l.avg_streams_per_track / nullif(t.market_total_streams::float / t.market_total_tracks, 0)) * 100, 
            1
        ) as efficiency_index,
        
        -- Content strategy
        l.primary_genre,
        l.genre_diversity,
        case
            when l.genre_diversity >= 10 then 'Diversified'
            when l.genre_diversity >= 5 then 'Multi-Genre'
            else 'Specialist'
        end as content_strategy,
        
        l.explicit_content_pct,
        l.avg_track_length_min,
        
        -- Geographic strategy
        l.primary_market,
        l.market_reach,
        case
            when l.market_reach >= 8 then 'Global'
            when l.market_reach >= 4 then 'Multi-Regional'
            else 'Regional'
        end as geographic_strategy,
        
        -- Activity profile
        l.earliest_release,
        l.latest_release,
        l.active_years,
        case
            when l.latest_release >= 2024 then 'Active'
            when l.latest_release >= 2022 then 'Slowing'
            else 'Legacy'
        end as release_activity,
        
        -- Competitive tier
        case
            when rank() over (order by l.total_streams desc) <= 3 then 'Major'
            when rank() over (order by l.total_streams desc) <= 7 then 'Mid-Tier'
            else 'Indie/Boutique'
        end as competitive_tier
        
    from label_metrics l
    cross join total_market t
)

select * from label_report
order by stream_rank
