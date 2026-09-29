-- Grain: one completed league match.
select
    m.match_id as match_key,
    m.match_date as date_key,
    m.league_code as league_key,
    m.season_code as season_key,
    md5(m.home_team) as home_team_key,
    md5(m.away_team) as away_team_key,
    m.home_goals,
    m.away_goals,
    m.result,
    m.home_points,
    m.away_points,
    m.home_shots,
    m.away_shots,
    m.home_shots_on_target,
    m.away_shots_on_target,
    m.home_yellows,
    m.away_yellows,
    m.home_reds,
    m.away_reds
from {{ ref('int_football__matches') }} as m
