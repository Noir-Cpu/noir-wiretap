-- Grain: one commit on the default-branch listing returned by the GitHub API.
select
    md5(c.repo_name || '|' || c.commit_sha) as commit_key,
    repo.repo_key,
    cast(c.committed_at as date) as date_key,
    c.commit_sha,
    c.author_login,
    c.committed_at,
    length(c.message_headline) as message_headline_length
from {{ ref('stg_github__commits') }} as c
inner join {{ ref('dim_repo') }} as repo on repo.repo_name = c.repo_name
