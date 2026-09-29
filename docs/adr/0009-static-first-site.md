# ADR 0009: A static HTML site is the default; Evidence lives under /explore

Status: accepted

Measured problem: the Evidence-only site scored Lighthouse performance 39 on mobile (LCP 10.2 s, 10.6 MiB transferred) on the deployed URL.

What was tried and found:

- Evidence queries run in the browser: charts and tables are empty without JavaScript (checked with JavaScript disabled: the prerendered HTML has the text but no chart or table data).
- With the DuckDB-WASM binary replaced by a stub, the page still rendered, but Lighthouse performance only reached 44 (LCP 8.4 s, 3.2 MiB): the rest of Evidence's JavaScript is the bulk, and the stub added a console error. Evidence has no supported switch for static-only pages.

Decision: `scripts/build_static.py` renders the pages that need no interactivity (overview, three analyses, about) as plain HTML with inline SVG charts and semantic tables, straight from the same mart columns, with no JavaScript. The Evidence report stays as the interactive version under `/explore` (`deployment.basePath`). Both are published in one Workers assets directory, `site/`.

Consequences:

- The default pages are fast and keyboard/screen-reader friendly. The written findings come from `docs/analyses/*.md`, one source for the repo and the site.
- Two renderers show the same marts. Neither computes a metric, so they cannot disagree; the static charts are simpler than Evidence's (no hover, no sorting).
- Evidence's DataTable scroll container is made keyboard-focusable by a small injected script after the build (`scripts/externalize_wasm.mjs`), which will need revisiting if Evidence changes its markup.
- Evidence cannot store an empty query result (zero-row parquet fails the build), so its source queries for the empty prediction marts return one all-null placeholder row; the page checks the status query first.
