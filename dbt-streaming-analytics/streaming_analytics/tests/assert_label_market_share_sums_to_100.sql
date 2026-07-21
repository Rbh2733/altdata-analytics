/*
    Test: Label market share sums to 100%
    
    Business rule: Label stream market share percentages should sum to
    approximately 100%. Deviation indicates calculation errors.
    
    Tolerance: 0.5% variance allowed for floating point rounding
    
    Returns: A row if total market share deviates from 100% (should be zero rows)
*/

with market_share_total as (
    select 
        sum(stream_market_share_pct) as total_share
    from {{ ref('rpt_label_market_share') }}
)

select
    total_share,
    abs(total_share - 100.0) as deviation_from_100
from market_share_total
where abs(total_share - 100.0) > 0.5
