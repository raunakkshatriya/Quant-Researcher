"""Phase 1 in-sample exploration for momentum_12_1_sp500top50.

Sweeps the formation period J over {3, 6, 9, 12} months (Jegadeesh &
Titman's own grid) on the IN-SAMPLE window only, 2016-01-01 to 2023-12-31.
The 2024-01-01 to 2026-07-31 holdout is NOT touched here — it is reserved
for gate 2, decided before this sweep (lessons_learned 2026-09-08).

Same universe and pipeline as sma_crossover_sp500top50 (universe_snapshot.csv,
fetch_price_history, run_backtest), so the two strategies are compared on the
same stocks. Uses adj_close (dividends included) for both signal and P&L.

Run locally from the repo root (needs Yahoo Finance):
    python research/momentum_12_1_sp500top50/run_is_exploration.py
Then paste the printed results into the Project chat for the gate-1 review.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json

import pandas as pd

from src.data.price_history import fetch_price_history
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest
from src.features.momentum import compute_momentum
from src.strategies.momentum_12_1_sp500top50 import monthly_target_weights

FORMATION_MONTHS = [3, 6, 9, 12]
SKIP_DAYS = 21
DAYS_PER_MONTH = 21
N_LONG = 5
N_SHORT = 5
WEIGHT_PER_POSITION = 0.10
PRICE_START = "2014-12-01"      # 12+1 months of history before the first IS rebalance
PRICE_END = "2024-01-01"        # exclusive: last price used is 2023-12-29
IS_START = pd.Timestamp("2016-01-01").date()
IS_END = pd.Timestamp("2023-12-31").date()

REPO_ROOT = Path(__file__).resolve().parents[2]
FOLDER = REPO_ROOT / "research/momentum_12_1_sp500top50"
universe = pd.read_csv(REPO_ROOT / "research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

df = fetch_price_history(tickers, start_date=PRICE_START, end_date=PRICE_END)
print(f"Got {df['ticker'].nunique()} of {len(tickers)} tickers, {len(df)} rows, "
      f"{df['date'].min()} to {df['date'].max()}")
prices = pivot_long_to_wide(df, value_col="adj_close")
in_sample = (prices.index >= IS_START) & (prices.index <= IS_END)

all_results = {}
for months in FORMATION_MONTHS:
    momentum = compute_momentum(prices, formation_days=months * DAYS_PER_MONTH, skip_days=SKIP_DAYS)
    weights = monthly_target_weights(momentum, N_LONG, N_SHORT, WEIGHT_PER_POSITION)
    pf = run_backtest(prices.loc[in_sample], weights.loc[in_sample])
    stats = pf.stats()
    results = {
        "strategy_id": "momentum_12_1_sp500top50",
        "formation_months": months,
        "skip_days": SKIP_DAYS,
        "n_long": N_LONG,
        "n_short": N_SHORT,
        "in_sample_start": str(IS_START),
        "in_sample_end": str(IS_END),
        "n_tickers_with_data": int(df["ticker"].nunique()),
        "total_return_pct": float(stats["Total Return [%]"]),
        "benchmark_return_pct": float(stats["Benchmark Return [%]"]),
        "sharpe_ratio": float(stats["Sharpe Ratio"]),
        "sortino_ratio": float(stats["Sortino Ratio"]),
        "max_drawdown_pct": float(stats["Max Drawdown [%]"]),
        "win_rate_pct": float(stats["Win Rate [%]"]),
        "total_trades": int(stats["Total Trades"]),
        "total_orders": int(pf.orders.count()),
    }
    with open(FOLDER / f"is_results_J{months}.json", "w") as f:
        json.dump(results, f, indent=2)
    all_results[months] = results

print()
print("J (months)  total_ret%  sharpe  sortino  max_dd%  win%   trades  orders")
for months, r in all_results.items():
    print(f"{months:>10}  {r['total_return_pct']:>10.1f}  {r['sharpe_ratio']:>6.2f}  {r['sortino_ratio']:>7.2f}  "
          f"{r['max_drawdown_pct']:>7.1f}  {r['win_rate_pct']:>5.1f}  {r['total_trades']:>6}  {r['total_orders']:>6}")
