# CASE 004 / WIRETAP

**Verdict: a small, tested warehouse over the NOIR systems is running end to end on real data (GitHub activity and 7,719 league matches), with metrics defined once; the INFORMANT prediction ledger is wired in and tested but still empty, and the DISPATCH and WITNESS sources are specified but not loaded because their data does not exist yet.**

Live: https://noir-wiretap.noir-cpu.workers.dev

## The brief

Data-engineering roles screen for SQL, data modelling, pipelines, data quality and reporting. WIRETAP listens in on the NOIR cases and answers questions from data John owns. Rule from the programme brief: WITNESS data enters only as aggregates.

## The evidence

All from runs on 2026-09-29. Commands in brackets.

- `make run` from a warm venv: extract, freshness, `dbt build`. dbt: 307 of 307 nodes pass: 273 data tests, 32 models, 1 seed, 1 snapshot, 0 warnings [`dbt build`]. The earlier 46 s wall-clock timing was before the prediction models; not re-timed.
- Python tests: 16 passed [`make test`]: rate-limit handling, CSV and ledger parsing, the WITNESS guard failing on `voter_id`, `ballot_reference`, an unknown column and an unguarded WITNESS model, and the calibration mart against hand-computed RPS and log loss on fixture rows (fixtures exist only inside that test).
- All 21 mart models have every column documented and a `unique` + `not_null` test on their key. Marts also carry relationship tests to dimensions and singular tests (rollup rows equal the sum of detail rows, rates in 0..1, ledger hash chain, probabilities sum to 1).
- Loaded: 7,719 matches (Premier League 3,850, La Liga 3,869), 6 repos, 205 workflow runs, 0 predictions (ledger empty) [`make findings`].
- Source freshness passes: GitHub load within 26 h warn / 30 h error; INFORMANT collector heartbeat (`last_checked.json`) within 14 h warn / 30 h error [`dbt source freshness`].
- The type 2 snapshot `snap_repo` works: changing a repo description in a copy of the warehouse produced a second version and flipped `is_current` [tested by hand on a copy; not an automated test].
- Site, deployed URL, Lighthouse mobile defaults [`npx lighthouse`], one run per page: the static pages `/`, `/analyses/home-advantage/`, `/analyses/delivery-and-ci/`, `/analyses/calibration/`, `/about/` all score 100 / 100 / 100 / 100 (performance, accessibility, best practices, SEO), LCP 1.1 to 1.2 s, 3 to 5 KiB transferred. The interactive Evidence report at `/explore/analyses/home-advantage` scored performance 55 (LCP 22.1 s, 10.6 MiB) in the same run; it downloads a 34 MB in-browser database engine (ADR 0009). axe (WCAG 2.0/2.1 A and AA, 390 px wide, light and dark): 0 violations on the 5 static and 7 tested `/explore` pages; the earlier `scrollable-region-focusable` violation is fixed by a post-build script.

Three analyses, with the numbers and the caveats: [home advantage, Premier League vs La Liga](docs/analyses/01-home-advantage.md) (Premier League 2020/21 home win rate 37.9% against 45.4% in its other nine seasons, suggestive after multiple-comparison correction; the leagues overall do not differ, 44.5% vs 45.5%) and [delivery cadence and CI reliability](docs/analyses/02-delivery-and-ci.md) (all history is one day long, so it shows a starting point, not a cadence; CI pass rate is shown with and without Dependabot runs), and [calibration](docs/analyses/03-calibration.md) (**not enough data yet**: the prediction ledger is empty, so the page shows no accuracy number until 30 predictions are scored).

## The method

```
GitHub REST API ──┐                         ┌── staging (views)
                  ├─ dlt ─▶ DuckDB raw_* ─▶ dbt ── intermediate ── marts (star schema) ─▶ Evidence (/explore) + static HTML (/) ─▶ Workers assets
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
| INFORMANT predictions | built and tested on fixtures; ledger empty (ADR 0005) |
| DISPATCH `order_events` | contract only (ADR 0004); not faked |
| WITNESS | aggregates only, schema-only model plus guard (ADR 0003) |

ADRs: [docs/adr](docs/adr). Setup for John: [docs/SETUP.md](docs/SETUP.md). Open items: [docs/NEXT.md](docs/NEXT.md).

## The verdict

Good enough to show as a modelling and data-quality exercise, not yet as the "warehouse over every case" the brief describes. Cost: free tier throughout; the nightly job runtime is not measured yet (see the Actions tab). Scale is not tested: the warehouse is under 100 MB and the pipeline is a single-process batch.

## Open leads

- On-time delivery (needs DISPATCH events).
- WITNESS export job and minimum bucket size (ADR 0003).
- Warehouse state on R2 Parquet instead of the Actions cache (ADR 0006).
- Evidence loads its DuckDB-WASM binaries from jsDelivr because of the Workers 25 MiB asset limit (ADR 0008); the default pages are static HTML (ADR 0009).
- The calibration analysis on real data, once the ledger has 30 scored predictions.
- Hash recomputation for the ledger chain (needs INFORMANT's hashing spec).
