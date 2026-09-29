{# The single definition of CI reliability. A run counts only when it reached a verdict:
   success is a pass; failure and timed_out are fails. cancelled, skipped, neutral and
   action_required runs say nothing about reliability and are counted separately. #}
{% macro ci_metrics() %}
    count(*) filter (where ci_outcome in ('pass', 'fail')) as decided_runs,
    count(*) filter (where ci_outcome = 'pass') as passed_runs,
    count(*) filter (where ci_outcome = 'fail') as failed_runs,
    count(*) filter (where ci_outcome = 'excluded') as excluded_runs,
    round(count(*) filter (where ci_outcome = 'pass') * 1.0
          / nullif(count(*) filter (where ci_outcome in ('pass', 'fail')), 0), 4) as ci_pass_rate,
    median(duration_seconds) filter (where ci_outcome in ('pass', 'fail')) as median_duration_seconds
{% endmacro %}
