"""Checks the RPS / log-loss mart against hand-computed values, using a throwaway warehouse with fixture rows.

The fixtures exist only inside this test's temp directory; they never touch the real warehouse.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DBT = Path(sys.executable).parent / "dbt"

RESULTS = [  # league, season, line, date, home, away, fthg, ftag, ftr
    ("E0", "2526", 2, "16/08/2025", "Aston", "Brent", "2", "0", "H"),
    ("E0", "2526", 3, "17/08/2025", "Cardiff", "Derby", "1", "1", "D"),
    ("E0", "2526", 4, "18/08/2025", "Ely", "Fulham", "0", "3", "A"),
]

PREDS = [  # seq, hash, date, home, away, probs, book, model
    (1, "h1", "2025-08-16", "Aston", "Brent", [0.5, 0.3, 0.2], [0.6, 0.25, 0.15], "m1"),
    (2, "h2", "2025-08-17", "Cardiff", "Derby", [0.2, 0.5, 0.3], [0.25, 0.45, 0.30], "m1"),
    (3, "h3", "2025-08-18", "Ely", "Fulham", [0.3, 0.3, 0.4], None, "m1"),
    (4, "h4", "2025-08-16", "Aston", "Brent", [0.9, 0.05, 0.05], None, "m1"),  # re-publication: ignored
    (5, "h5", "2099-01-01", "Future", "Match", [0.4, 0.3, 0.3], None, "m1"),  # not played: not scored
]


def _rps(p, obs):
    return 0.5 * ((p[0] - obs[0]) ** 2 + (p[0] + p[1] - obs[0] - obs[1]) ** 2)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    work = tmp_path_factory.mktemp("cal")
    shutil.copytree(ROOT / "dbt", work / "dbt", ignore=shutil.ignore_patterns("target", "logs"))
    db = work / "wiretap.duckdb"
    con = duckdb.connect(str(db))
    con.execute("create schema raw_informant")
    cols = ("league_code season_code source_line date time hometeam awayteam fthg ftag ftr hthg htag hs \"as\" "
            "hst ast hy ay hr ar").split()
    con.execute("create table raw_informant.results (" + ", ".join(f"{c} varchar" for c in cols) + ")")
    for lg, se, ln, d, h, a, fh, fa, r in RESULTS:
        vals = {"league_code": lg, "season_code": se, "source_line": str(ln), "date": d, "hometeam": h,
                "awayteam": a, "fthg": fh, "ftag": fa, "ftr": r}
        con.execute("insert into raw_informant.results values (" + ",".join("?" * len(cols)) + ")",
                    [vals.get(c.strip('"')) for c in cols])
    con.execute("""create table raw_informant.predictions (seq bigint, prev varchar, hash varchar,
        match_division varchar, match_date varchar, match_home varchar, match_away varchar, kickoff_utc varchar,
        p_home double, p_draw double, p_away double, book_home double, book_draw double, book_away double,
        model varchar, params_sha varchar, data_sha varchar, published_at varchar)""")
    prev = None
    for seq, h, d, home, away, p, b, m in PREDS:
        con.execute("insert into raw_informant.predictions values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [seq, prev, h, "E0", d, home, away, None, *p, *(b or [None] * 3), m, "p", "d",
                     "2025-08-01T00:00:00Z"])
        prev = h
    con.close()
    env = {**os.environ, "WIRETAP_DB": str(db)}

    def run(*extra):
        built = subprocess.run(
            [str(DBT), "run", "--select", "+mart_calibration +mart_calibration_bins", "--profiles-dir", ".", *extra],
            cwd=work / "dbt", env=env, capture_output=True, text=True)
        if built.returncode:
            return built
        return subprocess.run(  # the tests of the models under check, including the ledger and probability tests
            [str(DBT), "test", "--select", "mart_calibration mart_calibration_bins fct_prediction stg_informant__predictions "
             "assert_ledger_hash_chain assert_prediction_probabilities_valid assert_calibration_rollup_matches_months",
             "--profiles-dir", ".", *extra],
            cwd=work / "dbt", env=env, capture_output=True, text=True)

    return db, run


def rows(db, sql):
    con = duckdb.connect(str(db), read_only=True)
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_scores_match_hand_computation(built):
    db, run = built
    result = run()
    assert result.returncode == 0, result.stdout[-3000:]
    mean_rps = (_rps([.5, .3, .2], [1, 0, 0]) + _rps([.2, .5, .3], [0, 1, 0]) + _rps([.3, .3, .4], [0, 0, 0])) / 3
    mean_ll = (-math.log(.5) - math.log(.5) - math.log(.4)) / 3
    book_rps = (_rps([.6, .25, .15], [1, 0, 0]) + _rps([.25, .45, .30], [0, 1, 0])) / 2
    model_on_book = (_rps([.5, .3, .2], [1, 0, 0]) + _rps([.2, .5, .3], [0, 1, 0])) / 2
    (n, rps, ll, bm, mob, brps, diff, enough), = rows(db, """
        select scored_predictions, mean_rps, mean_log_loss, book_matches, model_rps_on_book_matches,
               book_mean_rps, rps_minus_book, has_enough_data
        from marts.mart_calibration where grain = 'all_time'""")
    assert n == 3  # duplicate and unplayed predictions are excluded
    assert rps == pytest.approx(mean_rps, abs=1e-5) and ll == pytest.approx(mean_ll, abs=1e-5)
    assert bm == 2 and mob == pytest.approx(model_on_book, abs=1e-5) and brps == pytest.approx(book_rps, abs=1e-5)
    assert diff == pytest.approx(model_on_book - book_rps, abs=1e-5)
    assert enough is False  # 3 < 30: the report must show no headline


def test_enough_data_flag_follows_threshold(built):
    db, run = built
    assert run("--vars", "{min_scored_predictions: 3}").returncode == 0
    assert rows(db, "select has_enough_data from marts.mart_calibration where grain = 'all_time'") == [(True,)]


def test_reliability_bins_cover_every_scored_prediction(built):
    db, run = built
    run()
    assert rows(db, "select sum(predictions) from marts.mart_calibration_bins") == [(9,)]  # 3 predictions x 3 outcomes
