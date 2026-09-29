-- Reliability table: for each model, outcome and 10%-wide probability bin, the mean predicted probability against
-- the observed frequency. Each scored first prediction contributes three rows (home, draw, away).
with scored as (
    select * from {{ ref('fct_prediction') }} where is_scored and is_first_for_match_model
),

long as (
    select model_name, 'home' as outcome, p_home as p, (result = 'H')::int as happened from scored
    union all
    select model_name, 'draw', p_draw, (result = 'D')::int from scored
    union all
    select model_name, 'away', p_away, (result = 'A')::int from scored
)

select
    md5(model_name || '|' || outcome || '|' || least(floor(p * 10), 9)) as calibration_bin_key,
    model_name,
    outcome,
    least(floor(p * 10), 9)::int as bin_index,
    count(*) as predictions,
    round(avg(p), 4) as mean_predicted,
    round(avg(happened), 4) as observed_frequency
from long
group by model_name, outcome, least(floor(p * 10), 9)
