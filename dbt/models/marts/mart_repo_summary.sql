-- One row per NOIR repo: delivery totals, plus the all-time CI pass rate read from mart_ci_reliability (not recomputed).
with commits as (
    select repo_key, count(*) as commits, count(distinct date_key) as active_days,
           min(committed_at) as first_commit_at, max(committed_at) as last_commit_at
    from {{ ref('fct_commit') }} group by repo_key
),

prs as (
    select repo_key, count(*) as prs_opened, count(*) filter (where is_merged) as prs_merged,
           median(hours_to_merge) as median_hours_to_merge
    from {{ ref('fct_pull_request') }} group by repo_key
),

releases as (
    select repo_key, count(*) as releases from {{ ref('fct_release') }} group by repo_key
),

ci as (
    select repo_key, decided_runs, passed_runs, failed_runs, ci_pass_rate, decided_runs_excl_dependabot,
           ci_pass_rate_excl_dependabot, median_duration_seconds
    from {{ ref('mart_ci_reliability') }} where grain = 'all_time'
)

select
    r.repo_key,
    r.repo_name,
    coalesce(commits.commits, 0) as commits,
    coalesce(commits.active_days, 0) as active_days,
    commits.first_commit_at,
    commits.last_commit_at,
    coalesce(prs.prs_opened, 0) as prs_opened,
    coalesce(prs.prs_merged, 0) as prs_merged,
    prs.median_hours_to_merge,
    coalesce(releases.releases, 0) as releases,
    coalesce(ci.decided_runs, 0) as ci_decided_runs,
    coalesce(ci.passed_runs, 0) as ci_passed_runs,
    coalesce(ci.failed_runs, 0) as ci_failed_runs,
    ci.ci_pass_rate,
    ci.decided_runs_excl_dependabot as ci_decided_runs_excl_dependabot,
    ci.ci_pass_rate_excl_dependabot,
    ci.median_duration_seconds as ci_median_duration_seconds
from {{ ref('dim_repo') }} as r
left join commits on commits.repo_key = r.repo_key
left join prs on prs.repo_key = r.repo_key
left join releases on releases.repo_key = r.repo_key
left join ci on ci.repo_key = r.repo_key
