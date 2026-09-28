"""Daily OOS ledger update for momentum_12_1_sp500top50 (J = 12 months).

Twin of research/sma_crossover_sp500top50/update_oos_ledger.py, run by the
scheduled GitHub Action (.github/workflows/daily_oos_update_momentum.yml).
Running it by hand is harmless — it no-ops if there is no new trading day.

SCOPE NOTE: this extends a forward OUT-OF-SAMPLE BACKTEST from 2026-08-01
one real trading day at a time, on real closing prices. It is NOT live paper
trading against a broker (no Alpaca integration yet). J = 12 is the
hypothesis's pre-registered primary setting; the gate decisions stay manual
in the Project chat.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import csv
import os
from datetime import date

import pandas as pd

from src.data.price_history import fetch_price_history
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest
from src.features.momentum import compute_momentum
from src.strategies.momentum_12_1_sp500top50 import monthly_target_weights

FORMATION_MONTHS = 12
SKIP_DAYS = 21
DAYS_PER_MONTH = 21
N_LONG = 5
N_SHORT = 5
WEIGHT_PER_POSITION = 0.10
LOOKBACK_START = "2025-06-01"   # > 12 months of history before the first OOS rebalance
OOS_START_DATE = "2026-08-01"

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "research/momentum_12_1_sp500top50/oos_ledger.csv"

universe = pd.read_csv(REPO_ROOT / "research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

# Same cache caveat as the SMA script: end=None always maps to the same
# "latest" cache file, so it must be deleted or today's close is hidden.
cache_file = REPO_ROOT / f"src/data/.cache/price_history_{LOOKBACK_START}_latest.parquet"
if cache_file.exists():
    os.remove(cache_file)

df = fetch_price_history(tickers, start_date=LOOKBACK_START, end_date=None)
prices = pivot_long_to_wide(df, value_col="adj_close")
momentum = compute_momentum(prices, formation_days=FORMATION_MONTHS * DAYS_PER_MONTH, skip_days=SKIP_DAYS)
weights = monthly_target_weights(momentum, N_LONG, N_SHORT, WEIGHT_PER_POSITION)

oos = prices.index >= pd.Timestamp(OOS_START_DATE).date()
prices_oos = prices.loc[oos]
weights_oos = weights.loc[oos]
latest_date = prices_oos.index.max()

if LEDGER_PATH.exists():
    existing = pd.read_csv(LEDGER_PATH)
    if not existing.empty and str(latest_date) in existing["as_of_date"].astype(str).values:
        print(f"No new trading day since last run (latest available: {latest_date}). Skipping.")
        sys.exit(0)

pf = run_backtest(prices_oos, weights_oos)
stats = pf.stats()
n_orders = int(pf.orders.count())
trade_status = pf.trades.records_readable["Status"].value_counts() if n_orders > 0 else pd.Series(dtype=int)

row = {
    "run_date": date.today().isoformat(),
    "as_of_date": str(latest_date),
    "n_oos_trading_days": int(prices_oos.shape[0]),
    "total_return_pct": float(stats["Total Return [%]"]),
    "sharpe_ratio": float(stats["Sharpe Ratio"]),
    "sortino_ratio": float(stats["Sortino Ratio"]),
    "max_drawdown_pct": float(stats["Max Drawdown [%]"]),
    "win_rate_pct": float(stats["Win Rate [%]"]),
    "total_orders": n_orders,
    "closed_trades": int(trade_status.get("Closed", 0)),
    "open_trades": int(trade_status.get("Open", 0)),
    "n_rebalances": int(weights_oos.notna().any(axis=1).sum()),
}

file_exists = LEDGER_PATH.exists()
with open(LEDGER_PATH, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(row.keys()))
    if not file_exists:
        writer.writeheader()
    writer.writerow(row)

print("Appended ledger row:")
print(row)
