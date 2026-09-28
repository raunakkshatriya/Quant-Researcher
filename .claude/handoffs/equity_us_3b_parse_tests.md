# Handoff — equity_us_shared — 3b: tests for parse_sp500_wikipedia_html

## Objective
Create a new test file with a small literal HTML fixture and eight tests, transcribed exactly from below.

## Allowed files
- tests/data/equity_us/test_sp500_wikipedia.py   (create)
src/data/equity_us/sp500_wikipedia.py is READ-ONLY. No scratch or debug scripts.

## Budget rules for this session
- Transcribe the file below exactly. The fixture and expected values are FIXED and already verified. Never change them to make a test pass.
- Run pytest once. If a test fails, do NOT touch the source file. Write the failing test name and error in the self-check and stop.

## File content — write exactly this

```python
import pandas as pd
import pytest
from pandas.api import types as ptypes
from src.data.equity_us.sp500_wikipedia import parse_sp500_wikipedia_html

FIXTURE = """<html><body>
<table class="wikitable sortable" id="constituents">
<thead><tr><th>Symbol</th><th>Security</th><th>GICS Sector</th><th>GICS Sub-Industry</th><th>Headquarters Location</th><th>Date added</th><th>CIK</th><th>Founded</th></tr></thead>
<tbody>
<tr><td><a href="#">MMM</a></td><td><a href="#">3M</a></td><td>Industrials</td><td>Industrial Conglomerates</td><td>Saint Paul, Minnesota</td><td>1957-03-04</td><td>0000066740</td><td>1902</td></tr>
<tr><td><a href="#">BRK.B</a></td><td><a href="#">Berkshire Hathaway</a></td><td>Financials</td><td>Multi-Sector Holdings</td><td>Omaha, Nebraska</td><td>2010-02-16</td><td>0001067983</td><td>1839</td></tr>
<tr><td><a href="#">HONA</a></td><td><a href="#">Honeywell Aerospace</a><sup class="reference">[6]</sup></td><td>Industrials</td><td>Aerospace &amp; Defense</td><td>Phoenix, Arizona</td><td>2026-06-29</td><td>0002089271</td><td>1914</td></tr>
</tbody></table>
<table class="wikitable sortable" id="changes">
<tbody>
<tr><th rowspan="2">Effective Date</th><th colspan="2">Added</th><th colspan="2">Removed</th><th rowspan="2">Reason</th></tr>
<tr><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr>
<tr><td>June 30, 2026</td><td></td><td></td><td>CAG</td><td>Conagra Brands</td><td>Market capitalization change.</td></tr>
<tr><td>June 29, 2026<sup class="reference">[6]</sup></td><td>HONA</td><td>Honeywell Aerospace</td><td></td><td></td><td>S&amp;P 500 constituent Honeywell spun off Honeywell Aerospace.<sup class="reference">[6]</sup></td></tr>
<tr><td>December 18, 2009</td><td>V</td><td>Visa</td><td>CIEN</td><td>Ciena</td><td>Market capitalization change.<sup>[citation needed]</sup></td></tr>
</tbody></table>
</body></html>"""


def fmt(v):
    if v is pd.NaT:
        return "NaT"
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return v


def as_rows(df):
    return [tuple(fmt(v) for v in row) for row in df.itertuples(index=False)]


def test_current_table():
    current, _ = parse_sp500_wikipedia_html(FIXTURE)
    assert list(current.columns) == ["ticker", "security", "cik"]
    assert as_rows(current) == [
        ("BRK.B", "Berkshire Hathaway", "0001067983"),
        ("HONA", "Honeywell Aerospace", "0002089271"),
        ("MMM", "3M", "0000066740"),
    ]


def test_changes_table():
    _, changes = parse_sp500_wikipedia_html(FIXTURE)
    assert list(changes.columns) == ["date", "added_ticker", "added_security",
                                     "removed_ticker", "removed_security", "reason"]
    assert as_rows(changes) == [
        ("2026-06-30", None, None, "CAG", "Conagra Brands", "Market capitalization change."),
        ("2026-06-29", "HONA", "Honeywell Aerospace", None, None,
         "S&P 500 constituent Honeywell spun off Honeywell Aerospace."),
        ("2009-12-18", "V", "Visa", "CIEN", "Ciena", "Market capitalization change."),
    ]


def test_output_dtypes():
    current, changes = parse_sp500_wikipedia_html(FIXTURE)
    assert ptypes.is_string_dtype(current["ticker"])
    assert ptypes.is_string_dtype(current["cik"])
    assert ptypes.is_datetime64_any_dtype(changes["date"])
    assert changes["date"].isna().sum() == 0


def test_missing_changes_table_raises():
    with pytest.raises(ValueError):
        parse_sp500_wikipedia_html(FIXTURE.replace('id="changes"', 'id="something_else"'))


def test_bad_date_format_raises():
    with pytest.raises(ValueError):
        parse_sp500_wikipedia_html(FIXTURE.replace("June 30, 2026", "Junee 30, 2026"))


def test_change_row_with_no_ticker_raises():
    with pytest.raises(ValueError):
        parse_sp500_wikipedia_html(FIXTURE.replace("<td>CAG</td>", "<td></td>"))


def test_duplicate_current_ticker_raises():
    with pytest.raises(ValueError):
        parse_sp500_wikipedia_html(FIXTURE.replace('<a href="#">HONA</a>', '<a href="#">MMM</a>'))


def test_blank_current_ticker_raises():
    with pytest.raises(ValueError):
        parse_sp500_wikipedia_html(FIXTURE.replace('<a href="#">HONA</a>', ''))
```

## Done so far
parse_sp500_wikipedia_html() created in session 3a, imports OK.

## This session's task
Create the file with exactly the content above. Run:
    python -m pytest tests/data/equity_us/ -q
Expected: 35 passed (27 old + 8 new). Fill in the self-check and stop.

## Resume point
If out of budget: the next session finishes transcribing the test file.

## Session self-check
None — all 8 tests transcribed exactly as specified, fixture and expected values match handoff specification.
