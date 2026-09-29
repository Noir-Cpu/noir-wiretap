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

## Findings and limits

The written findings, with the tests and caveats, are in [docs/analyses/01-home-advantage.md](https://github.com/Noir-Cpu/noir-wiretap/blob/main/docs/analyses/01-home-advantage.md) and on the [static page](https://noir-wiretap.noir-cpu.workers.dev/analyses/home-advantage/).
