-- The league rollup must equal the sum of its season rows.
select a.league_key
from {{ ref('mart_home_advantage') }} as a
inner join (
    select league_key, sum(matches) as matches, sum(home_wins) as home_wins
    from {{ ref('mart_home_advantage') }}
    where is_single_season
    group by league_key
) as s on s.league_key = a.league_key
where a.season_key = 'ALL' and (a.matches <> s.matches or a.home_wins <> s.home_wins)
