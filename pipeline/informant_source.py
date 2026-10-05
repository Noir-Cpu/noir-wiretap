"""INFORMANT match results (Premier League E0, La Liga SP1) from the public noir-informant repo.

Reads only result and match-statistics columns. Betting odds in the results files are ignored on purpose: the results source is
model-agnostic. Predictions come from the separate append-only ledger (predictions/ledger.jsonl, see docs/adr/0005).
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


def _fetch_optional(path: str) -> str:
    """The ledger files exist but may be empty (no fixtures yet); a missing file is treated as empty."""
    try:
        return _fetch(path)
    except (FileNotFoundError, requests.HTTPError) as exc:
        status = getattr(getattr(exc, "response", None), "status_code", 404)
        if isinstance(exc, FileNotFoundError) or status == 404:
            return ""
        raise


def _triple(value: list | None, prefix: str) -> dict:
    keys = (f"{prefix}_home", f"{prefix}_draw", f"{prefix}_away")
    if not value:
        return dict.fromkeys(keys)
    if len(value) != 3:
        raise ValueError(f"{prefix} must have 3 entries, got {value!r}")
    return dict(zip(keys, (float(v) for v in value)))


def parse_ledger(text: str, skipped: bool = False) -> Iterator[dict]:
    """Flatten hash-chained JSONL records: one row per line, nested match/probs/book unpacked."""
    for n, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        rec = json.loads(line)
        match = rec["match"]
        row = {
            "seq": rec["seq"], "prev": rec.get("prev"), "hash": rec["hash"],
            "match_division": match["division"], "match_date": match["date"],
            "match_home": match["home"], "match_away": match["away"],
            "kickoff_utc": match.get("kickoff_utc"),
            **_triple(rec.get("probs"), "p"), **_triple(rec.get("book"), "book"),
            "model": rec.get("model"), "params_sha": rec.get("params_sha"),
            "data_sha": rec.get("data_sha"), "published_at": rec.get("published_at"),
        }
        if skipped:
            row["reason"] = rec.get("reason")
        yield row


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

    @dlt.resource(name="collector_heartbeat", write_disposition="replace")
    def heartbeat_resource() -> Iterator[dict]:
        # Written by the collector on every clean run, even when no data file changed (unlike manifest fetched_at).
        yield {"checked_at": json.loads(_fetch("last_checked.json"))["checked_at"]}

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

    @dlt.resource(name="predictions", write_disposition="merge", primary_key="hash")
    def predictions_resource() -> Iterator[dict]:
        yield from parse_ledger(_fetch_optional("predictions/ledger.jsonl"))

    @dlt.resource(name="skipped_predictions", write_disposition="merge", primary_key="hash")
    def skipped_resource() -> Iterator[dict]:
        yield from parse_ledger(_fetch_optional("predictions/skipped.jsonl"), skipped=True)

    return manifest_resource, heartbeat_resource, results_resource, predictions_resource, skipped_resource
