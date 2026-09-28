# Handoff — equity_us_shared — 1d: docstring + small cleanup in sp500_membership.py

## Objective
Replace one docstring with the exact text below and remove three small pieces of code that were not in the spec. No logic changes.

## Allowed files
- src/data/equity_us/sp500_membership.py          (edit)
- tests/data/equity_us/test_sp500_membership.py   (edit: only the deletion in change 4)
Nothing else. No scratch or debug scripts.

## Budget rules for this session
- Make exactly the four changes below and nothing else. Do not reformat, rename, or reorder anything.
- These are small edits, not a rewrite: do not keep commented-out copies of the old lines (git history already has them).
- Run pytest once at the end. If it fails, do NOT try to fix it: write the error in the self-check and stop.

## The four changes
1. In src/data/equity_us/sp500_membership.py, replace the ENTIRE docstring of reconstruct_membership (everything between the opening and closing triple quotes, inclusive) with exactly:

    """Reconstruct historical S&P 500 index membership intervals.

    Walks backward from the constituent list at `as_of_date` through the change
    log, down to `start_date`. Pure function: no network, no file I/O, no
    datetime.now().

    Inputs:
        current: DataFrame with column `ticker` (constituents at as_of_date).
        changes: DataFrame with columns `date` (datetime), `added_ticker`,
            `removed_ticker`; ticker columns may be None/NaN.
        as_of_date, start_date: tz-naive pd.Timestamp, start_date < as_of_date.
        Tickers are normalized with .strip().upper().

    Returns (membership, anomalies):
        membership columns: ticker (str); date_added (datetime64[ns], first
            member day, INCLUSIVE); date_removed (datetime64[ns], first
            NON-member day, EXCLUSIVE; NaT = still a member at as_of_date);
            start_censored (bool, True = already a member at start_date, real
            add date unknown). Sorted by (ticker, date_added). A ticker can
            have several rows (removed then re-added).
        anomalies columns: date (datetime64[ns]); ticker (str); event ("add"
            or "remove"); reason ("added_ticker_not_in_working_set" or
            "removed_ticker_already_in_working_set"). Sorted by (date, ticker).
            Change events that don't fit the backward walk are logged here,
            never raised.

    Raises ValueError if a required column is missing or start_date >= as_of_date.
    """

2. In the same file, find the two occurrences of `, errors="coerce"` inside pd.to_datetime(...) calls and delete just that text (so the calls become pd.to_datetime(membership["date_removed"]) and pd.to_datetime(anomalies["date"])).

3. In the same file, delete the whole `if __name__ == "__main__":` block at the bottom of the file (and the lines inside it).

4. In tests/data/equity_us/test_sp500_membership.py, delete the whole `if __name__ == "__main__":` block at the bottom of the file (and the line inside it).

## Done so far
reconstruct_membership() and 10 tests exist, all passing, committed.

## This session's task
Make the four changes above. Then run:
    python -m pytest tests/data/equity_us/ -q
Expected: 10 passed. Fill in the self-check and stop.

## Resume point
If out of budget: note which of the four changes are done; the next session does the rest.

## Session self-check
All four changes completed successfully:

1. ✅ Docstring of `reconstruct_membership` replaced with exact text specified (lines 13-46)
2. ✅ Two `errors="coerce"` removed from `pd.to_datetime()` calls (line 78 and 83 in sp500_membership.py)
3. ✅ `if __name__ == "__main__":` block deleted from `src/data/equity_us/sp500_membership.py`
4. ✅ `if __name__ == "__main__":` block deleted from `tests/data/equity_us/test_sp500_membership.py`

All 10 tests pass with expected behavior.

No uncertainties, assumptions, or skipped tests.
