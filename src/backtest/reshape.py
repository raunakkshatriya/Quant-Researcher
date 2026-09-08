import pandas as pd


def pivot_long_to_wide(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Reshape a long-format (date, ticker, value_col) DataFrame into
    a wide date x ticker matrix. Missing (date, ticker) pairs become
    NaN. Index is 'date', sorted ascending. Columns are tickers,
    sorted alphabetically.
    """
    wide = df.pivot(index="date", columns="ticker", values=value_col)
    wide = wide.sort_index()
    wide = wide.sort_index(axis=1)
    return wide
