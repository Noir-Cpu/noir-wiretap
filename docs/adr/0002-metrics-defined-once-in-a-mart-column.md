# ADR 0002: Metrics are defined once, in a macro and a mart column

Status: accepted

Two metrics matter: `home_win_rate` (per league-season) and `ci_pass_rate` (per repo and month). Each is computed in exactly one dbt macro (`home_advantage_metrics`, `ci_metrics`) that is used by exactly one mart model. The report only selects those columns; it never divides or aggregates counts. Rollups (all seasons, all time) are extra rows produced by the same macro in the same model, not recomputed in the report. Tests (`assert_all_rows_equal_sum_of_seasons`, `assert_ci_monthly_sums_to_all_time`) check that rollup rows agree with detail rows.

Why not the dbt Semantic Layer: MetricFlow needs an extra dependency and its own query path, and Evidence cannot query it. A metric that the report cannot read is a second definition waiting to happen. Revisit if a second consumer (an app) needs the metric via an API.

Trade-off: the metric is bound to the grain of the mart. A new grain needs a new mart model that reuses the macro.
