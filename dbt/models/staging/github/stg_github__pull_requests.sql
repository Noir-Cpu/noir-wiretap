select
    repo as repo_name,
    id as pull_request_id,
    number as pull_request_number,
    state,
    draft as is_draft,
    created_at,
    updated_at,
    closed_at,
    merged_at,
    author_login,
    base_ref
from {{ source('github', 'pull_requests') }}
