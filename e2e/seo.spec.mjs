import { test, expect } from "@playwright/test";
import { STATIC_PAGES, EXPLORE_PAGES } from "./helpers.mjs";

const meta = (page, sel) => page.locator(sel).first().getAttribute("content");

for (const path of STATIC_PAGES) {
  test(`${path}: title, description, canonical, social tags, JSON-LD`, async ({ page, request }) => {
    await page.goto(path);
    const title = await page.title();
    expect(title.length).toBeGreaterThanOrEqual(30);
    expect(title.length).toBeLessThanOrEqual(65);
    const desc = await meta(page, 'meta[name="description"]');
    expect(desc.length).toBeGreaterThanOrEqual(70);
    expect(desc.length).toBeLessThanOrEqual(165);
    const canonical = await page.locator('link[rel="canonical"]').getAttribute("href");
    expect(new URL(canonical).pathname).toBe(path);
    expect(await meta(page, 'meta[property="og:url"]')).toBe(canonical);
    expect(await meta(page, 'meta[property="og:title"]')).toBe(title);
    const image = await meta(page, 'meta[property="og:image"]');
    expect(await meta(page, 'meta[name="twitter:image"]')).toBe(image);
    expect(await meta(page, 'meta[name="twitter:card"]')).toBe("summary_large_image");
    expect(await meta(page, 'meta[property="og:image:alt"]')).toBeTruthy();
    const img = await request.get(new URL(image).pathname);
    expect(img.status()).toBe(200);
    expect(img.headers()["content-type"]).toBe("image/png");
    const ld = JSON.parse(await page.locator('script[type="application/ld+json"]').textContent());
    expect(ld["@context"]).toBe("https://schema.org");
    expect(["WebSite", "Article", "AboutPage"]).toContain(ld["@type"]);
    expect(ld.url).toBe(canonical);
  });
}

test("titles and descriptions are unique", async ({ page }) => {
  const titles = new Set(), descs = new Set();
  for (const p of STATIC_PAGES) {
    await page.goto(p);
    titles.add(await page.title());
    descs.add(await meta(page, 'meta[name="description"]'));
  }
  expect(titles.size).toBe(STATIC_PAGES.length);
  expect(descs.size).toBe(STATIC_PAGES.length);
});

test("sitemap lists every static page and nothing from /explore; robots points at it", async ({ request }) => {
  const xml = await (await request.get("/sitemap.xml")).text();
  const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => new URL(m[1]).pathname);
  expect(locs.sort()).toEqual([...STATIC_PAGES].sort());
  for (const p of locs) expect((await request.get(p)).status()).toBe(200);
  const robots = await (await request.get("/robots.txt")).text();
  expect(robots).toMatch(/Sitemap: https:\/\/.+\/sitemap\.xml/);
  expect(robots).not.toMatch(/Disallow:\s*\/explore/); // a blocked page never shows its noindex
});

test("404 page: status 404, noindex, links back", async ({ request, page }) => {
  const res = await request.get("/does/not/exist", { headers: { "sec-fetch-mode": "navigate" } });
  expect(res.status()).toBe(404);
  const body = await res.text();
  expect(body).toContain("Page not found");
  expect(body).toContain('name="robots" content="noindex"');
  expect(body).not.toContain('rel="canonical"');
});

for (const path of EXPLORE_PAGES) {
  test(`${path}: noindex by header and meta, description present, no twitter:site of a third party`, async ({ page }) => {
    const res = await page.goto(path);
    expect(res.headers()["x-robots-tag"]).toBe("noindex, follow");
    expect(await meta(page, 'meta[name="robots"]')).toContain("noindex");
    expect(await meta(page, 'meta[name="description"]')).toBeTruthy();
    expect(await page.locator('meta[name="twitter:site"]').count()).toBe(0);
    expect(await page.locator('script[type="application/ld+json"]').count()).toBe(0);
  });
}
