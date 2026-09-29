select
    id as repo_id,
    name as repo_name,
    full_name,
    description,
    language,
    default_branch,
    archived as is_archived,
    fork as is_fork,
    visibility,
    coalesce(topics, '') as topics,
    stargazers_count,
    forks_count,
    open_issues_count,
    created_at as created_at,
    pushed_at,
    updated_at,
    to_timestamp(cast(_dlt_load_id as double)) as loaded_at
from {{ source('github', 'repos') }}
