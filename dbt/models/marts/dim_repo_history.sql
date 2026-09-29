-- Type 2 slowly changing dimension over repo attributes, from the snap_repo snapshot.
select
    dbt_scd_id as repo_version_key,
    repo_id as repo_key,
    repo_name,
    description,
    language,
    default_branch,
    is_archived,
    topics,
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    dbt_valid_to is null as is_current
from {{ ref('snap_repo') }}
