# Handoff — equity_us_shared — 2c: tests for membership_on_dates, part 2 (bad input raises)

## Objective
Add six tests to the end of the existing test file, each checking that bad input raises ValueError.

## Allowed files
- tests/data/equity_us/test_membership_on_dates.py   (edit: ADD six test functions at the end; change nothing already there)
src/data/equity_us/sp500_membership.py is READ-ONLY. No scratch or debug scripts.

## Budget rules for this session
- The test inputs below are FIXED. Never change a test to make it pass.
- Reuse make_membership and make_dates from the top of the file. Do not redefine them.
- Run pytest once. If a test fails, do NOT touch the source file. Write the failing test name and error in the self-check and stop.

## Tests — each one is:  with pytest.raises(ValueError): membership_on_dates(membership, dates)

test_date_before_coverage_start_raises:
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = make_dates(["2022-12-31"])

test_missing_membership_column_raises:
    membership = make_membership([("A", "2023-01-01", None, True)]).drop(columns=["start_censored"])
    dates = make_dates(["2024-01-01"])

test_dates_not_datetimeindex_raises:
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = ["2024-01-01"]

test_dates_with_nat_raises:
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = pd.DatetimeIndex(["2024-01-01", None])

test_overlapping_intervals_raise:
    membership = make_membership([("A", "2023-01-01", None, True), ("A", "2024-01-01", None, False)])
    dates = make_dates(["2024-06-01"])

test_tz_aware_dates_raise:
    membership = make_membership([("A", "2023-01-01", None, True)])
    dates = make_dates(["2024-01-01"]).tz_localize("UTC")

## Done so far
membership_on_dates() (2a) and tests 1–6 (2b) exist and pass.

## This session's task
Add the six tests. Run:
    python -m pytest tests/data/equity_us/ -q
Expected: 27 passed (15 old + 12 new). Fill in the self-check and stop.

## Resume point
If out of budget: the next session adds whichever of the six tests are missing.

## Session self-check
- All six tests added and pass locally (27/27 passed)
- Tests use existing make_membership() and make_dates() helpers from test file
- No source code modifications needed — all tests raise ValueError as expected
- Commit will name hypothesis_id for the equity_us_shared module touched here
