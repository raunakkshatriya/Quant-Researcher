"""Parse the Wikipedia 'List of S&P 500 companies' page into clean DataFrames.

This module has two parts:
- parse_sp500_wikipedia_html(): pure function, no network (this session).
- fetch_sp500_wikipedia_html(): network fetch (added in a later session).
"""

import re
from io import StringIO

import requests
import pandas as pd


def _clean(x):
    """Remove Wikipedia citation markers like [6] or [citation needed], strip
    whitespace, and return None for missing or empty cells."""
    if pd.isna(x):
        return None
    s = re.sub(r"\[[^\]]*\]", "", str(x)).strip()
    if s == "":
        return None
    return s


def parse_sp500_wikipedia_html(html):
    """Parse the saved Wikipedia S&P 500 page HTML.

    Pure function: no network, no file I/O, no datetime.now().

    Input:
        html: str, the full page HTML. Must contain one table with
            id="constituents" and one table with id="changes".

    Returns (current, changes):
        current columns: ticker (str), security (str), cik (str, 10 digits,
            zero-padded). One row per current constituent, sorted by ticker.
        changes columns: date (datetime64[ns], effective date), added_ticker,
            added_security, removed_ticker, removed_security, reason (str or
            missing). One row per change event, sorted by date descending.
        Citation markers like [6] are removed from every text cell.
        Tickers are kept exactly as Wikipedia writes them (e.g. "BRK.B").

    Raises ValueError if a table is missing or has the wrong shape, a current
    ticker is blank or duplicated, a change date is blank or not in
    "Month D, YYYY" format, or a change row has neither an added nor a
    removed ticker. Bad input is never silently dropped or coerced.
    """
    # --- current constituents table ---
    tables = pd.read_html(StringIO(html), attrs={"id": "constituents"}, flavor="lxml")
    if len(tables) != 1:
        raise ValueError("expected exactly one table with id='constituents'")
    cur = tables[0]
    for col in ["Symbol", "Security", "CIK"]:
        if col not in cur.columns:
            raise ValueError(f"constituents table is missing column {col!r}")
    current = pd.DataFrame({
        "ticker": [_clean(v) for v in cur["Symbol"]],
        "security": [_clean(v) for v in cur["Security"]],
        "cik": [str(int(v)).zfill(10) for v in cur["CIK"]],
    })
    if current["ticker"].isna().any():
        raise ValueError("constituents table has a blank ticker")
    if current["ticker"].duplicated().any():
        raise ValueError("constituents table has a duplicated ticker")
    current = current.sort_values("ticker").reset_index(drop=True)

    # --- changes table ---
    tables = pd.read_html(StringIO(html), attrs={"id": "changes"}, flavor="lxml")
    if len(tables) != 1:
        raise ValueError("expected exactly one table with id='changes'")
    ch = tables[0]
    if ch.shape[1] != 6:
        raise ValueError(f"changes table must have 6 columns, found {ch.shape[1]}")
    raw_dates = [_clean(v) for v in ch.iloc[:, 0]]
    if any(d is None for d in raw_dates):
        raise ValueError("changes table has a blank date")
    changes = pd.DataFrame({
        "date": pd.to_datetime(raw_dates, format="%B %d, %Y"),
        "added_ticker": [_clean(v) for v in ch.iloc[:, 1]],
        "added_security": [_clean(v) for v in ch.iloc[:, 2]],
        "removed_ticker": [_clean(v) for v in ch.iloc[:, 3]],
        "removed_security": [_clean(v) for v in ch.iloc[:, 4]],
        "reason": [_clean(v) for v in ch.iloc[:, 5]],
    })
    if (changes["added_ticker"].isna() & changes["removed_ticker"].isna()).any():
        raise ValueError("changes table has a row with neither an added nor a removed ticker")
    changes["date"] = changes["date"].astype("datetime64[ns]")
    changes = changes.sort_values("date", ascending=False, kind="stable").reset_index(drop=True)

    return current, changes


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
