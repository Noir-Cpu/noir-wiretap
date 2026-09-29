-- Grain: one pull request.
select
    p.pull_request_id as pull_request_key,
    repo.repo_key,
    cast(p.created_at as date) as date_key,
    p.pull_request_number,
    p.state,
    p.is_draft,
    p.author_login,
    p.created_at,
    p.merged_at,
    p.merged_at is not null as is_merged,
    case when p.merged_at is not null
         then date_diff('second', p.created_at, p.merged_at) / 3600.0 end as hours_to_merge
from {{ ref('stg_github__pull_requests') }} as p
inner join {{ ref('dim_repo') }} as repo on repo.repo_name = p.repo_name
