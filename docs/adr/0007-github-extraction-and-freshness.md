# ADR 0007: GitHub extraction scope, rate limits and freshness rules

Status: accepted

- Scope: repos owned by Noir-Cpu whose name starts with `noir-` (public only; `WIRETAP_REPO_PREFIX` overrides). Course repos are out.
- Not collected: commit author names and e-mail addresses. Only public logins are kept. Commit message text is reduced to its length in the fact table.
- Auth: `GITHUB_TOKEN` in Actions, `gh auth token` locally, otherwise unauthenticated (60 requests per hour). Tokens are read from the environment at run time and never written anywhere.
- Rate limits: on 403/429 the client sleeps until `Retry-After` or `X-RateLimit-Reset`, and gives up with a clear message if the wait exceeds 15 minutes. Covered by `tests/test_github_client.py`.
- Incremental: commits, runs and PRs keep a per-repo cursor in dlt state and re-read a 3-day window each run, because runs and PRs change after creation. Merge on primary key makes re-reads idempotent.
- CI pass rate is reported twice, all runs and excluding runs triggered by `dependabot[bot]` (updater runs and checks on its PRs), both defined in `macros/ci_metrics.sql` (decided by John, 2026-09-29).
- Freshness (`dbt source freshness`, fails the nightly workflow on error):
  - `github.repos`, load time: warn 26 h, error 30 h. This is a heartbeat of our own load, since a quiet repo has no new events to measure.
  - `informant.collector_heartbeat.checked_at` (data/last_checked.json): warn 14 h, error 30 h. The collector writes it on every clean run (every 6 h), so a dead collector fails our build while a quiet stretch with no matches does not. Thresholds allow for GitHub schedule lag. The earlier rule used manifest `fetched_at`, which only changes when a data file changes, and failed the nightly on 2026-10-05 after two weeks without matches; manifest `fetched_at` is now the `last_data_change_at` column and not a freshness signal.
