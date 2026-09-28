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


# ============================================================
# Test case 1 — test_normal_case
# ============================================================

def test_normal_case():
    current = pd.DataFrame({"ticker": ["A", "B", "C"]})
    changes = make_changes(["2024-03-01"], ["C"], ["D"])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    expected_membership = [
        ("A", "2023-01-01", "NaT", True),
        ("B", "2023-01-01", "NaT", True),
        ("C", "2024-03-01", "NaT", False),
        ("D", "2023-01-01", "2024-03-01", True),
    ]

    expected_anomalies = []

    assert as_rows(membership) == expected_membership, f"Expected membership:\n{expected_membership}\nGot: {as_rows(membership)}"
    assert as_rows(anomalies) == expected_anomalies, f"Expected anomalies:\n{expected_anomalies}\nGot: {as_rows(anomalies)}"


# ============================================================
# Test case 1b — test_output_columns_and_dtypes (same inputs as case 1)
# ============================================================

def test_output_columns_and_dtypes():
    current = pd.DataFrame({"ticker": ["A", "B", "C"]})
    changes = make_changes(["2024-03-01"], ["C"], ["D"])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    assert list(membership.columns) == ["ticker", "date_added", "date_removed", "start_censored"]
    assert list(anomalies.columns) == ["date", "ticker", "event", "reason"]
    assert ptypes.is_string_dtype(membership["ticker"])
    assert ptypes.is_datetime64_any_dtype(membership["date_added"])
    assert ptypes.is_datetime64_any_dtype(membership["date_removed"])
    assert ptypes.is_bool_dtype(membership["start_censored"])
    assert ptypes.is_datetime64_any_dtype(anomalies["date"])


# ============================================================
# Test case 2 — test_removed_then_readded
# ============================================================

def test_removed_then_readded():
    current = pd.DataFrame({"ticker": ["E"]})
    changes = make_changes(["2023-06-01", "2024-06-01"], [None, "E"], ["E", None])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    expected_membership = [
        ("E", "2023-01-01", "2023-06-01", True),
        ("E", "2024-06-01", "NaT", False),
    ]

    expected_anomalies = []

    assert as_rows(membership) == expected_membership, f"Expected membership:\n{expected_membership}\nGot: {as_rows(membership)}"
    assert as_rows(anomalies) == expected_anomalies, f"Expected anomalies:\n{expected_anomalies}\nGot: {as_rows(anomalies)}"


# ============================================================
# Test case 3 — test_changes_outside_window_ignored
# ============================================================

def test_changes_outside_window_ignored():
    current = pd.DataFrame({"ticker": ["A"]})
    changes = make_changes(["2022-06-01", "2026-12-01"], ["A", None], [None, "X"])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    expected_membership = [
        ("A", "2023-01-01", "NaT", True),
    ]

    expected_anomalies = []

    assert as_rows(membership) == expected_membership, f"Expected membership:\n{expected_membership}\nGot: {as_rows(membership)}"
    assert as_rows(anomalies) == expected_anomalies, f"Expected anomalies:\n{expected_anomalies}\nGot: {as_rows(anomalies)}"


# ============================================================
# Test case 4 — test_anomalies_recorded_not_raised
# ============================================================

def test_anomalies_recorded_not_raised():
    current = pd.DataFrame({"ticker": ["A"]})
    changes = make_changes(["2024-01-01", "2024-02-01"], ["Z", None], [None, "A"])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    expected_membership = [
        ("A", "2023-01-01", "NaT", True),
    ]

    expected_anomalies = [
        ("2024-01-01", "Z", "add", "added_ticker_not_in_working_set"),
        ("2024-02-01", "A", "remove", "removed_ticker_already_in_working_set"),
    ]

    assert as_rows(membership) == expected_membership, f"Expected membership:\n{expected_membership}\nGot: {as_rows(membership)}"
    assert as_rows(anomalies) == expected_anomalies, f"Expected anomalies:\n{expected_anomalies}\nGot: {as_rows(anomalies)}"


# ============================================================
# Test case 5 — test_empty_changes
# ============================================================

def test_empty_changes():
    current = pd.DataFrame({"ticker": ["A", "B"]})
    changes = make_changes([], [], [])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    expected_membership = [
        ("A", "2023-01-01", "NaT", True),
        ("B", "2023-01-01", "NaT", True),
    ]

    expected_anomalies = []

    assert as_rows(membership) == expected_membership, f"Expected membership:\n{expected_membership}\nGot: {as_rows(membership)}"
    assert as_rows(anomalies) == expected_anomalies, f"Expected anomalies:\n{expected_anomalies}\nGot: {as_rows(anomalies)}"
    assert list(anomalies.columns) == ["date", "ticker", "event", "reason"]


# ============================================================
# Test case 6 — test_missing_values_and_ticker_normalization
# ============================================================

def test_missing_values_and_ticker_normalization():
    current = pd.DataFrame({"ticker": [" aapl ", "MSFT"]})
    changes = make_changes(["2024-06-01", "2024-09-01", "2025-06-01"],
                           [None, None, "msft"],
                           ["goog ", None, None])

    membership, anomalies = reconstruct_membership(current, changes, AS_OF, START)

    expected_membership = [
        ("AAPL", "2023-01-01", "NaT", True),
        ("GOOG", "2023-01-01", "2024-06-01", True),
        ("MSFT", "2025-06-01", "NaT", False),
    ]

    expected_anomalies = []

    assert as_rows(membership) == expected_membership, f"Expected membership:\n{expected_membership}\nGot: {as_rows(membership)}"
    assert as_rows(anomalies) == expected_anomalies, f"Expected anomalies:\n{expected_anomalies}\nGot: {as_rows(anomalies)}"


# ============================================================
# Test case 7 — test_invalid_inputs_raise (three separate with pytest.raises blocks)
# ============================================================

def test_invalid_inputs_raise_changes_missing_column():
    bad = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "added_ticker": ["A"]})
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), bad, AS_OF, START)


def test_invalid_inputs_raise_start_after_as_of():
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), make_changes([], [], []), START, AS_OF)


def test_invalid_inputs_raise_start_equal_to_as_of():
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), make_changes([], [], []), AS_OF, AS_OF)


# ============================================================
# Test case 8 — test_date_column_as_strings_raises
# ============================================================

def test_date_column_as_strings_raises():
    changes = pd.DataFrame({"date": ["2024-01-01"], "added_ticker": ["B"], "removed_ticker": [None]})
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), changes, AS_OF, START)


# ============================================================
# Test case 9 — test_date_column_with_nat_raises
# ============================================================

def test_date_column_with_nat_raises():
    changes = make_changes(["2024-01-01", None], ["B", None], [None, "C"])
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), changes, AS_OF, START)


# ============================================================
# Test case 10 — test_tz_aware_dates_raise
# ============================================================

def test_tz_aware_dates_raise():
    changes = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]).tz_localize("UTC"),
                            "added_ticker": ["B"], "removed_ticker": [None]})
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), changes, AS_OF, START)


# ============================================================
# Test case 11 — test_missing_ticker_in_current_raises
# ============================================================

def test_missing_ticker_in_current_raises():
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A", None]}), make_changes([], [], []), AS_OF, START)


# ============================================================
# Test case 12 — test_blank_ticker_in_current_raises
# ============================================================

def test_blank_ticker_in_current_raises():
    with pytest.raises(ValueError):
        reconstruct_membership(pd.DataFrame({"ticker": ["A", "   "]}), make_changes([], [], []), AS_OF, START)
