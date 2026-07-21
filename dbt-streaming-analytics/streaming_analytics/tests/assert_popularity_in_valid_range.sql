/*
    Test: Popularity scores within valid range
    
    Business rule: popularity is a 0-100 integer scale.
    Values outside this range indicate data quality issues.
    
    Returns: Rows where popularity is outside [0, 100] (should be zero)
*/

select
    track_id,
    track_name,
    popularity
from {{ ref('stg_streaming_tracks') }}
where popularity < 0 
   or popularity > 100
