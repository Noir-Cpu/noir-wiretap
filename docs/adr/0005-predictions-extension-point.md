# ADR 0005: INFORMANT predictions are read from the ledger

Status: accepted (supersedes the earlier extension-point-only version)

INFORMANT publishes predictions to `predictions/ledger.jsonl` in noir-informant: one hash-chained JSON object per line with `seq`, `prev`, `hash`, `match {division, date, home, away, kickoff_utc}`, `probs [pH, pD, pA]`, `book [pH, pD, pA] | null` (bookmaker, margin removed), `model`, `params_sha`, `data_sha`, `published_at`. `predictions/skipped.jsonl` has the same shape plus `reason` for matches first seen under 2 hours before kick-off.

Decisions:

- dlt reads both files (raw GitHub URL, or `INFORMANT_LOCAL_DIR`), flattens them and merges on `hash`. An empty file yields no rows, and dlt then creates no table, so staging falls back to a typed empty relation (`source_or_empty`, the same trick as releases). Zero rows pass every test.
- Joined to results on division, date, home team and away team. `assert_predictions_match_a_result` warns (not fails) when a prediction for a match played over 3 days ago has no result, because a team-name mismatch would silently shrink the scored sample.
- Scores: ranked probability score over ordered outcomes H, D, A, and log loss; bookmaker scores on the same matches; the model is also scored on only the bookmaker-covered matches. Only the first prediction per match and model counts. All defined once in `macros/calibration_metrics.sql` (ADR 0002).
- Below `min_scored_predictions` (30) scored predictions the mart flags `has_enough_data = false` and both report versions show coverage counts only, no accuracy number.
- Chain integrity: `assert_ledger_hash_chain` checks that each `prev` equals the previous record's `hash`. It does not recompute hashes (the hashing scheme is INFORMANT's to define); a stronger check needs that spec.

Verified against hand-computed values on fixture rows in `tests/test_calibration.py`. Not verified on real data: the ledger is empty.
