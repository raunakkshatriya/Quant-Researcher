# Handoff — sma_crossover_sp500top50 — Task 7b: Clean up test_runner.py

## Important
This is a cleanup task on an existing file, not new functionality.
Do NOT touch `src/backtest/runner.py` — only
`tests/backtest/test_runner.py`.

## Allowed files
- tests/backtest/test_runner.py (edit existing file)

## Background
The current file has three problems from the previous session:
1. The block `import os` / `os.environ["VBT_DISABLE_PLOT"] = "True"`
   appears twice, verbatim, back to back.
2. `VBT_DISABLE_PLOT` is not a documented vectorbt setting (searched
   official docs/README/PyPI, found nothing) — its actual effect is
   unconfirmed.
3. The price fixture was supposed to have ~10 rows of trending
   prices, but a bug (`base_apple = 175.0 + 2.0 * (len(dates) - 1)`
   computes one scalar, then assigns that same scalar to the whole
   column) makes every row identical instead of trending.

## This session's task

### 1. Fix the duplicate import
Remove one of the two identical `import os` /
`os.environ["VBT_DISABLE_PLOT"] = "True"` blocks so it appears once.

### 2. Test whether VBT_DISABLE_PLOT actually matters
Temporarily remove the `os.environ["VBT_DISABLE_PLOT"] = "True"` line
entirely and re-run the full test file.
- If all tests still pass without it: leave it removed. It wasn't
  the fix. Note this in your summary back to the chat.
- If removing it causes an import error or test failure: put the
  line back, but change the comment to something honest, e.g.
  `# Empirically required to avoid an import error on this
  vectorbt/plotly combination — exact mechanism not confirmed,
  VBT_DISABLE_PLOT is not a documented vectorbt setting.` Do not
  leave the original confident-sounding comment claiming it's a known
  compatibility fix, since that isn't verified.

### 3. Fix the price fixture to actually trend
Replace the fixture so prices genuinely increase row-over-row across
10 dates, e.g.:

```python
@pytest.fixture(scope="function")
def synthetic_prices_and_weights():
    """Synthetic fixture for smoke testing run_backtest()."""
    dates = pd.date_range(end="2024-10-08", periods=10)
    tickers = ["AAPL", "GOOGL"]
    prices_wide = pd.DataFrame(
        index=dates,
        columns=tickers,
        data={
            "AAPL": [175.0 + 2.0 * i for i in range(len(dates))],
            "GOOGL": [140.0 + 3.0 * i for i in range(len(dates))],
        },
    )
    weights_wide = pd.DataFrame(
        index=dates,
        columns=tickers,
        data={
            "AAPL": [None, None, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
            "GOOGL": [None, None, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02],
        },
    )
    return prices_wide, weights_wide
```

### 4. Run the full test file, confirm all 3 tests still pass.
5. Commit with a message describing this as a cleanup of the previous
   session's test file, not new functionality.

## Resume point
If removing VBT_DISABLE_PLOT causes something confusing (not a clean
pass/fail but a different, unrelated-looking error), stop and write
the exact error here rather than guessing at further fixes — bring it
back to the chat instead of iterating.
