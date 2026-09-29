select
    repo as repo_name,
    sha as commit_sha,
    committed_at,
    authored_at,
    author_login,
    committer_login,
    message_headline
from {{ source('github', 'commits') }}
