"""A quiet stretch with no new matches must not trip freshness; a dead collector must.

Regression for the 2026-10-05 nightly failure: manifest fetched_at only changes when a data file changes.
Uses a throwaway warehouse; `dbt source freshness` is run for real.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DBT = Path(sys.executable).parent / "dbt"


def freshness(tmp_path: Path, heartbeat_age_h: float, manifest_age_days: float) -> subprocess.CompletedProcess:
    shutil.copytree(ROOT / "dbt", tmp_path / "dbt", ignore=shutil.ignore_patterns("target", "logs"))
    now = datetime.now(timezone.utc)
    iso = lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    con = duckdb.connect(str(tmp_path / "wiretap.duckdb"))
    con.execute("create schema raw_github; create schema raw_informant")
    con.execute("create table raw_github.repos (_dlt_load_id varchar)")
    con.execute("insert into raw_github.repos values (?)", [str(now.timestamp())])
    con.execute("create table raw_informant.collector_heartbeat (checked_at varchar)")
    con.execute("insert into raw_informant.collector_heartbeat values (?)", [iso(now - timedelta(hours=heartbeat_age_h))])
    con.execute("create table raw_informant.collector_manifest (path varchar, fetched_at timestamptz)")
    con.execute("insert into raw_informant.collector_manifest values ('results/E0/2627.csv', ?)",
                [now - timedelta(days=manifest_age_days)])
    con.close()
    return subprocess.run([str(DBT), "source", "freshness", "--profiles-dir", "."], cwd=tmp_path / "dbt",
                          env={**os.environ, "WIRETAP_DB": str(tmp_path / "wiretap.duckdb")},
                          capture_output=True, text=True)


def test_quiet_stretch_does_not_trip_freshness(tmp_path):
    # Data file unchanged for 20 days, collector checked 2 hours ago: fresh.
    result = freshness(tmp_path, heartbeat_age_h=2, manifest_age_days=20)
    assert result.returncode == 0, result.stdout[-2000:]


def test_dead_collector_trips_freshness(tmp_path):
    result = freshness(tmp_path, heartbeat_age_h=40, manifest_age_days=0)
    assert result.returncode != 0
    assert "collector_heartbeat" in result.stdout
