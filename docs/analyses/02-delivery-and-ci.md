# Analysis 2: delivery cadence and CI reliability across the NOIR repos

Data: GitHub REST API for Noir-Cpu `noir-*` repos, loaded 2026-09-29 at about 20:20 UTC. Sources: `marts.mart_repo_summary` and `marts.mart_ci_reliability` (metric `ci_pass_rate`, ADR 0002). Reproduce with `make findings`; the numbers below are that day's snapshot and the live tables above update nightly.

## Numbers (decided runs = passed + failed; cancelled, skipped and neutral runs are excluded)

| Repo | Decided runs | Pass rate | Decided, no Dependabot | Pass rate, no Dependabot | Commits |
| --- | --- | --- | --- | --- | --- |
| noir-template | 118 | 89.8% | 72 | 95.8% | 17 |
| noir-informant | 20 | 90.0% | 11 | 81.8% | 5 |
| noir-wiretap | 20 | 95.0% | 7 | 100% | 3 |
| noir-witness | 19 | 100% | 12 | 100% | 7 |
| noir-dispatch | 12 | 83.3% | 7 | 71.4% | 3 |
| noir-hub | 8 | 100% | 3 | 100% | 1 |

"No Dependabot" leaves out every run triggered by `dependabot[bot]`: its updater runs and the checks on its pull requests.

## Findings

1. All workflow runs in the warehouse fall within one day (first run 12:47 UTC, last about 20:15 UTC). There is no cadence to measure yet, only a starting point. The weekly commits table has one row per repo.
2. Dependabot runs change the picture in both directions. In noir-template they hold the rate down: 9 of its 12 failures are Dependabot-triggered (7 updater runs, 2 `CI` runs on Dependabot branches), so the rate without them is 95.8%. In noir-informant and noir-dispatch the opposite happens: the Dependabot runs were mostly passing, so leaving them out lowers the rate (90.0% to 81.8%, 83.3% to 71.4%).
3. Counts are small. With 3 to 20 decided runs, one failure moves a rate by 5 to 33 points. Do not rank repos on these rates.

## Limits

- The pipeline stores conclusions, not logs, so it cannot say why a run failed or whether a failure was a flaky test or a real defect.
- Median time to merge exists only for noir-template's 14 merged PRs (0.11 hours median, driven by Dependabot auto-merge); no other repo has a merged PR.
- Commits are the default-branch listing. Private repos are invisible to the pipeline. `duration_seconds` is start to last update, an approximation.
- The Dependabot flag is the run's triggering actor. It does not separate a failing dependency bump from a real regression.
