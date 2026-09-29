# Analysis 1: home advantage, Premier League against La Liga

Data: INFORMANT results, `data/results/E0` and `SP1`, seasons 2016/17 to 2025/26 complete (380 matches each) and 2026/27 in progress (50 and 69 matches on 2026-09-29). Source: `marts.mart_home_advantage`, metric `home_win_rate` (ADR 0002). Reproduce every number with `make findings`.

## Numbers

| | Matches | Home win rate | 95% interval |
| --- | --- | --- | --- |
| Premier League, all seasons | 3,850 | 44.5% | 42.9% to 46.1% |
| La Liga, all seasons | 3,869 | 45.5% | 43.9% to 47.1% |

Premier League by season (home win rate): 49.2, 45.5, 47.6, 45.3, **37.9** (2020/21), 42.9, 48.4, 46.1, 40.8, 42.6. La Liga: 47.6, 47.1, 44.2, 45.8, 41.6, 43.4, 47.9, 44.0, 44.5, 49.0.

## Findings

1. Over ten seasons the two leagues do not differ detectably: 44.5% against 45.5%, two-proportion z-test z = -0.86, p = 0.39.
2. The Premier League's 2020/21 season (37.9%, 144 home wins in 380) is below the pooled rate of its other nine complete seasons (45.4%, n = 3,420): z = -2.78, p = 0.005. La Liga's 2020/21 (41.6%) is its lowest season but is not distinguishable from its pooled rest (45.9%): z = -1.62, p = 0.11.
3. The Premier League's two most recent complete seasons (40.8% and 42.6%) sit at the low end of the range, but a single 380-match season has a 95% interval of about plus or minus 5 points, so this is not a demonstrated trend.

## Limits

- I looked at the season-by-season table first and then tested the lowest one, so the p-values in finding 2 are not corrected for having picked the extreme of 20 league-seasons. A Bonferroni correction for 20 league-seasons multiplies the Premier League p-value by 20 (0.005 x 20 = about 0.11), so it is suggestive, not established.
- 2020/21 was played largely without spectators, but the data has no attendance column. The data shows a lower home win rate; it cannot attribute the cause.
- No adjustment for team strength, schedule or referee. Results are full-time only.
- Two leagues, ten seasons: a small sample of league-seasons. The 2026/27 rows are partial and excluded from the trend chart.
