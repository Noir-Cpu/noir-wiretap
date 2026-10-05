# NEXT

## Decided by John (2026-09-29)

- Q2: WITNESS hourly buckets under 10 ballots are merged into the neighbouring hour (ADR 0003; a requirement on the future export).
- Q3: DISPATCH `order_events` contract accepted, with `is_simulated` (ADR 0004).
- Q4: CI pass rate shown with and without Dependabot runs (done).
- Q5: warehouse state stays in the Actions cache for now (ADR 0006).
- Predictions format: read from `predictions/ledger.jsonl` and `skipped.jsonl` (ADR 0005, done, ledger currently empty).

## Fixed 2026-10-05

- Nightly failed on stale `informant.collector_manifest`: its `fetched_at` only changes when a data file changes, and there were no matches since 20 Sept. Freshness now reads the collector heartbeat `data/last_checked.json` (`checked_at`, warn 14 h, error 30 h); manifest `fetched_at` is the `last_data_change_at` column only. `tests/test_freshness.py` proves a 20-day-old manifest passes and a 40-hour-old heartbeat fails (ADR 0007).

## Actions only John can do, in order

1. Set the Cloudflare secrets so the nightly workflow publishes (see docs/SETUP.md):
   `gh secret set CLOUDFLARE_API_TOKEN --repo Noir-Cpu/noir-wiretap` and `gh secret set CLOUDFLARE_ACCOUNT_ID --repo Noir-Cpu/noir-wiretap`.
2. Trigger a first nightly run to confirm: `gh workflow run nightly.yml --repo Noir-Cpu/noir-wiretap`.

## Open questions

1. What is INFORMANT's ledger hashing scheme (algorithm and fields hashed)? Default: keep checking only the `prev` links until it is written down; then recompute hashes in a dbt test.
2. Team names in the ledger must match the results files (football-data spelling). Default: assume they do; a warning test flags predictions with no matching result after 3 days.
3. The 30-prediction floor for showing a calibration number: keep it? Default: yes.

## Still open

- Calibration on real data (waits for the ledger). DISPATCH and WITNESS sources (do not exist yet).
- Evidence at `/explore` is slow to open (10.6 MiB, in-browser DuckDB); the static pages are the default.
