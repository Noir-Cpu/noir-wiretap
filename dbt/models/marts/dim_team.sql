with appearances as (
    select league_code, season_code, home_team as team_name from {{ ref('int_football__matches') }}
    union all
    select league_code, season_code, away_team from {{ ref('int_football__matches') }}
)

select
    md5(team_name) as team_key,
    team_name,
    min(season_code) as first_season_key,
    max(season_code) as last_season_key,
    count(distinct league_code || season_code) as league_seasons_played
from appearances
group by team_name
