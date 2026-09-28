"""Reconstruct S&P 500 membership from changes data."""

import pandas as pd

from pandas.api import types as ptypes


def _norm(x):
    """Normalize a value to uppercase string or None."""
    if pd.isna(x):
        return None
    return str(x).strip().upper()


def reconstruct_membership(current, changes, as_of_date, start_date):
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

    Raises ValueError if a required column is missing, start_date >= as_of_date,
    changes['date'] is not a tz-naive datetime column or contains NaT, or
    current['ticker'] contains missing/blank tickers. Bad input is never
    silently dropped or coerced.
    """
    # 0. Validation
    if "ticker" not in current.columns:
        raise ValueError("Ticker column not found in current DataFrame")
    if "date" not in changes.columns or "added_ticker" not in changes.columns or "removed_ticker" not in changes.columns:
        raise ValueError("Required columns not found in changes DataFrame")
    if start_date >= as_of_date:
        raise ValueError("start_date must be less than as_of_date")

    # Validate date column
    if not ptypes.is_datetime64_any_dtype(changes["date"]):
        raise ValueError("changes['date'] must be a datetime column")
    if changes["date"].dt.tz is not None:
        raise ValueError("changes['date'] must be tz-naive")
    if changes["date"].isna().any():
        raise ValueError("changes['date'] contains missing dates (NaT)")

    # Validate ticker column in current
    if any(_norm(t) is None or _norm(t) == "" for t in current["ticker"]):
        raise ValueError("current['ticker'] contains missing or blank tickers")

    # 1. Filter and sort changes
    changes_filtered = changes[(changes["date"] >= start_date) & (changes["date"] <= as_of_date)]
    changes_sorted = changes_filtered.sort_values("date", ascending=False, kind="stable")

    # 2. Initialize working set
    working = { _norm(t): pd.NaT for t in current["ticker"] }

    # 3. Process change rows in order (most recent first)
    mem_rows = []
    anomaly_rows = []
    for _, row in changes_sorted.iterrows():
        d = row["date"]
        X = _norm(row["added_ticker"])
        Y = _norm(row["removed_ticker"])

        # Handle adds
        if X is not None:
            if X in working:
                mem_rows.append((X, d, working[X], False))
                del working[X]
            else:
                anomaly_rows.append((d, X, "add", "added_ticker_not_in_working_set"))

        # Handle removes
        if Y is not None:
            if Y not in working:
                working[Y] = d
            else:
                anomaly_rows.append((d, Y, "remove", "removed_ticker_already_in_working_set"))

    # 4. Add remaining members (still in at start_date)
    for t, end in working.items():
        mem_rows.append((t, start_date, end, True))

    # 5. Build outputs
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


def membership_on_dates(membership, dates):
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
    # 0. Validation
    if "ticker" not in membership.columns:
        raise ValueError("membership['ticker'] column not found")
    if "date_added" not in membership.columns:
        raise ValueError("membership['date_added'] column not found")
    if "date_removed" not in membership.columns:
        raise ValueError("membership['date_removed'] column not found")
    if "start_censored" not in membership.columns:
        raise ValueError("membership['start_censored'] column not found")
    if not isinstance(dates, pd.DatetimeIndex):
        raise ValueError("dates must be a DatetimeIndex")
    if dates.tz is not None:
        raise ValueError("dates must be tz-naive")
    if dates.isna().any():
        raise ValueError("dates contains NaT values")
    if membership["date_added"].isna().any():
        raise ValueError("membership['date_added'] contains missing values")
    for t in membership["ticker"]:
        n = _norm(t)
        if n is None or n == "":
            raise ValueError("membership['ticker'] contains missing/blank tickers")
    censored = membership[membership["start_censored"]]
    if len(censored) > 0 and len(dates) > 0 and dates.min() < censored["date_added"].min():
        raise ValueError(
            "dates extends before coverage start (earliest date_added among start_censored rows)"
        )

    # 1. Sort and deduplicate dates
    dates = dates.unique().sort_values()

    # 2. Expand intervals
    rows = []
    for r in membership.itertuples(index=False):
        if pd.isna(r.date_removed):
            sel = dates[dates >= r.date_added]
        else:
            sel = dates[(dates >= r.date_added) & (dates < r.date_removed)]
        for d in sel:
            rows.append((d, r.ticker))

    # 3. Build DataFrame
    out = pd.DataFrame(rows, columns=["date", "ticker"])
    out["date"] = pd.to_datetime(out["date"]).astype("datetime64[ns]")
    out["ticker"] = out["ticker"].astype(str)

    # 4. Check for overlapping intervals
    if out.duplicated(["date", "ticker"]).any():
        raise ValueError("overlapping membership intervals for the same ticker")

    # 5. Sort and reset index
    return out.sort_values(["date", "ticker"]).reset_index(drop=True)

