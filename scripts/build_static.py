"""Builds the lightweight static site (plain HTML, inline SVG, no JavaScript) from the dbt marts.

The interactive Evidence report is built separately and served under /explore. This site is the default entry
because Evidence needs ~3 MB of JavaScript plus an in-browser DuckDB-WASM engine to draw anything
(see docs/adr/0009-static-first-site.md). Metrics are read from mart columns as they are; nothing here
recomputes a rate.

Run: python scripts/build_static.py   (after `make build`)
"""
from __future__ import annotations

import html
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import markdown

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("WIRETAP_DB", ROOT / "warehouse" / "wiretap.duckdb"))
OUT = ROOT / "site"
MIN_SCORED = 30  # keep in step with var min_scored_predictions in dbt_project.yml

CSS = """
:root{--ink:#1c1a17;--bone:#f0ebe0;--graphite:#5d574f;--smoke:#d9d3c6;--signal:#b3261e;--paper:#f7f4ec}
@media (prefers-color-scheme:dark){:root{--ink:#f0ebe0;--bone:#171512;--graphite:#b5ada1;--smoke:#3a362f;--signal:#ff6b5e;--paper:#1f1c18}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bone);color:var(--ink);font:1rem/1.55 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--ink);text-underline-offset:.18em}a:hover{color:var(--signal)}
:focus-visible{outline:3px solid var(--signal);outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:16px;top:8px;background:var(--paper);padding:8px;z-index:9}
header.site,main,footer{padding-left:16px;padding-right:16px}
.wrap{max-width:52rem;margin:0 auto}
header.site{border-bottom:2px solid var(--ink);padding-top:12px;padding-bottom:12px}
header.site .wrap{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:baseline}
.brand{font:700 1.05rem "Archivo",system-ui,sans-serif;letter-spacing:.06em;text-decoration:none}
nav{display:flex;flex-wrap:wrap;gap:4px 16px}
nav a{font-size:.95rem;padding:6px 0;min-height:32px;display:inline-block}
nav a[aria-current=page]{font-weight:700;text-decoration-color:var(--signal);text-decoration-thickness:3px}
h1{font:800 clamp(1.9rem,6vw,2.8rem)/1.08 "Archivo",system-ui,sans-serif;margin:1.4rem 0 .6rem;letter-spacing:-.01em}
h2{font:700 1.35rem/1.2 "Archivo",system-ui,sans-serif;margin:2rem 0 .5rem}
h3{font-size:1.05rem;margin:1.4rem 0 .3rem}
.case{font:600 .8rem "IBM Plex Mono",ui-monospace,monospace;color:var(--signal);letter-spacing:.08em;margin:1.4rem 0 0}
.lede{font-size:1.15rem;max-width:40rem}
code{font:.9em "IBM Plex Mono",ui-monospace,monospace;background:var(--paper);padding:.05em .3em;border:1px solid var(--smoke)}
.scroll{overflow-x:auto;margin:1rem 0;border:1px solid var(--smoke)}
table{border-collapse:collapse;width:100%;font-size:.92rem;font-variant-numeric:tabular-nums}
caption{text-align:left;padding:8px;font-weight:600}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid var(--smoke);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
thead th{border-bottom:2px solid var(--ink)}
.stat{display:inline-block;margin:0 24px 8px 0}.stat b{display:block;font:700 1.9rem/1.1 "Archivo",system-ui,sans-serif}
.stat span{font-size:.85rem;color:var(--graphite)}
.note{border-left:4px solid var(--signal);background:var(--paper);padding:10px 14px;margin:1rem 0}
figure{margin:1rem 0}figcaption{font-size:.88rem;color:var(--graphite)}
svg{max-width:100%;height:auto;display:block}
svg text{fill:var(--ink);font:12px "IBM Plex Sans",system-ui,sans-serif}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:.9rem;margin:.4rem 0}
.legend i{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:-1px}
footer{border-top:1px solid var(--smoke);margin-top:3rem;padding-top:16px;padding-bottom:32px;color:var(--graphite);font-size:.88rem}
ul{padding-left:1.2rem}li{margin:.3rem 0}
"""

NAV = [
    ("/", "Overview"),
    ("/analyses/home-advantage/", "Home advantage"),
    ("/analyses/delivery-and-ci/", "Delivery and CI"),
    ("/analyses/calibration/", "Calibration"),
    ("/about/", "About"),
    ("/explore/", "Interactive report"),
]

e = html.escape


def page(path: str, title: str, description: str, body: str, generated: str) -> str:
    nav = "".join(
        f'<a href="{href}"{" aria-current=page" if href == path else ""}>{e(label)}</a>' for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} | WIRETAP</title>
<meta name="description" content="{e(description)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23b3261e'/%3E%3C/svg%3E">
<style>{CSS}</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="/">NOIR / WIRETAP</a><nav aria-label="Main">{nav}</nav></div></header>
<main id="main"><div class="wrap">{body}</div></main>
<footer><div class="wrap">Built {e(generated)} from the dbt marts. Source: <a href="https://github.com/Noir-Cpu/noir-wiretap">Noir-Cpu/noir-wiretap</a>.</div></footer>
</body></html>"""


def pct(x, d=1):
    return "" if x is None else f"{x * 100:.{d}f}%"


def table(caption: str, headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th scope=col>{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    # tabindex + role make the scrollable region keyboard reachable (axe: scrollable-region-focusable).
    return (f'<div class="scroll" role="region" aria-label="{e(caption)}" tabindex="0">'
            f"<table><caption>{e(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def line_chart(title: str, desc: str, labels: list[str], series: dict[str, list[float]], lo: float, hi: float) -> str:
    w, h, ml, mr, mt, mb = 480, 280, 44, 12, 12, 34
    pw, ph = w - ml - mr, h - mt - mb
    colours = ["var(--signal)", "var(--ink)"]
    shapes = ["circle", "square"]
    x = lambda i: ml + pw * i / (len(labels) - 1)
    y = lambda v: mt + ph * (1 - (v - lo) / (hi - lo))
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d"><title id="t">{e(title)}</title><desc id="d">{e(desc)}</desc>']
    steps = 5
    for k in range(steps + 1):
        v = lo + (hi - lo) * k / steps
        parts.append(f'<line x1="{ml}" x2="{w - mr}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--smoke)"/>'
                     f'<text x="{ml - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{v * 100:.0f}%</text>')
    for i, lab in enumerate(labels):
        if i % 2 == 0 or len(labels) < 7:
            parts.append(f'<text x="{x(i):.1f}" y="{h - 12}" text-anchor="middle">{e(lab)}</text>')
    for n, (name, vals) in enumerate(series.items()):
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colours[n]}" stroke-width="2.5"/>')
        for i, v in enumerate(vals):
            if shapes[n] == "circle":
                parts.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4" fill="{colours[n]}"/>')
            else:
                parts.append(f'<rect x="{x(i) - 3.5:.1f}" y="{y(v) - 3.5:.1f}" width="7" height="7" fill="{colours[n]}"/>')
    parts.append("</svg>")
    legend = "".join(
        f'<span><i style="background:{colours[n]}{";border-radius:50%" if n == 0 else ""}"></i>{e(name)}</span>'
        for n, name in enumerate(series))
    return f'<figure><div class="legend">{legend}</div>{"".join(parts)}<figcaption>{e(desc)}</figcaption></figure>'


def bar_chart(title: str, desc: str, groups: list[tuple[str, float | None, float | None]]) -> str:
    """Two bars per repo: all runs (signal) and excluding Dependabot (ink). Values 0..1."""
    row_h, ml, w = 44, 118, 480
    h = row_h * len(groups) + 8
    pw = w - ml - 50
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-labelledby="bt bd"><title id="bt">{e(title)}</title><desc id="bd">{e(desc)}</desc>']
    for i, (name, a, b) in enumerate(groups):
        y0 = 4 + i * row_h
        parts.append(f'<text x="{ml - 8}" y="{y0 + 22}" text-anchor="end">{e(name.removeprefix("noir-"))}</text>')
        for j, (v, col) in enumerate(((a, "var(--signal)"), (b, "var(--ink)"))):
            yy = y0 + 4 + j * 17
            if v is None:
                parts.append(f'<text x="{ml + 4}" y="{yy + 11}">no runs</text>')
                continue
            parts.append(f'<rect x="{ml}" y="{yy}" width="{max(pw * v, 1):.1f}" height="14" fill="{col}"/>'
                         f'<text x="{ml + pw * v + 5:.1f}" y="{yy + 11}">{v * 100:.1f}%</text>')
    parts.append("</svg>")
    legend = ('<span><i style="background:var(--signal)"></i>All runs</span>'
              '<span><i style="background:var(--ink)"></i>Excluding Dependabot runs</span>')
    return f'<figure><div class="legend">{legend}</div>{"".join(parts)}<figcaption>{e(desc)}</figcaption></figure>'


def md(path: str) -> str:
    text = (ROOT / "docs" / "analyses" / path).read_text(encoding="utf-8")
    text = re.sub(r"^# .*\n", "", text, count=1)  # page has its own h1
    out = markdown.markdown(text, extensions=["tables", "sane_lists"])
    n = 0

    def wrap(_m):
        nonlocal n
        n += 1
        return f'<div class="scroll" role="region" aria-label="Table {n} of the written analysis" tabindex="0"><table>'

    out = re.sub(r"<table>", wrap, out)
    return out.replace("</table>", "</table></div>")


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    q = lambda sql: con.execute(sql).fetchall()
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pages: dict[str, tuple[str, str, str]] = {}

    # ---------- overview
    load = q("select max(loaded_at) from staging.stg_github__repos")[0][0]
    fetched = q("select max(checked_at) from staging.stg_informant__collector_heartbeat")[0][0]
    changed = q("select max(last_data_change_at) from staging.stg_informant__collector_manifest")[0][0]
    counts = dict(q("""select 'matches', count(*) from marts.fct_match union all
        select 'runs', count(*) from marts.fct_workflow_run union all
        select 'commits', count(*) from marts.fct_commit union all
        select 'repos', count(*) from marts.dim_repo union all
        select 'predictions', count(*) from marts.fct_prediction"""))
    fmt = lambda t: t.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pages["/"] = ("Analytics warehouse over the NOIR systems", "A small warehouse over the NOIR systems: GitHub delivery, CI reliability and football results, modelled in dbt on DuckDB.", f"""
<p class="case">CASE 004 / WIRETAP</p>
<h1>A warehouse that listens in on the NOIR cases.</h1>
<p class="lede">GitHub activity and league results are loaded nightly, modelled as a star schema in dbt, tested, and reported here. Every number on this site is a column of a dbt mart. Nothing on a page recomputes a metric.</p>
<div>
<div class="stat"><b>{counts['matches']:,}</b><span>matches (Premier League, La Liga)</span></div>
<div class="stat"><b>{counts['runs']:,}</b><span>CI runs</span></div>
<div class="stat"><b>{counts['commits']:,}</b><span>commits, {counts['repos']} repos</span></div>
<div class="stat"><b>{counts['predictions']:,}</b><span>INFORMANT predictions scored so far</span></div>
</div>
<p>GitHub last loaded {fmt(load)}. INFORMANT collector last checked {fmt(fetched)}; its data last changed {fmt(changed)}.</p>
<h2>Analyses</h2>
<ul>
<li><a href="/analyses/home-advantage/">Home advantage: Premier League against La Liga</a></li>
<li><a href="/analyses/delivery-and-ci/">Delivery cadence and CI reliability across the NOIR repos</a></li>
<li><a href="/analyses/calibration/">How well calibrated is INFORMANT?</a> (waiting for data)</li>
</ul>
<p>The <a href="/explore/">interactive Evidence report</a> shows the same marts with sortable tables. It downloads a large in-browser database engine, so it is slower to open.</p>
""")

    # ---------- home advantage
    rows = q("""select league_name, season_label, season_start_year, matches, home_win_rate, home_win_rate_ci_low,
                home_win_rate_ci_high, is_complete_season, is_single_season
                from marts.mart_home_advantage order by season_start_year, league_name""")
    complete = [r for r in rows if r[8] and r[7]]
    seasons = sorted({r[1] for r in complete})
    series = {name: [next(r[4] for r in complete if r[0] == name and r[1] == s) for s in seasons]
              for name in ("Premier League", "La Liga")}
    short = [s[2:4] + "/" + s[5:7] for s in seasons]
    overall = [r for r in rows if not r[8]]
    body = ['<p class="case">ANALYSIS 1</p><h1>Home advantage: Premier League against La Liga</h1>',
            '<p class="lede"><code>home_win_rate</code> is one column of the <code>mart_home_advantage</code> dbt model: home wins divided by completed matches. The chart and tables read that column as it is. The season in progress is left out of the chart.</p>',
            line_chart("Home win rate by season", "Home win rate by season, complete seasons 2016/17 to 2025/26, Premier League and La Liga.", short, series, 0.30, 0.55),
            "<h2>By season</h2>",
            table("Home win rate by league and season", ["League", "Season", "Matches", "Home win", "95% low", "95% high"],
                  [[r[0], r[1] + ("" if r[7] else " (in progress)"), r[3], pct(r[4]), pct(r[5]), pct(r[6])]
                   for r in rows if r[8]]),
            "<h2>All seasons</h2>",
            table("Home win rate across all seasons in the warehouse", ["League", "Matches", "Home win", "95% low", "95% high"],
                  [[r[0], f"{r[3]:,}", pct(r[4]), pct(r[5]), pct(r[6])] for r in overall]),
            "<h2>Findings and limits</h2>", md("01-home-advantage.md")]
    pages["/analyses/home-advantage/"] = ("Home advantage, Premier League and La Liga", "Home win rate by season in the Premier League and La Liga, 2016/17 to 2025/26, with intervals and limits.", "".join(body))

    # ---------- delivery and CI
    ci = q("""select r.repo_name, r.commits, r.active_days, r.prs_merged, r.median_hours_to_merge, r.ci_decided_runs,
              r.ci_pass_rate, r.ci_decided_runs_excl_dependabot, r.ci_pass_rate_excl_dependabot
              from marts.mart_repo_summary r order by r.ci_decided_runs desc, r.repo_name""")
    body = ['<p class="case">ANALYSIS 2</p><h1>Delivery cadence and CI reliability across the NOIR repos</h1>',
            '<p class="lede"><code>ci_pass_rate</code> is one column of <code>mart_ci_reliability</code>: passed runs divided by runs that reached a verdict. Cancelled and skipped runs are not in the rate. A second column leaves out runs triggered by Dependabot; both are shown.</p>',
            bar_chart("CI pass rate per repo", "CI pass rate per repo, all runs and excluding Dependabot runs.", [(r[0], r[6], r[8]) for r in ci]),
            table("CI and delivery per repo", ["Repo", "Decided runs", "Pass rate", "Decided runs, no Dependabot", "Pass rate, no Dependabot", "Commits", "Active days", "PRs merged", "Median h to merge"],
                  [[r[0], r[5], pct(r[6]), r[7], pct(r[8]), r[1], r[2], r[3], "" if r[4] is None else f"{r[4]:.1f}"] for r in ci]),
            "<h2>Findings and limits</h2>", md("02-delivery-and-ci.md")]
    pages["/analyses/delivery-and-ci/"] = ("Delivery cadence and CI reliability", "Commits, pull requests and CI pass rate for the NOIR repos, with and without Dependabot runs.", "".join(body))

    # ---------- calibration
    total, scored, skipped = q("""select
        (select count(*) from marts.fct_prediction),
        (select count(*) from marts.fct_prediction where is_scored and is_first_for_match_model),
        (select count(*) from marts.fct_skipped_prediction)""")[0]
    body = ['<p class="case">ANALYSIS 3</p><h1>How well calibrated is INFORMANT?</h1>']
    if scored < MIN_SCORED:
        body += [
            f'<div class="note"><b>Not enough data yet.</b> {scored} scored prediction{"" if scored == 1 else "s"}; this page publishes no accuracy number until there are at least {MIN_SCORED}. Any figure from a handful of matches would mostly be noise.</div>',
            table("Ledger coverage", ["Measure", "Count"],
                  [["Predictions in the ledger", total], ["Scored (played, first prediction per match and model)", scored],
                   ["Skipped (first seen under 2 hours before kick-off)", skipped]]),
            "<p>INFORMANT publishes predictions to an append-only, hash-chained ledger (<code>predictions/ledger.jsonl</code>) when fixtures for the Premier League and La Liga appear on matchdays. WIRETAP joins each prediction to the result of the same match and scores it with the ranked probability score (RPS) and log loss, next to the bookmaker probabilities on the same matches. The models and tests are in place and were checked against hand-computed values on fixture rows; there are no real scored predictions yet.</p>"]
    else:
        cal = q("""select model_name, scored_predictions, mean_rps, mean_log_loss, book_matches, model_rps_on_book_matches,
                   book_mean_rps, rps_minus_book from marts.mart_calibration where grain = 'all_time' and has_enough_data""")
        body += [table("Forecast quality per model (lower is better)", ["Model", "Scored", "Mean RPS", "Mean log loss", "Matches with bookmaker", "Model RPS on those", "Bookmaker RPS", "Model minus bookmaker"],
                       [[r[0], r[1], f"{r[2]:.4f}", f"{r[3]:.4f}", r[4], "" if r[5] is None else f"{r[5]:.4f}", "" if r[6] is None else f"{r[6]:.4f}", "" if r[7] is None else f"{r[7]:+.4f}"] for r in cal])]
        bins = q("""select model_name, outcome, bin_index, predictions, mean_predicted, observed_frequency
                    from marts.mart_calibration_bins order by 1, 2, 3""")
        body += ["<h2>Reliability</h2>",
                 table("Predicted against observed frequency, 10% bins", ["Model", "Outcome", "Bin", "Pairs", "Mean predicted", "Observed"],
                       [[r[0], r[1], f"{r[2] * 10}-{r[2] * 10 + 10}%", r[3], pct(r[4]), pct(r[5])] for r in bins])]
    pages["/analyses/calibration/"] = ("Calibration of INFORMANT predictions", "Ranked probability score and log loss of INFORMANT predictions against results and bookmaker probabilities.", "".join(body))

    # ---------- about
    pages["/about/"] = ("Sources, limits and exclusions", "What the WIRETAP warehouse loads, what it deliberately leaves out and why.", """
<p class="case">ABOUT</p><h1>Sources, limits and exclusions</h1>
""" + table("Sources", ["Source", "State", "Notes"], [
        ["GitHub, Noir-Cpu noir-* repos", "Live", "Repos, commits, workflow runs, pull requests, releases. Author names and emails are not extracted."],
        ["INFORMANT results (E0, SP1)", "Live", "Results and match statistics; no odds."],
        ["INFORMANT predictions", "Live, ledger empty", "Hash-chained ledger read nightly; scored when matches are played (ADR 0005)."],
        ["DISPATCH order events", "Not built", "The source does not exist yet; contract in ADR 0004."],
        ["WITNESS turnout", "Not built", "Aggregates only, guarded by a dbt test. Ballots and participation never enter the warehouse (ADR 0003)."]]) + """
<p>The warehouse is rebuilt nightly by GitHub Actions and this site is published from that build. Decisions are recorded as <a href="https://github.com/Noir-Cpu/noir-wiretap/tree/main/docs/adr">ADRs</a>.</p>""")

    if OUT.exists():
        for child in OUT.iterdir():
            if child.name != "explore":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    for path, (title, desc, body) in pages.items():
        target = OUT / path.strip("/") / "index.html" if path != "/" else OUT / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page(path, title, desc, body, generated), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    print(f"wrote {len(pages)} pages to {OUT}")


if __name__ == "__main__":
    main()
