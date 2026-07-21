/*
    Test: Artist career timeline consistency
    
    Business rule: An artist's first release year cannot be after
    their latest release year. This would indicate a calculation
    error in the intermediate model.
    
    Returns: Rows where career timeline is inverted (should be zero)
*/

select
    artist_name,
    first_release_year,
    latest_release_year,
    career_span_years
from {{ ref('int_artist_metrics') }}
where first_release_year > latest_release_year
   or career_span_years < 0
