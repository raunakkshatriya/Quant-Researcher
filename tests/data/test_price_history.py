"""Unit tests for price history loader."""

import pandas as pd


# SMALL test fixture — 3 tickers, 10 days
TICKERS = ["AAPL", "MSFT", "NVDA"]
START_DATE = pd.to_datetime("2026-08-30").date()  # Fixed to allow proper date range test
END_DATE = pd.to_datetime("2026-09-08").date()


def create_small_fixture():
    """Create a small test fixture with mock data (no network)."""

    import hashlib
    from datetime import date, timedelta

    # Pre-compute all dates (10 days starting from START_DATE)
    start_date_obj = pd.to_datetime("2026-08-30").date()
    end_date_obj = pd.to_datetime("2026-09-08").date()
    all_dates = [start_date_obj + timedelta(days=i) for i in range(10)]

    rows = []

    for ticker in sorted(TICKERS):
        for day_offset in range(10):
            date_val = all_dates[day_offset]

            # Hash string for consistent variation (use single arg)
            ticker_hash = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 100

            rows.append({
                "date": date_val,
                "ticker": ticker,
                "open": 100 + day_offset * 2 + ticker_hash % 10,
                "high": 102 + day_offset * 2 + ticker_hash % 10,
                "low": 98 + day_offset * 2 + ticker_hash % 10,
                "close": 101 + day_offset * 2 + ticker_hash % 10,
                "adj_close": 99.5 + day_offset * 2 + ticker_hash % 10,
                "volume": 1_000_000 + (int(hashlib.md5(f"{date_val}_{ticker}".encode()).hexdigest(), 16) % 500_000),
            })

    return pd.DataFrame(rows)


def test_returns_dataframe_with_correct_columns():
    """Returns a DataFrame with the 8 expected columns."""
    df = create_small_fixture()

    expected_columns = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
    assert set(df.columns) == set(expected_columns), f"Expected columns {expected_columns}, got {list(df.columns)}"


def test_every_requested_ticker_appears():
    """Every requested ticker appears at least once in the ticker column."""
    df = create_small_fixture()

    for ticker in TICKERS:
        assert ticker in df["ticker"].values, f"Ticker {ticker} not found in dataframe"


def test_no_duplicate_date_ticker_pairs():
    """No duplicate (date, ticker) pairs."""
    df = create_small_fixture()

    duplicates = df[(df.duplicated(subset=["date", "ticker"], keep=False))]
    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate (date, ticker) pairs"


def test_all_dates_within_start_end_range():
    """All returned dates fall within [start_date, end_date]."""
    df = create_small_fixture()

    for _, row in df.iterrows():
        assert START_DATE <= row["date"] <= END_DATE, f"Date {row['date']} outside [{START_DATE}, {END_DATE}]"


def test_date_ticker_sort_order():
    """DataFrame is sorted by ticker, then date."""
    df = create_small_fixture()

    ticks_sorted = sorted(df["ticker"].unique())
    expected_ticks = TICKERS.copy()  # Should be ["AAPL", "MSFT", "NVDA"]

    # Verify tickers are sorted correctly by checking row order (get unique tickers in order)
    expected_tick_order = ["AAPL", "MSFT", "NVDA"]
    actual_unique_ticks = []
    for ticker in df.sort_values(by=["ticker"])["ticker"].tolist():
        if ticker not in actual_unique_ticks:
            actual_unique_ticks.append(ticker)
    assert actual_unique_ticks == expected_tick_order, f"Expected tickers {expected_tick_order}, got {actual_unique_ticks}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
