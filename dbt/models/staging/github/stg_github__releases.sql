with src as (
    {{ source_or_empty('github', 'releases', "select null::varchar as repo, null::bigint as id, null::varchar as tag_name, null::varchar as name, null::boolean as draft, null::boolean as prerelease, null::timestamptz as created_at, null::timestamptz as published_at where false") }}
)

select
    repo as repo_name,
    id as release_id,
    tag_name,
    name as release_name,
    draft as is_draft,
    prerelease as is_prerelease,
    created_at,
    published_at
from src
