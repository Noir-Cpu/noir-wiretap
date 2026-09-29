select a.repo_key
from {{ ref('mart_ci_reliability') }} as a
inner join (
    select repo_key, sum(decided_runs) as decided_runs
    from {{ ref('mart_ci_reliability') }} where grain = 'month' group by repo_key
) as m on m.repo_key = a.repo_key
where a.grain = 'all_time' and a.decided_runs <> m.decided_runs
