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

<BarChart data={ci_all} x=repo_name y=ci_pass_rate yFmt=pct0 yMax=1 title="CI pass rate, all time" />

<DataTable data={ci_all}>
  <Column id=repo_name title="Repo" />
  <Column id=decided_runs title="Decided runs" />
  <Column id=ci_pass_rate title="Pass rate" fmt="pct1" />
</DataTable>

## Delivery per repo

<DataTable data={repos}>
  <Column id=repo_name title="Repo" />
  <Column id=commits title="Commits" />
  <Column id=prs_merged title="PRs merged" />
  <Column id=median_hours_to_merge title="Median h to merge" fmt="0.0" />
</DataTable>

<BarChart data={weekly} x=week_start xType=category y=commits series=repo_name title="Commits per week" />

## Findings

Written for the data as loaded at about 20:00 UTC on 2026-09-29; the tables above update nightly, this text does not. Working is in [docs/analyses/02-delivery-and-ci.md](https://github.com/Noir-Cpu/noir-wiretap/blob/main/docs/analyses/02-delivery-and-ci.md).

- The workflow-run history spans about seven hours on 2026-09-29 (12:47 to about 20:00 UTC). This is the start of the programme, not a trend.
- noir-template has the most CI history: 118 decided runs, 106 passed, 12 failed (89.8%). noir-witness passed all 15; noir-hub all 8; noir-informant 18 of 20; noir-dispatch 7 of 8. noir-wiretap had no runs yet.
- Of the template's 12 failures, 7 are Dependabot updater runs, 3 are the `CI` workflow and 2 are `Deploy`. The pass rate mixes workflows, so a single repo-level number hides that the product CI passed 42 of 45 decided runs in that repo.
- Small counts: one failure moves an 8-run repo's rate by about 12 points. Do not rank repos on these rates.

## What this can and cannot show

It shows counts of runs and their conclusions for public repos. It cannot show why a run failed, whether a failure was a flaky test or a real defect, or a trend: the window is a few hours. Commit counts are the default-branch commit list only, and PR data covers only repos that have PRs. Private repos are invisible to the pipeline.
