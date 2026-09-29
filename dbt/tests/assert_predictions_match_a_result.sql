{{ config(severity='warn') }}
-- Warns (does not fail) when a prediction for a match played more than 3 days ago has no result row: usually a
-- team-name mismatch between the ledger and the results files, which would silently shrink the scored sample.
select prediction_key, home_team, away_team, date_key
from {{ ref('fct_prediction') }}
where not is_scored and date_key < current_date - interval 3 day
