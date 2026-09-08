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

def test_hold_until_signal_change_masks_repeated_values():
    """A weight held constant across many days should only produce a
    non-NaN value on the transition day — regression test for the
    empirically-confirmed daily-rebalancing bug."""
    from src.strategies.sma_crossover_sp500top50 import hold_until_signal_change

    df = pd.DataFrame({
        "ticker": ["A"] * 6,
        "date": pd.date_range("2026-01-01", periods=6),
        "target_weight_20": [float("nan"), float("nan"), 0.02, 0.02, 0.02, 0.02],
    })
    result = hold_until_signal_change(df, window=20)

    non_nan = result["rebalance_weight_20"].notna()
    assert non_nan.sum() == 1, "Only the transition day should be non-NaN"
    assert result.loc[non_nan, "date"].iloc[0] == pd.Timestamp("2026-01-03")


def test_hold_until_signal_change_direction_flip():
    """A flip from long to short should re-trigger a non-NaN value on
    the flip day, not just the initial entry."""
    from src.strategies.sma_crossover_sp500top50 import hold_until_signal_change

    df = pd.DataFrame({
        "ticker": ["A"] * 5,
        "date": pd.date_range("2026-01-01", periods=5),
        "target_weight_20": [0.02, 0.02, -0.02, -0.02, -0.02],
    })
    result = hold_until_signal_change(df, window=20)

    non_nan_dates = result.loc[result["rebalance_weight_20"].notna(), "date"].tolist()
    assert non_nan_dates == [pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-03")]


def test_hold_until_signal_change_nan_to_nan_is_not_a_change():
    """Consecutive NaN rows (still in warmup) must not be flagged as a
    change — NaN != NaN is True by default in pandas and must be
    guarded against."""
    from src.strategies.sma_crossover_sp500top50 import hold_until_signal_change

    df = pd.DataFrame({
        "ticker": ["A"] * 4,
        "date": pd.date_range("2026-01-01", periods=4),
        "target_weight_20": [float("nan")] * 4,
    })
    result = hold_until_signal_change(df, window=20)

    assert result["rebalance_weight_20"].notna().sum() == 0


def test_hold_until_signal_change_per_ticker_isolation():
    """Ticker B's first real signal must not be suppressed just because
    ticker A already has a non-NaN value earlier in the sorted frame."""
    from src.strategies.sma_crossover_sp500top50 import hold_until_signal_change

    df = pd.DataFrame({
        "ticker": ["A", "A", "B", "B"],
        "date": pd.to_datetime(["2026-01-01", "2026-01-02"] * 2),
        "target_weight_20": [0.02, 0.02, -0.02, -0.02],
    })
    result = hold_until_signal_change(df, window=20)

    a_rows = result[result["ticker"] == "A"]
    b_rows = result[result["ticker"] == "B"]
    assert a_rows["rebalance_weight_20"].notna().sum() == 1
    assert b_rows["rebalance_weight_20"].notna().sum() == 1
