# Handoff — sma_crossover_sp500top50 — Task 4: Crossover signal function

## Objective
Implement ONE function, `compute_signal(df: pd.DataFrame, window: int)
-> pd.DataFrame`, that turns a price-vs-SMA comparison into a
long/short/flat signal.

## Allowed files
- src/strategies/sma_crossover_sp500top50.py
- tests/strategies/test_sma_crossover_sp500top50.py
(Nothing outside this list. If the task seems to need another file,
stop and flag it instead of creating it.)

## Input schema
pandas.DataFrame, long-format, containing at minimum:
- date: datetime64
- ticker: str
- close: float
- sma_{window}: float (e.g. "sma_20" if window=20 — this is the
  output column name produced by `compute_sma()` in
  src/features/moving_average.py for that window)

This function does NOT compute the SMA itself — it assumes
`compute_sma(df, window)` has already been called and its output is
what's passed in here.

## Output schema
The same DataFrame, with one new column added:
- signal_{window}: float — e.g. "signal_20" if window=20. Values:
  - 1.0 if close > sma_{window} (long)
  - -1.0 if close < sma_{window} (short)
  - 0.0 if close == sma_{window} (exact tie — rare with floats, but
    defined behavior, don't leave it to chance)
  - NaN if sma_{window} is NaN (insufficient history — propagate the
    NaN forward, do NOT treat missing SMA as a 0/flat signal; those
    are different things and downstream backtest code needs to tell
    them apart)

## This session's task
1. Write `compute_signal()` in
   `src/strategies/sma_crossover_sp500top50.py` exactly as scoped
   above.
2. Write `tests/strategies/test_sma_crossover_sp500top50.py` with
   these 4 cases only, using small hand-constructed DataFrames (no
   network calls, no calling compute_sma or fetch_price_history from
   this test file — just construct rows with close and sma_{window}
   values directly):
   - close > sma_{window} → signal is 1.0
   - close < sma_{window} → signal is -1.0
   - close == sma_{window} → signal is 0.0
   - sma_{window} is NaN → signal is NaN (not 0.0)
3. Run the tests. Keep scope to exactly the four items above — no
   position sizing, no portfolio logic, just the per-row signal.

## Done so far
`compute_sma()` (src/features/moving_average.py) is complete and
committed, producing the sma_{window} column this function consumes.
`fetch_price_history()` and `build_sp500_top50_snapshot()` are also
complete and committed.

## Resume point
If you run out of budget before all tests pass: write one line here
with which test is failing and the exact error message, then stop.
Do not keep iterating past your budget trying different fixes.
