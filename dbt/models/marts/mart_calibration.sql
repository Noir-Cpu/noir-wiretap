-- Forecast quality per model and calendar month of the match, plus one all_time row per model.
-- Metrics come from macros/calibration_metrics.sql. has_enough_data is false below var('min_scored_predictions')
-- scored first predictions; the report shows no headline number for such rows.
with scored as (
    select f.*, d.month_start
    from {{ ref('fct_prediction') }} as f
    inner join {{ ref('dim_date') }} as d on d.date_key = f.date_key
    where f.is_scored and f.is_first_for_match_model
),

monthly as (
    select model_name, 'month' as grain, month_start as period_start, {{ calibration_metrics() }}
    from scored group by model_name, month_start
),

all_time as (
    select model_name, 'all_time' as grain, null::date as period_start, {{ calibration_metrics() }}
    from scored group by model_name
),

combined as (
    select * from monthly
    union all
    select * from all_time
)

select
    md5(model_name || '|' || grain || '|' || coalesce(cast(period_start as varchar), '')) as calibration_key,
    *
from combined
