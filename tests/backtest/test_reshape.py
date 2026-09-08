"""Tests for pivot_long_to_wide() reshape function."""

import pandas as pd
import pytest
from src.backtest.reshape import pivot_long_to_wide


@pytest.fixture(scope="function")
def input_df():
    """Fixture: 5 rows with AAPL missing on 2026-01-03."""
    return pd.DataFrame([
        {"date": "2026-01-01", "ticker": "AAPL", "value": 10},
        {"date": "2026-01-01", "ticker": "MSFT", "value": 20},
        {"date": "2026-01-02", "ticker": "AAPL", "value": 11},
        {"date": "2026-01-02", "ticker": "MSFT", "value": 21},
        {"date": "2026-01-03", "ticker": "MSFT", "value": 22},
    ])


def test_reshape_index_order(input_df):
    """Assert index order is ascending date."""
    result = pivot_long_to_wide(input_df, value_col="value")

    expected_date_values = ["2026-01-01", "2026-01-02", "2026-01-03"]
    assert list(result.index) == expected_date_values


def test_reshape_columns_order(input_df):
    """Assert columns are alphabetical (single-level Index)."""
    result = pivot_long_to_wide(input_df, value_col="value")

    assert list(result.columns) == ["AAPL", "MSFT"]
    assert isinstance(result.columns, pd.Index)


def test_reshape_cell_values(input_df):
    """Assert specific cell values match expected table."""
    result = pivot_long_to_wide(input_df, value_col="value")

    assert result.loc["2026-01-01", "AAPL"] == 10
    assert result.loc["2026-01-01", "MSFT"] == 20
    assert result.loc["2026-01-02", "AAPL"] == 11
    assert result.loc["2026-01-02", "MSFT"] == 21
    assert result.loc["2026-01-03", "MSFT"] == 22


def test_reshape_missing_value_is_nan(input_df):
    """Assert missing combination (AAPL on 2026-01-03) is NaN."""
    result = pivot_long_to_wide(input_df, value_col="value")

    assert pd.isna(result.loc["2026-01-03", "AAPL"])
