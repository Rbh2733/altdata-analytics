/*
    Test: Audio features within valid ranges
    
    Business rule: audio features have defined ranges:
    - danceability: 0.0 to 1.0
    - energy: 0.0 to 1.0
    - instrumentalness: 0.0 to 1.0
    - tempo: typically 0-250 BPM (allowing up to 300 for edge cases)
    - loudness: typically -60 to 0 dB
    
    Values outside these ranges indicate parsing or extraction errors.
    
    Returns: Rows with out-of-range audio features (should be zero)
*/

select
    track_id,
    track_name,
    danceability,
    energy,
    instrumentalness,
    tempo,
    loudness
from {{ ref('stg_streaming_tracks') }}
where danceability < 0 or danceability > 1
   or energy < 0 or energy > 1
   or instrumentalness < 0 or instrumentalness > 1
   or tempo < 0 or tempo > 300
   or loudness > 0 or loudness < -60
