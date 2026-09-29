-- Classifies each workflow run for CI reliability. Rules live in macros/ci_metrics.sql.
select
    r.*,
    r.actor_login = 'dependabot[bot]' as is_dependabot,
    case
        when r.status <> 'completed' then 'in_progress'
        when r.conclusion = 'success' then 'pass'
        when r.conclusion in ('failure', 'timed_out') then 'fail'
        else 'excluded'
    end as ci_outcome,
    case
        when r.status = 'completed'
        then date_diff('second', coalesce(r.run_started_at, r.created_at), r.updated_at)
    end as duration_seconds
from {{ ref('stg_github__workflow_runs') }} as r
