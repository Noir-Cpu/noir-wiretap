-- Delivery activity per repo and ISO week (weeks with no activity have no row).
with activity as (
    select repo_key, d.week_start, 'commit' as kind, 1 as n
    from {{ ref('fct_commit') }} as c inner join {{ ref('dim_date') }} as d on d.date_key = c.date_key
    union all
    select repo_key, d.week_start, 'pr_opened', 1
    from {{ ref('fct_pull_request') }} as p inner join {{ ref('dim_date') }} as d on d.date_key = p.date_key
    union all
    select repo_key, d.week_start, 'pr_merged', 1
    from {{ ref('fct_pull_request') }} as p
    inner join {{ ref('dim_date') }} as d on d.date_key = cast(p.merged_at as date)
    where p.is_merged
    union all
    select repo_key, d.week_start, 'release', 1
    from {{ ref('fct_release') }} as rel inner join {{ ref('dim_date') }} as d on d.date_key = rel.date_key
)

select
    md5(a.repo_key || '|' || a.week_start) as delivery_cadence_key,
    a.repo_key,
    r.repo_name,
    a.week_start,
    count(*) filter (where kind = 'commit') as commits,
    count(*) filter (where kind = 'pr_opened') as prs_opened,
    count(*) filter (where kind = 'pr_merged') as prs_merged,
    count(*) filter (where kind = 'release') as releases
from activity as a
inner join {{ ref('dim_repo') }} as r on r.repo_key = a.repo_key
group by a.repo_key, r.repo_name, a.week_start
