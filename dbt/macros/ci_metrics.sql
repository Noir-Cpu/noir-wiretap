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
    -- Same rule with runs triggered by dependabot[bot] left out (its updater runs and its PR checks).
    count(*) filter (where ci_outcome in ('pass', 'fail') and not is_dependabot) as decided_runs_excl_dependabot,
    count(*) filter (where ci_outcome = 'pass' and not is_dependabot) as passed_runs_excl_dependabot,
    count(*) filter (where ci_outcome = 'fail' and not is_dependabot) as failed_runs_excl_dependabot,
    round(count(*) filter (where ci_outcome = 'pass' and not is_dependabot) * 1.0
          / nullif(count(*) filter (where ci_outcome in ('pass', 'fail') and not is_dependabot), 0), 4) as ci_pass_rate_excl_dependabot,
    median(duration_seconds) filter (where ci_outcome in ('pass', 'fail')) as median_duration_seconds
{% endmacro %}
