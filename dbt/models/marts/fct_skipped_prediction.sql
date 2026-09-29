-- Grain: one match the predictor skipped (first seen under 2 hours before kickoff). Coverage, not scoring.
select
    skipped_id as skipped_prediction_key,
    ledger_seq,
    league_code as league_key,
    match_date as date_key,
    home_team,
    away_team,
    kickoff_at,
    published_at,
    reason
from {{ ref('stg_informant__skipped_predictions') }}
