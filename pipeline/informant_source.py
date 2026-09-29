"""INFORMANT match results (Premier League E0, La Liga SP1) from the public noir-informant repo.

Reads only result and match-statistics columns. Betting odds are ignored on purpose: the source is
model-agnostic, and predictions will arrive separately (see docs/adr/0005-predictions-extension-point.md).
Set INFORMANT_LOCAL_DIR to a checkout's data/ directory to read from disk instead of GitHub.
"""
from __future__ import annotations

import csv
import io
import json
import os
from pathlib import Path
from typing import Iterator

import dlt
import requests

RAW = "https://raw.githubusercontent.com/Noir-Cpu/noir-informant/main/data"
LEAGUES = ("E0", "SP1")
CORE_COLUMNS = (
    "Div", "Date", "Time", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "HTHG", "HTAG", "HTR",
    "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR",
)


def _fetch(path: str) -> str:
    local = os.environ.get("INFORMANT_LOCAL_DIR")
    if local:
        return (Path(local) / path).read_text(encoding="utf-8")
    resp = requests.get(f"{RAW}/{path}", timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_results(text: str, league: str, season: str) -> Iterator[dict]:
    """Yield one row per match. Blank cells become None; extra columns are dropped."""
    for n, row in enumerate(csv.DictReader(io.StringIO(text)), start=2):
        if not row.get("HomeTeam"):
            continue
        out = {"league_code": league, "season_code": season, "source_line": n}
        for col in CORE_COLUMNS:
            value = (row.get(col) or "").strip()
            out[col.lower()] = value or None
        yield out


@dlt.source(name="informant")
def informant_source():
    manifest = json.loads(_fetch("manifest.json"))

    @dlt.resource(name="collector_manifest", write_disposition="replace", primary_key="path")
    def manifest_resource() -> Iterator[dict]:
        for path, meta in manifest.items():
            yield {"path": path, **meta}

    @dlt.resource(
        name="results",
        write_disposition="merge",
        primary_key=("league_code", "season_code", "source_line"),
    )
    def results_resource() -> Iterator[dict]:
        for path in sorted(manifest):
            parts = path.split("/")  # results/E0/2425.csv
            if len(parts) != 3 or parts[0] != "results" or parts[1] not in LEAGUES:
                continue
            season = parts[2].removesuffix(".csv")
            yield from parse_results(_fetch(path), parts[1], season)

    return manifest_resource, results_resource
