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


def test_normal_case():
    membership = make_membership([("A", "2023-01-01", None, True), ("B", "2023-01-01", "2024-01-01", True)])
    dates = make_dates(["2023-06-01", "2024-01-01", "2025-01-01"])
    expected = [("2023-06-01", "A"), ("2023-06-01", "B"), ("2024-01-01", "A"), ("2025-01-01", "A")]
    out = membership_on_dates(membership, dates)
    assert as_rows(out) == expected


def test_boundaries_inclusive_start_exclusive_end():
    membership = make_membership([("C", "2024-03-01", "2024-06-01", False)])
    dates = make_dates(["2024-02-29", "2024-03-01", "2024-05-31", "2024-06-01"])
    expected = [("2024-03-01", "C"), ("2024-05-31", "C")]
    out = membership_on_dates(membership, dates)
    assert as_rows(out) == expected


def test_removed_then_readded():
    membership = make_membership([("E", "2023-01-01", "2023-06-01", True), ("E", "2024-06-01", None, False)])
    dates = make_dates(["2023-03-01", "2024-01-01", "2024-07-01"])
    expected = [("2023-03-01", "E"), ("2024-07-01", "E")]
    out = membership_on_dates(membership, dates)
    assert as_rows(out) == expected


def test_unsorted_duplicate_dates():
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = make_dates(["2024-02-01", "2024-01-01", "2024-02-01"])
    expected = [("2024-01-01", "A"), ("2024-02-01", "A")]
    out = membership_on_dates(membership, dates)
    assert as_rows(out) == expected


def test_empty_membership():
    membership = make_membership([])
    dates = make_dates(["2024-01-01"])
    expected = []
    out = membership_on_dates(membership, dates)
    assert as_rows(out) == expected
    assert list(out.columns) == ["date", "ticker"]


def test_output_dtypes():
    membership = make_membership([("A", "2023-01-01", None, True), ("B", "2023-01-01", "2024-01-01", True)])
    dates = make_dates(["2023-06-01"])
    out = membership_on_dates(membership, dates)
    assert list(out.columns) == ["date", "ticker"]
    assert ptypes.is_datetime64_any_dtype(out["date"])
    assert ptypes.is_string_dtype(out["ticker"])


def test_date_before_coverage_start_raises():
    """Test that dates before the earliest start_censored date raise ValueError."""
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = make_dates(["2022-12-31"])

    with pytest.raises(ValueError):
        membership_on_dates(membership, dates)


def test_missing_membership_column_raises():
    """Test that missing required columns raise ValueError."""
    membership = make_membership([("A", "2023-01-01", None, True)]).drop(columns=["start_censored"])
    dates = make_dates(["2024-01-01"])

    with pytest.raises(ValueError):
        membership_on_dates(membership, dates)


def test_dates_not_datetimeindex_raises():
    """Test that non-DatetimeIndex input raises ValueError."""
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = ["2024-01-01"]

    with pytest.raises(ValueError):
        membership_on_dates(membership, dates)


def test_dates_with_nat_raises():
    """Test that NaT values in dates raise ValueError."""
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = pd.DatetimeIndex(["2024-01-01", None])

    with pytest.raises(ValueError):
        membership_on_dates(membership, dates)


def test_overlapping_intervals_raise():
    """Test that overlapping membership intervals raise ValueError."""
    membership = make_membership([("A", "2023-01-01", None, False), ("A", "2024-01-01", None, False)])
    dates = make_dates(["2024-06-01"])

    with pytest.raises(ValueError):
        membership_on_dates(membership, dates)


def test_tz_aware_dates_raise():
    """Test that timezone-aware timestamps raise ValueError."""
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = make_dates(["2024-01-01"]).tz_localize("UTC")

    with pytest.raises(ValueError):
        membership_on_dates(membership, dates)
