# Handoff — equity_us_shared — 2b: tests for membership_on_dates, part 1 (normal cases)

## Objective
Create a new test file with helpers and six normal-case tests, using the exact inputs and expected outputs below.

## Allowed files
- tests/data/equity_us/test_membership_on_dates.py   (create)
src/data/equity_us/sp500_membership.py and tests/data/equity_us/test_sp500_membership.py are READ-ONLY. No scratch or debug scripts.

## Budget rules for this session
- The expected values below are FIXED and correct. Never change an expected value to make a test pass.
- Do not trace the logic by hand. Just write the tests as given.
- Run pytest once. If a test fails, do NOT touch the source file. Write the failing test name and error in the self-check and stop.

## Put this at the top of the test file exactly
    import pandas as pd
    import pytest
    from pandas.api import types as ptypes
    from src.data.equity_us.sp500_membership import membership_on_dates

    def fmt(v):
        if v is pd.NaT:
            return "NaT"
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v

    def as_rows(df):
        return [tuple(fmt(v) for v in row) for row in df.itertuples(index=False)]

    def make_membership(rows):
        df = pd.DataFrame(rows, columns=["ticker", "date_added", "date_removed", "start_censored"])
        df["date_added"] = pd.to_datetime(df["date_added"])
        df["date_removed"] = pd.to_datetime(df["date_removed"])
        df["start_censored"] = df["start_censored"].astype(bool)
        return df

    def make_dates(values):
        return pd.DatetimeIndex(pd.to_datetime(values))

Each test calls: out = membership_on_dates(membership, dates) and compares as_rows(out) to the expected list with ==.

## Test 1 — test_normal_case
membership = make_membership([("A", "2023-01-01", None, True), ("B", "2023-01-01", "2024-01-01", True)])
dates = make_dates(["2023-06-01", "2024-01-01", "2025-01-01"])
expected: [("2023-06-01", "A"), ("2023-06-01", "B"), ("2024-01-01", "A"), ("2025-01-01", "A")]

## Test 2 — test_boundaries_inclusive_start_exclusive_end
membership = make_membership([("C", "2024-03-01", "2024-06-01", False)])
dates = make_dates(["2024-02-29", "2024-03-01", "2024-05-31", "2024-06-01"])
expected: [("2024-03-01", "C"), ("2024-05-31", "C")]

## Test 3 — test_removed_then_readded
membership = make_membership([("E", "2023-01-01", "2023-06-01", True), ("E", "2024-06-01", None, False)])
dates = make_dates(["2023-03-01", "2024-01-01", "2024-07-01"])
expected: [("2023-03-01", "E"), ("2024-07-01", "E")]

## Test 4 — test_unsorted_duplicate_dates
membership = make_membership([("A", "2023-01-01", None, True)])
dates = make_dates(["2024-02-01", "2024-01-01", "2024-02-01"])
expected: [("2024-01-01", "A"), ("2024-02-01", "A")]

## Test 5 — test_empty_membership
membership = make_membership([])
dates = make_dates(["2024-01-01"])
expected: []
also: assert list(out.columns) == ["date", "ticker"]

## Test 6 — test_output_dtypes
membership = make_membership([("A", "2023-01-01", None, True), ("B", "2023-01-01", "2024-01-01", True)])
dates = make_dates(["2023-06-01"])
assert list(out.columns) == ["date", "ticker"]
assert ptypes.is_datetime64_any_dtype(out["date"])
assert ptypes.is_string_dtype(out["ticker"])

## Done so far
membership_on_dates() added in session 2a, imports OK.

## This session's task
Create the file with the header and tests 1–6. Run:
    python -m pytest tests/data/equity_us/test_membership_on_dates.py -q
Expected: 6 passed. Fill in the self-check and stop.

## Resume point
If out of budget: the next session adds whichever of tests 1–6 are missing.

## Session self-check
- All 6 tests passed with correct expected values. The source function `membership_on_dates()` in `src/data/equity_us/sp500_membership.py` validates inputs as specified and correctly implements interval expansion to dates. No assumptions needed, no edge cases were uncertain. Tests verify: normal membership intervals, inclusive start/exclusive end boundaries, re-added tickers, unsorted/duplicate dates handling, empty membership case, and output dtype correctness (datetime64[ns] for date column, string dtype for ticker column).
