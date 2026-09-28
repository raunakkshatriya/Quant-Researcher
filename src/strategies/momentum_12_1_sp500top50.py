import pandas as pd


def month_end_rebalance_dates(index: pd.Index) -> list:
    """Dates in `index` that are the last trading day of their month.

    A date counts only if the NEXT date in the index falls in a different
    month, so the final date in the data is never a rebalance date — its
    month may still have trading days to come. (Which calendar day ends a
    month is known in advance, so using it is not lookahead.)

    Pure function. Input: sorted index of dates (datetime.date or
    Timestamp). Output: list of those dates, ascending.
    """
    dates = list(index)
    out = []
    for current, following in zip(dates[:-1], dates[1:]):
        if (current.year, current.month) != (following.year, following.month):
            out.append(current)
    return out


def monthly_target_weights(momentum_wide: pd.DataFrame, n_long: int, n_short: int,
                           weight_per_position: float = 0.10) -> pd.DataFrame:
    """Turn a momentum table into monthly long/short target weights.

    On each month-end rebalance date (month_end_rebalance_dates), rank the
    tickers that have a momentum value: the n_long highest get
    +weight_per_position, the n_short lowest get -weight_per_position, every
    other ticker gets 0.0 (flat — closes any old position). Ties are broken
    by ticker name so results are reproducible. If fewer than
    n_long + n_short tickers have a value, that date is skipped (all NaN).
    Every non-rebalance date is NaN, which the backtest engine
    (src/backtest/runner.py, size_type='targetpercent') reads as "no order,
    hold" — so positions change only once a month.

    Pure function. Input: momentum_wide (index = sorted dates, columns =
    tickers), from compute_momentum(). Output: DataFrame, same index and
    columns, float.

    Raises ValueError if n_long or n_short < 1 or weight_per_position <= 0.
    """
    if n_long < 1 or n_short < 1:
        raise ValueError("n_long and n_short must be at least 1")
    if weight_per_position <= 0:
        raise ValueError("weight_per_position must be positive")
    weights = pd.DataFrame(float("nan"), index=momentum_wide.index, columns=momentum_wide.columns)
    for date in month_end_rebalance_dates(momentum_wide.index):
        row = momentum_wide.loc[date].dropna()
        if len(row) < n_long + n_short:
            continue
        ranked = sorted(row.items(), key=lambda item: (-item[1], item[0]))
        longs = [ticker for ticker, _ in ranked[:n_long]]
        shorts = [ticker for ticker, _ in ranked[-n_short:]]
        weights.loc[date, :] = 0.0
        weights.loc[date, longs] = weight_per_position
        weights.loc[date, shorts] = -weight_per_position
    return weights
