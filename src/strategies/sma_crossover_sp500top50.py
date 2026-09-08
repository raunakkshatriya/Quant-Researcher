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

    # Start with NaN signals for rows where SMA is NaN (insufficient history)
    df = df.copy()
    df["signal_{}" .format(window)] = pd.NA

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
