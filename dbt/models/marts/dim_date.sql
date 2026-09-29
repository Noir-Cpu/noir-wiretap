with spine as (
    select cast(d as date) as date_key
    from generate_series(date '2016-07-01', date '2028-12-31', interval 1 day) as t(d)
)

select
    date_key,
    year(date_key) as year,
    month(date_key) as month,
    date_trunc('month', date_key)::date as month_start,
    date_trunc('week', date_key)::date as week_start,
    isodow(date_key) as iso_day_of_week,
    isodow(date_key) >= 6 as is_weekend
from spine
