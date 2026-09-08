"""SMAs crossover strategy for S&P 500 top 50 tickers."""
import pandas as pd


def compute_signal(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Turn a price-vs-SMA comparison into a long/short/flat signal.

    Assumes compute_sma() has already been called and sma_{window} column exists.

    Args:
        df: Long-format DataFrame with columns date, ticker, close, and sma_{window}.
        window: Number of days for the SMA (used to name the output column).

    Returns:
        DataFrame with same shape as input, plus new column signal_{window}
        with values: 1.0 (long), -1.0 (short), 0.0 (tie), or NaN (insufficient history).
    """
    # Get the SMA column name
    sma_col = "sma_{}".format(window)

    # Start with NaN signals for rows where SMA is NaN (insufficient history).
    # Use float('nan'), not pd.NA — pd.NA is pandas' nullable-dtype marker and
    # is not interchangeable with a plain float NaN: float(pd.NA) raises
    # TypeError, which broke compute_target_weights()'s .astype(float) call
    # downstream even though both values satisfy pd.isna() equally.
    df = df.copy()
    df["signal_{}" .format(window)] = float("nan")

    # For rows where both close and SMA have values, assign based on comparison
    mask_valid = pd.notna(df[sma_col]) & pd.notna(df["close"])

    # 1.0 if close > SMA (long)
    df.loc[mask_valid & (df.loc[mask_valid, "close"] > df.loc[mask_valid, sma_col]),
          "signal_{}" .format(window)] = 1.0

    # -1.0 if close < SMA (short)
    df.loc[mask_valid & (df.loc[mask_valid, "close"] < df.loc[mask_valid, sma_col]),
          "signal_{}" .format(window)] = -1.0

    # 0.0 if close == SMA (exact tie)
    df.loc[mask_valid & (df.loc[mask_valid, "close"] == df.loc[mask_valid, sma_col]),
          "signal_{}" .format(window)] = 0.0

    return df


def compute_target_weights(df: pd.DataFrame, window: int, weight_per_position: float = 0.02) -> pd.DataFrame:
    """Convert a per-row signal into a fixed target portfolio weight.

    This function takes a signal (1.0/ -1.0 / 0.0 / NaN) and converts it
    to a fixed target weight, where the magnitude is determined by weight_per_position.

    IMPORTANT: This is a FIXED weight per active name. Do NOT renormalize based
    on how many tickers are currently active. A fixed 2% per signal is tied to
    the portfolio's leverage ceiling (max_portfolio_leverage: 1.0 in risk_and_costs.yaml).

    Args:
        df: Long-format DataFrame with columns date, ticker, signal_{window}
        window: Number of days for the SMA (used to name the output column)
        weight_per_position: Weight to allocate per active position (default 0.02 = +2%)

    Returns:
        DataFrame with same shape as input, plus new column target_weight_{window}
    """
    # Get the signal column name
    signal_col = "signal_{}".format(window)

    # Ensure we have a float64 series for proper arithmetic
    df = df.copy()
    df[signal_col] = df[signal_col].astype(float)

    # Compute target weight as: signal * weight_per_position
    # This automatically handles:
    # - 1.0 → +weight_per_position (e.g., +2%)
    # - -1.0 → -weight_per_position (e.g., -2%)
    # - 0.0 → 0.0
    # - NaN → NaN (propagates, not converted to 0.0)
    target_weight_col = "target_weight_{}".format(window)
    df[target_weight_col] = df[signal_col] * weight_per_position

    return df


def hold_until_signal_change(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Mask target_weight_{window} down to only the days the signal
    actually changes, per ticker — every other day becomes NaN.

    This matters because of how the backtest engine interprets weights:
    with size_type='targetpercent', a non-NaN weight causes a rebalancing
    order EVERY day it appears, even if the value is identical to the
    previous day's — it does not mean "trade only when this changes."
    A constant +2% weight held for 27 straight days was empirically
    confirmed to generate 27 separate rebalancing orders, not 1, which
    silently violated the strategy's design intent ("rebalanced on
    signal flips only," per hypothesis.md) and inflated both trade
    count and transaction-cost drag in every backtest run before this
    function existed.

    Args:
        df: Long-format DataFrame with columns date, ticker,
            target_weight_{window} (output of compute_target_weights()).
        window: Number of days for the SMA (used to name columns).

    Returns:
        DataFrame with same shape as input, plus new column
        rebalance_weight_{window}: the target weight on days the signal
        changed from the previous day for that ticker, NaN elsewhere.
        Pass THIS column (not target_weight_{window}) into
        pivot_long_to_wide() before run_backtest().
    """
    weight_col = "target_weight_{}".format(window)
    out_col = "rebalance_weight_{}".format(window)

    df = df.copy()
    df = df.sort_values(by=["ticker", "date"])

    prev = df.groupby("ticker")[weight_col].shift(1)
    # NaN != NaN is True by default in pandas comparisons, which would
    # wrongly flag every still-in-warmup NaN row as a "change." Guard
    # against that explicitly rather than relying on != alone.
    both_nan = df[weight_col].isna() & prev.isna()
    changed = (df[weight_col] != prev) & ~both_nan

    df[out_col] = df[weight_col].where(changed)

    return df
