# CASE 004 / WIRETAP

**Verdict: a small, tested warehouse over the NOIR systems is running end to end on real data (GitHub activity and 7,719 league matches), with metrics defined once; the INFORMANT prediction ledger is wired in and tested but still empty, and the DISPATCH and WITNESS sources are specified but not loaded because their data does not exist yet.**

Live: https://noir-wiretap.noir-cpu.workers.dev

## The brief

Data-engineering roles screen for SQL, data modelling, pipelines, data quality and reporting. WIRETAP listens in on the NOIR cases and answers questions from data John owns. Rule from the programme brief: WITNESS data enters only as aggregates.

## The evidence

All from runs on 2026-09-29. Commands in brackets.

- `make run` from a warm venv: extract, freshness, `dbt build`. dbt: 309 of 309 nodes pass (re-run 2026-10-06): 274 data tests, 33 models, 1 seed, 1 snapshot, 0 warnings [`dbt build`]. The earlier 46 s wall-clock timing was before the prediction models; not re-timed.
- Python tests: 18 passed [`make test`]: rate-limit handling, CSV and ledger parsing, the WITNESS guard failing on `voter_id`, `ballot_reference`, an unknown column and an unguarded WITNESS model, and the calibration mart against hand-computed RPS and log loss on fixture rows (fixtures exist only inside that test).
- All 21 mart models have every column documented and a `unique` + `not_null` test on their key. Marts also carry relationship tests to dimensions and singular tests (rollup rows equal the sum of detail rows, rates in 0..1, ledger hash chain, probabilities sum to 1).
- Loaded: 7,719 matches (Premier League 3,850, La Liga 3,869), 6 repos, 205 workflow runs, 0 predictions (ledger empty) [`make findings`].
- Source freshness passes: GitHub load within 26 h warn / 30 h error; INFORMANT collector heartbeat (`last_checked.json`) within 14 h warn / 30 h error [`dbt source freshness`].
- The type 2 snapshot `snap_repo` works: changing a repo description in a copy of the warehouse produced a second version and flipped `is_current` [tested by hand on a copy; not an automated test].
- Site quality, measured 2026-10-06 with Lighthouse 13.5 (`npx lighthouse`, mobile and desktop presets), one run per page. Before (deployed URL): the five static pages score 100 / 100 / 100 / 100 (performance, accessibility, best practices, SEO), mobile LCP 0.8 to 1.5 s, 3 to 5 KiB; `/explore/` scored performance 67 (LCP 9.5 s, TBT 160 ms, 10.4 MiB), `/explore/analyses/home-advantage` 68 (LCP 5.5 s, TBT 280 ms), SEO 91, no security headers. After (the same code built and served locally with `wrangler dev`, which also serves the `_headers` rules): the static pages still score 100 on all four, mobile LCP 0.6 to 0.7 s, 3.7 to 5.7 KiB. `/explore/` opens as a notice with a "Load interactive explorer" button and downloads 0.08 MiB until it is pressed: performance 100, LCP 1.4 s, TBT 0 ms (a local build of the previous version measured 71, LCP 8.4 s, so local and deployed numbers agree). `/explore/` SEO is 63 on purpose: it is `noindex` (ADR 0010). The deployed numbers after merge are not measured yet.
- Accessibility and security tests in `e2e/` (Playwright, 58 tests, run in CI against `wrangler dev`): axe (WCAG 2.0 to 2.2 A and AA plus best practices) with 0 violations on the 5 static pages and the 404 page, light and dark, at 320 px and 1280 px; the explorer notice at 320 px, light and dark; two loaded explorer pages, light and dark. No Content-Security-Policy violation or page error on any page, with the policies of ADR 0010 enforced.
- Dependency audit 2026-10-06: `pip-audit` flagged `pytest` 8.4.2, now pinned to 9.0.3, clean. `npm audit` at the repo root 0 (a high advisory in `sharp`, pulled in by wrangler's local-dev runtime, is fixed with an `overrides` entry); for `report/` (Evidence) 42 advisories with no upstream fix, all in the build toolchain (ADR 0010).

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
- Nightly workflow (`.github/workflows/nightly.yml`): restore warehouse cache, extract, freshness gate (fails the run and skips the deploy), build and test, build site, deploy (only from `main`, only in this repository). Commits nothing. CI (`ci.yml`) also builds the site and runs the Playwright tests, `pip-audit` and `npm audit`.

| Source | State |
| --- | --- |
| GitHub | built |
| INFORMANT results | built |
| INFORMANT predictions | built and tested on fixtures; ledger empty (ADR 0005) |
| DISPATCH `order_events` | contract only (ADR 0004); not faked |
| WITNESS | aggregates only, schema-only model plus guard (ADR 0003) |

Security headers, SEO and the explorer gate: [ADR 0010](docs/adr/0010-security-headers-and-seo.md). ADRs: [docs/adr](docs/adr). Setup for John: [docs/SETUP.md](docs/SETUP.md). Open items: [docs/NEXT.md](docs/NEXT.md).

## The verdict

Good enough to show as a modelling and data-quality exercise, not yet as the "warehouse over every case" the brief describes. Cost: free tier throughout; the nightly job runtime is not measured yet (see the Actions tab). Scale is not tested: the warehouse is under 100 MB and the pipeline is a single-process batch.

## Open leads

- On-time delivery (needs DISPATCH events).
- WITNESS export job and minimum bucket size (ADR 0003).
- Warehouse state on R2 Parquet instead of the Actions cache (ADR 0006).
- Evidence loads its DuckDB-WASM binaries from jsDelivr (with an integrity hash) because of the Workers 25 MiB asset limit (ADR 0008), and a parquet extension from `extensions.duckdb.org`; it only loads when a visitor presses a button, and the report renders from prerendered results without it (ADR 0010). The default pages are static HTML (ADR 0009).
- The calibration analysis on real data, once the ledger has 30 scored predictions.
- Hash recomputation for the ledger chain (needs INFORMANT's hashing spec).
