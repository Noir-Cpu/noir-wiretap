-- CI pass rate per repo and calendar month, plus an all-time row per repo (period_start is null, grain = 'all_time').
-- The rule for what counts as a pass or a fail is one macro (macros/ci_metrics.sql).
with monthly as (
    select
        f.repo_key,
        'month' as grain,
        d.month_start as period_start,
        {{ ci_metrics() }}
    from {{ ref('fct_workflow_run') }} as f
    inner join {{ ref('dim_date') }} as d on d.date_key = f.date_key
    where f.ci_outcome <> 'in_progress'
    group by f.repo_key, d.month_start
),

all_time as (
    select
        f.repo_key,
        'all_time' as grain,
        null::date as period_start,
        {{ ci_metrics() }}
    from {{ ref('fct_workflow_run') }} as f
    where f.ci_outcome <> 'in_progress'
    group by f.repo_key
),

combined as (
    select * from monthly
    union all
    select * from all_time
)

select
    md5(c.repo_key || '|' || c.grain || '|' || coalesce(cast(c.period_start as varchar), '')) as ci_reliability_key,
    c.repo_key,
    r.repo_name,
    c.grain,
    c.period_start,
    c.decided_runs,
    c.passed_runs,
    c.failed_runs,
    c.excluded_runs,
    c.ci_pass_rate,
    c.decided_runs_excl_dependabot,
    c.passed_runs_excl_dependabot,
    c.failed_runs_excl_dependabot,
    c.ci_pass_rate_excl_dependabot,
    c.median_duration_seconds
from combined as c
inner join {{ ref('dim_repo') }} as r on r.repo_key = c.repo_key
