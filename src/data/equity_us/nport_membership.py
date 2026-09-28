"""Turn saved quarterly IVV N-PORT snapshots into S&P 500 membership intervals.

Two functions:
- load_equity_snapshots(): reads the saved XML files (file I/O, no network)
  and returns every common-equity holding per snapshot date.
- snapshots_to_intervals(): pure — quarterly presence -> membership intervals.

Convention (decided 2026-09-28): a snapshot describes the index on its
holdings date and stays in force until the next snapshot date. So a security
first seen at snapshot t_k is a member from t_k (inclusive); if it is missing
from a later snapshot t_j, its interval ends at t_j (exclusive). Changes that
happen between two quarter-ends therefore show up at the next snapshot date.
Intervals are keyed by ISIN; mapping ISIN -> trading ticker is a later step.
"""

from pathlib import Path

import pandas as pd

from src.data.equity_us.nport import parse_nport_holdings

SNAPSHOT_COLUMNS = ["rep_pd_date", "isin", "cusip", "name", "value_usd", "pct_value"]
INTERVAL_COLUMNS = ["isin", "date_added", "date_removed", "start_censored"]


def load_equity_snapshots(snapshots, raw_dir):
    """Read the chosen snapshot files and keep common equity (asset_category "EC").

    Inputs:
        snapshots: output of select_snapshots() — needs columns rep_pd_date
            and file_name, one row per holdings date.
        raw_dir: str or Path, folder holding the saved XML files.

    Returns a DataFrame with columns rep_pd_date (datetime64[ns]), isin (str),
    cusip (str or missing), name (str), value_usd (float), pct_value (float,
    percent). Sorted by (rep_pd_date, isin), RangeIndex.

    Raises ValueError if a column is missing, snapshots is empty, a file's own
    holdings date differs from the manifest, an equity row has no ISIN, or an
    ISIN appears twice on the same date.
    """
    for col in ["rep_pd_date", "file_name"]:
        if col not in snapshots.columns:
            raise ValueError(f"snapshots is missing column {col!r}")
    if len(snapshots) == 0:
        raise ValueError("snapshots is empty")
    raw_dir = Path(raw_dir)
    parts = []
    for row in snapshots.itertuples(index=False):
        meta, holdings = parse_nport_holdings((raw_dir / row.file_name).read_text(encoding="utf-8"))
        if meta["rep_pd_date"] != pd.Timestamp(row.rep_pd_date):
            raise ValueError(f"{row.file_name}: holdings date {meta['rep_pd_date']:%Y-%m-%d} "
                             f"does not match manifest {pd.Timestamp(row.rep_pd_date):%Y-%m-%d}")
        equity = holdings[holdings["asset_category"] == "EC"].copy()
        if equity["isin"].isna().any():
            raise ValueError(f"{row.file_name}: an equity position has no ISIN")
        equity["rep_pd_date"] = meta["rep_pd_date"]
        parts.append(equity[SNAPSHOT_COLUMNS])
    out = pd.concat(parts, ignore_index=True)
    out["rep_pd_date"] = pd.to_datetime(out["rep_pd_date"]).astype("datetime64[ns]")
    if out.duplicated(["rep_pd_date", "isin"]).any():
        raise ValueError("an ISIN appears twice on the same snapshot date")
    return out.sort_values(["rep_pd_date", "isin"]).reset_index(drop=True)


def snapshots_to_intervals(equity_snapshots):
    """Convert quarterly presence into membership intervals.

    Pure function: no network, no file I/O, no datetime.now().

    Input: DataFrame with at least columns rep_pd_date (datetime) and isin
        (str) — e.g. the output of load_equity_snapshots().

    Returns a DataFrame with columns isin (str), date_added (datetime64[ns],
    INCLUSIVE, a snapshot date), date_removed (datetime64[ns], EXCLUSIVE, the
    first later snapshot date where the ISIN is absent; NaT if present in the
    last snapshot), start_censored (bool, True if present in the first
    snapshot, i.e. real add date unknown). One row per consecutive run of
    presence, so a security that leaves and returns gets two rows. Sorted by
    (isin, date_added), RangeIndex.

    Raises ValueError if a column is missing, the input is empty, a date is
    missing (NaT), an ISIN is missing or blank, or an (rep_pd_date, isin)
    pair appears twice.
    """
    for col in ["rep_pd_date", "isin"]:
        if col not in equity_snapshots.columns:
            raise ValueError(f"equity_snapshots is missing column {col!r}")
    if len(equity_snapshots) == 0:
        raise ValueError("equity_snapshots is empty")
    if equity_snapshots["rep_pd_date"].isna().any():
        raise ValueError("equity_snapshots has a missing rep_pd_date")
    if any(pd.isna(v) or str(v).strip() == "" for v in equity_snapshots["isin"]):
        raise ValueError("equity_snapshots has a missing or blank isin")
    if equity_snapshots.duplicated(["rep_pd_date", "isin"]).any():
        raise ValueError("an (rep_pd_date, isin) pair appears twice")

    dates = sorted(pd.to_datetime(equity_snapshots["rep_pd_date"]).unique())
    position = {d: i for i, d in enumerate(dates)}
    rows = []
    for isin, group in equity_snapshots.groupby("isin"):
        present = sorted(position[d] for d in pd.to_datetime(group["rep_pd_date"]))
        run_start = present[0]
        previous = present[0]
        for idx in present[1:] + [None]:
            if idx is not None and idx == previous + 1:
                previous = idx
                continue
            end = previous + 1
            rows.append((
                str(isin),
                dates[run_start],
                dates[end] if end < len(dates) else pd.NaT,
                run_start == 0,
            ))
            if idx is not None:
                run_start = idx
                previous = idx

    out = pd.DataFrame(rows, columns=INTERVAL_COLUMNS)
    out["isin"] = out["isin"].astype(str)
    out["date_added"] = pd.to_datetime(out["date_added"]).astype("datetime64[ns]")
    out["date_removed"] = pd.to_datetime(out["date_removed"]).astype("datetime64[ns]")
    out["start_censored"] = out["start_censored"].astype(bool)
    return out.sort_values(["isin", "date_added"]).reset_index(drop=True)
