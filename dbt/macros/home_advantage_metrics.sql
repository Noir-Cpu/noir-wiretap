{# The single definition of the home-advantage metrics. Both the per-season rows and the all-seasons rows of
   mart_home_advantage use it, and the report reads the columns as they are. #}
{% macro home_advantage_metrics() %}
    count(*) as matches,
    count(*) filter (where result = 'H') as home_wins,
    count(*) filter (where result = 'D') as draws,
    count(*) filter (where result = 'A') as away_wins,
    round(count(*) filter (where result = 'H') * 1.0 / count(*), 4) as home_win_rate,
    round(count(*) filter (where result = 'D') * 1.0 / count(*), 4) as draw_rate,
    round(count(*) filter (where result = 'A') * 1.0 / count(*), 4) as away_win_rate,
    -- 95% normal-approximation interval; matches is a few hundred per season, so it is wide.
    round(count(*) filter (where result = 'H') * 1.0 / count(*)
        - 1.96 * sqrt((count(*) filter (where result = 'H') * 1.0 / count(*))
                      * (1 - count(*) filter (where result = 'H') * 1.0 / count(*)) / count(*)), 4) as home_win_rate_ci_low,
    round(count(*) filter (where result = 'H') * 1.0 / count(*)
        + 1.96 * sqrt((count(*) filter (where result = 'H') * 1.0 / count(*))
                      * (1 - count(*) filter (where result = 'H') * 1.0 / count(*)) / count(*)), 4) as home_win_rate_ci_high,
    round(avg(home_goals), 4) as avg_home_goals,
    round(avg(away_goals), 4) as avg_away_goals,
    round(avg(home_goals) - avg(away_goals), 4) as home_goal_advantage,
    round(avg(home_points) * 1.0, 4) as avg_home_points
{% endmacro %}
