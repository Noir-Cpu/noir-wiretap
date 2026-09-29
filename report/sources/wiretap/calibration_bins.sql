-- Placeholder row when empty, see calibration.sql.
select * from marts.mart_calibration_bins
union all by name
select null as calibration_bin_key where not exists (select 1 from marts.mart_calibration_bins)
