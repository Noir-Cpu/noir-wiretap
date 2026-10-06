import { defineConfig } from "@playwright/test";

// Tests run against `wrangler dev` serving site/ (the same _headers handling as the deployed Workers assets).
// Point BASE_URL at another origin (for example the deployed site) to run the same tests there; no server is started then.
const port = Number(process.env.WIRETAP_PORT || 8787);
const baseURL = process.env.BASE_URL || `http://localhost:${port}`;
const local = !process.env.BASE_URL;

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 30_000 },
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: { baseURL, browserName: "chromium" },
  webServer: local
    ? {
        command: `npx wrangler dev --port ${port} --inspector-port ${port + 1000}`,
        url: `http://localhost:${port}/`,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        env: { WRANGLER_SEND_METRICS: "false", CI: "1" },
      }
    : undefined,
});
