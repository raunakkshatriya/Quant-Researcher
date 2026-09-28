# Handoff — equity_us_shared — 1b: tests for reconstruct_membership, part 1 (cases 1–3)

## Objective
Create the test file with a helper and test cases 1–3, using the exact inputs and expected outputs below.

## Allowed files
- tests/data/equity_us/test_sp500_membership.py   (create)
- tests/data/equity_us/__init__.py                (create empty ONLY if tests/data/ already has an __init__.py; otherwise do not create it)
src/data/equity_us/sp500_membership.py is READ-ONLY this session. Do not edit it. No scratch or debug scripts.

## Budget rules for this session
- The expected values below are FIXED and correct. Never change an expected value to make a test pass.
- Do not trace the algorithm by hand. Just write the tests as given.
- Run pytest once. If a test fails, do NOT try to fix the source file. Write the failing test name and the error message in the self-check and stop.

## Put this at the top of the test file exactly
    import pandas as pd
    import pytest
    from pandas.api import types as ptypes
    from src.data.equity_us.sp500_membership import reconstruct_membership

    START = pd.Timestamp("2023-01-01")
    AS_OF = pd.Timestamp("2026-09-01")

    def fmt(v):
        if v is pd.NaT:
            return "NaT"
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v

    def as_rows(df):
        return [tuple(fmt(v) for v in row) for row in df.itertuples(index=False)]

    def make_changes(dates, added, removed):
        return pd.DataFrame({
            "date": pd.to_datetime(dates),
            "added_ticker": added,
            "removed_ticker": removed,
        })

Every test calls: membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)
and compares as_rows(membership) and as_rows(anomalies) to the expected lists with ==.

## Test case 1 — test_normal_case
current = pd.DataFrame({"ticker": ["A", "B", "C"]})
changes = make_changes(["2024-03-01"], ["C"], ["D"])
expected membership rows:
    [("A", "2023-01-01", "NaT", True),
     ("B", "2023-01-01", "NaT", True),
     ("C", "2024-03-01", "NaT", False),
     ("D", "2023-01-01", "2024-03-01", True)]
expected anomalies rows: []

## Test case 1b — test_output_columns_and_dtypes (same inputs as case 1)
assert list(membership.columns) == ["ticker", "date_added", "date_removed", "start_censored"]
assert list(anomalies.columns) == ["date", "ticker", "event", "reason"]
assert ptypes.is_string_dtype(membership["ticker"])
assert ptypes.is_datetime64_any_dtype(membership["date_added"])
assert ptypes.is_datetime64_any_dtype(membership["date_removed"])
assert ptypes.is_bool_dtype(membership["start_censored"])
assert ptypes.is_datetime64_any_dtype(anomalies["date"])

## Test case 2 — test_removed_then_readded
current = pd.DataFrame({"ticker": ["E"]})
changes = make_changes(["2023-06-01", "2024-06-01"], [None, "E"], ["E", None])
expected membership rows:
    [("E", "2023-01-01", "2023-06-01", True),
     ("E", "2024-06-01", "NaT", False)]
expected anomalies rows: []

## Test case 3 — test_changes_outside_window_ignored
current = pd.DataFrame({"ticker": ["A"]})
changes = make_changes(["2022-06-01", "2026-12-01"], ["A", None], [None, "X"])
expected membership rows:
    [("A", "2023-01-01", "NaT", True)]
expected anomalies rows: []

## Done so far
src/data/equity_us/sp500_membership.py exists (session 1a), imports OK.

## This session's task
Create the test file with the header above and the four test functions (1, 1b, 2, 3). Run:
    pytest tests/data/equity_us/test_sp500_membership.py -q
Fill in the self-check with the pass/fail result and stop.

## Resume point
If out of budget: next session adds whichever of tests 1, 1b, 2, 3 are missing.

## Session self-check
All 4 test cases passed (`test_normal_case`, `test_output_columns_and_dtypes`, `test_removed_then_readded`, `test_changes_outside_window_ignored`). No ambiguities or assumptions required; the implementation matches expected outputs exactly.
