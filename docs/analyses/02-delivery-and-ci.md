# Analysis 2: delivery cadence and CI reliability across the NOIR repos

Data: GitHub REST API for Noir-Cpu `noir-*` repos, loaded 2026-09-29 at about 20:00 UTC. Sources: `marts.mart_repo_summary`, `marts.mart_ci_reliability` (metric `ci_pass_rate`, ADR 0002). Reproduce with `make findings`; the numbers below are that day's snapshot and the live site updates nightly.

## Numbers (decided runs = passed + failed; cancelled/skipped/neutral excluded)

| Repo | Decided runs | Passed | Failed | Pass rate | Commits |
| --- | --- | --- | --- | --- | --- |
| noir-template | 118 | 106 | 12 | 89.8% | 17 |
| noir-informant | 20 | 18 | 2 | 90.0% | 5 |
| noir-witness | 15 | 15 | 0 | 100% | 6 |
| noir-hub | 8 | 8 | 0 | 100% | 1 |
| noir-dispatch | 8 | 7 | 1 | 87.5% | 1 |
| noir-wiretap | 0 | 0 | 0 | none | 0 |

noir-template: 8 further runs (the Dependabot auto-merge workflow) were skipped or otherwise excluded.

## Findings

1. Every workflow run in the warehouse falls within one day (first run 12:47 UTC, last about 20:00 UTC), and 17 of the template's commits were made in the same period. There is no cadence to measure yet, only a starting point. The weekly commits chart has one bar.
2. noir-template's 12 failures split as 7 Dependabot updater runs, 3 runs of the `CI` workflow and 2 of `Deploy`. Its `CI` workflow alone passed 42 of 45 decided runs (93.3%); the repo-level 89.8% mixes workflows with different jobs.
3. With 8 to 20 decided runs per repo, a single failure moves the rate by 5 to 12 points. The ranking of repos on pass rate is noise at this size.

## Limits

- Cannot say why runs failed, or whether a failure was flaky or a real defect: the pipeline stores conclusions, not logs.
- Median time to merge exists only for the template's 14 merged PRs (0.11 hours median, driven by Dependabot auto-merge); no other repo has a merged PR.
- Commits are the default-branch listing. Private repos are invisible. The pass rate counts every workflow, including Dependabot's own.
- `duration_seconds` is start to last update, an approximation.
