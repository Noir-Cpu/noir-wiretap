select
    league_code as league_key,
    league_name,
    country
from {{ ref('leagues') }}
