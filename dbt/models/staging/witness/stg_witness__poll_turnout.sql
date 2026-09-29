{{ config(tags=['witness']) }}

-- Schema-only contract for the future WITNESS aggregates export: zero rows, no source table yet.
-- Column names must stay inside var('witness_allowed_columns'); see docs/adr/0003-witness-aggregates-only.md.
select
    null::varchar as poll_id,
    null::timestamp as hour_bucket_utc,
    null::integer as eligible_count,
    null::integer as ballots_cast_count,
    null::integer as cast_count
where false
