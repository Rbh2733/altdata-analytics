/*
    Test: Track duration sanity check
    
    Business rule: Track duration should be reasonable.
    - Minimum: 30 seconds (30,000 ms) - shorter is likely a glitch or intro
    - Maximum: 60 minutes (3,600,000 ms) - longer is likely a podcast/audiobook mislabel
    
    Returns: Rows with implausible durations (should be zero)
*/

select
    track_id,
    track_name,
    artist_name,
    duration_ms,
    duration_minutes
from {{ ref('stg_streaming_tracks') }}
where duration_ms <= 0
   or duration_ms < 30000      -- Less than 30 seconds
   or duration_ms > 3600000    -- More than 60 minutes
