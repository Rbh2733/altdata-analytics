/*
    Test: Release dates within dataset boundaries
    
    Business rule: This dataset covers 2015-2025.
    Dates outside this range indicate data loading errors or
    incorrect date parsing.
    
    Returns: Rows with release_year outside [2015, 2025] (should be zero)
*/

select
    track_id,
    track_name,
    release_date,
    release_year
from {{ ref('stg_streaming_tracks') }}
where release_year < 2015 
   or release_year > 2025
