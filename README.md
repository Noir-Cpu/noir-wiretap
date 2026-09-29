# CASE 004 / WIRETAP

**Verdict: a small, tested warehouse over the NOIR systems is running end to end on real data (GitHub activity and 7,719 league matches), with metrics defined once; DISPATCH, WITNESS and prediction sources are specified but not loaded, because their data does not exist yet.**

Live: https://noir-wiretap.noir-cpu.workers.dev

## The brief

Data-engineering roles screen for SQL, data modelling, pipelines, data quality and reporting. WIRETAP listens in on the NOIR cases and answers questions from data John owns. Rule from the programme brief: WITNESS data enters only as aggregates.

## The evidence

All from runs on 2026-09-29. Commands in brackets.

- `make run` from a warm venv: extract, freshness, `dbt build` in 46 s wall clock [`time make run`]. dbt: 231 of 231 nodes pass: 204 data tests, 25 models, 1 seed, 1 snapshot, 0 warnings [`dbt build`].
- Python tests: 10 passed [`make test`]: rate-limit handling, CSV parsing, and the WITNESS guard failing on `voter_id`, `ballot_reference`, an unknown column and an unguarded WITNESS model.
- All 15 mart models have every column documented (checked against the built tables) and a `unique` + `not_null` test on their key. Marts also carry relationship tests to dimensions and singular tests (rollup rows equal the sum of detail rows, rates in 0..1, counts add up).
- Loaded: 7,719 matches (Premier League 3,850, La Liga 3,869), 6 repos, 158+ workflow runs, 29+ pull requests [`make findings`].
- Source freshness passes: GitHub load within 26 h warn / 30 h error; INFORMANT collector `fetched_at` within 12 h warn / 26 h error [`dbt source freshness`].
- The type 2 snapshot `snap_repo` works: changing a repo description in a copy of the warehouse produced a second version and flipped `is_current` [tested by hand on a copy; not an automated test].
- Site: axe (WCAG 2.0/2.1 A and AA) on four pages at 390 px width, light and dark: 0 violations on `/` and `/about`; on the two analysis pages only `scrollable-region-focusable` (2 and 1 nodes), which comes from Evidence's DataTable scroll container. No horizontal page scroll. Lighthouse (mobile default, local static server without compression) on `/analyses/home-advantage`: performance 42, accessibility 100, best practices 100, SEO 90. Production numbers are in the report below.

Two analyses, with the numbers and the caveats: [home advantage, Premier League vs La Liga](docs/analyses/01-home-advantage.md) (Premier League 2020/21 home win rate 37.9% against 45.4% in its other nine seasons, suggestive after multiple-comparison correction; the leagues overall do not differ, 44.5% vs 45.5%) and [delivery cadence and CI reliability](docs/analyses/02-delivery-and-ci.md) (all history is one day long, so it shows a starting point, not a cadence).

## The method

```
GitHub REST API ──┐                         ┌── staging (views)
                  ├─ dlt ─▶ DuckDB raw_* ─▶ dbt ── intermediate ── marts (star schema) ─▶ Evidence ─▶ Workers assets
INFORMANT CSVs ───┘                         └── snapshot snap_repo (SCD 2)
```

- `pipeline/`: dlt sources. `dbt/`: models, macros, tests, snapshot. `report/`: Evidence. `tests/`: pytest.
- Star schema: facts `fct_match`, `fct_workflow_run`, `fct_commit`, `fct_pull_request`, `fct_release`; dimensions `dim_date`, `dim_league`, `dim_season`, `dim_team`, `dim_repo`, `dim_repo_history` (SCD 2). Report marts: `mart_home_advantage`, `mart_ci_reliability`, `mart_delivery_cadence`, `mart_repo_summary`.
- Metrics defined once: `home_win_rate` and `ci_pass_rate` (ADR 0002).
- Nightly workflow (`.github/workflows/nightly.yml`): restore warehouse cache, extract, freshness gate (fails the run and skips the deploy), build and test, build site, deploy. Commits nothing.

| Source | State |
| --- | --- |
| GitHub | built |
| INFORMANT results | built |
| INFORMANT predictions | extension point only (ADR 0005) |
| DISPATCH `order_events` | contract only (ADR 0004); not faked |
| WITNESS | aggregates only, schema-only model plus guard (ADR 0003) |

ADRs: [docs/adr](docs/adr). Setup for John: [docs/SETUP.md](docs/SETUP.md). Open items: [docs/NEXT.md](docs/NEXT.md).

## The verdict

Good enough to show as a modelling and data-quality exercise, not yet as the "warehouse over every case" the brief describes. Cost: free tier throughout; the nightly job runtime is not measured yet (see the Actions tab). Scale is not tested: the warehouse is under 100 MB and the pipeline is a single-process batch.

## Open leads

- Calibration analysis (needs the predictions format) and on-time delivery (needs DISPATCH events).
- WITNESS export job and minimum bucket size (ADR 0003).
- Warehouse state on R2 Parquet instead of the Actions cache (ADR 0006).
- Evidence loads its DuckDB-WASM binaries from jsDelivr because of the Workers 25 MiB asset limit (ADR 0008).
- `scrollable-region-focusable` on Evidence data tables.
