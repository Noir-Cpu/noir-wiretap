{%- set cols = "null::bigint as seq, null::varchar as prev, null::varchar as hash, null::varchar as match_division, null::varchar as match_date, null::varchar as match_home, null::varchar as match_away, null::varchar as kickoff_utc, null::double as p_home, null::double as p_draw, null::double as p_away, null::double as book_home, null::double as book_draw, null::double as book_away, null::varchar as model, null::varchar as params_sha, null::varchar as data_sha, null::varchar as published_at" -%}
with src as (
    {{ source_or_empty('informant', 'predictions', "select " ~ cols ~ " where false") }}
)

select
    hash as prediction_id,
    seq as ledger_seq,
    prev as prev_hash,
    match_division as league_code,
    try_cast(match_date as date) as match_date,
    match_home as home_team,
    match_away as away_team,
    try_cast(kickoff_utc as timestamptz) as kickoff_at,
    p_home,
    p_draw,
    p_away,
    book_home,
    book_draw,
    book_away,
    model as model_name,
    params_sha,
    data_sha,
    try_cast(published_at as timestamptz) as published_at
from src
