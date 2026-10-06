// Post-processes the Evidence build (report/build) before it is copied to site/explore:
//  1. Replaces Evidence's inline start script with a gate (scripts/explore/wiretap-gate.js) so the heavy
//     JavaScript and the DuckDB-WASM engine load only after the visitor presses "Load interactive explorer".
//  2. Drops the modulepreload hints (they would fetch the whole module graph up front); the gate re-adds them on click.
//  3. Adds a description and noindex, removes Evidence's twitter:site (@evidence_dev), links the static twin of each page.
// Every inline script left in the pages is the theme bootstrap, which scripts/build_headers.py hashes for the CSP.
// Throws if Evidence's markup changes. See docs/adr/0010-security-headers-and-seo.md.
import { readFileSync, writeFileSync, readdirSync, statSync, copyFileSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const here = fileURLToPath(new URL("./", import.meta.url));
const build = join(here, "../report/build");
const esc = (t) => t.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

copyFileSync(join(here, "explore/wiretap-gate.js"), join(build, "wiretap-gate.js"));
copyFileSync(join(here, "explore/wiretap-gate.css"), join(build, "wiretap-gate.css"));

function walk(dir, out = []) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (f.endsWith(".html")) out.push(p);
  }
  return out;
}

// /explore/analyses/home-advantage.html or /explore/index.html -> the static page that shows the same marts.
function staticTwin(rel) {
  const route = "/" + rel.replace(/index\.html$/, "").replace(/\.html$/, "").replace(/\/$/, "");
  return route === "/" ? "/" : route + "/";
}

let n = 0;
for (const file of walk(build)) {
  let html = readFileSync(file, "utf8");
  if (html.includes("wiretap-gate.js")) continue;
  const rel = relative(build, file);
  if (!html.includes("__sveltekit_")) continue; // not an Evidence page (e.g. 404 shell)

  const m = html.match(/<script>\s*\{\s*(__sveltekit_\w+) = \{\s*base: "([^"]*)",\s*assets: "([^"]*)"\s*\};\s*const element = document\.currentScript\.parentElement;\s*const data = (\[[^\]]*\]);\s*Promise\.all\(\[\s*import\("([^"]+)"\),\s*import\("([^"]+)"\)\s*\]\)\.then\(\(\[kit, app\]\) => \{\s*kit\.start\(app, element, \{\s*node_ids: (\[[^\]]*\]),[\s\S]*?\}\);\s*\}\);\s*\}\s*<\/script>/);
  if (!m) throw new Error(`${rel}: Evidence start script not recognised; its markup changed`);
  const [whole, global, base, assets, data, start, app, nodeIds] = m;

  const preload = [...html.matchAll(/<link rel="modulepreload" href="([^"]+)">/g)].map((x) => x[1]);
  html = html.replace(/\s*<link rel="modulepreload" href="[^"]+">/g, "");

  const title = (html.match(/<title>([^<]*)<\/title>/) || [, "WIRETAP"])[1];
  const twin = staticTwin(rel);
  const gate = `<div class="wt-gate" id="wiretap-gate"><main>
<p class="wt-case">INTERACTIVE REPORT</p>
<h1>${title}</h1>
<p>This is the interactive version of the WIRETAP report, built with Evidence. It runs a database engine (DuckDB, compiled to WebAssembly) inside your browser. That is a download of about 10 MB and a noticeable amount of memory, so it only starts when you ask.</p>
<p><button type="button" class="wt-btn" id="wt-load" hidden>Load interactive explorer</button></p>
<p role="status" id="wt-status"></p>
<div class="wt-note">The same numbers are on a <a href="${twin}">lightweight static page</a> that needs no JavaScript.</div>
<noscript><p>The interactive explorer needs JavaScript. The <a href="${twin}">static page</a> does not.</p></noscript>
</main></div>`;
  const loader = `<script src="/explore/wiretap-gate.js" data-global="${global}" data-base="${esc(base)}" data-assets="${esc(assets)}" data-start="${esc(start)}" data-app="${esc(app)}" data-node-ids="${esc(nodeIds)}" data-data="${esc(data)}" data-preload="${esc(preload.join(" "))}"></script>`;
  html = html.replace(whole, () => loader);

  // The empty <script></script> Evidence leaves at the top of <body> is inline code the CSP would have to allow.
  html = html.replace(/<body>\s*<script>\s*<\/script>/, "<body>");
  html = html.replace("<body>", () => "<body>\n" + gate);

  const description = `${title.replace(/^WIRETAP$/, "Overview")}: the interactive Evidence version of a WIRETAP warehouse report. A static version with the same numbers is linked from the page.`;
  html = html
    .replace(/<meta name="twitter:site" content="[^"]*">/, "")
    .replace("</head>", () => `<meta name="description" content="${esc(description)}"><meta name="robots" content="noindex, follow"><link rel="stylesheet" href="/explore/wiretap-gate.css"></head>`);
  // The old scrollbox patch (appended by an earlier version of this build) is now part of wiretap-gate.js.
  html = html.replace(/<script>new MutationObserver[\s\S]*?<\/script>/, "");
  writeFileSync(file, html);
  n++;
}
if (n === 0) throw new Error("no Evidence pages processed");
console.log(`gated ${n} Evidence pages`);
