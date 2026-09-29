"""Proves the WITNESS guard fails when it should. Runs dbt against a throwaway copy of the project and database.

    pytest tests/test_witness_guard.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DBT = Path(sys.executable).parent / "dbt"

GOOD = "select 'p1' as poll_id, 12 as ballots_cast_count"
BAD_VOTER = "select 'p1' as poll_id, 'abc' as voter_id"
BAD_BALLOT_ROW = "select 'p1' as poll_id, 'ballot-123' as ballot_reference"
BAD_UNKNOWN = "select 'p1' as poll_id, 1 as something_else"


def dbt_build(workdir: Path, extra_model: tuple[str, str, bool] | None) -> subprocess.CompletedProcess:
    project = workdir / "dbt"
    shutil.copytree(ROOT / "dbt", project, ignore=shutil.ignore_patterns("target", "logs", "dbt_packages"))
    if extra_model:
        name, sql, attach_guard = extra_model
        (project / "models" / "staging" / "witness" / f"{name}.sql").write_text(
            "{{ config(tags=['witness']) }}\n" + sql + "\n"
        )
        if attach_guard:
            (project / "models" / "staging" / "witness" / f"{name}.yml").write_text(
                f"version: 2\nmodels:\n  - name: {name}\n    data_tests: [witness_aggregates_only]\n"
            )
    env = {**os.environ, "WIRETAP_DB": str(workdir / "guard.duckdb")}
    return subprocess.run(
        [str(DBT), "build", "--select", "tag:witness assert_witness_models_are_guarded", "--profiles-dir", "."],
        cwd=project, env=env, capture_output=True, text=True,
    )


def test_schema_only_model_passes(tmp_path):
    result = dbt_build(tmp_path, None)
    assert result.returncode == 0, result.stdout[-2000:]


def test_allowed_columns_pass(tmp_path):
    result = dbt_build(tmp_path, ("stg_witness__ok", GOOD, True))
    assert result.returncode == 0, result.stdout[-2000:]


@pytest.mark.parametrize("sql", [BAD_VOTER, BAD_BALLOT_ROW, BAD_UNKNOWN])
def test_identifier_like_column_fails(tmp_path, sql):
    result = dbt_build(tmp_path, ("stg_witness__bad", sql, True))
    assert result.returncode != 0
    assert "witness_aggregates_only" in result.stdout


def test_unguarded_witness_model_fails(tmp_path):
    result = dbt_build(tmp_path, ("stg_witness__unguarded", GOOD, False))
    assert result.returncode != 0
    assert "assert_witness_models_are_guarded" in result.stdout
