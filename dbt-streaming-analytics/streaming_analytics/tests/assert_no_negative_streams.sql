/*
    Test: No negative stream counts
    
    Business rule: Stream counts represent cumulative plays.
    A negative value indicates data corruption or ETL error.
    
    Returns: Rows where stream_count < 0 (should be zero)
*/

select
    track_id,
    track_name,
    artist_name,
    stream_count
from {{ ref('stg_streaming_tracks') }}
where stream_count < 0
