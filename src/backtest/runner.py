import pandas as pd
import vectorbt as vbt


def run_backtest(
    prices_wide: pd.DataFrame,
    weights_wide: pd.DataFrame,
    slippage: float = 0.0005,
    fees: float = 0.0,
    init_cash: float = 100000.0,
) -> vbt.Portfolio:
    """Build a vectorbt Portfolio from a wide (date x ticker) price
    matrix and a wide (date x ticker) target-weight matrix. Assumes a
    single shared-cash portfolio across all tickers (cash_sharing).
    NaN in weights_wide means "no order" (hold existing position),
    which is vectorbt's default behavior for from_orders — this is
    intentional, matching how target weights were designed upstream.
    """
    pf = vbt.Portfolio.from_orders(
        close=prices_wide,
        size=weights_wide,
        size_type="targetpercent",
        group_by=True,
        cash_sharing=True,
        call_seq="auto",  # sell before buy, avoids rejected orders
        fees=fees,
        slippage=slippage,
        init_cash=init_cash,
        freq="1D",
    )
    return pf
