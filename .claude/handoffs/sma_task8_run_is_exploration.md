# Handoff — sma_crossover_sp500top50 — Task 8: Run Phase 1 in-sample backtest (window=20)

## Important — before you start
This session wires together functions that already exist and are
verified — it does not write new reusable functions, and it does not
judge whether the results are good. Just run the pipeline, capture
the output, and report back.

Fetching ~4.5 years of daily data for 50 tickers may take a while on
first run (network-bound, not a hang). Subsequent runs should be fast
due to the existing cache in `fetch_price_history()`.

## Allowed files
- research/sma_crossover_sp500top50/run_is_exploration.py (new file)
- research/sma_crossover_sp500top50/is_results_window20.json (new
  file — the script's output)
(Nothing else. Do not modify any file under src/.)

## This session's task

Create `research/sma_crossover_sp500top50/run_is_exploration.py` with
this logic (adapt import paths to match how this repo's modules are
actually importable, e.g. `from src.data.price_history import
fetch_price_history` — check an existing test file if unsure of the
exact import style already used in this repo, don't guess a different
convention):

```python
import json
import pandas as pd

from src.data.price_history import fetch_price_history
from src.features.moving_average import compute_sma
from src.strategies.sma_crossover_sp500top50 import compute_signal, compute_target_weights
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest

WINDOW = 20
START_DATE = "2022-01-01"
END_DATE = "2026-07-31"  # train/test split cutoff — never pass a later date here

universe = pd.read_csv("research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

df = fetch_price_history(tickers, start_date=START_DATE, end_date=END_DATE)
df = compute_sma(df, window=WINDOW)
df = compute_signal(df, window=WINDOW)
df = compute_target_weights(df, window=WINDOW)

prices_wide = pivot_long_to_wide(df, value_col="close")
weights_wide = pivot_long_to_wide(df, value_col=f"target_weight_{WINDOW}")

pf = run_backtest(prices_wide, weights_wide)
stats = pf.stats()

results = {
    "window": WINDOW,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "n_tickers_requested": len(tickers),
    "n_tickers_with_data": prices_wide.shape[1],
    "total_return": float(stats.get("Total Return [%]", stats.get("Total Return"))),
    "sharpe_ratio": float(stats.get("Sharpe Ratio")),
    "max_drawdown": float(stats.get("Max Drawdown [%]", stats.get("Max Drawdown"))),
    "total_orders": int(pf.orders.count()),
}

with open("research/sma_crossover_sp500top50/is_results_window20.json", "w") as f:
    json.dump(results, f, indent=2)

print(json.dumps(results, indent=2))
```

Adjust the exact `stats` dict key names if `pf.stats()` uses slightly
different labels in the installed vectorbt version (1.1.0, per earlier
sessions) — print `stats.index.tolist()` once if a KeyError occurs to
see the real key names, rather than guessing repeatedly.

### Known risk — a ticker with incomplete history
`prices_wide` may have NaN for some tickers on some early dates if a
company didn't have public price history back to 2022 (unlikely for a
top-50-by-market-cap universe, but possible). If `run_backtest()`
raises an error that traces back to a NaN close price rather than a
normal exception, note which ticker and the exact error, then stop —
do not silently drop or patch the ticker yourself. This is a
data-quality judgment call, not an implementation bug.

### Run and report
1. Run the script.
2. Confirm `is_results_window20.json` was created with real (non-null)
   values for all fields.
3. Do not interpret the Sharpe ratio, do not decide if the strategy
   "works," do not proceed to sweep other windows. Just report the
   numbers back.

## Done so far
Every function this script calls — `fetch_price_history()`,
`compute_sma()`, `compute_signal()`, `compute_target_weights()`,
`pivot_long_to_wide()`, `run_backtest()` — is implemented, tested, and
committed. `universe_snapshot.csv` exists with 50 tickers.

## Resume point
If you run out of budget or hit an error you can't resolve in one or
two tries: paste the exact error and how far the script got (e.g.
"data fetch completed, backtest construction failed with: ...") here
and stop.
