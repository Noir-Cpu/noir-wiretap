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


LEDGER = (
    '{"seq":1,"prev":null,"hash":"h1","match":{"division":"E0","date":"2026-10-03","home":"Arsenal",'
    '"away":"Chelsea","kickoff_utc":"2026-10-03T11:30:00Z"},"probs":[0.5,0.3,0.2],"book":[0.48,0.29,0.23],'
    '"model":"m1","params_sha":"p","data_sha":"d","published_at":"2026-10-02T09:00:00Z"}\n'
    '{"seq":2,"prev":"h1","hash":"h2","match":{"division":"SP1","date":"2026-10-03","home":"Getafe",'
    '"away":"Eibar","kickoff_utc":null},"probs":[0.4,0.3,0.3],"book":null,"model":"m1","params_sha":"p",'
    '"data_sha":"d","published_at":"2026-10-02T09:00:00Z"}\n'
)


def test_empty_ledger_yields_nothing():
    from pipeline.informant_source import parse_ledger
    assert list(parse_ledger("")) == [] and list(parse_ledger("\n")) == []


def test_ledger_is_flattened():
    from pipeline.informant_source import parse_ledger
    rows = list(parse_ledger(LEDGER))
    assert rows[0]["p_home"] == 0.5 and rows[0]["book_away"] == 0.23
    assert rows[1]["book_home"] is None and rows[1]["prev"] == "h1"
    assert rows[0]["match_division"] == "E0" and rows[0]["hash"] == "h1"


def test_bad_probability_triple_is_rejected():
    import pytest
    from pipeline.informant_source import parse_ledger
    bad = LEDGER.replace("[0.5,0.3,0.2]", "[0.5,0.5]")
    with pytest.raises(ValueError):
        list(parse_ledger(bad))
