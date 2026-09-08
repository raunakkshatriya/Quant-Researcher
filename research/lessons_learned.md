# Lessons Learned — S&P 500 Data Fetching Issue (2026-09-08)

## Finding
The `pd.read_html()` call to Wikipedia's "List of S&P 500 companies" page returns HTTP 403: Forbidden. Wikipedia blocks automated scraping requests from Python/pandas.

## Impact
Task 1a cannot complete as written — the network fetch fails. The cache is never populated because the request is rejected before any data loading or caching can occur.

## Why this was non-obvious
The handoff file stated "Do NOT rename columns, filter rows, or reformat tickers" and assumed Wikipedia would be reachable via `pd.read_html()`. It didn't anticipate that Wikipedia's anti-scraping measures would block the request at runtime.

## How to apply in next session
- Do not proceed with Task 1b (column normalization) until data source is available.
- Options:
  1. Use a proxy/maintenance window URL for Wikipedia tables.
  2. Alternative stable source (FRED, SEC EDGAR via CSV API).
  3. Manual download + local refresh on schedule (not auto-fetched).

## Resume point for next session
Report the column names from `pd.read_html()` to ensure Task 1b remains aligned. If Wikipedia remains blocked, a new data source must be selected before any column-normalization logic can be implemented.
