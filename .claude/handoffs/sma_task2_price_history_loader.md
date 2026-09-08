# Handoff — sma_crossover_sp500top50 — Task 2: Price history loader

## Objective
Implement ONE function, `fetch_price_history(tickers: list[str],
start_date: str, end_date: str | None = None) -> pd.DataFrame`, that
fetches daily OHLCV price history for a list of tickers and returns it
in long format. This function must be generic — it takes tickers and
dates as arguments, it does NOT read `universe_snapshot.csv` itself
and does NOT hardcode any cutoff date. It will be called with
different date ranges later for in-sample vs. out-of-sample use;
that's the caller's responsibility, not this function's.

## Allowed files
- src/data/price_history.py
- tests/data/test_price_history.py
(Nothing outside this list. If the task seems to need another file,
stop and flag it instead of creating it.)

## Input schema
- tickers: list[str], yfinance-compatible symbols (e.g. "BRK-B" not
  "BRK.B")
- start_date: str, "YYYY-MM-DD"
- end_date: str or None, "YYYY-MM-DD". If None, fetch through the most
  recent available trading day.

## Output schema
pandas.DataFrame, default RangeIndex, one row per (date, ticker) pair,
columns:
- date: datetime64
- ticker: str
- open: float
- high: float
- low: float
- close: float
- adj_close: float
- volume: int

Sort by ticker, then date.

## Implementation notes
- Use `yfinance.download(tickers, start=start_date, end=end_date,
  group_by='ticker', auto_adjust=False)` in a single batched call —
  do not loop over tickers one at a time.
- yfinance returns wide format with multi-index columns when given
  multiple tickers; reshape this into the long format specified above.
- Cache the fetched result to
  `src/data/.cache/price_history_{start_date}_{end_date_or_'latest'}.parquet`
  keyed only on the date range (not on the specific ticker list) —
  on a cache hit for that date range, load from the cached file
  instead of re-fetching.
- If yfinance fails to return data for a given ticker (delisted,
  typo, etc.), skip that ticker and continue rather than raising —
  this function does not need to guarantee every requested ticker
  comes back, just that valid ones do.

## Done so far
`build_sp500_top50_snapshot()` is complete and committed (commit
52fa3b7). `research/sma_crossover_sp500top50/universe_snapshot.csv`
exists with 50 tickers, already yfinance-formatted (no dots). This
session's function does not need to read that file — it just needs to
accept a tickers list as an argument.

## This session's task
1. Write `fetch_price_history()` in `src/data/price_history.py`
   exactly as scoped above.
2. Write `tests/data/test_price_history.py` with these cases only,
   using a SMALL test fixture — 3-5 tickers (e.g. ["AAPL", "MSFT",
   "NVDA"]) and a SHORT date range (e.g. the last 10 calendar days) —
   do not test against the full 50-ticker universe or a long date
   range, that's unnecessary network load for a unit test:
   - Returns a DataFrame with the 8 expected columns.
   - Every requested ticker appears at least once in the `ticker`
     column.
   - No duplicate (date, ticker) pairs.
   - All returned dates fall within [start_date, end_date].
3. Run the tests. Keep scope to exactly the four items above.

## Resume point
If you run out of budget before all tests pass: write one line here
with which test is failing and the exact error message, then stop.
Do not keep iterating past your budget trying different fixes.
