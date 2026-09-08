"""Moving average feature functions."""
import pandas as pd


def compute_sma(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Compute T-day simple moving average per ticker.

    Adds an `sma_{window}` column to a long-format price DataFrame,
    computed independently for each ticker.

    Args:
        df: Long-format DataFrame with columns date, ticker, close (and optionally open/high/low/volume).
        window: Number of days for the SMA calculation.

    Returns:
        DataFrame with same shape as input, plus one new column named `sma_{window}`.
    """
    # Sort by ticker, then date to ensure correct rolling computation per ticker
    df = df.sort_values(by=["ticker", "date"]).copy()

    # Compute rolling mean of close per ticker
    # Without min_periods, pandas uses 1 by default - rows without enough
    # history for the full window will be NaN (not a partial average)
    df["sma_{}" .format(window)] = (
        df.groupby("ticker")["close"]
        .transform(lambda x: x.rolling(window=window).mean())
    )

    return df
