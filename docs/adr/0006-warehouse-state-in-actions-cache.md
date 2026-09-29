# ADR 0006: The warehouse file persists between nightly runs in the Actions cache

Status: accepted

Two things need state across runs: dlt incremental cursors (stored in the DuckDB file) and the `snap_repo` snapshot, which only has history if earlier versions survive. Each Actions run starts empty, so the nightly workflow restores `warehouse/` from `actions/cache` (newest `warehouse-*` key) and saves it under `warehouse-<run_id>` after a successful build. No commit to main, no secrets, no external store.

Failure modes, stated plainly:

- Caches are evicted after 7 days without access or under the repository size limit. A nightly run keeps it alive; if it is lost, incremental loads restart from the 2020-01-01 floor (safe, the load is idempotent) but snapshot history restarts (data loss for the SCD).
- A failed build does not save the cache, so a bad run cannot poison the next.

Alternatives considered: committing the database to a branch (noisy, and the brief says commit nothing to main), Parquet on R2 (better, needs a bucket and keys that do not exist yet; the intended upgrade).
