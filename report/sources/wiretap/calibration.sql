-- Evidence cannot store a zero-row result (empty parquet), so one all-null placeholder row is returned when the
-- mart is empty. The page only reads this after checking calibration_status.scored.
select * from marts.mart_calibration where grain = 'all_time' and has_enough_data
union all by name
select null as calibration_key where not exists (select 1 from marts.mart_calibration where grain = 'all_time' and has_enough_data)
