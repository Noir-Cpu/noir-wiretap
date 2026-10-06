---
title: Delivery cadence and CI reliability
---

# Delivery cadence and CI reliability across the NOIR repos

```sql repos
select * from wiretap.repo_summary order by commits desc
```

```sql ci_all
select * from wiretap.ci_reliability where grain = 'all_time' order by decided_runs desc
```

```sql ci_month
select * from wiretap.ci_reliability where grain = 'month' order by period_start, repo_name
```

```sql weekly
select * from wiretap.delivery_cadence order by week_start
```

`ci_pass_rate` is one column of the `mart_ci_reliability` dbt model: runs that passed divided by runs that reached a verdict (pass or fail). Cancelled, skipped and neutral runs are counted separately and are not in the rate.

## CI pass rate per repo

<BarChart data={ci_all} x=repo_name y={['ci_pass_rate','ci_pass_rate_excl_dependabot']} yFmt=pct0 yMax=1 type=grouped title="CI pass rate, all time: all runs and excluding Dependabot runs" />

<DataTable data={ci_all}>
  <Column id=repo_name title="Repo" />
  <Column id=decided_runs title="Decided runs" />
  <Column id=ci_pass_rate title="Pass rate" fmt="pct1" />
  <Column id=ci_pass_rate_excl_dependabot title="No Dependabot" fmt="pct1" />
</DataTable>

## Delivery per repo

<DataTable data={repos}>
  <Column id=repo_name title="Repo" />
  <Column id=commits title="Commits" />
  <Column id=prs_merged title="PRs merged" />
  <Column id=median_hours_to_merge title="Median h to merge" fmt="0.0" />
</DataTable>

<BarChart data={weekly} x=week_start xType=category sort=false y=commits series=repo_name title="Commits per week" />

## Findings and limits

The written findings, with the numbers and caveats, are in [docs/analyses/02-delivery-and-ci.md](https://github.com/Noir-Cpu/noir-wiretap/blob/main/docs/analyses/02-delivery-and-ci.md) and on the [static page](https://noir-wiretap.noir-cpu.workers.dev/analyses/delivery-and-ci/). The history is one day long, counts are small, and the pipeline cannot say why a run failed.
