# Handoff — sma_crossover_sp500top50 — Task 6a: Reshape function (implementation only)

## Important
This session writes ONLY the function below. Do NOT write any tests in
this session — that's a separate task that comes next. Do NOT modify,
extend, or "improve" the function below in any way (no reset_index(),
no extra sorting logic, no extra parameters). Copy it exactly as
given.

## Allowed files
- src/backtest/reshape.py (new file)
(Nothing else. No test file in this session.)

## This session's task
Create `src/backtest/reshape.py` with exactly this content:

```python
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
```

After creating the file:
1. Run `python -c "import src.backtest.reshape"` (or the equivalent
   import path for this repo) to confirm it imports without error.
2. Do not run pytest, do not write any test file, do not add anything
   beyond the function above.
3. Commit with a message noting this is implementation-only, tests
   follow in the next session.

## Done so far
`compute_target_weights()`, `compute_signal()`, `compute_sma()`,
`fetch_price_history()`, and `build_sp500_top50_snapshot()` are all
complete and committed. A previous attempt at this reshape function
was discarded after it got stuck reconciling a `reset_index()` call
that was never part of the spec — that's why this session is
implementation-only with the exact code given verbatim.

## Resume point
This task is small enough that it should not run out of budget. If it
somehow does, note here whether the file was created and whether the
import check passed.
