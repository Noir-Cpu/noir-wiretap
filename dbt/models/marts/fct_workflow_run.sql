-- Grain: one GitHub Actions workflow run.
select
    r.run_id as workflow_run_key,
    repo.repo_key,
    cast(r.created_at as date) as date_key,
    r.workflow_name,
    r.event,
    r.head_branch,
    r.status,
    r.conclusion,
    r.ci_outcome,
    r.is_dependabot,
    r.run_attempt,
    r.duration_seconds,
    r.created_at
from {{ ref('int_github__workflow_runs') }} as r
inner join {{ ref('dim_repo') }} as repo on repo.repo_name = r.repo_name
