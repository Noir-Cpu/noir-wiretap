from pipeline.informant_source import parse_results

CSV = """Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H
E0,16/08/2024,20:00,Man United,Fulham,1,0,H,1.6
E0,17/08/2024,,Ipswich,Liverpool,0,2,A,8.5
,,,,,,,,
"""


def test_keeps_core_columns_and_drops_odds():
    rows = list(parse_results(CSV, "E0", "2425"))
    assert len(rows) == 2
    assert rows[0]["hometeam"] == "Man United" and rows[0]["fthg"] == "1"
    assert "b365h" not in rows[0]
    assert rows[1]["time"] is None
    assert rows[0]["season_code"] == "2425" and rows[0]["source_line"] == 2
