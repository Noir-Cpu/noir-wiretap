select ci_reliability_key
from {{ ref('mart_ci_reliability') }}
where passed_runs + failed_runs <> decided_runs
   or ci_pass_rate not between 0 and 1
   or (decided_runs = 0 and ci_pass_rate is not null)
