// Cloudflare Workers assets allow files up to 25 MiB; Evidence's in-browser DuckDB binaries are 33-39 MiB.
// Point the two wasm imports at the same version on jsDelivr and drop the binaries from the build.
// The worker that downloads the binary is patched to pass a Subresource Integrity hash (sha384 of the file in
// node_modules), so the browser refuses a binary that differs from the one this build was made with.
// See docs/adr/0008-duckdb-wasm-from-cdn.md and docs/adr/0010-security-headers-and-seo.md.
import { readFileSync, writeFileSync, readdirSync, rmSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../report/", import.meta.url));
const pkg = join(root, "node_modules/@duckdb/duckdb-wasm");
const version = JSON.parse(readFileSync(join(pkg, "package.json"), "utf8")).version;
const assets = join(root, "build/_app/immutable/assets");
const chunks = join(root, "build/_app/immutable/chunks");
const workers = join(root, "build/_app/immutable/workers");

for (const variant of ["eh", "mvp"]) {
  const wasm = readdirSync(assets).find((f) => f.startsWith(`duckdb-${variant}.`) && f.endsWith(".wasm"));
  const chunk = readdirSync(chunks).find((f) => new RegExp(`^duckdb-${variant}\\.[^.]+\\.js$`).test(f));
  const worker = readdirSync(workers).find((f) => f.startsWith(`duckdb-browser-${variant}.worker-`) && f.endsWith(".js"));
  if (!wasm || !chunk || !worker) throw new Error(`duckdb-${variant} wasm, chunk or worker not found; Evidence layout changed`);
  const url = `https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${version}/dist/duckdb-${variant}.wasm`;
  const file = join(chunks, chunk);
  const before = readFileSync(file, "utf8");
  if (!before.includes(wasm)) throw new Error(`${chunk} does not reference ${wasm}`);
  writeFileSync(file, before.replace(/"[^"]*\.wasm"/, JSON.stringify(url)));

  // The installed package file and the build's copy must be the same bytes, or the hash would not describe what Evidence compiled against.
  const sri = "sha384-" + createHash("sha384").update(readFileSync(join(pkg, "dist", `duckdb-${variant}.wasm`))).digest("base64");
  const wfile = join(workers, worker);
  const wsrc = readFileSync(wfile, "utf8");
  const needle = "new Request(this.mainModuleURL)";
  const count = wsrc.split(needle).length - 1;
  if (count < 1) throw new Error(`${worker}: ${needle} not found; duckdb-wasm changed how it fetches the binary`);
  writeFileSync(wfile, wsrc.replaceAll(needle, `new Request(this.mainModuleURL,{integrity:${JSON.stringify(sri)}})`));

  rmSync(join(assets, wasm));
  console.log(`duckdb-${variant}.wasm -> ${url} (${sri.slice(0, 20)}..., ${count} fetch sites)`);
}
