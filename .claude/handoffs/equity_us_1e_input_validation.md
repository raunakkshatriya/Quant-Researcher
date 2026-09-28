# Handoff — equity_us_shared — 1e: reject bad input instead of silently dropping it

## Objective
Add four input checks to step 0 of reconstruct_membership() so bad dates or blank tickers raise ValueError, and add five tests for them.

## Allowed files
- src/data/equity_us/sp500_membership.py          (edit: step 0 and the import line only)
- tests/data/equity_us/test_sp500_membership.py   (edit: ADD five test functions at the end; change nothing already there)
Nothing else. No scratch or debug scripts.

## Budget rules for this session
- Make exactly the changes below. Do not touch steps 1-5 of the function or any existing test.
- Small edit, not a rewrite: do not keep commented-out copies of old lines.
- The test inputs below are FIXED. Never change a test to make it pass.
- Run pytest once at the end. If anything fails, make at most ONE fix to the source file; if it still fails, write the error in the self-check and stop.

## Why (context only, do not act on it beyond the changes below)
Without these checks: a NaT in changes["date"] makes that change row silently disappear in the step-1 date filter, and a None/blank ticker in current silently becomes a ticker called "nan"/"None"/"" in the output. Both corrupt membership history without any error.

## Change 1 — import
Add this line directly below `import pandas as pd`:
    from pandas.api import types as ptypes

## Change 2 — add these four checks at the END of step 0 (after the existing start_date >= as_of_date check, before step 1)
    if not ptypes.is_datetime64_any_dtype(changes["date"]):
        raise ValueError("changes['date'] must be a datetime column")
    if changes["date"].dt.tz is not None:
        raise ValueError("changes['date'] must be tz-naive")
    if changes["date"].isna().any():
        raise ValueError("changes['date'] contains missing dates (NaT)")
    if any(_norm(t) is None or _norm(t) == "" for t in current["ticker"]):
        raise ValueError("current['ticker'] contains missing or blank tickers")

## Change 3 — update the docstring's last line
Replace the line:
    Raises ValueError if a required column is missing or start_date >= as_of_date.
with:
    Raises ValueError if a required column is missing, start_date >= as_of_date,
    changes['date'] is not a tz-naive datetime column or contains NaT, or
    current['ticker'] contains missing/blank tickers. Bad input is never
    silently dropped or coerced.
(If that line is not in the docstring exactly, add the new text as the last paragraph of the docstring instead, and note it in the self-check.)

## Change 4 — add these five tests at the end of the test file (each uses `with pytest.raises(ValueError):`)
Reuse START, AS_OF, make_changes from the top of the file.

test_date_column_as_strings_raises:
    changes = pd.DataFrame({"date": ["2024-01-01"], "added_ticker": ["B"], "removed_ticker": [None]})
    reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), changes, AS_OF, START)

test_date_column_with_nat_raises:
    changes = make_changes(["2024-01-01", None], ["B", None], [None, "C"])
    reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), changes, AS_OF, START)

test_tz_aware_dates_raise:
    changes = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]).tz_localize("UTC"),
                            "added_ticker": ["B"], "removed_ticker": [None]})
    reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), changes, AS_OF, START)

test_missing_ticker_in_current_raises:
    reconstruct_membership(pd.DataFrame({"ticker": ["A", None]}), make_changes([], [], []), AS_OF, START)

test_blank_ticker_in_current_raises:
    reconstruct_membership(pd.DataFrame({"ticker": ["A", "   "]}), make_changes([], [], []), AS_OF, START)

## Done so far
All changes from handoff implemented: input validation added to `sp500_membership.py`, five new tests added to test file; 15/15 pytest tests pass (all previous tests plus the five new ones for bad datetime and ticker inputs).

## This session's task
Make changes 1-4. Then run:
    python -m pytest tests/data/equity_us/ -q
Expected: 15 passed. Fill in the self-check and stop.

## Resume point
If out of budget: note which of changes 1-4 are done; the next session does the rest.

## Session self-check
All four changes implemented successfully; 15/15 tests pass.

- Changes to `sp500_membership.py`: Added import of `ptypes`, added four validation checks at the end of step 0 (datetime dtype check, tz-naive check, NaT check, blank ticker check), updated docstring's Raises paragraph. No superseded code retained per handoff §13.
- Tests: All five new tests added (`test_date_column_as_strings_raises`, `test_date_column_with_nat_raises`, `test_tz_aware_dates_raise`, `test_missing_ticker_in_current_raises`, `test_blank_ticker_in_current_raises`). Combined with existing 10 passing tests = 15 total.
- No uncertainties or assumptions encountered; implementation followed handoff exactly without deviation.
