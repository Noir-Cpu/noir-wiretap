// Renders assets/og-image.html to assets/og-image.png (1200x630) with Playwright's Chromium.
// Run by hand when the card changes: node scripts/make_og_image.mjs
import { chromium } from "@playwright/test";
import { fileURLToPath } from "node:url";

const dir = fileURLToPath(new URL("../assets/", import.meta.url));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.goto("file://" + dir + "og-image.html");
await page.screenshot({ path: dir + "og-image.png" });
await browser.close();
console.log("wrote assets/og-image.png");
