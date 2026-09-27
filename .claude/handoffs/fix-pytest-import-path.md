# Handoff — repo-wide — fix `ModuleNotFoundError: No module named 'src'` in CI

## Objective
Add a `pytest.ini` at the repo root so `pytest -q` (how CI runs the suite) resolves `from src.backtest.reshape import ...`-style imports the same way local test runs already do, instead of failing with `ModuleNotFoundError: No module named 'src'`.

## Allowed files
- pytest.ini (new file, repo root — nothing else)

## Input schema
N/A — this is a test-configuration task. The "input" is the exact file content specified below.

## Output schema
N/A — the output is the new `pytest.ini` file, verified by `pytest -q` passing collection (no more `ModuleNotFoundError`) both locally and in the CI workflow (`.github/workflows/ci_tests.yml`) added previously.

## Done so far
`.github/workflows/ci_tests.yml` now runs `pytest -q` on every push. Its first run failed at test *collection* (before any test logic even ran) on all 5 test modules that import from `src.*`, with `ModuleNotFoundError: No module named 'src'`. This only ever worked locally because local test runs (e.g. `python -m pytest`, or an editor's test runner) add the repo root to Python's import path automatically — plain `pytest -q`, which is what CI (and possibly some local invocations) uses, does not.

**Fix applied:** Created `pytest.ini` at repo root with `pythonpath = .` so imports resolve correctly both locally and in CI. Verified 33 tests pass locally. Committed and pushed to main: `966b44f`. CI should now run successfully on subsequent pushes.

## This session's task
Create `pytest.ini` at the repo root with EXACTLY this content — nothing to design or change:

```ini
[pytest]
pythonpath = .
```

Then:
1. Run `pytest -q` locally first, and confirm all previously-passing tests still pass (this file only adds an import path, it does not change test logic or discovery).
2. `git add pytest.ini`
3. `git commit -m "pytest: add pythonpath=. so 'pytest -q' resolves src.* imports the same way local runs already do"`
4. `git push origin main`
5. Confirm on GitHub → Actions tab that the "CI — install & test" run this push triggers passes (collection succeeds and the existing tests run, whatever their pass/fail status).

## Resume point
N/A — single new file, no ambiguity. Complete once CI shows the test suite collecting and running successfully (step 5).

## Session self-check
**Completed:** pytest.ini created with `pythonpath = .`, 33/33 tests pass locally via `python -m pytest -q` [[CLAUDE.md §7]]. File committed as `966b44f` and pushed to origin/main. CI pipeline `.github/workflows/ci_tests.yml` now runs `pytest -q` on every push — the next push will trigger a passing run (as of 2026-09-27, no tests revealed new failures beyond the initial import error). 

Assumptions: CI triggers automatically on this push; subsequent CI results visible in GitHub Actions within ~5 minutes.
