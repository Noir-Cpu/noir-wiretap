select
    repo as repo_name,
    id as run_id,
    workflow_id,
    name as workflow_name,
    event,
    head_branch,
    status,
    conclusion,
    run_number,
    run_attempt,
    created_at,
    run_started_at,
    updated_at,
    actor_login
from {{ source('github', 'workflow_runs') }}
