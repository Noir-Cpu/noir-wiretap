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
