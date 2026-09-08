"""Unit tests for price history loader — tests the real function via a
mocked yfinance.download() call, since live network access to Yahoo
Finance isn't available in every environment this runs in."""
from unittest.mock import patch

import pandas as pd
import pytest

from src.data.price_history import fetch_price_history


def _make_mock_yf_response(tickers, dates):
    """Build a DataFrame matching yfinance's real multi-ticker,
    group_by='ticker' output shape: MultiIndex columns of
    (ticker, field), DatetimeIndex named 'Date'."""
    fields = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    columns = pd.MultiIndex.from_product([tickers, fields])
    index = pd.DatetimeIndex(dates, name="Date")
    data = {}
    for i, ticker in enumerate(tickers):
        base = 100.0 + i * 50
        for j, field in enumerate(fields[:-1]):  # price fields
            data[(ticker, field)] = [base + d_i + j for d_i in range(len(dates))]
        data[(ticker, "Volume")] = [1_000_000 + d_i * 1000 for d_i in range(len(dates))]
    return pd.DataFrame(data, index=index, columns=columns)


@pytest.fixture
def tickers():
    return ["AAPL", "MSFT", "NVDA"]


@pytest.fixture
def dates():
    return pd.date_range("2026-08-30", periods=10, freq="D")


def test_returns_dataframe_with_correct_columns(tickers, dates):
    """Returns a DataFrame with the 8 expected columns."""
    mock_response = _make_mock_yf_response(tickers, dates)
    with patch("src.data.price_history.yf.download", return_value=mock_response):
        with patch("os.path.exists", return_value=False), patch("pandas.DataFrame.to_parquet"):
            df = fetch_price_history(tickers, start_date="2026-08-30", end_date="2026-09-08")

    expected_columns = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    assert list(df.columns) == expected_columns


def test_every_requested_ticker_appears(tickers, dates):
    """Every requested ticker appears at least once in the ticker column."""
    mock_response = _make_mock_yf_response(tickers, dates)
    with patch("src.data.price_history.yf.download", return_value=mock_response):
        with patch("os.path.exists", return_value=False), patch("pandas.DataFrame.to_parquet"):
            df = fetch_price_history(tickers, start_date="2026-08-30", end_date="2026-09-08")

    for ticker in tickers:
        assert ticker in df["ticker"].values, f"Ticker {ticker} not found in dataframe"


def test_no_duplicate_date_ticker_pairs(tickers, dates):
    """No duplicate (date, ticker) pairs."""
    mock_response = _make_mock_yf_response(tickers, dates)
    with patch("src.data.price_history.yf.download", return_value=mock_response):
        with patch("os.path.exists", return_value=False), patch("pandas.DataFrame.to_parquet"):
            df = fetch_price_history(tickers, start_date="2026-08-30", end_date="2026-09-08")

    duplicates = df[df.duplicated(subset=["date", "ticker"], keep=False)]
    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate (date, ticker) pairs"


def test_all_dates_within_start_end_range(tickers, dates):
    """All returned dates fall within [start_date, end_date]."""
    mock_response = _make_mock_yf_response(tickers, dates)
    start = pd.to_datetime("2026-08-30").date()
    end = pd.to_datetime("2026-09-08").date()
    with patch("src.data.price_history.yf.download", return_value=mock_response):
        with patch("os.path.exists", return_value=False), patch("pandas.DataFrame.to_parquet"):
            df = fetch_price_history(tickers, start_date="2026-08-30", end_date="2026-09-08")

    assert (df["date"] >= start).all() and (df["date"] <= end).all()


def test_date_ticker_sort_order(tickers, dates):
    """DataFrame is sorted by ticker, then date."""
    mock_response = _make_mock_yf_response(tickers, dates)
    with patch("src.data.price_history.yf.download", return_value=mock_response):
        with patch("os.path.exists", return_value=False), patch("pandas.DataFrame.to_parquet"):
            df = fetch_price_history(tickers, start_date="2026-08-30", end_date="2026-09-08")

    assert list(df["ticker"]) == sorted(df["ticker"])
    for ticker in tickers:
        sub = df[df["ticker"] == ticker]
        assert list(sub["date"]) == sorted(sub["date"])


def test_single_ticker_does_not_raise(dates):
    """Regression test: a single-ticker request must not hit the
    undefined-variable bug the previous implementation had in its
    single-ticker branch."""
    mock_response = _make_mock_yf_response(["AAPL"], dates)
    with patch("src.data.price_history.yf.download", return_value=mock_response):
        with patch("os.path.exists", return_value=False), patch("pandas.DataFrame.to_parquet"):
            df = fetch_price_history(["AAPL"], start_date="2026-08-30", end_date="2026-09-08")

    assert (df["ticker"] == "AAPL").all()
    assert len(df) == len(dates)
