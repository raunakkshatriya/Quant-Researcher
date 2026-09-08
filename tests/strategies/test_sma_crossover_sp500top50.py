"""Tests for compute_signal() function."""
import pytest
import pandas as pd
from src.strategies.sma_crossover_sp500top50 import compute_signal


def test_long_signal():
    """Test: close > SMA produces signal = 1.0."""
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "close": [150.0],
        "sma_20": [140.0],  # SMA < close
    })

    result = compute_signal(df, window=20)

    assert pd.notna(result["signal_20"].iloc[0])
    assert result["signal_20"].iloc[0] == 1.0


def test_short_signal():
    """Test: close < SMA produces signal = -1.0."""
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "close": [130.0],
        "sma_20": [140.0],  # SMA > close
    })

    result = compute_signal(df, window=20)

    assert pd.notna(result["signal_20"].iloc[0])
    assert result["signal_20"].iloc[0] == -1.0


def test_tie_signal():
    """Test: close == SMA produces signal = 0.0."""
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "close": [140.0],
        "sma_20": [140.0],  # Exact match
    })

    result = compute_signal(df, window=20)

    assert pd.notna(result["signal_20"].iloc[0])
    assert result["signal_20"].iloc[0] == 0.0


def test_nan_sma_signal():
    """Test: NaN SMA produces signal = NaN (not 0.0)."""
    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "close": [140.0],
        "sma_20": [float("nan")],  # Insufficient history
    })

    result = compute_signal(df, window=20)

    assert pd.isna(result["signal_20"].iloc[0])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
