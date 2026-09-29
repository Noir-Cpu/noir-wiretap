# ADR 0001: Python, dbt and DuckDB, not the Workers template

Status: accepted

The NOIR template is a Hono and Drizzle app on Workers. WIRETAP is a batch analytics job: extract, load, model, test, report. It has no API, no users and no auth, and the target roles (data and analytics engineering) screen for SQL, dbt and pipelines, so the repo keeps the template's CI, Dependabot, ADR and case-file conventions and drops `apps/api`, `packages/db`, auth and the Vite app.

Choices:

- dlt loads into DuckDB (schema inference, incremental state, merge on primary key).
- dbt Core with `dbt-duckdb` models staging, intermediate and marts (star schema).
- Evidence builds a static site from the marts. It deploys as a Workers static-assets site named `noir-wiretap`; it needs no secrets and no database at run time because the data is baked into the build.
- Everything runs in a repo-local Python venv (`.venv`), never globally.

Trade-off: DuckDB is a single-writer file, which is fine for a nightly batch and not for concurrent writers. Moving to BigQuery or Snowflake means swapping the dbt adapter and the dlt destination; this has not been tested here.
