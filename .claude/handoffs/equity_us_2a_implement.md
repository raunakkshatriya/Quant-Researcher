# Handoff — equity_us_shared — 2a: implement membership_on_dates (no tests)

## Objective
Add the function membership_on_dates() to the existing module, following the numbered steps below literally. No tests this session.

## Allowed files
- src/data/equity_us/sp500_membership.py   (edit: ADD the new function at the END of the file; do not change reconstruct_membership or _norm)
Nothing else. Do NOT create tests, debug scripts, or scratch files.

## Budget rules for this session
- Implement the steps exactly as written. Do not re-derive or hand-trace them; they are already verified.
- Small addition, not a rewrite: do not copy or comment out existing code.
- The only command you run is the import check at the end. If it fails, you may make ONE fix. If it still fails, stop and write the error in the self-check.

## Function signature
    def membership_on_dates(membership, dates):
        -> returns one pandas DataFrame

`pd` and `ptypes` are already imported at the top of the file. Do not add imports.

## Docstring (copy exactly)
    """Expand membership intervals into a long (date, ticker) table.

    Pure function: no network, no file I/O, no datetime.now().

    Inputs:
        membership: the first output of reconstruct_membership() — columns
            ticker, date_added (INCLUSIVE), date_removed (EXCLUSIVE, NaT =
            still a member), start_censored.
        dates: tz-naive pd.DatetimeIndex with no NaT. May be unsorted or
            contain duplicates; it is sorted and de-duplicated here.

    Returns a DataFrame with columns date (datetime64[ns]) and ticker (str):
        one row per (date, ticker) where date_added <= date and
        (date_removed is NaT or date < date_removed). Sorted by
        (date, ticker), RangeIndex.

    Raises ValueError if a membership column is missing, dates is not a
    tz-naive DatetimeIndex without NaT, membership has a missing date_added
    or a missing/blank ticker, a requested date is earlier than the coverage
    start (earliest date_added among start_censored rows), or a ticker's
    intervals overlap. Bad input is never silently dropped or coerced.
    """

## Steps
0. Validation — raise ValueError (with a short message) if any of these is true:
   a. any of "ticker", "date_added", "date_removed", "start_censored" is not a column of membership
   b. not isinstance(dates, pd.DatetimeIndex)
   c. dates.tz is not None
   d. dates.isna().any()
   e. membership["date_added"].isna().any()
   f. any(_norm(t) is None or _norm(t) == "" for t in membership["ticker"])
   g. coverage check:
        censored = membership[membership["start_censored"]]
        if len(censored) > 0 and len(dates) > 0 and dates.min() < censored["date_added"].min(): raise ValueError
1. dates = dates.unique().sort_values()
2. rows = []. For r in membership.itertuples(index=False):
      if pd.isna(r.date_removed): sel = dates[dates >= r.date_added]
      else: sel = dates[(dates >= r.date_added) & (dates < r.date_removed)]
      for d in sel: rows.append((d, r.ticker))
3. out = pd.DataFrame(rows, columns=["date", "ticker"])
   out["date"] = pd.to_datetime(out["date"]).astype("datetime64[ns]")
   out["ticker"] = out["ticker"].astype(str)
4. if out.duplicated(["date", "ticker"]).any(): raise ValueError("overlapping membership intervals for the same ticker")
5. return out.sort_values(["date", "ticker"]).reset_index(drop=True)

## Done so far
reconstruct_membership() with input validation and 15 passing tests, committed.

## This session's task
Add the function. Then run exactly this one command from the repo root and nothing else:
    python -c "from src.data.equity_us.sp500_membership import membership_on_dates; print('import ok')"
Fill in the self-check and stop.

## Resume point
If out of budget: the function exists but may be incomplete — the next session finishes the remaining steps only.

## Session self-check
- Implementation complete: `membership_on_dates()` function added following all steps from the handoff.
- Import verification passed: `python -c "from src.data.equity_us.sp500_membership import membership_on_dates; print('import ok')"` returns "import ok".
- No tests were run this session per the handoff instructions (tests deferred to equity_us_2b_tests_part1.md).
- Assumed no changes needed to existing code (`reconstruct_membership()` and `_norm()` remain untouched).
- Session ended as specified: implement only, then verify with import command.

