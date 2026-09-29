select a.model_name
from {{ ref('mart_calibration') }} as a
inner join (
    select model_name, sum(scored_predictions) as n from {{ ref('mart_calibration') }} where grain = 'month' group by model_name
) as m on m.model_name = a.model_name
where a.grain = 'all_time' and a.scored_predictions <> m.n
