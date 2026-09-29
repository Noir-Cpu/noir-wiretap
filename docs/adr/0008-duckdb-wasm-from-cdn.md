# ADR 0008: Evidence's DuckDB-WASM binaries load from jsDelivr

Status: accepted

Evidence runs queries in the browser with DuckDB-WASM. Its two binaries (33 MiB and 37 MiB) exceed the 25 MiB per-file limit of Workers static assets, so `wrangler deploy` refuses the build. `scripts/externalize_wasm.mjs` runs after the Evidence build, rewrites the two chunk modules that export the binary URLs to the same version on `cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@<installed version>`, and removes the binaries from the output. The script throws if Evidence's layout changes.

Consequences: the site has a runtime dependency on jsDelivr (a page cannot render its charts if it is unreachable), and the pinned Evidence version must keep matching `@duckdb/duckdb-wasm` in `node_modules`. The file sizes are from `ls -la` on the build output.

Alternative not taken: a pure-HTML export with the results inlined would avoid the dependency but abandons Evidence.
