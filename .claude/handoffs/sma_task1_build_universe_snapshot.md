# Handoff — sma_crossover_sp500top50 — Task 1 (revised): Build top-50 universe snapshot

## Important — do this before anything else
If `src/data/sp500_universe.py` or `tests/data/test_sp500_universe.py`
already exist with any content, DO NOT try to read, understand, or fix
that content. Delete/overwrite it completely and start both files
fresh from empty. A previous approach (Wikipedia scraping) is being
abandoned entirely in favor of the approach below — do not try to
combine the two.

## Objective
Implement ONE function, `build_sp500_top50_snapshot() -> pd.DataFrame`,
that fetches a public S&P 500 constituents-with-financials CSV,
selects the top 50 rows by market cap, and saves the result as the
strategy's universe snapshot.

## Allowed files
- src/data/sp500_universe.py (code)
- tests/data/test_sp500_universe.py (tests)
- research/sma_crossover_sp500top50/universe_snapshot.csv (generated
  output — the function writes this, it is not source code)
(Nothing outside this list. If the task seems to need another file,
stop and flag it instead of creating it.)

## Data source
```
https://raw.githubusercontent.com/datasets/s-and-p-500-companies-financials/main/data/constituents-financials.csv
```
This is a static CSV, no scraping, no auth, no rate limits. Columns
include (at minimum): `Symbol`, `Name`, `Sector`, `Market Cap`. Some
rows may have a missing/null `Market Cap` (documented behavior of this
source when Yahoo Finance doesn't report a value for that company) —
drop those rows before ranking, don't error on them.

## Input schema
None — the function takes no arguments.

## Output schema
pandas.DataFrame, exactly 50 rows, sorted by market cap descending,
columns:
- ticker: str (yfinance-compatible — replace "." with "-" if present,
  e.g. "BRK.B" becomes "BRK-B")
- company_name: str (from `Name`)
- sector: str (from `Sector`)
- market_cap_usd: int or float (from `Market Cap`, raw USD, not
  billions)
- snapshot_date: str, ISO format `YYYY-MM-DD`, today's date for every
  row (this is a one-time snapshot, so the date is constant across
  all 50 rows)

The function must also write this DataFrame to
`research/sma_crossover_sp500top50/universe_snapshot.csv` (index=False)
before returning it.

## Caching behavior
- On first call, fetch the CSV via `pandas.read_csv(url)`, then save a
  local copy to `src/data/.cache/sp500_financials_raw.csv`.
- On subsequent calls, if that cache file exists, read from it instead
  of hitting the network again.
- Ensure `src/data/.cache/` is listed in `.gitignore` (create the file
  if missing, append the line if it isn't already there).

## Done so far
Nothing — this is a fresh start replacing an abandoned approach (see
the note at the top of this file).

## This session's task
1. Write `build_sp500_top50_snapshot()` in `src/data/sp500_universe.py`
   exactly as scoped above.
2. Write `tests/data/test_sp500_universe.py` with these cases only:
   - The function returns a DataFrame with exactly 50 rows and the
     five expected columns.
   - `market_cap_usd` is sorted descending (validates the ranking
     logic).
   - No `ticker` value contains a literal "." character.
3. Run the tests. Keep scope to exactly the three items above — no
   extra retries, logging, or robustness beyond what's asked.

## Resume point
If you run out of budget before all tests pass: write one line here
with which test is failing and the exact error message, then stop.
Do not keep iterating past your budget trying different fixes.
