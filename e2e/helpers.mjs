export const STATIC_PAGES = [
  "/",
  "/analyses/home-advantage/",
  "/analyses/delivery-and-ci/",
  "/analyses/calibration/",
  "/about/",
];
export const EXPLORE_PAGES = ["/explore/", "/explore/analyses/home-advantage", "/explore/about"];

/** Records Content-Security-Policy violations (the browser's own report) and uncaught page errors. */
export function watch(page) {
  const problems = [];
  page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() === "error") problems.push(`console.error: ${m.text()}`);
  });
  page.addInitScript(() => {
    window.__csp = [];
    document.addEventListener("securitypolicyviolation", (e) =>
      window.__csp.push(`${e.violatedDirective} blocked ${e.blockedURI || "inline"} (${e.sourceFile || "page"}:${e.lineNumber})`)
    );
  });
  return {
    problems,
    async violations() {
      const seen = await page.evaluate(() => window.__csp || []).catch(() => []);
      return [...seen, ...problems.filter((p) => /Content Security Policy|Refused to/i.test(p))];
    },
  };
}
