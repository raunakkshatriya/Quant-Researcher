"""Price history loader — fetches OHLCV data in long format."""
import os

import pandas as pd
import yfinance as yf


def fetch_price_history(
    tickers: list[str],
    start_date: str,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Fetch daily OHLCV price history for a list of tickers.

    Args:
        tickers: List of yfinance-compatible symbols (e.g., "AAPL" not "AAPL.B").
        start_date: Start date in "YYYY-MM-DD" format.
        end_date: End date in "YYYY-MM-DD" format, or None for most recent day.

    Returns:
        pandas.DataFrame in long format with columns: date, ticker, open, high,
        low, close, adj_close, volume. Sorted by ticker, then date.
        Only tickers that successfully returned data are included.

    Cache: Result is cached to src/data/.cache/price_history_{start_date}_{end_or_latest}.parquet
            keyed on the date range (not on the specific ticker list).
    """
    if end_date is None:
        end_date = "2030-12-31"  # Future date to ensure we get latest data
        cache_key_suffix = "latest"
    else:
        cache_key_suffix = end_date

    cache_file = os.path.join(
        os.path.dirname(__file__),
        ".cache",
        f"price_history_{start_date}_{cache_key_suffix}.parquet",
    )

    if os.path.exists(cache_file):
        return pd.read_parquet(cache_file)

    try:
        data = yf.download(
            tickers,
            start=start_date,
            end=end_date,
            group_by="ticker",
            auto_adjust=False,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fetch price history from yfinance: {e}")

    if data.empty:
        return pd.DataFrame(
            columns=["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]
        )

    # Normalize to a (ticker, field) MultiIndex on columns even for a single
    # ticker, so there is exactly one reshape path below, not a separate
    # single-vs-multi branch (the previous version's single-ticker branch
    # referenced an undefined variable and would have raised NameError).
    if not isinstance(data.columns, pd.MultiIndex):
        data.columns = pd.MultiIndex.from_product([tickers, data.columns])

    frames = []
    for ticker in data.columns.get_level_values(0).unique():
        ticker_df = data[ticker].copy()
        ticker_df = ticker_df.reset_index()
        ticker_df["ticker"] = ticker
        frames.append(ticker_df)

    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    })
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.dropna(subset=["close"])  # ticker had no trade data on this date
    df = df[["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]]
    df = df.sort_values(by=["ticker", "date"]).reset_index(drop=True)

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    if len(df) > 0:
        df.to_parquet(cache_file, index=False)

    return df
