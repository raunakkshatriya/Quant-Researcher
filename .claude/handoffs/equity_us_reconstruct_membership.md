# Handoff — equity_us_shared — reconstruct_membership

## Objective
Implement a pure function that reconstructs historical S&P 500 membership intervals by walking backward from a current constituent list through a table of change events.

## Allowed files
- src/data/equity_us/__init__.py            (create, empty)
- src/data/equity_us/sp500_membership.py    (create)
- tests/data/equity_us/__init__.py          (create ONLY if tests/data/ already contains an __init__.py; otherwise do not create it)
- tests/data/equity_us/test_sp500_membership.py (create)
(Nothing outside this list. Do NOT edit or move any existing file under src/data/. If the task seems to need another file, stop and flag it in the self-check.)

## Input schema
Function signature:
    reconstruct_membership(current: pd.DataFrame, changes: pd.DataFrame,
                           as_of_date: pd.Timestamp, start_date: pd.Timestamp
                           ) -> tuple[pd.DataFrame, pd.DataFrame]

- current: one column `ticker` (str). The constituents as of `as_of_date`. Any index.
- changes: columns `date` (datetime64[ns], tz-naive), `added_ticker` (str or NaN), `removed_ticker` (str or NaN). One row per change event; a row may have both an added and a removed ticker. Rows where both are NaN are ignored.
- as_of_date, start_date: tz-naive pd.Timestamp, start_date < as_of_date.
- Normalize every ticker with .strip().upper(). Do not change any other characters (e.g. keep "BRK.B" as is).
- Raise ValueError if a required column is missing or if start_date >= as_of_date.
- No network calls, no datetime.now(), no file I/O.

## Output schema
Returns (membership, anomalies).

membership: columns exactly, in this order:
- ticker (str)
- date_added (datetime64[ns]) — inclusive first member day
- date_removed (datetime64[ns], NaT if still a member at as_of_date) — exclusive, first NON-member day
- start_censored (bool) — True if the ticker was already a member at start_date (its real add date is unknown)
Sorted by (ticker, date_added), index reset to RangeIndex. A ticker can have more than one row (removed then re-added).

anomalies: columns exactly, in this order:
- date (datetime64[ns]), ticker (str), event (str: "add" or "remove"), reason (str)
Sorted by (date, ticker), RangeIndex. Must have these columns and dtypes even when empty.

## Algorithm (follow exactly)
1. Keep only change rows with start_date <= date <= as_of_date. Sort by date DESCENDING.
2. working = dict {ticker: open_interval_end}. Initialize with every current ticker -> NaT.
3. For each change row, in that order:
   a. If added_ticker is not NaN (call it X):
      - if X in working: append membership row (X, date_added=row date, date_removed=working[X], start_censored=False); delete working[X].
      - else: append anomaly (row date, X, "add", "added_ticker_not_in_working_set"); do nothing else.
   b. If removed_ticker is not NaN (call it Y):
      - if Y not in working: working[Y] = row date.
      - else: append anomaly (row date, Y, "remove", "removed_ticker_already_in_working_set"); do nothing else.
4. For every ticker left in working: append membership row (ticker, date_added=start_date, date_removed=working[ticker], start_censored=True).
5. Build both DataFrames with the exact columns/dtypes above, sort, reset index, return.

## Done so far
SMA strategy exists with a snapshot universe (legacy loaders in src/data/, untouched). This is the first module in the new src/data/equity_us/ namespace.

## This session's task
Create src/data/equity_us/sp500_membership.py with reconstruct_membership() and a docstring stating the input/output schemas above. Write tests/data/equity_us/test_sp500_membership.py with these cases (build tiny DataFrames inline, no network):
1. Normal: current {A,B,C}; one change 2024-03-01 added C, removed D; start 2023-01-01, as_of 2026-09-01. Expect A,B censored from 2023-01-01 to NaT; C from 2024-03-01 to NaT not censored; D censored from 2023-01-01 to 2024-03-01. No anomalies.
2. Re-add: current {E}; changes 2023-06-01 removed E, 2024-06-01 added E. Expect two E rows: (2023-01-01, 2023-06-01, censored True) and (2024-06-01, NaT, False).
3. Out-of-window: a change dated after as_of_date and one before start_date are both ignored.
4. Anomaly: a change adds ticker Z that is not in current and never removed later. Expect Z in anomalies with reason "added_ticker_not_in_working_set", no Z in membership, no exception.
5. Empty changes (correct columns, zero rows): every current ticker censored from start_date to NaT; anomalies empty but with correct columns.
6. Data gap: a row with added_ticker NaN and removed_ticker set, a row with both NaN, and a ticker given as " aapl " — the NaN-both row is ignored and the ticker normalizes to "AAPL".
7. Missing column in changes raises ValueError; start_date >= as_of_date raises ValueError.
Run pytest on this test file; all must pass. Then fill in the Session self-check below.

## Resume point
If out of budget: function written but tests incomplete — next session writes the remaining numbered test cases only.

## Session self-check
(fill in before finishing, per CLAUDE.md §7)
