"""Tests for compute_sma feature."""
import pytest
import pandas as pd
from src.features.moving_average import compute_sma


@pytest.fixture
def ticker_df():
    """Single ticker with enough history for window=3."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
            ],
            "ticker": ["AAPL"] * 5,
            "close": [10.0, 11.0, 12.0, 13.0, 14.0],
        }
    )


@pytest.fixture
def ticker_insufficient_history():
    """Single ticker with insufficient history for window=3."""
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "ticker": ["GOOGL"] * 2,
            "close": [150.0, 152.0],
        }
    )


@pytest.fixture
def ticker_with_gap():
    """Single ticker with a gap in dates (non-consecutive days)."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-05",  # gap here
                "2024-01-06",
            ],
            "ticker": ["MSFT"] * 4,
            "close": [100.0, 101.0, 103.0, 105.0],
        }
    )


@pytest.fixture
def two_tickers_df():
    """Two tickers in the same DataFrame."""
    return pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"],
            "ticker": ["AAPL", "GOOGL", "AAPL", "GOOGL"],
            "close": [10.0, 150.0, 11.0, 152.0],
        }
    )


def test_normal_window(ticker_df):
    """Normal window: SMA value matches manually computed average."""
    result = compute_sma(ticker_df, window=3)

    # Expected SMAs (rolling 3-day mean of close):
    # Row 0: NaN (not enough history)
    # Row 1: NaN (only 2 rows)
    # Row 2: 11.0 (average of 10, 11, 12)
    # Row 3: 12.0 (average of 11, 12, 13)
    # Row 4: 13.0 (average of 12, 13, 14)
    expected_sma = [float("nan"), float("nan"), 11.0, 12.0, 13.0]

    for i in range(len(result)):
        expected = expected_sma[i]
        actual = result.iloc[i]["sma_3"]
        if pd.isna(expected):
            assert pd.isna(actual), f"Row {i}: Expected NaN but got {actual}"
        else:
            assert actual == expected, f"Row {i}: Expected {expected} but got {actual}"


def test_insufficient_history(ticker_insufficient_history):
    """Insufficient history: first (window - 1) rows should be NaN."""
    result = compute_sma(ticker_insufficient_history, window=3)

    # First two rows have insufficient history for window=3
    assert pd.isna(result.iloc[0]["sma_3"]), "First row should be NaN"
    assert pd.isna(result.iloc[1]["sma_3"]), "Second row should be NaN"


def test_gap_in_dates(ticker_with_gap):
    """Ticker with gap: rolling window computed over actual rows, not calendar days."""
    result = compute_sma(ticker_with_gap, window=3)

    # Row 0: NaN (only 1 data point before - not enough for window=3)
    assert pd.isna(result.iloc[0]["sma_3"])

    # Row 1: 100.5 (average of 100, 101 - min_periods=3 allows this since we pass 2)
    # Actually with min_periods=window=3, pandas will NOT compute until we have 3
    assert pd.isna(result.iloc[1]["sma_3"])

    # Row 2: average of 3 points (100, 101, 103) = 101.333
    expected = (100.0 + 101.0 + 103.0) / 3
    assert result.iloc[2]["sma_3"] == expected

    # Row 3: average of next 3 points (101, 103, 105) = 103.0
    expected = (101.0 + 103.0 + 105.0) / 3
    assert result.iloc[3]["sma_3"] == expected


def test_two_tickers_isolation(two_tickers_df):
    """Two tickers: ticker A's SMA unaffected by ticker B's prices."""
    # DataFrame is sorted by ticker (alphabetically), then date before computing
    result = compute_sma(df=two_tickers_df.copy(), window=2)

    # After sort, the order in the copy is:
    # - Row 0: index=0, ticker=AAPL, close=10.0
    # - Row 1: index=2, ticker=AAPL, close=11.0
    # - Row 2: index=1, ticker=GOOGL, close=150.0
    # - Row 3: index=3, ticker=GOOGL, close=152.0

    # The result preserves original indices but follows sorted order for content
    # Result iloc[0]: AAPL (first data point) -> SMA=NaN
    # Result iloc[1]: AAPL (second data point) -> SMA=10.5 (has 2 points now)
    # Result iloc[2]: GOOGL (first data point) -> SMA=NaN
    # Result iloc[3]: GOOGL (second data point) -> SMA=151.0 (has 2 points now)

    assert pd.isna(result.iloc[0]["sma_2"])  # AAPL, first data point
    assert result.iloc[1]["sma_2"] == 10.5   # AAPL, now has 2 points
    assert pd.isna(result.iloc[2]["sma_2"])  # GOOGL, first data point
    assert result.iloc[3]["sma_2"] == 151.0  # GOOGL, now has 2 points

    # Verify ticker isolation: AAPL's SMA at row 1 (10.5) should NOT be
    # affected by GOOGL's prices at rows 2 and 3 (computed per-ticker independently)
    assert result.iloc[1]["sma_2"] == 10.5, "AAPL SMA should be unaffected by GOOGL prices"
