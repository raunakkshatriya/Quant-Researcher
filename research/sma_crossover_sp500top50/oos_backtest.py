"""Phase 2 out-of-sample test for sma_crossover_sp500top50 -- window=200 only.

IMPORTANT CAVEATS (see hypothesis_log.csv and lessons_learned.md for
the full Gate 1 review):
- The only genuinely unseen data available is the short post-cutoff
  window (2026-08-01 onward, ~5-6 weeks as of writing). This is barely
  above the ~30-day floor already flagged elsewhere in this project as
  producing near-meaningless Sharpe estimates on its own. Treat this
  run's Sharpe/Sortino as a preliminary sanity check, NOT a definitive
  Gate 2 verdict.
- Only window=200 is tested here -- the single window that passed
  Gate 1. Re-sweeping all four windows in Phase 2 would repeat the
  same multiple-testing problem Phase 2 exists to guard against.

Methodology note: the price fetch reaches back to 2022-01-01 (same as
Phase 1) so the 200-day SMA is properly warmed up BEFORE the OOS
window starts. Only the period from OOS_START_DATE onward is scored --
the lookback period is context for the indicator, not part of the
evaluated result.

Run this locally -- needs live network access to Yahoo Finance.
Requires: pip install -r requirements.txt
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import json

import pandas as pd

from src.data.price_history import fetch_price_history
from src.features.moving_average import compute_sma
from src.strategies.sma_crossover_sp500top50 import compute_signal, compute_target_weights, hold_until_signal_change
from src.backtest.reshape import pivot_long_to_wide
from src.backtest.runner import run_backtest

WINDOW = 200  # the only window that passed Gate 1 -- do not sweep here
LOOKBACK_START = "2022-01-01"  # ample warmup for a 200-day SMA
OOS_START_DATE = "2026-08-01"  # first genuinely unseen day (> Phase 1 cutoff)
OOS_END_DATE = None  # through the most recent available trading day

REPO_ROOT = Path(__file__).resolve().parents[2]
universe = pd.read_csv(REPO_ROOT / "research/sma_crossover_sp500top50/universe_snapshot.csv")
tickers = universe["ticker"].tolist()

print(f"Fetching price history for {len(tickers)} tickers, {LOOKBACK_START} through latest...")
df = fetch_price_history(tickers, start_date=LOOKBACK_START, end_date=OOS_END_DATE)
print(f"Got {df['ticker'].nunique()} of {len(tickers)} requested tickers, {len(df)} rows.")

# Compute SMA/signal/target weight over the FULL fetched range (lookback
# included) so the 200-day SMA is valid from day 1 of the OOS window --
# not computed fresh starting at OOS_START_DATE with no prior context.
df = compute_sma(df, window=WINDOW)
df = compute_signal(df, window=WINDOW)
df = compute_target_weights(df, window=WINDOW)

# Truncate to the genuinely out-of-sample period BEFORE masking to
# signal-change-only. Applying hold_until_signal_change() on the
# truncated frame correctly treats day 1 of the OOS window as a
# "change" from nothing (within this frame), so it re-enters whatever
# position the already-warmed-up signal implies at that point -- it
# does not require the signal to have literally flipped exactly on
# OOS_START_DATE. Verified directly before writing this script.
oos_cutoff = pd.to_datetime(OOS_START_DATE).date()
oos_df = df[df["date"] >= oos_cutoff].copy()
oos_df = hold_until_signal_change(oos_df, window=WINDOW)

prices_wide = pivot_long_to_wide(oos_df, value_col="close")
weights_wide = pivot_long_to_wide(oos_df, value_col=f"rebalance_weight_{WINDOW}")

n_days = prices_wide.shape[0]
print(f"OOS evaluation window: {n_days} trading days ({OOS_START_DATE} onward)")
if n_days < 30:
    print("WARNING: fewer than 30 trading days in the OOS window -- any "
          "Sharpe/Sortino figure below is close to statistically "
          "meaningless on its own. Treat as a sanity check only, not a "
          "Gate 2 verdict.")

pf = run_backtest(prices_wide, weights_wide)
stats = pf.stats()

results = {
    "phase": "2_oos",
    "window": WINDOW,
    "lookback_start": LOOKBACK_START,
    "oos_start_date": OOS_START_DATE,
    "oos_end_date": "latest" if OOS_END_DATE is None else OOS_END_DATE,
    "n_oos_trading_days": int(n_days),
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

out_path = REPO_ROOT / "research/sma_crossover_sp500top50/oos_results_window200.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

print("\n--- OOS RESULTS (preliminary -- short window, see caveats above) ---")
print(json.dumps(results, indent=2))
