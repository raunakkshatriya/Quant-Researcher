import pandas as pd


def compute_momentum(prices_wide: pd.DataFrame, formation_days: int, skip_days: int = 21) -> pd.DataFrame:
    """Cross-sectional momentum: each stock's return from `formation_days`
    trading days ago to `skip_days` trading days ago.

    12-1 momentum (Jegadeesh & Titman 1993) = formation_days=252 (~12
    months), skip_days=21 (~1 month): the most recent month is skipped
    because over one month prices tend to reverse rather than trend.

    Pure function: no network, no wall-clock reads. The value on date t uses
    only prices on or before t (t - skip_days and t - formation_days), so
    there is no lookahead.

    Input:
        prices_wide: DataFrame, index = trading dates (sorted ascending, no
            duplicates), one column per ticker, values = prices (use
            adj_close, so dividends and splits don't distort returns).
        formation_days: int > skip_days.
        skip_days: int >= 0.

    Output: DataFrame with the same index and columns; value =
        price[t - skip_days] / price[t - formation_days] - 1. NaN where
        either price is missing or there is not enough history.

    Raises ValueError for bad day counts, an unsorted or duplicated index,
    or a zero/negative price.
    """
    if not isinstance(formation_days, int) or not isinstance(skip_days, int):
        raise ValueError("formation_days and skip_days must be integers")
    if skip_days < 0 or formation_days <= skip_days:
        raise ValueError("need formation_days > skip_days >= 0")
    if not prices_wide.index.is_monotonic_increasing:
        raise ValueError("prices_wide index must be sorted ascending")
    if prices_wide.index.duplicated().any():
        raise ValueError("prices_wide index has duplicate dates")
    if (prices_wide <= 0).any().any():
        raise ValueError("prices_wide has a zero or negative price")
    recent = prices_wide.shift(skip_days)
    past = prices_wide.shift(formation_days)
    return recent / past - 1.0
