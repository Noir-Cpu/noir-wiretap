# ADR 0005: INFORMANT predictions extension point

Status: accepted (extension point only)

INFORMANT will publish model predictions in the same repo under `predictions/`, in a format the lead has not defined. WIRETAP must not guess it.

What exists:

- `informant.predictions` is declared in `dbt/models/staging/_sources.yml` with a description and no columns, no freshness rule and no tests, so nothing depends on a table that does not exist.
- The match data model is model-agnostic: `fct_match` holds results only, keyed by `match_key`, which is a hash of league, season, date, home team and away team. Predictions will join on that natural key.
- `pipeline/informant_source.py` is the place to add a second resource once the format exists.

What to do when the format is defined: add a resource that reads `predictions/`, add columns and freshness to the source declaration, add `stg_informant__predictions`, `fct_prediction` (grain: one prediction per match per model version) and a calibration mart. Do not add a prediction column to `fct_match`: several model versions will predict the same match.

Calibration (the second analysis in the brief) depends on this and is not built.
