{%- set cols = "null::bigint as seq, null::varchar as hash, null::varchar as match_division, null::varchar as match_date, null::varchar as match_home, null::varchar as match_away, null::varchar as kickoff_utc, null::varchar as model, null::varchar as published_at, null::varchar as reason" -%}
with src as (
    {{ source_or_empty('informant', 'skipped_predictions', "select " ~ cols ~ " where false") }}
)

select
    hash as skipped_id,
    seq as ledger_seq,
    match_division as league_code,
    try_cast(match_date as date) as match_date,
    match_home as home_team,
    match_away as away_team,
    try_cast(kickoff_utc as timestamptz) as kickoff_at,
    model as model_name,
    try_cast(published_at as timestamptz) as published_at,
    reason
from src
