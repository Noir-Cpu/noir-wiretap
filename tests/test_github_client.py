import time

import pytest
import requests

from pipeline import http


class FakeResp:
    def __init__(self, status, headers=None, body=None, links=None):
        self.status_code, self.headers, self._body, self.links = status, headers or {}, body, links or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def test_waits_out_a_rate_limit_then_succeeds(monkeypatch):
    calls = iter([
        FakeResp(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(time.time()) + 2)}),
        FakeResp(200, body=[{"id": 1}]),
    ])
    sleeps = []
    monkeypatch.setattr(http.time, "sleep", sleeps.append)
    client = http.GitHubClient()
    monkeypatch.setattr(client.session, "get", lambda *a, **k: next(calls))
    assert client.get("https://x").status_code == 200
    assert len(sleeps) == 1 and 1 <= sleeps[0] <= 4


def test_refuses_to_wait_more_than_the_cap(monkeypatch):
    resp = FakeResp(403, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(time.time()) + 3600)})
    client = http.GitHubClient()
    monkeypatch.setattr(client.session, "get", lambda *a, **k: resp)
    with pytest.raises(RuntimeError, match="rate limit"):
        client.get("https://x")


def test_follows_link_header_pages(monkeypatch):
    pages = iter([
        FakeResp(200, body=[{"n": 1}], links={"next": {"url": "https://x?page=2"}}),
        FakeResp(200, body=[{"n": 2}]),
    ])
    client = http.GitHubClient()
    monkeypatch.setattr(client.session, "get", lambda *a, **k: next(pages))
    assert [p for p in client.pages("/x")] == [[{"n": 1}], [{"n": 2}]]
