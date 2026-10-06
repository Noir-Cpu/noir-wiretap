import { test, expect } from "@playwright/test";
import { STATIC_PAGES, EXPLORE_PAGES, watch } from "./helpers.mjs";

const COMMON = {
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
  "referrer-policy": "strict-origin-when-cross-origin",
  "cross-origin-opener-policy": "same-origin",
};

test.describe("static pages: strict CSP, no violations", () => {
  for (const path of STATIC_PAGES) {
    test(path, async ({ page }) => {
      const w = watch(page);
      const res = await page.goto(path);
      await page.waitForLoadState("networkidle");
      const h = res.headers();
      for (const [k, v] of Object.entries(COMMON)) expect(h[k], k).toBe(v);
      expect(h["permissions-policy"]).toContain("camera=()");
      expect(h["strict-transport-security"]).toContain("max-age=");
      const csp = h["content-security-policy"];
      expect(csp).toContain("default-src 'none'");
      expect(csp).not.toContain("unsafe-inline");
      expect(csp).not.toContain("unsafe-eval");
      expect(csp).not.toContain("script-src"); // no scripts at all: default-src 'none' covers it
      expect(h["x-robots-tag"]).toBeUndefined();
      expect(await w.violations()).toEqual([]);
      expect(w.problems).toEqual([]);
      // No third-party requests, no scripts.
      expect(await page.evaluate(() => document.scripts.length - document.querySelectorAll('script[type="application/ld+json"]').length)).toBe(0);
    });
  }

  test("unknown path: 404 page carries the strict CSP too", async ({ request }) => {
    const res = await request.get("/no-such-page", { headers: { "sec-fetch-mode": "navigate" } });
    expect(res.status()).toBe(404);
    expect(res.headers()["content-security-policy"]).toContain("default-src 'none'");
    expect(res.headers()["x-content-type-options"]).toBe("nosniff");
  });

  test("the violation detector works: an injected inline script is reported", async ({ page }) => {
    const w = watch(page);
    await page.goto("/about/");
    await page.evaluate(() => {
      const s = document.createElement("script");
      s.textContent = "window.__ran = true";
      document.body.appendChild(s);
    });
    expect(await page.evaluate(() => window.__ran)).toBeUndefined();
    expect((await w.violations()).join("\n")).toMatch(/script-src|default-src/);
  });
});

test.describe("explorer: gated, heavy files only on request, CSP clean", () => {
  test("nothing heavy loads before the button is pressed", async ({ page }) => {
    const requests = [];
    page.on("request", (r) => requests.push(r.url()));
    const w = watch(page);
    const res = await page.goto("/explore/analyses/home-advantage");
    await page.waitForLoadState("networkidle");
    const h = res.headers();
    expect(h["content-security-policy"]).toContain("wasm-unsafe-eval");
    expect(h["content-security-policy"]).toContain("https://cdn.jsdelivr.net");
    expect(h["content-security-policy"]).not.toContain("default-src 'none'; style-src 'sha256"); // not the static policy
    expect(h["x-robots-tag"]).toBe("noindex, follow");
    await expect(page.getByRole("button", { name: "Load interactive explorer" })).toBeVisible();
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(requests.filter((u) => /jsdelivr|\.wasm|\.arrow|\/_app\/immutable\/(entry|nodes)/.test(u))).toEqual([]);
    expect(await w.violations()).toEqual([]);
  });

  test("pressing the button loads Evidence and the WASM engine, with no CSP violations", async ({ page }) => {
    test.slow();
    const requests = [];
    page.on("response", (r) => requests.push({ url: r.url(), status: r.status() }));
    const w = watch(page);
    await page.goto("/explore/analyses/home-advantage");
    await page.getByRole("button", { name: "Load interactive explorer" }).click();
    // Charts and tables only appear after DuckDB-WASM has run the page's queries in the browser.
    await expect(page.getByRole("cell", { name: "Premier League" }).first()).toBeVisible({ timeout: 90_000 });
    await expect(page.locator("canvas").first()).toBeVisible();
    // The engine starts after the first render (the prerendered query results draw the page), so wait for it.
    await expect.poll(() => requests.find((r) => /duckdb-(eh|mvp)\.wasm$/.test(r.url)), { timeout: 90_000 }).toBeTruthy();
    const wasm = requests.find((r) => /duckdb-(eh|mvp)\.wasm$/.test(r.url));
    await expect.poll(() => requests.some((r) => /parquet\.duckdb_extension\.wasm$/.test(r.url)), { timeout: 60_000 }).toBe(true);
    await page.waitForTimeout(2000);
    expect(wasm.url).toMatch(/^https:\/\/cdn\.jsdelivr\.net\/npm\/@duckdb\/duckdb-wasm@\d+\.\d+\.\d+\/dist\//);
    expect(wasm.status).toBe(200);
    expect(await w.violations()).toEqual([]);
    expect(w.problems).toEqual([]);
  });

  test("the integrity hash is enforced: a binary that does not match is refused", async ({ page }) => {
    test.slow();
    // Serve different bytes for the CDN file; the worker's fetch carries an integrity hash, so the engine must not start.
    let served = 0;
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.route(/cdn\.jsdelivr\.net\/.*duckdb-(eh|mvp)\.wasm$/, (route) => {
      served++;
      return route.fulfill({ status: 200, contentType: "application/wasm", headers: { "access-control-allow-origin": "*" }, body: Buffer.from("\0asm\x01\0\0\0") });
    });
    await page.goto("/explore/analyses/home-advantage");
    await page.getByRole("button", { name: "Load interactive explorer" }).click();
    await expect.poll(() => served, { timeout: 30_000 }).toBeGreaterThan(0); // the tampered file was the one requested
    // The page still draws (its query results are prerendered), but the engine's fetch is rejected by the integrity check.
    await expect.poll(() => errors.join("\n"), { timeout: 30_000 }).toContain("Failed to fetch");
  });

  for (const path of EXPLORE_PAGES) {
    test(`${path}: gate has a static twin link`, async ({ page }) => {
      await page.goto(path);
      const link = page.getByRole("link", { name: "lightweight static page" });
      await expect(link).toBeVisible();
      const href = await link.getAttribute("href");
      expect((await page.request.get(href)).status()).toBe(200);
    });
  }
});
