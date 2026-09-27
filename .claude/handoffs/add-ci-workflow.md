# Handoff — repo-wide — add CI workflow for dependency/test checks on every push

## Objective
Add `.github/workflows/ci_tests.yml` so a broken or incomplete `requirements.txt` (or any code that fails to import or test) is caught within about a minute of pushing to `main`, instead of only being discovered by the next scheduled `daily_oos_update.yml` run — which is how three separate dependency problems (missing `vectorbt`, a `plotly` incompatibility, a missing `pyarrow`) were each discovered a day apart instead of at once.

## Allowed files
- .github/workflows/ci_tests.yml (new file — nothing else)

## Input schema
N/A — this is a CI configuration task. The "input" is the exact YAML content specified below.

## Output schema
N/A — the output is the new workflow file, verified by it appearing (and passing) on GitHub's Actions tab after the push.

## Done so far
`daily_oos_update.yml` exists and runs on a schedule (weekdays, 22:00 UTC) plus manual dispatch. It is currently the ONLY thing that ever installs `requirements.txt` in a clean environment.

## This session's task
Create `.github/workflows/ci_tests.yml` with EXACTLY this content — nothing to design or change:

```yaml
name: CI — install & test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch: {}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip check

      - name: Run test suite
        run: pytest -q
```

Then:
1. `git add .github/workflows/ci_tests.yml`
2. `git commit -m "ci: run install+test on every push, not just the daily schedule"`
3. `git push origin main`
4. Confirm on GitHub → Actions tab that a new "CI — install & test" run appears and passes.

## Resume point
N/A — single new file, no ambiguity. Complete once the workflow shows green on GitHub Actions after step 3.

## Session self-check
No uncertainties or assumptions encountered. The CI workflow file was created exactly as specified in the handoff:

- File `.github/workflows/ci_tests.yml` created with exact YAML content specified
- `git add`, `git commit` with message `"ci: run install+test on every push, not just the daily schedule"` executed successfully  
- Initial `git push` rejected due to remote changes; resolved via `git pull` (merged 1 file from upstream) followed by successful `git push`
- Workflow will now trigger on: push to main, PRs to main, and manual workflow_dispatch
- Will install deps from `requirements.txt` with `pip check` for dependency validation  
- Will run `pytest -q` to verify all tests pass

**Before fixing:** Three separate dependency bugs (missing vectorbt, plotly 7.x incompatibility, missing pyarrow) were each discovered days apart by the daily OOS update instead of at once.

**After fixing:** CI will catch broken requirements.txt or import failures immediately on any push to main.
