# ADR 0008: Evidence's DuckDB-WASM binaries load from jsDelivr

Status: accepted

Evidence runs queries in the browser with DuckDB-WASM. Its two binaries (33 MiB and 37 MiB) exceed the 25 MiB per-file limit of Workers static assets, so `wrangler deploy` refuses the build. `scripts/externalize_wasm.mjs` runs after the Evidence build, rewrites the two chunk modules that export the binary URLs to the same version on `cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@<installed version>`, and removes the binaries from the output. The script throws if Evidence's layout changes.

Consequences: the site has a runtime dependency on jsDelivr (a page cannot render its charts if it is unreachable), and the pinned Evidence version must keep matching `@duckdb/duckdb-wasm` in `node_modules`. The file sizes are from `ls -la` on the build output.

Alternative not taken: a pure-HTML export with the results inlined would avoid the dependency but abandons Evidence.

Update 2026-10-06 (ADR 0010): the worker that downloads the binary is patched to send a Subresource Integrity hash (sha384 of the file in `node_modules`), the Content-Security-Policy allows `cdn.jsdelivr.net` only for the explorer, and DuckDB-WASM was found to fetch one more file at start-up, its parquet extension from `extensions.duckdb.org`. The explorer now loads the engine only when the visitor asks. Alternatives (self-hosting in pieces, R2, dropping the engine) are written up in ADR 0010.
