select distinct
    season_code as season_key,
    season_label,
    season_start_year
from {{ ref('int_football__matches') }}
