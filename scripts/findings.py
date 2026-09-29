"""Prints every number quoted in docs/analyses/*.md, straight from the marts. Run: make findings"""
from __future__ import annotations

import math
import os
from pathlib import Path

import duckdb

DB = os.environ.get("WIRETAP_DB", Path(__file__).resolve().parents[1] / "warehouse" / "wiretap.duckdb")
con = duckdb.connect(str(DB), read_only=True)


def z_two_prop(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (x1 / n1 - x2 / n2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))  # two-sided p


print("== Analysis 1: home advantage ==")
for row in con.sql("""
    select league_key, season_label, matches, home_wins, home_win_rate, home_win_rate_ci_low,
           home_win_rate_ci_high, is_complete_season
    from marts.mart_home_advantage order by league_key, season_start_year""").fetchall():
    print(row)

for league in ("E0", "SP1"):
    target, rest = con.sql(f"""
        select
          (select (matches, home_wins) from marts.mart_home_advantage where league_key='{league}' and season_key='2021'),
          (select (sum(matches), sum(home_wins)) from marts.mart_home_advantage
             where league_key='{league}' and is_single_season and is_complete_season and season_key <> '2021')
    """).fetchone()
    z, p = z_two_prop(target["home_wins"] if isinstance(target, dict) else target[1], target[0] if not isinstance(target, dict) else target["matches"],
                      rest[1], rest[0])
    print(f"{league} 2020/21 vs other complete seasons pooled: rest rate={rest[1]/rest[0]:.4f} (n={rest[0]}), z={z:.2f}, two-sided p={p:.4f}")

x = {k: con.sql(f"select matches, home_wins from marts.mart_home_advantage where league_key='{k}' and season_key='ALL'").fetchone() for k in ("E0", "SP1")}
z, p = z_two_prop(x["E0"][1], x["E0"][0], x["SP1"][1], x["SP1"][0])
print(f"E0 vs SP1 all seasons: z={z:.2f}, two-sided p={p:.4f}")

print("\n== Analysis 2: delivery and CI ==")
for row in con.sql("select * from marts.mart_repo_summary order by commits desc").fetchall():
    print(row)
print(con.sql("""select ci.repo_name, ci.grain, ci.period_start, decided_runs, passed_runs, failed_runs, excluded_runs, ci_pass_rate
                 from marts.mart_ci_reliability ci order by 1, 2, 3""").fetchall())
print(con.sql("""select workflow_name, ci_outcome, count(*) from marts.fct_workflow_run f join marts.dim_repo r using (repo_key)
                 where r.repo_name='noir-template' group by 1,2 order by 1,2""").fetchall())
print(con.sql("select min(created_at), max(created_at) from marts.fct_workflow_run").fetchall())
