-- Home-advantage metrics per league-season and per league across all seasons.
-- The metrics come from one macro (macros/home_advantage_metrics.sql); this is the only place they are computed.
-- Rows with season_key = 'ALL' cover every season; is_complete_season is false for the season still being played.
with league_season as (
    select
        league_key,
        season_key,
        season_key as season_scope,
        {{ home_advantage_metrics() }}
    from {{ ref('fct_match') }}
    group by league_key, season_key
),

league_all as (
    select
        league_key,
        'ALL' as season_key,
        'ALL' as season_scope,
        {{ home_advantage_metrics() }}
    from {{ ref('fct_match') }}
    group by league_key
),

combined as (
    select * from league_season
    union all
    select * from league_all
)

select
    md5(c.league_key || '|' || c.season_key) as home_advantage_key,
    c.league_key,
    l.league_name,
    c.season_key,
    coalesce(s.season_label, 'All seasons') as season_label,
    coalesce(s.season_start_year, 0) as season_start_year,
    c.season_key <> 'ALL' as is_single_season,
    -- A full season is 380 matches (20 teams). The 'ALL' rows are complete by definition.
    (c.season_key = 'ALL' or c.matches = 380) as is_complete_season,
    c.matches,
    c.home_wins,
    c.draws,
    c.away_wins,
    c.home_win_rate,
    c.draw_rate,
    c.away_win_rate,
    c.home_win_rate_ci_low,
    c.home_win_rate_ci_high,
    c.avg_home_goals,
    c.avg_away_goals,
    c.home_goal_advantage,
    c.avg_home_points
from combined as c
inner join {{ ref('dim_league') }} as l on l.league_key = c.league_key
left join {{ ref('dim_season') }} as s on s.season_key = c.season_key
