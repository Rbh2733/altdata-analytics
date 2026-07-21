/*
    Test: All tracks have valid dimension keys
    
    Business rule: Every track in the fact table should successfully
    join to both dim_artists and dim_genres. Null keys indicate
    a join failure that needs investigation.
    
    This catches edge cases the relationship test might miss,
    like empty strings or whitespace-only values that hash differently.
    
    Returns: Rows with missing dimension keys (should be zero)
*/

select
    track_id,
    track_name,
    artist_name,
    genre,
    artist_key,
    genre_key
from {{ ref('fct_track_performance') }}
where artist_key is null
   or genre_key is null
   or artist_key = ''
   or genre_key = ''
