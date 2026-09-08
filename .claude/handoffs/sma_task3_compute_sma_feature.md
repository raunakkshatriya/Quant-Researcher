# Handoff — sma_crossover_sp500top50 — Task 3: SMA feature function

## Objective
Implement ONE function, `compute_sma(df: pd.DataFrame, window: int) ->
pd.DataFrame`, that adds a T-day simple moving average column to a
long-format price DataFrame, computed independently per ticker.

## Allowed files
- src/features/moving_average.py
- tests/features/test_moving_average.py
(Nothing outside this list. If the task seems to need another file,
stop and flag it instead of creating it.)

## Input schema
pandas.DataFrame, long-format, at minimum containing columns:
- date: datetime64
- ticker: str
- close: float
(This matches the output of `fetch_price_history()` from
src/data/price_history.py — the function may receive extra columns
like open/high/low/volume too; ignore them, just pass them through
unchanged.)

## Output schema
The same DataFrame, with one new column added:
- sma_{window}: float — e.g. if window=20, the column is named
  "sma_20". Use an f-string, not a fixed name — this function gets
  called with different window values later (20, 50, 100, 200).

Row order and all original columns are preserved. Sort by ticker,
then date, before computing (do not assume the input is already
sorted).

## Implementation notes
- Compute per-ticker: group by `ticker`, then take a rolling mean of
  `close` over `window` periods.
- Use `min_periods=window` (NOT a smaller value). Rows without enough
  trailing history for that ticker must be NaN, not a partial-window
  average — a short-window average silently mislabeled as a full
  T-day SMA would be wrong data, not just missing data.
- Each ticker's rolling window must be computed independently — a
  rolling calculation that isn't grouped by ticker first will
  incorrectly blend one ticker's prices into another's window.

## Done so far
`fetch_price_history()` (src/data/price_history.py) is complete and
committed, producing the long-format input this function consumes.
`build_sp500_top50_snapshot()` is complete and committed, producing
the 50-ticker universe.

## This session's task
1. Write `compute_sma()` in `src/features/moving_average.py` exactly
   as scoped above.
2. Write `tests/features/test_moving_average.py` with these 4 cases
   only, using small hand-constructed DataFrames (not real fetched
   data — no network calls in this test file):
   - Normal window: a single ticker with enough history; the SMA
     value on a specific known row matches a manually-computed
     expected average.
   - Insufficient history: the first (window - 1) rows for a ticker
     are NaN.
   - A ticker with a gap in its dates: function doesn't error, and
     the rolling window is computed over however many actual rows
     precede each point (not calendar days).
   - Two tickers in the same DataFrame: confirm ticker A's SMA values
     are unaffected by ticker B's prices (catches the "forgot to
     group by ticker" bug specifically).
3. Run the tests. Keep scope to exactly the four items above — no
   extra parameters, no EMA variant, nothing beyond what's asked.

## Resume point
If you run out of budget before all tests pass: write one line here
with which test is failing and the exact error message, then stop.
Do not keep iterating past your budget trying different fixes.
