"""Writes site/_headers from scripts/headers.template.

The Content-Security-Policy for the static pages allows exactly one inline stylesheet (the same CSS block on
every page), identified by hash; the explorer policy allows the theme-bootstrap script Evidence puts in every
page, also by hash. The hashes are computed from the built HTML, so a change to either block cannot leave the
policy behind. Fails if a static page has an inline script, a style attribute, or a second distinct stylesheet.

Run after scripts/build_static.py:  python scripts/build_headers.py
"""
from __future__ import annotations

import base64
import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
TEMPLATE = ROOT / "scripts" / "headers.template"

def sha256(text: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode() + "'"


class _Inline(HTMLParser):
    """Collects the text of inline <script> and <style> elements, using a real HTML parser rather than a regex."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.scripts: list[str] = []
        self.styles: list[str] = []
        self._open: tuple[str, dict, list[str]] | None = None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._open = (tag, dict(attrs), [])

    def handle_data(self, data):
        if self._open:
            self._open[2].append(data)

    def handle_endtag(self, tag):
        if self._open and self._open[0] == tag:
            kind, attrs, parts = self._open
            self._open = None
            if kind == "style":
                self.styles.append("".join(parts))
            elif "src" not in attrs and attrs.get("type") in (None, "text/javascript", "module"):
                # JSON-LD and Evidence's JSON data blocks are never executed, so CSP does not apply to them.
                self.scripts.append("".join(parts))


def parse_inline(html: str) -> _Inline:
    parser = _Inline()
    parser.feed(html)
    parser.close()
    return parser


def executable_inline_scripts(html: str) -> list[str]:
    return parse_inline(html).scripts


def main() -> None:
    static_pages = [p for p in SITE.rglob("*.html") if "explore" not in p.relative_to(SITE).parts]
    explore_pages = list((SITE / "explore").rglob("*.html"))
    if not static_pages or not explore_pages:
        sys.exit("site/ has no static pages or no explorer pages; run make site first")

    styles: set[str] = set()
    for p in static_pages:
        html = p.read_text(encoding="utf-8")
        if executable_inline_scripts(html):
            sys.exit(f"{p.relative_to(ROOT)}: inline script in a static page; the static CSP forbids scripts")
        if re.search(r"<[a-z][^>]*\sstyle=", html, re.I):
            sys.exit(f"{p.relative_to(ROOT)}: style attribute in a static page; use a class")
        styles.update(parse_inline(html).styles)
    if len(styles) != 1:
        sys.exit(f"expected one distinct inline stylesheet across static pages, found {len(styles)}")

    scripts: set[str] = set()
    for p in explore_pages:
        scripts.update(executable_inline_scripts(p.read_text(encoding="utf-8")))
    script_hashes = " ".join(sorted(sha256(s) for s in scripts))

    static_csp = "; ".join([
        "default-src 'none'",
        f"style-src {sha256(next(iter(styles)))}",
        "img-src 'self' data:",
        # No script runs on these pages; connect-src 'self' is there only because Lighthouse fetches robots.txt
        # from inside the page and reports "robots.txt is not valid" when default-src 'none' blocks that fetch.
        "connect-src 'self'",
        "base-uri 'none'",
        "form-action 'none'",
        "frame-ancestors 'none'",
    ])
    # wasm-unsafe-eval: DuckDB-WASM compiles a WebAssembly module (it is not JavaScript eval).
    # cdn.jsdelivr.net: the DuckDB-WASM binary (ADR 0008), fetched with a Subresource Integrity hash.
    # extensions.duckdb.org: DuckDB-WASM downloads its signed parquet extension at start-up (measured on the live
    # site; no integrity hash can be attached, DuckDB verifies the extension signature itself).
    # style-src 'unsafe-inline': Evidence/Svelte set style attributes on elements; there is no way to hash those.
    explore_csp = "; ".join([
        "default-src 'none'",
        f"script-src 'self' 'wasm-unsafe-eval' {script_hashes}".rstrip(),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self' https://cdn.jsdelivr.net https://extensions.duckdb.org",
        "worker-src 'self' blob:",
        "manifest-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ])
    out = (TEMPLATE.read_text(encoding="utf-8")
           .replace("{{STATIC_CSP}}", static_csp).replace("{{EXPLORE_CSP}}", explore_csp))
    (SITE / "_headers").write_text(out, encoding="utf-8")
    print(f"wrote site/_headers ({len(static_pages)} static pages, {len(explore_pages)} explorer pages, "
          f"{len(scripts)} inline script hash(es))")


if __name__ == "__main__":
    main()
