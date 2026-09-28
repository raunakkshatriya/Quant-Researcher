# Handoff — equity_us_shared — 1a: implement reconstruct_membership (no tests)

## Objective
Write the function reconstruct_membership() in one new file, following the numbered steps below literally. No tests this session.

## Allowed files
- src/data/equity_us/__init__.py            (create, completely empty)
- src/data/equity_us/sp500_membership.py    (create)
Nothing else. Do NOT create tests, debug scripts, or scratch files. Do NOT edit anything under src/data/ outside src/data/equity_us/.

## Budget rules for this session
- Implement the steps exactly as written. Do not re-derive, re-interpret, or trace the algorithm by hand. The steps are already correct.
- Do not write comments that explain what the algorithm "means". Copy the "Steps" section below into the function docstring word for word; that is the explanation.
- The only command you run is the import check at the end. If it fails, you may make ONE fix. If it still fails, stop and write the error in the self-check.

## Function signature
    def reconstruct_membership(current, changes, as_of_date, start_date):
        -> returns a tuple (membership, anomalies), both pandas DataFrames

Imports allowed: pandas only (import pandas as pd).

## Inputs
- current: DataFrame with a column `ticker`.
- changes: DataFrame with columns `date` (datetimes), `added_ticker`, `removed_ticker`. The ticker columns may contain None/NaN.
- as_of_date, start_date: pd.Timestamp.

## Helper (write this exactly, as a module-level function)
    def _norm(x):
        if pd.isna(x):
            return None
        return str(x).strip().upper()

## Steps
0. Validation: if `ticker` is not a column of current, raise ValueError. If any of `date`, `added_ticker`, `removed_ticker` is not a column of changes, raise ValueError. If start_date >= as_of_date, raise ValueError.
1. Keep only rows of changes where start_date <= date <= as_of_date. Sort them by date DESCENDING (use sort_values("date", ascending=False, kind="stable")).
2. working = a dict. For every value t in current["ticker"]: working[_norm(t)] = pd.NaT.
3. mem_rows = [] and anomaly_rows = []. Loop over the kept change rows in order. For each row: d = row date, X = _norm(added_ticker), Y = _norm(removed_ticker).
   a. If X is not None:
      - if X in working: mem_rows.append((X, d, working[X], False)); then del working[X]
      - else: anomaly_rows.append((d, X, "add", "added_ticker_not_in_working_set"))
   b. If Y is not None:
      - if Y not in working: working[Y] = d
      - else: anomaly_rows.append((d, Y, "remove", "removed_ticker_already_in_working_set"))
4. For every (t, end) in working.items(): mem_rows.append((t, start_date, end, True)).
5. Build the outputs:
   membership = pd.DataFrame(mem_rows, columns=["ticker", "date_added", "date_removed", "start_censored"])
   membership["ticker"] = membership["ticker"].astype(str)
   membership["date_added"] = pd.to_datetime(membership["date_added"]).astype("datetime64[ns]")
   membership["date_removed"] = pd.to_datetime(membership["date_removed"]).astype("datetime64[ns]")
   membership["start_censored"] = membership["start_censored"].astype(bool)
   membership = membership.sort_values(["ticker", "date_added"]).reset_index(drop=True)

   anomalies = pd.DataFrame(anomaly_rows, columns=["date", "ticker", "event", "reason"])
   anomalies["date"] = pd.to_datetime(anomalies["date"]).astype("datetime64[ns]")
   anomalies["ticker"] = anomalies["ticker"].astype(str)
   anomalies["event"] = anomalies["event"].astype(str)
   anomalies["reason"] = anomalies["reason"].astype(str)
   anomalies = anomalies.sort_values(["date", "ticker"]).reset_index(drop=True)

   return membership, anomalies

## Output meaning (for the docstring, copy as-is)
membership columns: ticker; date_added (first member day, inclusive); date_removed (first NON-member day, exclusive; NaT = still a member at as_of_date); start_censored (True = already a member at start_date, real add date unknown).
anomalies columns: date, ticker, event ("add"/"remove"), reason.
Pure function: no network, no file I/O, no datetime.now().

## Done so far
Nothing committed. A previous attempt was deleted.

## This session's task
Create the two allowed files. Then run exactly this one command from the repo root and nothing else:
    python -c "from src.data.equity_us.sp500_membership import reconstruct_membership; print('import ok')"
Then fill in the self-check and stop.

## Resume point
If out of budget: the file exists but may be incomplete — the next session finishes step 5 only.

## Session self-check

**Assumptions made:** None — the steps were followed exactly as written.

**Import check output:** `import ok`

**Nothing uncertain.**
