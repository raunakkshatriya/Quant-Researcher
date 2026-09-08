# Handoff — sma_crossover_sp500top50 — Task 7: Backtest runner (portfolio construction only)

## Important — before you start
`import vectorbt` compiles Numba functions on first import and can
take 30-60+ seconds (sometimes longer) the first time it runs in this
environment. This is normal, not a hang. Do not interrupt it or
"debug" a slow-but-completing import.

This session builds the portfolio and confirms it runs. It does NOT
extract formal performance stats (Sharpe, max drawdown) for the
hypothesis log, and it does NOT include borrow costs for the short
leg — both are separate follow-up sessions.

## Objective
Implement ONE function, `run_backtest(prices_wide: pd.DataFrame,
weights_wide: pd.DataFrame, slippage: float = 0.0005, fees: float =
0.0, init_cash: float = 100000.0)`, that builds a vectorbt Portfolio
from a wide price matrix and a wide target-weight matrix.

## Allowed files
- src/backtest/runner.py (new file)
- tests/backtest/test_runner.py (new file)
(Nothing outside this list.)

## Dependency
Add `vectorbt` to the project's requirements file (`pip install -U
vectorbt` locally to confirm it installs before writing code against
it).

## This session's task

### 1. Create `src/backtest/runner.py` with this content:

```python
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
```

Do not modify this function beyond what's written. Do not add
borrow-cost logic, do not add integer-share constraints, do not add
extra parameters.

### 2. Create `tests/backtest/test_runner.py`

Use a small SYNTHETIC fixture (no real data, no network calls, no
calling fetch_price_history or the pivot function from earlier
tasks) — hand-construct two small wide DataFrames directly, e.g. 2
tickers, 10 rows of made-up prices trending upward, and a weights
DataFrame that goes long both tickers at 0.02 partway through.

This is a SMOKE TEST, not a correctness test of vectorbt's internal
math — do not try to hand-verify exact portfolio values, that's
vectorbt's own tested responsibility, not ours. Write exactly these
3 checks:
1. Calling `run_backtest()` on the fixture does not raise an
   exception.
2. The returned object has a working `.total_return()` method that
   returns a finite float (not NaN, not an error) when called on the
   grouped portfolio.
3. `.orders.count()` (or equivalent order-count accessor) is greater
   than 0 — confirms the target-weight orders actually executed
   rather than silently doing nothing.

If you're unsure of the exact vectorbt accessor name for check 2 or
3, print `dir(pf)` or `pf.stats()` once to find the right one rather
than guessing repeatedly — one exploratory print is fine, don't loop
trying random attribute names.

### 3. Run the tests, confirm all 3 pass.

## Done so far
`pivot_long_to_wide()`, `compute_target_weights()`,
`compute_signal()`, `compute_sma()`, `fetch_price_history()`, and
`build_sp500_top50_snapshot()` are all complete and committed. This
session's test fixture does NOT need to call any of them — it uses
its own small synthetic data as described above.

## Resume point
If you run out of budget: note here exactly which of the 3 checks is
failing and the exact error message, then stop. If the import itself
seems to hang for more than ~2 minutes, note that specifically rather
than continuing to wait indefinitely.
