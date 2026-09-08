# NOTE: Removed VBT_DISABLE_PLOT - all tests pass without it (wasn't the fix)

import numpy as np
import pandas as pd
import pytest
from src.backtest.runner import run_backtest


@pytest.fixture(scope="function")
def synthetic_prices_and_weights():
    """Synthetic fixture for smoke testing run_backtest()."""
    dates = pd.date_range(end="2024-10-08", periods=5)
    tickers = ["AAPL", "GOOGL"]

    prices_wide = pd.DataFrame(
        index=dates,
        columns=tickers,
        data={
            "AAPL": [175.0 + 2.0 * i for i in range(len(dates))],
            "GOOGL": [140.0 + 3.0 * i for i in range(len(dates))],
        },
    )

    # NaN in weights means "no order" (hold existing position) - vectorbt default
    weights_wide = pd.DataFrame(
        index=dates,
        columns=tickers,
        data={
            "AAPL": [None, None, 0.02, 0.02, 0.02],
            "GOOGL": [None, None, 0.02, 0.02, 0.02],
        }
    )

    return prices_wide, weights_wide


def _is_numeric(val):
    """Check if val is a numeric type (handles np.int64, np.float64, etc.)."""
    return isinstance(val, (int, float)) or isinstance(val, (np.integer, np.floating))


def test_backtest_runs_without_exception(synthetic_prices_and_weights):
    """Check 1: Calling run_backtest() does not raise an exception."""
    prices_wide, weights_wide = synthetic_prices_and_weights
    pf = run_backtest(prices_wide, weights_wide)


def test_backtest_has_total_return(synthetic_prices_and_weights):
    """Check 2: The returned object has a working .total_return() method
    that returns a finite float (not NaN). Note: vectorbt v1.x doesn't
    accept a 'grouped' parameter - use pf.stats()['Total Return'] instead.
    """
    prices_wide, weights_wide = synthetic_prices_and_weights

    pf = run_backtest(prices_wide, weights_wide)

    # VectorBT v1.x: total_return() returns scalar without 'grouped' param
    total_return = pf.total_return()
    assert _is_numeric(total_return), "total_return should be a numeric type"
    assert not pd.isna(total_return), "total_return should not be NaN"

    # Also verify via stats dict
    stats_dict = pf.stats()
    total_return_from_stats = stats_dict.get("Total Return", None)
    if total_return_from_stats is not None:
        assert _is_numeric(total_return_from_stats)
        assert not pd.isna(total_return_from_stats), "total_return in stats should not be NaN"


def test_backtest_generated_orders(synthetic_prices_and_weights):
    """Check 3: .orders.count() is greater than 0 - confirms orders executed."""
    prices_wide, weights_wide = synthetic_prices_and_weights

    pf = run_backtest(prices_wide, weights_wide)

    # VectorBT v1.x: use pf.orders.count() for order count
    order_count = pf.orders.count()
    assert _is_numeric(order_count), "order_count should be a numeric type"
    assert order_count > 0, "Orders should have been executed"
