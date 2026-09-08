"""Phase 1 in-sample backtest for sma_crossover_sp500top50, window=20.

Run this locally (not in a sandboxed environment) — it needs live
network access to Yahoo Finance via yfinance, which is not available
in every environment. Requires: pip install -r requirements.txt
"""
import sys
from pathlib import Path

# Make the repo's src/ package importable regardless of the current
# working directory or how this script is invoked. Running a script
# directly (`python path/to/script.py`) only adds the script's own
# folder to sys.path, not the repo root — this line fixes that.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json

import pandas as pd

from src.data.price_history import fetch_price_history
from src.features.moving_average import compute_sma
from src.strategies.sma_crossover_sp500top50 import compute_signal, compute_target_weights, hold_until_signal_change
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest

WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 20
START_DATE = "2022-01-01"
END_DATE = "2026-07-31"  # train/test split cutoff — never pass a later date here

REPO_ROOT = Path(__file__).resolve().parents[2]
universe = pd.read_csv(REPO_ROOT / "research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

print(f"Fetching price history for {len(tickers)} tickers, {START_DATE} to {END_DATE}...")
print("(First run will hit the network and may take a few minutes; cached after that.)")
df = fetch_price_history(tickers, start_date=START_DATE, end_date=END_DATE)
print(f"Got {df['ticker'].nunique()} of {len(tickers)} requested tickers, {len(df)} rows.")

df = compute_sma(df, window=WINDOW)
df = compute_signal(df, window=WINDOW)
df = compute_target_weights(df, window=WINDOW)
df = hold_until_signal_change(df, window=WINDOW)

prices_wide = pivot_long_to_wide(df, value_col="close")
weights_wide = pivot_long_to_wide(df, value_col=f"rebalance_weight_{WINDOW}")

pf = run_backtest(prices_wide, weights_wide)
stats = pf.stats()

results = {
    "window": WINDOW,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "n_tickers_requested": len(tickers),
    "n_tickers_with_data": int(prices_wide.shape[1]),
    "total_return_pct": float(stats["Total Return [%]"]),
    "benchmark_return_pct": float(stats["Benchmark Return [%]"]),
    "sharpe_ratio": float(stats["Sharpe Ratio"]),
    "sortino_ratio": float(stats["Sortino Ratio"]),
    "max_drawdown_pct": float(stats["Max Drawdown [%]"]),
    "win_rate_pct": float(stats["Win Rate [%]"]),
    "total_trades": int(stats["Total Trades"]),
    "total_orders": int(pf.orders.count()),
}

out_path = REPO_ROOT / f"research/sma_crossover_sp500top50/is_results_window{WINDOW}.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print("\n--- RESULTS ---")
print(json.dumps(results, indent=2))
