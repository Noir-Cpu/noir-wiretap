-- Grain: one published release. Empty until a NOIR repo cuts its first release.
select
    r.release_id as release_key,
    repo.repo_key,
    cast(r.published_at as date) as date_key,
    r.tag_name,
    r.is_prerelease,
    r.published_at
from {{ ref('stg_github__releases') }} as r
inner join {{ ref('dim_repo') }} as repo on repo.repo_name = r.repo_name
where not r.is_draft and r.published_at is not null
