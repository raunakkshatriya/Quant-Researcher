# Handoff — equity_us_shared — 1c: tests for reconstruct_membership, part 2 (cases 4–7)

## Objective
Add test cases 4–7 to the existing test file, using the exact inputs and expected outputs below.

## Allowed files
- tests/data/equity_us/test_sp500_membership.py   (edit: ADD new test functions at the end; do not change anything already in the file)
src/data/equity_us/sp500_membership.py is READ-ONLY this session. No scratch or debug scripts.

## Budget rules for this session
- The expected values below are FIXED and correct. Never change an expected value to make a test pass.
- Reuse the helpers already at the top of the file (START, AS_OF, as_rows, make_changes). Do not redefine them.
- Run pytest once. If a test fails, do NOT try to fix the source file. Write the failing test name and the error message in the self-check and stop.

## Test case 4 — test_anomalies_recorded_not_raised
current = pd.DataFrame({"ticker": ["A"]})
changes = make_changes(["2024-01-01", "2024-02-01"], ["Z", None], [None, "A"])
expected membership rows:
    [("A", "2023-01-01", "NaT", True)]
expected anomalies rows:
    [("2024-01-01", "Z", "add", "added_ticker_not_in_working_set"),
     ("2024-02-01", "A", "remove", "removed_ticker_already_in_working_set")]

## Test case 5 — test_empty_changes
current = pd.DataFrame({"ticker": ["A", "B"]})
changes = make_changes([], [], [])
expected membership rows:
    [("A", "2023-01-01", "NaT", True),
     ("B", "2023-01-01", "NaT", True)]
expected anomalies rows: []
also: assert list(anomalies.columns) == ["date", "ticker", "event", "reason"]

## Test case 6 — test_missing_values_and_ticker_normalization
current = pd.DataFrame({"ticker": [" aapl ", "MSFT"]})
changes = make_changes(["2024-06-01", "2024-09-01", "2025-06-01"],
                       [None, None, "msft"],
                       ["goog ", None, None])
expected membership rows:
    [("AAPL", "2023-01-01", "NaT", True),
     ("GOOG", "2023-01-01", "2024-06-01", True),
     ("MSFT", "2025-06-01", "NaT", False)]
expected anomalies rows: []

## Test case 7 — test_invalid_inputs_raise (three separate `with pytest.raises(ValueError):` blocks)
a. changes missing a column:
   bad = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"]), "added_ticker": ["A"]})
   reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), bad, AS_OF, START)
b. start after as_of:
   reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), make_changes([], [], []), START, AS_OF)
   (note: START and AS_OF are deliberately swapped here — the 3rd argument is as_of_date, the 4th is start_date)
c. start equal to as_of:
   reconstruct_membership(pd.DataFrame({"ticker": ["A"]}), make_changes([], [], []), AS_OF, AS_OF)

## Done so far
Implementation (1a) and tests 1, 1b, 2, 3 (1b session) exist and pass.

## This session's task
Add the four test functions above to the end of the file. Run:
    pytest tests/data/equity_us/test_sp500_membership.py -q
Expected: 8 passed. Fill in the self-check with the result and stop.

## Resume point
If out of budget: next session adds whichever of tests 4–7 are missing.

## Session self-check
(fill in before finishing, per CLAUDE.md §7)
