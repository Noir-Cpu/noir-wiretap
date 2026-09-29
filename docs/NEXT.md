# NEXT

## Actions only John can do, in order

1. Set the Cloudflare secrets so the nightly workflow publishes (see docs/SETUP.md):
   `gh secret set CLOUDFLARE_API_TOKEN --repo Noir-Cpu/noir-wiretap` and `gh secret set CLOUDFLARE_ACCOUNT_ID --repo Noir-Cpu/noir-wiretap`.
2. Trigger a first nightly run to confirm: `gh workflow run nightly.yml --repo Noir-Cpu/noir-wiretap`.
3. Decide the questions below.

## Questions

1. Which format will INFORMANT predictions use (columns, model-version field, one row per match per model)? Default: wait for your definition; the extension point is ADR 0005.
2. WITNESS: will the WITNESS export job emit only the five allowed columns, and what minimum poll size before an hourly bucket is published? Default: buckets under 10 ballots are merged into the neighbouring hour (not decided).
3. DISPATCH: accept the `order_events` contract in ADR 0004, and add an `is_simulated` flag? Default: yes to both.
4. Move the warehouse state from the Actions cache to Parquet on R2 (needs a bucket and keys)? Default: not until the SCD history matters.
5. Should CI pass rate exclude Dependabot updater runs? Default: keep them in for now, and add a `workflow_kind` split when there is more data.
