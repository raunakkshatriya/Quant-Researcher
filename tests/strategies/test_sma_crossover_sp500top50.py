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


# %% [markdown]
# ## Target Weight Tests for compute_target_weights()

# %%

def test_compute_target_weights_long_signal():
    """Test: signal = 1.0 → target_weight = weight_per_position."""
    from src.strategies.sma_crossover_sp500top50 import compute_target_weights

    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "signal_20": [1.0],  # Long signal
    })

    result = compute_target_weights(df, window=20, weight_per_position=0.02)

    assert pd.notna(result["target_weight_20"].iloc[0])
    assert result["target_weight_20"].iloc[0] == 0.02


def test_compute_target_weights_short_signal():
    """Test: signal = -1.0 → target_weight = -weight_per_position."""
    from src.strategies.sma_crossover_sp500top50 import compute_target_weights

    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "signal_20": [-1.0],  # Short signal
    })

    result = compute_target_weights(df, window=20, weight_per_position=0.02)

    assert pd.notna(result["target_weight_20"].iloc[0])
    assert result["target_weight_20"].iloc[0] == -0.02


def test_compute_target_weights_zero_signal():
    """Test: signal = 0.0 → target_weight = 0.0."""
    from src.strategies.sma_crossover_sp500top50 import compute_target_weights

    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "signal_20": [0.0],  # Flat signal (tie)
    })

    result = compute_target_weights(df, window=20, weight_per_position=0.02)

    assert pd.notna(result["target_weight_20"].iloc[0])
    assert result["target_weight_20"].iloc[0] == 0.0


def test_compute_target_weights_nan_signal():
    """Test: signal = NaN → target_weight = NaN (not 0.0)."""
    from src.strategies.sma_crossover_sp500top50 import compute_target_weights

    df = pd.DataFrame({
        "date": ["2024-01-01"],
        "ticker": ["AAPL"],
        "signal_20": [float("nan")],  # No signal yet (NaN)
    })

    result = compute_target_weights(df, window=20, weight_per_position=0.02)

    assert pd.isna(result["target_weight_20"].iloc[0])


# %% [markdown]
# ## Integration Test: Full signal → target weight pipeline

# %%

def test_full_pipeline():
    """Test end-to-end: compute_signal() → compute_target_weights()."""
    from src.strategies.sma_crossover_sp500top50 import compute_signal, compute_target_weights

    # Create sample data with all three signal states and NaN
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "ticker": ["AAPL", "MSFT", "GOOGL"],
        "close": [150.0, 130.0, 140.0],
        "sma_20": [140.0, 140.0, 140.0],
    })

    # First compute signal
    df_with_signal = compute_signal(df, window=20)

    assert df_with_signal["signal_20"].iloc[0] == 1.0  # close > SMA
    assert df_with_signal["signal_20"].iloc[1] == -1.0  # close < SMA
    assert df_with_signal["signal_20"].iloc[2] == 0.0  # close == SMA

    # Then compute target weights
    df_with_weights = compute_target_weights(df_with_signal, window=20, weight_per_position=0.02)

    assert df_with_weights["target_weight_20"].iloc[0] == 0.02
    assert df_with_weights["target_weight_20"].iloc[1] == -0.02
    assert df_with_weights["target_weight_20"].iloc[2] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])