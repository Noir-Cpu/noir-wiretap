/* Loads the interactive Evidence report only when asked.
 *
 * Evidence starts a DuckDB-WASM engine (a 34 MB binary, about 10 MB on the wire) as soon as a page opens.
 * scripts/postprocess_explore.mjs replaces Evidence's inline start script with this file. Until the visitor
 * presses the button, nothing heavy is requested: no Evidence JavaScript, no data, no WebAssembly.
 * Same-origin script, so the explore Content-Security-Policy needs no hash for it.
 */
(function () {
  var script = document.currentScript;
  var root = script.parentElement; // Evidence mounts into the element that held its inline start script
  var cfg = script.dataset;
  var KEY = "wiretap-explorer";
  var started = false;

  function remember() { try { sessionStorage.setItem(KEY, "1"); } catch (e) {} }
  function remembered() { try { return sessionStorage.getItem(KEY) === "1"; } catch (e) { return false; } }

  function fixScrollRegions() {
    // Evidence's DataTable wraps wide tables in a scrollable div that keyboard users cannot focus (axe rule
    // scrollable-region-focusable). Make each such region focusable and named as soon as it appears.
    new MutationObserver(function () {
      document.querySelectorAll(".scrollbox:not([tabindex])").forEach(function (el) {
        el.setAttribute("tabindex", "0");
        el.setAttribute("role", "region");
        el.setAttribute("aria-label", "Scrollable table");
      });
    }).observe(document.documentElement, { childList: true, subtree: true });
  }

  function boot() {
    if (started) return;
    started = true;
    document.documentElement.classList.add("wt-live");
    fixScrollRegions();
    // Fetch the whole module graph in parallel instead of discovering it one import at a time.
    (cfg.preload || "").split(" ").filter(Boolean).forEach(function (href) {
      var l = document.createElement("link");
      l.rel = "modulepreload";
      l.href = href;
      document.head.appendChild(l);
    });
    window[cfg.global] = { base: cfg.base, assets: cfg.assets };
    Promise.all([import(cfg.start), import(cfg.app)]).then(function (m) {
      m[0].start(m[1], root, { node_ids: JSON.parse(cfg.nodeIds), data: JSON.parse(cfg.data), form: null, error: null });
    }).catch(function () {
      document.documentElement.classList.remove("wt-live");
      started = false;
      var status = document.getElementById("wt-status");
      var button = document.getElementById("wt-load");
      if (status) status.textContent = "The interactive explorer could not be loaded. Check your connection and try again, or use the static page.";
      if (button) { button.disabled = false; button.removeAttribute("aria-busy"); }
    });
  }

  var button = document.getElementById("wt-load");
  if (remembered()) { boot(); return; }
  if (!button) return;
  button.hidden = false;
  button.addEventListener("click", function () {
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    var status = document.getElementById("wt-status");
    if (status) status.textContent = "Loading the interactive explorer. This downloads about 10 MB.";
    remember();
    boot();
  });
})();
