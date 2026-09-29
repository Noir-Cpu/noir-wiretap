{# The single definition of the forecast-quality metrics. Rows are scored first predictions only.
   book_* metrics use only the matches that have bookmaker probabilities, and model_rps_on_book_matches scores the
   model on exactly those matches, so the comparison is like for like. #}
{% macro calibration_metrics() %}
    count(*) as scored_predictions,
    round(avg(rps), 5) as mean_rps,
    round(avg(log_loss), 5) as mean_log_loss,
    count(*) filter (where has_book) as book_matches,
    round(avg(rps) filter (where has_book), 5) as model_rps_on_book_matches,
    round(avg(book_rps), 5) as book_mean_rps,
    round(avg(rps) filter (where has_book) - avg(book_rps), 5) as rps_minus_book,
    round(avg(log_loss) filter (where has_book), 5) as model_log_loss_on_book_matches,
    round(avg(book_log_loss), 5) as book_mean_log_loss,
    count(*) >= {{ var('min_scored_predictions') }} as has_enough_data
{% endmacro %}
