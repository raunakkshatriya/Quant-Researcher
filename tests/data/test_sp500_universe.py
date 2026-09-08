"""Unit tests for S&P 500 top-50 universe snapshot builder."""

import pytest
import pandas as pd


def test_50_rows_five_columns():
    """Verify function returns DataFrame with exactly 50 rows and correct columns."""
    from src.data.sp500_universe import build_sp500_top50_snapshot

    result = build_sp500_top50_snapshot()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 50, f"Expected exactly 50 rows, got {len(result)}"

    expected_columns = ["ticker", "company_name", "sector", "market_cap_usd", "snapshot_date"]
    assert list(result.columns) == expected_columns, \
        f"Expected columns {expected_columns}, got {list(result.columns)}"


def test_market_cap_sorted_descending():
    """Verify market_cap_usd is sorted in descending order."""
    from src.data.sp500_universe import build_sp500_top50_snapshot

    result = build_sp500_top50_snapshot()

    assert result["market_cap_usd"].is_monotonic_decreasing, \
        "market_cap_usd should be sorted in descending order"


def test_no_dots_in_ticker():
    """Verify no ticker value contains a literal '.' character."""
    from src.data.sp500_universe import build_sp500_top50_snapshot

    result = build_sp500_top50_snapshot()

    for idx, row in result.iterrows():
        ticker = str(row["ticker"])
        assert "." not in ticker, f"Ticker '{ticker}' contains a literal '.' character"


# Run tests when module is executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
