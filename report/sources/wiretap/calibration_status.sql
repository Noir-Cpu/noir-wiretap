select
    (select count(*) from marts.fct_prediction) as predictions,
    (select count(*) from marts.fct_prediction where is_scored and is_first_for_match_model) as scored,
    (select count(*) from marts.fct_skipped_prediction) as skipped
