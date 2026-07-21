/*
    Test: Genre market share sums to 100%
    
    Business rule: Market share percentages should sum to approximately
    100% (allowing for rounding). If they don't, there's a calculation
    error in the dimension model.
    
    Tolerance: 0.5% variance allowed for floating point rounding
    
    Returns: A row if total market share deviates from 100% (should be zero rows)
*/

with market_share_total as (
    select 
        sum(stream_market_share_pct) as total_share
    from {{ ref('dim_genres') }}
)

select
    total_share,
    abs(total_share - 100.0) as deviation_from_100
from market_share_total
where abs(total_share - 100.0) > 0.5
