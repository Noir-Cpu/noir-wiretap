-- Current state of each repo. History of changing attributes is in dim_repo_history.
select
    repo_id as repo_key,
    repo_name,
    full_name,
    description,
    language,
    default_branch,
    is_archived,
    topics,
    created_at
from {{ ref('stg_github__repos') }}
