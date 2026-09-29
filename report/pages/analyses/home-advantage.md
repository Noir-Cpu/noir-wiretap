---
title: Home advantage, Premier League and La Liga
---

# Home advantage: Premier League against La Liga

```sql seasons
select * from wiretap.home_advantage where is_single_season order by season_start_year, league_name
```

```sql overall
select * from wiretap.home_advantage where not is_single_season order by league_name
```

```sql complete
select * from wiretap.home_advantage where is_single_season and is_complete_season order by season_start_year, league_name
```

`home_win_rate` is one column of the `mart_home_advantage` dbt model: home wins divided by completed matches. The chart, the tables and the text below read that column as it is. The current season is excluded from the trend because it is incomplete.

## Home win rate by season

<LineChart data={complete} x=season_label y=home_win_rate series=league_name yFmt=pct1 yMin=0.3 yMax=0.55 markers=true title="Home win rate, complete seasons" />

<DataTable data={seasons} rows=24>
  <Column id=league_name title="League" />
  <Column id=season_label title="Season" />
  <Column id=home_win_rate title="Home win" fmt="pct1" />
  <Column id=home_win_rate_ci_low title="95% low" fmt="pct1" />
  <Column id=home_win_rate_ci_high title="95% high" fmt="pct1" />
</DataTable>

## All seasons in the warehouse

<DataTable data={overall}>
  <Column id=league_name title="League" />
  <Column id=matches title="Matches" />
  <Column id=home_win_rate title="Home win" fmt="pct1" />
  <Column id=home_win_rate_ci_low title="95% low" fmt="pct1" />
  <Column id=home_win_rate_ci_high title="95% high" fmt="pct1" />
</DataTable>

## Findings

Written for the data as loaded on 2026-09-29 (seasons 2016/17 to 2025/26 complete, 2026/27 in progress). Full working and the test used are in [docs/analyses/01-home-advantage.md](https://github.com/Noir-Cpu/noir-wiretap/blob/main/docs/analyses/01-home-advantage.md).

- Home advantage is real and similar in both leagues: over all seasons the home side won 44.5% of Premier League matches and 45.5% of La Liga matches, and the two intervals overlap.
- The one notable departure is the Premier League in 2020/21, the season played mostly without crowds: 37.9% home wins, against 41% to 49% in every other complete season (pooled 45.4%; two-proportion z-test p = 0.005, about 0.11 after correcting for 20 league-seasons, so suggestive). In La Liga the same season (41.6%) is the lowest of its complete seasons, but only about two points below the next lowest (43.4%), and not distinguishable from the pooled rest (p = 0.11).
- The Premier League drifted down in 2024/25 (40.8%) and 2025/26 (42.6%). With 380 matches a season the 95% interval on one season is about plus or minus 5 points, so a single season below or above another is usually not distinguishable.

## What this can and cannot show

It shows the rate at which home teams won, per season, from full-time results. It cannot separate crowd effects from schedule, team quality mix, travel or referee effects, and it does not adjust for who played whom. Two leagues over ten seasons is a small sample of league-seasons. The 2020/21 comparison is descriptive: the data has no attendance column.
