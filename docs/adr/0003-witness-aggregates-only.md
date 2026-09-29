# ADR 0003: WITNESS enters the warehouse as aggregates only

Status: accepted

WITNESS keeps voting secret by separating who participated from what was cast. Copying ballots or participation records into one warehouse would put both sides in one place with a join key, quietly undoing that design, however well the warehouse is secured.

Decision:

1. Only these shapes may be loaded: turnout per poll (a count of eligible voters and a count of ballots cast) and cast counts per poll per hour bucket (UTC). Poll identifiers are public poll ids, not people.
2. No voter, participant, ballot, receipt, session, token, e-mail or IP data, in any form, including hashed.
3. Enforcement is code, not convention. The dbt generic test `witness_aggregates_only` fails when a model has any column outside `var('witness_allowed_columns')` (`poll_id`, `hour_bucket_utc`, `eligible_count`, `ballots_cast_count`, `cast_count`); columns that look like voter or ballot identifiers get a specific failure reason. The singular test `assert_witness_models_are_guarded` fails when a model tagged `witness` (or reading a `witness` source) does not carry that test. `tests/test_witness_guard.py` runs dbt against throwaway models and checks that `voter_id`, `ballot_reference` and an unknown column fail, that an allowed model passes, and that an unguarded WITNESS model fails.
4. The producer side matters more: WITNESS should export the aggregate itself (a small export job or view that emits only these columns). The warehouse never gets read access to ballot or participation tables. The export does not exist yet; the WITNESS model here (`stg_witness__poll_turnout`) is a zero-row, schema-only contract.

Limit: small polls leak. A poll with three voters and hourly buckets can reveal who voted when. The export should suppress or merge buckets below a minimum size (a number John and the WITNESS design need to choose; not decided here).

The guard checks column names. It cannot detect an identifier hidden in an innocently named column, which is why the allowlist (not a blocklist) is the primary rule and why review of new WITNESS columns is required.
