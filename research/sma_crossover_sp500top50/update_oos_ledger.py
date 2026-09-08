"""Daily OOS ledger update for sma_crossover_sp500top50, window=200.

Meant to be run by the scheduled GitHub Action
(.github/workflows/daily_oos_update.yml), though running it by hand is
harmless -- it just no-ops if there's no new trading day since the
last recorded row.

IMPORTANT SCOPE NOTE: this extends the Phase 2 OUT-OF-SAMPLE BACKTEST
window by one real trading day at a time, using real historical
closing prices as they become available. It is NOT live paper trading
against a broker -- no Alpaca integration exists yet. That is Phase 3,
separate, later work. This script only re-scores the existing,
already-verified backtest pipeline so enough closed trades eventually
accumulate for a real Gate 2 read (see hypothesis_log.csv and
lessons_learned.md for why a longer window is needed and why no
historical shortcut exists for this hypothesis).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import csv
import os
from datetime import date

import pandas as pd

from src.data.price_history import fetch_price_history
from src.features.moving_average import compute_sma
from src.strategies.sma_crossover_sp500top50 import compute_signal, compute_target_weights, hold_until_signal_change
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest

WINDOW = 200
LOOKBACK_START = "2022-01-01"
OOS_START_DATE = "2026-08-01"

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "research/sma_crossover_sp500top50/oos_ledger.csv"

universe = pd.read_csv(REPO_ROOT / "research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

# fetch_price_history() caches by (start_date, end_date) and end=None
# always maps to the same "latest" cache key -- if left alone, a cache
# saved yesterday would silently hide today's new closing price. This
# is the one place that cache needs to be forced stale on every run.
cache_file = REPO_ROOT / "src/data/.cache/price_history_2022-01-01_latest.parquet"
if cache_file.exists():
    os.remove(cache_file)

df = fetch_price_history(tickers, start_date=LOOKBACK_START, end_date=None)
df = compute_sma(df, window=WINDOW)
df = compute_signal(df, window=WINDOW)
df = compute_target_weights(df, window=WINDOW)

oos_cutoff = pd.to_datetime(OOS_START_DATE).date()
oos_df = df[df["date"] >= oos_cutoff].copy()
oos_df = hold_until_signal_change(oos_df, window=WINDOW)

latest_date = oos_df["date"].max()

# Skip cleanly on weekends/holidays (no new trading day) or a re-run on
# the same day -- don't write a duplicate row.
if LEDGER_PATH.exists():
    existing = pd.read_csv(LEDGER_PATH)
    if not existing.empty and str(latest_date) in existing["as_of_date"].astype(str).values:
        print(f"No new trading day since last run (latest available: {latest_date}). Skipping.")
        sys.exit(0)

prices_wide = pivot_long_to_wide(oos_df, value_col="close")
weights_wide = pivot_long_to_wide(oos_df, value_col=f"rebalance_weight_{WINDOW}")

pf = run_backtest(prices_wide, weights_wide)
stats = pf.stats()
trade_status = pf.trades.records_readable["Status"].value_counts()

row = {
    "run_date": date.today().isoformat(),
    "as_of_date": str(latest_date),
    "n_oos_trading_days": int(prices_wide.shape[0]),
    "total_return_pct": float(stats["Total Return [%]"]),
    "sharpe_ratio": float(stats["Sharpe Ratio"]),
    "sortino_ratio": float(stats["Sortino Ratio"]),
    "max_drawdown_pct": float(stats["Max Drawdown [%]"]),
    "win_rate_pct": float(stats["Win Rate [%]"]),
    "total_orders": int(pf.orders.count()),
    "closed_trades": int(trade_status.get("Closed", 0)),
    "open_trades": int(trade_status.get("Open", 0)),
}

file_exists = LEDGER_PATH.exists()
with open(LEDGER_PATH, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(row.keys()))
    if not file_exists:
        writer.writeheader()
    writer.writerow(row)

print("Appended ledger row:")
print(row)
