"""Price history loader — fetches OHLCV data in long format."""


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
    import os
    from datetime import datetime

    import pandas as pd
    import yfinance as yf

    # Determine cache key based on date range
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

    # Try to load from cache first
    if os.path.exists(cache_file):
        return pd.read_parquet(cache_file)

    # Fetch data from yfinance in a single batched call
    try:
        data = yf.download(
            tickers,
            start=start_date,
            end=end_date if end_date else None,
            group_by="ticker",
            auto_adjust=False,
        )
    except Exception as e:
        # If yfinance fails completely, raise a clear error
        raise RuntimeError(f"Failed to fetch price history from yfinance: {e}")

    # Handle single ticker or multiple tickers (MultiIndex case)
    if isinstance(data.columns, pd.MultiIndex):
        # Multiple tickers — reshape into long format
        data = data.reset_index()  # ticker becomes a column
        df_long = []

        for ticker in data["ticker"].unique():
            ticker_data = data[data["ticker"] == ticker].drop(columns=["ticker"])

            for idx, row in ticker_data.iterrows():
                date_val = pd.to_datetime(row["Date"]).date()

                df_long.append({
                    "date": date_val,
                    "ticker": ticker,
                    "open": float(row["Open"]) if not pd.isna(row["Open"]) else None,
                    "high": float(row["High"]) if not pd.isna(row["High"]) else None,
                    "low": float(row["Low"]) if not pd.isna(row["Low"]) else None,
                    "close": float(row["Close"]) if not pd.isna(row["Close"]) else None,
                    "adj_close": float(row["Adj Close"]) if not pd.isna(row["Adj Close"]) else None,
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                })

        df = pd.DataFrame(df_long)
    else:
        # Single ticker or simple case — reshape directly
        data = data.reset_index(drop=True)

        for idx, row in data.iterrows():
            date_val = pd.to_datetime(row["Date"]).date()

            df_long.append({
                "date": date_val,
                "ticker": str(tickers[idx]),  # ticker is the index
                "open": float(row["Open"]) if not pd.isna(row["Open"]) else None,
                "high": float(row["High"]) if not pd.isna(row["High"]) else None,
                "low": float(row["Low"]) if not pd.isna(row["Low"]) else None,
                "close": float(row["Close"]) if not pd.isna(row["Close"]) else None,
                "adj_close": float(row["Adj Close"]) if not pd.isna(row["Adj Close"]) else None,
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
            })

        df = pd.DataFrame(df_long)

    # Sort by ticker, then date
    df = df.sort_values(by=["ticker", "date"]).reset_index(drop=True)

    # Check if cache directory exists, create if not
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)

    # Save to cache if not empty
    if len(df) > 0:
        df.to_parquet(cache_file, index=False)

    return df
