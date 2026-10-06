# ADR 0010: Security headers, a gated explorer, and what search engines see

Status: accepted (2026-10-06)

Measured on the live site before this change (`curl -I`): no security headers at all, no `robots.txt` sitemap line, no `sitemap.xml`, an empty default 404, no canonical or social tags, and `/explore/` scoring Lighthouse SEO 91 (no meta description).

## Headers (`scripts/headers.template`, written to `site/_headers` by `scripts/build_headers.py`)

| Header | Value | Why |
| --- | --- | --- |
| `Content-Security-Policy`, static pages | `default-src 'none'; style-src 'sha256-...'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'` | The static pages run no JavaScript. The one inline stylesheet is allowed by hash, computed from the built HTML. `build_headers.py` fails the build if a static page gains an inline script, a `style=` attribute or a second stylesheet. `connect-src 'self'` exists only because Lighthouse fetches `robots.txt` from inside the page and reported "robots.txt is not valid" (SEO 92) when `default-src 'none'` blocked it. |
| `Content-Security-Policy`, `/explore/*` | `script-src 'self' 'wasm-unsafe-eval' <hash of the theme script>; style-src 'self' 'unsafe-inline'; connect-src 'self' https://cdn.jsdelivr.net https://extensions.duckdb.org; worker-src 'self' blob:; img-src 'self' data: blob:; font-src 'self' data:; ...` | `wasm-unsafe-eval`: DuckDB-WASM compiles a WebAssembly module (not JavaScript `eval`; no `unsafe-eval` is needed, checked by the Playwright run with the policy enforced). `cdn.jsdelivr.net`: the DuckDB binary (ADR 0008). `extensions.duckdb.org`: **new finding**, DuckDB-WASM downloads its signed parquet extension from there at start-up; it was an undocumented runtime dependency (seen in the network log of the live site). `style-src 'unsafe-inline'`: Evidence and Svelte set `style` attributes; those cannot be hashed. The only inline script left is the theme bootstrap, allowed by hash. |
| `X-Content-Type-Options` | `nosniff` | |
| `X-Frame-Options` / `frame-ancestors` | `DENY` / `'none'` | No reason to be framed. |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | |
| `Permissions-Policy` | camera, microphone, geolocation, payment, usb, sensors, `interest-cohort` all off | The site uses none of them. |
| `Cross-Origin-Opener-Policy` | `same-origin` | Tested: the explorer and WASM work with it. |
| `Cross-Origin-Embedder-Policy` | **not set** | Nothing here needs cross-origin isolation (Evidence uses the non-threaded DuckDB bundles, not `SharedArrayBuffer`). `require-corp` would make the page depend on jsDelivr's CORP headers for no gain. Not tested. |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | No `preload`: that is a one-way decision for John. |
| `Cache-Control` | `immutable`, one year, for `/explore/_app/immutable/*` (content-hashed by Vite); one day for `og-image.png`; everything else keeps Cloudflare's `max-age=0, must-revalidate` (ETag revalidation) | `/explore/data/*` and `/explore/api/*` are not marked immutable: their names are not proven to change when the data changes. |

Cloudflare merges every matching `_headers` rule, so `/explore/*` first removes the static CSP with `! Content-Security-Policy`. Browsers enforce every CSP header they receive, so two policies would intersect and break the explorer. Verified locally with `wrangler dev` (the explorer gets exactly one policy, the 404 page gets the strict one). **Not yet verified on the deployed site**; the first post-merge `curl -I` should confirm it.

`e2e/csp.spec.mjs` fails on any CSP violation, any page error, a missing header, and a weakened static policy. It includes a self-test that injects an inline script and expects the browser to report it, so a broken detector cannot pass silently.

## The 34 MB WASM engine

Findings from running the page with the policy and with the file blocked or altered:

1. The page content (tables, charts) is drawn from the query results Evidence prerenders (`/explore/api/prerendered_queries/*.arrow`). With the DuckDB binary request aborted, or answered with wrong bytes, the page still rendered all 12 matching table cells and the chart (the only symptom is an uncaught `Failed to fetch`). **For this report, which has no inputs or dropdowns, the engine is not needed to display anything today.** Whether to keep it is a decision for John (below).
2. Lazy loading. Evidence starts the engine as soon as any page opens. `scripts/postprocess_explore.mjs` now replaces Evidence's inline start script with `wiretap-gate.js`: every `/explore/*` page opens as a short notice with a "Load interactive explorer" button and a link to the static twin of the page. Nothing heavy is requested until the button is pressed (no module preloads, no data, no WASM; checked by `e2e/csp.spec.mjs`). The choice is remembered for the browser tab (`sessionStorage`). Measured with Lighthouse on a local build of each version, mobile: `/explore/` performance 71 to 100, LCP 8.4 s to 1.4 s, TBT 160 ms to 0 ms, transfer 10.28 MiB to 0.08 MiB. Those are the numbers for the gate state, which is what a crawler or a first-time visitor gets. Pressing the button (Playwright, no throttling): content visible about 0.95 s after the click, about 3.2 MiB through the page plus the engine (about 6.7 MB on the wire, fetched by the worker).
3. Integrity. The two `new Request(this.mainModuleURL)` calls in the DuckDB worker are patched to pass `integrity: sha384-...`, computed at build time from the file in `node_modules`. The URL already pins an exact version. I checked the hash of the file served by jsDelivr against the build's hash (equal), and a test serves wrong bytes and expects the fetch to be rejected. The integrity check cannot be applied to the parquet extension: DuckDB downloads it internally and verifies its own signature.

### Alternatives for the binary, not taken

- **Self-host from Workers assets, in pieces.** The limit is 25 MiB per file, so each binary (34.2 and 39.4 MB) would be split in two and reassembled in the worker before instantiation. Removes jsDelivr from the CSP and the runtime. Costs: a second patch to minified third-party code, about double the memory during reassembly, and about 74 MB of new assets on first deploy (later deploys upload only changed files). Not tried.
- **R2.** A public bucket on a custom domain with CORS would also remove jsDelivr and compresses at the edge. Needs a custom domain and a bucket (John), and still adds a third-party-looking origin to the CSP. `r2.dev` URLs are rate limited and not meant for production. Not tried.
- **Drop the engine** (finding 1). Smallest build, no jsDelivr, no `extensions.duckdb.org`, no `wasm-unsafe-eval`. It would change how Evidence behaves and needs a check of every page; not done here.

## Search engines

- Titles 30 to 65 characters, unique descriptions (70 to 165), a canonical URL, Open Graph and Twitter tags with a generated 1200x630 image (`assets/og-image.png`, source `assets/og-image.html`), `theme-color`, one `h1` per page and no skipped heading levels (the markdown analyses were nested one level too high and are shifted down; checked by test).
- `sitemap.xml` lists the five static pages. `robots.txt` allows everything and names the sitemap. It does not disallow `/explore/`, because a crawler that cannot fetch a page never sees its `noindex`.
- `/explore/*` is `noindex, follow` (header and meta). Judgement: it is near-duplicate content, it needs JavaScript to show data, it was the slow page, and Evidence's template tagged it with `twitter:site=@evidence_dev` (removed). Indexing it would hand search engines the weakest copy of each analysis. Consequence, measured: its Lighthouse SEO score drops from 91 to 63 because the `is-crawlable` audit fails, by design.
- JSON-LD: `WebSite` on the overview, `Article` on the three analyses, `AboutPage` on About. No `Dataset`: the underlying data has no published licence or download, so the record would claim more than exists. `dateModified` is the build date; `datePublished` is left out because no honest publication date exists in the repo.
- A real 404 page (`404.html`, served by `not_found_handling = 404-page`), `noindex`.

## Accessibility changes

Charts are in a focusable, labelled scroll region with a minimum width so axis text stays at least 12 px effective on a 320 px screen (before: 480-unit viewBox scaled to about 7 px). Legend swatches use classes instead of `style` attributes (needed for the CSP). An empty table header in the written analysis is now "League". The Evidence line chart sorted its x axis by value (2016/17, 2025/26, 2022/23, ...); `sort=false` restores chronological order. The CSS has no animation; the explorer notice and Evidence's logo animation respect `prefers-reduced-motion`. Chart colours (red and near-black on the page background) passed the dataviz validator's CVD, normal-vision and contrast checks in both themes; its lightness-band and chroma checks fail by design because one series is neutral ink, and marker shape plus the legend carry identity as well.

## Dependencies and workflows

- `pip-audit -r requirements.txt` found `pytest 8.4.2` (PYSEC-2026-1845, fixed in 9.0.3); pinned to 9.0.3, the 18 tests pass, audit clean.
- `npm audit` for the new root `package.json` (wrangler, Playwright, axe): 0. For `report/` (Evidence 40.1.8, the latest release): 42 advisories (8 critical, 15 high) in Evidence's build toolchain (vitest, vite, tinypool, svelte-kit, ...), none with an upstream fix; the only suggested "fix" downgrades Evidence to 29.0.3. They run at build time on the CI runner, not in the deployed output (the site is prerendered, no server). CI reports them without failing.
- Workflows: all third-party actions pinned by commit SHA with the version in a comment (Dependabot keeps both current); `permissions: contents: read` at the top of every workflow; secrets named only in the steps that need them (the GitHub token in the extract step, the Cloudflare pair in the deploy step, never while `pip install` or `npm ci` run); `persist-credentials: false`; timeouts; deploy only when `github.repository` is this repo, the credentials exist, and the ref is `main`; `wrangler` pinned in `package-lock.json` instead of `npx --yes wrangler@4`; no `${{ }}` expression is interpolated into a `run` script; CodeQL also scans the workflows. The nightly job's `actions: write` was removed: `actions/cache` authenticates with the runner's cache token, and that permission only matters for deleting caches. **That removal is untested until the next nightly run** (I did not run the deploy workflow).
