-- One row per completed match with derived fields. Fixtures without a result (null goals) are dropped.
select
    match_id,
    league_code,
    season_code,
    2000 + cast(substr(season_code, 1, 2) as integer) as season_start_year,
    '20' || substr(season_code, 1, 2) || '/' || substr(season_code, 3, 2) as season_label,
    match_date,
    kickoff_time,
    home_team,
    away_team,
    home_goals,
    away_goals,
    result,
    case result when 'H' then 3 when 'D' then 1 else 0 end as home_points,
    case result when 'A' then 3 when 'D' then 1 else 0 end as away_points,
    home_shots,
    away_shots,
    home_shots_on_target,
    away_shots_on_target,
    home_yellows,
    away_yellows,
    home_reds,
    away_reds
from {{ ref('stg_informant__matches') }}
where home_goals is not null and away_goals is not null and result in ('H', 'D', 'A')
