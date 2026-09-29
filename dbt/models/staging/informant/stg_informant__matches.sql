with src as (
    select * from {{ source('informant', 'results') }}
),

typed as (
    select
        league_code,
        season_code,
        -- Older files use dd/mm/yy, newer dd/mm/yyyy.
        case
            when length(date) = 8 then try_strptime(date, '%d/%m/%y')
            else try_strptime(date, '%d/%m/%Y')
        end::date as match_date,
        try_cast(time as time) as kickoff_time,
        hometeam as home_team,
        awayteam as away_team,
        try_cast(fthg as integer) as home_goals,
        try_cast(ftag as integer) as away_goals,
        ftr as result,
        try_cast(hthg as integer) as home_goals_ht,
        try_cast(htag as integer) as away_goals_ht,
        try_cast(hs as integer) as home_shots,
        try_cast("as" as integer) as away_shots,
        try_cast(hst as integer) as home_shots_on_target,
        try_cast(ast as integer) as away_shots_on_target,
        try_cast(hy as integer) as home_yellows,
        try_cast(ay as integer) as away_yellows,
        try_cast(hr as integer) as home_reds,
        try_cast(ar as integer) as away_reds
    from src
)

select
    md5(concat_ws('|', league_code, season_code, match_date, home_team, away_team)) as match_id,
    *
from typed
