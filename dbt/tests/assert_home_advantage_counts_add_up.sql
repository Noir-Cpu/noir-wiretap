select home_advantage_key
from {{ ref('mart_home_advantage') }}
where home_wins + draws + away_wins <> matches
   or home_win_rate not between 0 and 1
   or abs(home_win_rate + draw_rate + away_win_rate - 1) > 0.0003
   or home_win_rate_ci_low > home_win_rate
   or home_win_rate_ci_high < home_win_rate
