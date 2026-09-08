# Handoff — sma_crossover_sp500top50 — Task 6b: Reshape function (tests only)

## Important
`pivot_long_to_wide()` already exists in `src/backtest/reshape.py`
(written in the previous session) and must NOT be modified in this
session — this session only adds a test file. If the tests below fail
against the existing function, stop and report the failure; do not
"fix" it by changing the implementation yourself.

## Allowed files
- tests/backtest/test_reshape.py (new file)
(Nothing else, including src/backtest/reshape.py.)

## This session's task
Create `tests/backtest/test_reshape.py` with tests using exactly this
fixture (copy it verbatim, do not invent a different one):

Input DataFrame (5 rows):
| date       | ticker | value |
|------------|--------|-------|
| 2026-01-01 | AAPL   | 10    |
| 2026-01-01 | MSFT   | 20    |
| 2026-01-02 | AAPL   | 11    |
| 2026-01-02 | MSFT   | 21    |
| 2026-01-03 | MSFT   | 22    |

Note: there is no 2026-01-03 / AAPL row — that combination is
deliberately absent from the input.

Call `pivot_long_to_wide(df, value_col="value")` and assert the result
matches exactly this expected wide DataFrame:

| date (index) | AAPL | MSFT |
|--------------|------|------|
| 2026-01-01   | 10   | 20   |
| 2026-01-02   | 11   | 21   |
| 2026-01-03   | NaN  | 22   |

Write these 4 assertions against that single call's result (one
fixture, one function call, four checks on its output — do not call
the function multiple times with different fixtures):
1. The result's index, in order, is
   [2026-01-01, 2026-01-02, 2026-01-03] (ascending date order).
2. The result's columns, in order, are ["AAPL", "MSFT"] (alphabetical,
   single-level — not a MultiIndex).
3. The specific cell values match the expected table above exactly
   (use `.loc[date, ticker]` lookups, e.g.
   `result.loc["2026-01-02", "AAPL"] == 11`).
4. `result.loc["2026-01-03", "AAPL"]` is NaN (use `pd.isna(...)`, not
   `== float('nan')`, which never evaluates True).

Run the test and confirm it passes. If it does not pass on the first
or second try, stop and write down the exact assertion error rather
than iterating further — see Resume point below.

## Done so far
`pivot_long_to_wide()` is implemented and committed in
`src/backtest/reshape.py` (previous session, implementation-only).
This session adds tests against that existing, unmodified function.

## Resume point
If the test fails and it's not immediately obvious why (e.g. a typo
in this file rather than a real bug), write the exact error message
here and stop — do not spend budget modifying the implementation file,
which is out of scope for this session.
