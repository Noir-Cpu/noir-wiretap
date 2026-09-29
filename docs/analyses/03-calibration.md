# Analysis 3: INFORMANT calibration and RPS

Status on 2026-09-29: **not enough data yet.** The prediction ledger (`predictions/ledger.jsonl` in noir-informant) is empty, so there are 0 scored predictions and this analysis publishes no accuracy number. The published page enforces the same rule in code: below 30 scored first predictions it shows coverage counts only.

## How it will be measured

- Source: the hash-chained ledger, one row per published prediction with probabilities `[pH, pD, pA]` and bookmaker probabilities (margin removed) when available. Predictions first seen under 2 hours before kick-off go to `skipped.jsonl` and are counted, not scored.
- Join: a prediction is scored when a result exists for the same division, date, home and away team. A warning test flags predictions for matches played more than 3 days ago that found no result (a team-name mismatch would silently shrink the sample).
- Scores (`mart_calibration`, defined once in `macros/calibration_metrics.sql`): ranked probability score over the ordered outcomes home, draw, away, and log loss, both lower-is-better. Bookmaker RPS is computed on exactly the same matches, and the model's RPS is also reported on only the bookmaker-covered matches, so the comparison is like for like.
- Only the first prediction per match and model is analysed, so a re-publication cannot be counted twice.
- Reliability: `mart_calibration_bins` compares mean predicted probability with the observed frequency in 10% bins.

## Verification done

`tests/test_calibration.py` builds a throwaway warehouse with three fixture matches (fixtures live only in that test) and checks the mart against RPS and log-loss values computed by hand: duplicates and unplayed matches are excluded, the bookmaker comparison uses only matches with odds, and `has_enough_data` is false with 3 scored predictions and true when the threshold is lowered to 3.

## Limits to keep in mind once data arrives

- 30 scored predictions is a floor for showing a number, not for drawing a conclusion. A season is 380 matches per league; a month has about 60 to 80.
- RPS differences between a model and the bookmaker are small in absolute terms; report the difference with its uncertainty, not a ranking.
- Predictions are scored once, at the first publication; later corrections are visible in the ledger but not in the metric.
