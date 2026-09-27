# Handoff — equity_us_shared — membership_on_dates

## Objective
Add a pure function that expands S&P 500 membership intervals into a long (date, ticker) table of who was a member on each requested date.

## Allowed files
- src/data/equity_us/sp500_membership.py    (edit: ADD the new function below the existing one; do not change reconstruct_membership)
- tests/data/equity_us/test_sp500_membership.py (edit: ADD new tests; do not change existing tests)
(Nothing outside this list. If the task seems to need another file, stop and flag it in the self-check.)

## Input schema
Function signature:
    membership_on_dates(membership: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.DataFrame

- membership: exactly the first output of reconstruct_membership(): columns ticker (str), date_added (datetime64[ns], inclusive), date_removed (datetime64[ns] or NaT, exclusive; NaT = still a member), start_censored (bool).
- dates: tz-naive pd.DatetimeIndex. May be unsorted or contain duplicates — sort and de-duplicate it first.
- Raise ValueError if a membership column is missing.
- Raise ValueError if any requested date is earlier than the coverage start. Coverage start = the minimum date_added among rows where start_censored is True (skip this check if there are no censored rows or membership is empty).
- No network calls, no datetime.now(), no file I/O.

## Output schema
DataFrame with columns exactly, in this order:
- date (datetime64[ns])
- ticker (str)
One row per (date, ticker) where date_added <= date AND (date_removed is NaT OR date < date_removed).
Sorted by (date, ticker), RangeIndex, no duplicate (date, ticker) pairs. Must have these columns and dtypes even when empty.

## Done so far
reconstruct_membership() exists in src/data/equity_us/sp500_membership.py with passing tests.

## This session's task
Add membership_on_dates() (with a docstring stating the schemas above) to src/data/equity_us/sp500_membership.py. Add these tests to tests/data/equity_us/test_sp500_membership.py, building the membership DataFrame inline (do not call reconstruct_membership in these tests):
1. Normal: two tickers, one open-ended (NaT), one closed; three dates; check exact expected rows.
2. Boundaries: a date equal to date_added IS included; a date equal to date_removed is NOT included.
3. Re-added ticker: ticker with intervals (2023-01-01, 2023-06-01) and (2024-06-01, NaT); dates 2023-03-01, 2024-01-01, 2024-07-01 -> present, absent, present.
4. Messy dates: unsorted dates with a duplicate -> output sorted, no duplicate rows.
5. Empty membership (correct columns, zero rows) -> empty output with correct columns.
6. A requested date before the coverage start raises ValueError.
7. Missing membership column raises ValueError.
Run pytest on the test file; ALL tests (old and new) must pass. Then fill in the Session self-check below.

## Resume point
If out of budget: function written but tests incomplete — next session adds the remaining numbered test cases only.

## Session self-check
(fill in before finishing, per CLAUDE.md §7)
