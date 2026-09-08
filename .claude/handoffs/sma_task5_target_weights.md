# Handoff — sma_crossover_sp500top50 — Task 5: Target position weights

## Objective
Implement ONE function, `compute_target_weights(df: pd.DataFrame,
window: int, weight_per_position: float = 0.02) -> pd.DataFrame`,
that converts a per-row signal into a fixed target portfolio weight.

## Allowed files
- src/strategies/sma_crossover_sp500top50.py (add to the existing
  file — do not remove or modify compute_signal(), just add this new
  function alongside it)
- tests/strategies/test_sma_crossover_sp500top50.py (add to the
  existing file — do not remove or modify the existing 4 tests)

## Input schema
pandas.DataFrame, long-format, containing at minimum:
- date: datetime64
- ticker: str
- signal_{window}: float (e.g. "signal_20" if window=20 — output of
  compute_signal(), values in {1.0, -1.0, 0.0, NaN})

## Output schema
The same DataFrame, with one new column added:
- target_weight_{window}: float — e.g. "target_weight_20" if
  window=20. This is simply signal_{window} * weight_per_position:
  - signal 1.0 → +weight_per_position (default 0.02, i.e. +2%)
  - signal -1.0 → -weight_per_position (default -0.02, i.e. -2%)
  - signal 0.0 → 0.0
  - signal NaN → NaN (propagate — do not convert to 0.0; a position
    we have no signal for yet is different from a position we've
    deliberately decided to hold flat)

## Important — do not renormalize
This is a FIXED weight per active name, not a weight that grows when
fewer names have an active signal. Do not add any logic that scales
weight_per_position based on how many tickers are currently long/short
on a given date. 50 names at a fixed 2% each is a deliberate design
choice tied to the portfolio's leverage ceiling (max_portfolio_leverage:
1.0 in risk_and_costs.yaml) — if only 30 of 50 names have an active
signal on some date, the portfolio is simply 60% invested that day,
not rebalanced up to 100%.

## This session's task
1. Write `compute_target_weights()` exactly as scoped above.
2. Add these 4 test cases to the existing test file (small
   hand-constructed rows, no network calls):
   - signal = 1.0 → target_weight = weight_per_position
   - signal = -1.0 → target_weight = -weight_per_position
   - signal = 0.0 → target_weight = 0.0
   - signal = NaN → target_weight = NaN
3. Run the full test file (all 8 tests now — the original 4 plus
   these 4) and confirm all pass.

## Done so far
`compute_signal()` is complete and committed (commit f7c577d),
producing the signal_{window} column this function consumes.
`compute_sma()`, `fetch_price_history()`, and
`build_sp500_top50_snapshot()` are also complete and committed.

## Resume point
If you run out of budget before all tests pass: write one line here
with which test is failing and the exact error message, then stop.
Do not keep iterating past your budget trying different fixes.
