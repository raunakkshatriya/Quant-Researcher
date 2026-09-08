# Helper script to run backtest exploration with correct imports
import os
import sys

# Add src to path explicitly (avoiding shell quoting issues)
sys.path.insert(0, 'C:/Users/rauna/Desktop/Quant research signals/Quant-Researcher')

# %% [markdown]
# ## Phase 1 In-Sample Backtest: Window = 20

# %%
import json
import pandas as pd

from src.data.price_history import fetch_price_history
from src.features.moving_average import compute_sma
from src.strategies.sma_crossover_sp500top50 import compute_signal, compute_target_weights
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest

# Phase 1 parameters — train/test split boundary
WINDOW = 20
START_DATE = "2022-01-01"
END_DATE = "2026-07-31"

# Load universe (top 50 by market cap at reference time)
universe = pd.read_csv("research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

print(f"Loading price history for {len(tickers)} tickers...")
df = fetch_price_history(tickers, start_date=START_DATE, end_date=END_DATE)
print(f"Fetched {len(df)} rows of price data.")

# Compute features
print("Computing SMA window =", WINDOW)
df = compute_sma(df, window=WINDOW)
print("Computing signal")
df = compute_signal(df, window=WINDOW)
print("Computing target weights")
df = compute_target_weights(df, window=WINDOW)

# Pivot to wide format (date x ticker matrix)
print("Reshaping to wide format...")
prices_wide = pivot_long_to_wide(df, value_col="close")
weights_wide = pivot_long_to_wide(df, value_col=f"target_weight_{WINDOW}")

print(f"Prices shape: {prices_wide.shape}")
print(f"Weights shape: {weights_wide.shape}")
print(f"Number of tickers with data: {len(prices_wide.columns)}")

# Run backtest
print("Running vectorbt backtest...")
pf = run_backtest(prices_wide, weights_wide)
stats = pf.stats()

# Print stats to screen (use as reference for KeyError handling if needed)
print("\n=== Portfolio Stats ===")
for key in stats.index.tolist():
    print(f"  {key}: {stats.loc[key]}")

# Extract results with fallbacks for different vectorbt key naming
results = {
    "window": WINDOW,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "n_tickers_requested": len(tickers),
    "n_tickers_with_data": prices_wide.shape[1],
}

# Try to get each stat — print KeyError if key name differs from expectation
total_return = stats.get("Total Return [%]") or stats.get("Total Return") or None
results["total_return"] = float(total_return) if total_return is not None else None

sharpe_ratio = stats.get("Sharpe Ratio") or None
results["sharpe_ratio"] = float(sharpe_ratio) if sharpe_ratio is not None else None

max_drawdown = stats.get("Max Drawdown [%]") or stats.get("Max Drawdown") or None
results["max_drawdown"] = float(max_drawdown) if max_drawdown is not None else None

total_orders = pf.orders.count()
results["total_orders"] = int(total_orders)

# Write results to JSON file
output_path = "research/sma_crossover_sp500top50/is_results_window20.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n=== Results Written to {output_path} ===")
print(json.dumps(results, indent=2))

# Summary
print("\n=== Execution Summary ===")
print(f"Window: {WINDOW}")
print(f"Date range: {START_DATE} to {END_DATE}")
print(f"Tickers requested: {results['n_tickers_requested']}")
print(f"Tickers with data: {results['n_tickers_with_data']}")
print(f"Total orders: {results['total_orders']}")
if results["total_return"] is not None:
    print(f"Total return: {results['total_return']:.2f}%")
else:
    print("Total return: NOT AVAILABLE (check stats key names above)")
if results["sharpe_ratio"] is not None:
    print(f"Sharpe ratio: {results['sharpe_ratio']:.4f}")
else:
    print("Sharpe ratio: NOT AVAILABLE (check stats key names above)")
if results["max_drawdown"] is not None:
    print(f"Max drawdown: {results['max_drawdown']:.2f}%")
else:
    print("Max drawdown: NOT AVAILABLE (check stats key names above)")
