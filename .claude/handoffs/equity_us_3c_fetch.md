# Handoff — equity_us_shared — 3c: add fetch_sp500_wikipedia_html + its tests

## Objective
Add a small network function that downloads the Wikipedia page with an identifying User-Agent (plain scraping gets HTTP 403), plus three tests that never touch the network.

## Allowed files
- src/data/equity_us/sp500_wikipedia.py            (edit: add one import line and the block below; change nothing else)
- tests/data/equity_us/test_sp500_wikipedia_fetch.py   (create)
Nothing else. No scratch or debug scripts. Do NOT run anything that makes a real network request.

## Budget rules for this session
- Transcribe the code below exactly. Do not redesign it.
- Copy the USER_AGENT line exactly as written, including the GitHub URL.
- Run pytest once. If anything fails, make at most ONE fix to the source file; if it still fails, write the error in the self-check and stop.

## Change 1 — in src/data/equity_us/sp500_wikipedia.py
a. Add this line directly below `import pandas as pd`:
    import requests

b. Add this block at the END of the file:

```python
WIKIPEDIA_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

# Wikipedia blocks generic scraper user agents (HTTP 403). Its policy asks for a
# descriptive User-Agent with contact details. The contact is the public repo URL.
USER_AGENT = "QuantResearcherBot/0.1 (personal research project; contact: https://github.com/raunakkshatriya/Quant-Researcher)"


def fetch_sp500_wikipedia_html(user_agent, url=WIKIPEDIA_SP500_URL, timeout=30):
    """Download the Wikipedia S&P 500 page and return its HTML as a str.

    Network call — lives in src/data/ per CLAUDE.md §3. Raises ValueError if
    user_agent is blank or still contains the CHANGE_ME placeholder (checked
    before any request is made), and RuntimeError if the HTTP status is not 200.
    """
    if "CHANGE_ME" in user_agent or user_agent.strip() == "":
        raise ValueError("Set USER_AGENT to include your real contact (email or GitHub URL) before fetching.")
    response = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(f"Wikipedia request failed with HTTP {response.status_code}")
    return response.text
```

## Change 2 — create tests/data/equity_us/test_sp500_wikipedia_fetch.py with exactly this

```python
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
```

## Done so far
parse_sp500_wikipedia_html() + 8 tests (sessions 3a/3b), 35 tests passing.

## This session's task
Make changes 1 and 2. Run:
    python -m pytest tests/data/equity_us/ -q
Expected: 38 passed. Fill in the self-check and stop.

## Resume point
If out of budget: note which changes are done; the next session does the rest.

## Session self-check
- Nothing uncertain: both source change (append `import requests` + function block) and test file matched the handoff exactly.
- No assumptions needed; changes were explicit in the handoff.
- All 38 tests pass (8 new tests added, previously 30 from sessions 3a/3b).
