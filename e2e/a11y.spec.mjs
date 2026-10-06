import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { STATIC_PAGES } from "./helpers.mjs";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"];
const SIZES = [{ width: 320, height: 640 }, { width: 1280, height: 800 }];

for (const scheme of ["light", "dark"]) {
  for (const size of SIZES) {
    test.describe(`static pages, ${scheme}, ${size.width}px`, () => {
      test.use({ colorScheme: scheme, viewport: size });
      for (const path of [...STATIC_PAGES, "/no-such-page"]) {
        test(path, async ({ page }) => {
          await page.goto(path);
          const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
          expect(results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
          // WCAG 1.4.10 reflow: nothing wider than the screen except inside a scrollable region.
          const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
          expect(overflow).toBeLessThanOrEqual(0);
        });
      }
    });
  }
}

test.describe("structure", () => {
  for (const path of STATIC_PAGES) {
    test(`${path}: one h1, no skipped heading levels, charts have names and a table`, async ({ page }) => {
      await page.goto(path);
      const levels = await page.$$eval("h1,h2,h3,h4,h5,h6", (hs) => hs.map((h) => Number(h.tagName[1])));
      expect(levels.filter((l) => l === 1)).toHaveLength(1);
      levels.forEach((l, i) => { if (i > 0) expect(l - levels[i - 1], `heading order ${levels.join(",")}`).toBeLessThanOrEqual(1); });
      for (const svg of await page.locator("svg").all()) {
        await expect(svg).toHaveAttribute("role", "img");
        expect(await svg.locator("title").textContent()).toBeTruthy();
        expect(await svg.locator("desc").textContent()).toBeTruthy();
      }
      // Every chart sits next to a table with the same numbers.
      if (await page.locator("svg").count()) expect(await page.locator("table").count()).toBeGreaterThan(0);
    });
  }

  test("keyboard: skip link first, chart and table regions reachable with a visible focus ring", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 640 });
    await page.goto("/analyses/delivery-and-ci/");
    await page.keyboard.press("Tab");
    await expect(page.locator(".skip")).toBeFocused();
    const seen = new Set();
    for (let i = 0; i < 30; i++) {
      await page.keyboard.press("Tab");
      const info = await page.evaluate(() => {
        const a = document.activeElement;
        return { tag: a.tagName, cls: a.className, label: a.getAttribute("aria-label"), outline: getComputedStyle(a).outlineStyle };
      });
      if (info.cls === "" && !info.label && info.tag === "BODY") break; // focus left the page
      if (info.label) seen.add(info.label);
      expect(info.outline, `${info.tag} ${info.label}`).not.toBe("none");
    }
    expect([...seen].some((l) => l.startsWith("Chart:"))).toBe(true);
    expect([...seen].some((l) => l.startsWith("CI and delivery"))).toBe(true);
  });

  test("chart text stays legible at 320 px (effective size of axis labels)", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 640 });
    await page.goto("/analyses/home-advantage/");
    const px = await page.evaluate(() => {
      const svg = document.querySelector(".chart svg");
      const t = svg.querySelector("text");
      const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
      return parseFloat(getComputedStyle(t).fontSize) * scale;
    });
    expect(px).toBeGreaterThanOrEqual(12);
  });
});

test.describe("explorer gate", () => {
  for (const scheme of ["light", "dark"]) {
    test(`gate passes axe (${scheme}, 320 px)`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.setViewportSize({ width: 320, height: 640 });
      await page.goto("/explore/analyses/home-advantage");
      await expect(page.getByRole("button", { name: "Load interactive explorer" })).toBeVisible();
      const results = await new AxeBuilder({ page }).withTags(TAGS).analyze();
      expect(results.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(0);
    });
  }

  test("loaded explorer pages pass axe (light and dark)", async ({ page }) => {
    test.slow();
    for (const scheme of ["light", "dark"]) {
      await page.emulateMedia({ colorScheme: scheme });
      for (const path of ["/explore/analyses/home-advantage", "/explore/analyses/delivery-and-ci"]) {
        await page.goto(path);
        await page.evaluate(() => sessionStorage.clear());
        await page.goto(path);
        await page.getByRole("button", { name: "Load interactive explorer" }).click();
        await expect(page.locator("canvas").first()).toBeVisible({ timeout: 90_000 });
        await page.waitForTimeout(1500);
        const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
        expect(results.violations.map((v) => `${path} ${scheme} ${v.id}: ${v.nodes.map((n) => n.target.join(" ")).join(", ")}`)).toEqual([]);
      }
    }
  });
});
