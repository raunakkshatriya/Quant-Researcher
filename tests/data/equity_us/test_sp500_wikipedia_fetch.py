import pytest

import src.data.equity_us.sp500_wikipedia as mod
from src.data.equity_us.sp500_wikipedia import fetch_sp500_wikipedia_html


class FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text


def test_success_sends_user_agent(monkeypatch):
    calls = {}

    def fake_get(url, headers, timeout):
        calls["url"] = url
        calls["headers"] = headers
        calls["timeout"] = timeout
        return FakeResponse(200, "<html>ok</html>")

    monkeypatch.setattr(mod.requests, "get", fake_get)
    result = fetch_sp500_wikipedia_html("TestBot/1.0 (contact: test@example.com)")
    assert result == "<html>ok</html>"
    assert calls["headers"] == {"User-Agent": "TestBot/1.0 (contact: test@example.com)"}
    assert calls["url"] == "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    assert calls["timeout"] == 30


def test_http_error_raises(monkeypatch):
    monkeypatch.setattr(mod.requests, "get", lambda url, headers, timeout: FakeResponse(403, "Forbidden"))
    with pytest.raises(RuntimeError):
        fetch_sp500_wikipedia_html("TestBot/1.0 (contact: test@example.com)")


def test_placeholder_user_agent_raises_without_network(monkeypatch):
    def fail_if_called(url, headers, timeout):
        raise AssertionError("network must not be called")

    monkeypatch.setattr(mod.requests, "get", fail_if_called)
    with pytest.raises(ValueError):
        fetch_sp500_wikipedia_html("QuantResearcherBot/0.1 (personal research project; contact: CHANGE_ME)")

