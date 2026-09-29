// Cloudflare Workers assets allow files up to 25 MiB; Evidence's in-browser DuckDB binaries are 33-39 MiB.
// Point the two wasm imports at the same version on jsDelivr and drop the binaries from the build.
// See docs/adr/0008-duckdb-wasm-from-cdn.md.
import { readFileSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../report/", import.meta.url));
const version = JSON.parse(readFileSync(join(root, "node_modules/@duckdb/duckdb-wasm/package.json"), "utf8")).version;
const assets = join(root, "build/_app/immutable/assets");
const chunks = join(root, "build/_app/immutable/chunks");

for (const variant of ["eh", "mvp"]) {
  const wasm = readdirSync(assets).find((f) => f.startsWith(`duckdb-${variant}.`) && f.endsWith(".wasm"));
  const chunk = readdirSync(chunks).find((f) => new RegExp(`^duckdb-${variant}\\.[^.]+\\.js$`).test(f));
  if (!wasm || !chunk) throw new Error(`duckdb-${variant} wasm or chunk not found; Evidence layout changed`);
  const url = `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${version}/dist/duckdb-${variant}.wasm`;
  const file = join(chunks, chunk);
  const before = readFileSync(file, "utf8");
  if (!before.includes(wasm)) throw new Error(`${chunk} does not reference ${wasm}`);
  writeFileSync(file, before.replace(/"[^"]*\.wasm"/, JSON.stringify(url)));
  rmSync(join(assets, wasm));
  console.log(`duckdb-${variant}.wasm -> ${url}`);
}

// Evidence's DataTable wraps wide tables in a scrollable div that keyboard users cannot focus (axe rule
// scrollable-region-focusable). Make each such region focusable and named as soon as it appears.
import { readdirSync as ls, statSync } from "node:fs";
const fix = `<script>new MutationObserver(function(){document.querySelectorAll('.scrollbox:not([tabindex])').forEach(function(el){el.setAttribute('tabindex','0');el.setAttribute('role','region');el.setAttribute('aria-label','Scrollable table')})}).observe(document.documentElement,{childList:true,subtree:true})</script>`;
function walk(dir) {
  for (const f of ls(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (f.endsWith(".html")) {
      const t = readFileSync(p, "utf8");
      if (!t.includes("scrollbox:not")) writeFileSync(p, t.replace("</body>", fix + "</body>"));
    }
  }
}
walk(join(root, "build"));
console.log("focusable scroll regions patched");
