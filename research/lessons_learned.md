# Lessons Learned — sma_crossover_sp500top50 build-out (2026-09-08)

## On trusting Claude Code's self-diagnosis of *why* something works
Two separate sessions gave a plausible-sounding but incorrect
explanation for behavior that was either already fine or caused by
something else entirely:
- Task 3 claimed it "used pandas default of 1" for `min_periods` on a
  rolling window. Pandas' actual default for a fixed integer window
  is the window size itself, not 1 (that default only applies to
  offset/time-based windows). The code was correct; the stated reason
  it was correct was not.
- Task 7 claimed a `VBT_DISABLE_PLOT` environment variable fixed a
  vectorbt/plotly import compatibility issue. That setting is not
  documented anywhere in vectorbt. The Task 7b cleanup removed it and
  all tests still passed — it was never the fix; something else
  resolved the import, or it was never actually broken in the way
  described.

Neither error broke anything downstream, but both would have gone
unnoticed without an independent check against outside sources.
Treat a small model's causal explanation of *why* its own fix works
as a hypothesis to verify, not a fact to record as-is.

## On "committed" not always meaning committed
Task 3's session reported "changes are committed with message:
sma_crossover_sp500top50: add compute_sma() + unit tests" — but a
later `git status` showed `src/features/` and `tests/features/` as
entirely untracked, four tasks later. The commit never actually
happened, and nothing surfaced this until an unrelated review. Worth
a standing habit: spot-check `git log --oneline -1` after any session
that claims to have committed, rather than trusting the summary at
face value.

## On scope and allowed-files discipline
Task 7 (introducing vectorbt) hit a real dependency-compatibility
problem, and in the course of chasing a fix, touched files well
outside its two allowed files — including generating this very file
under the previous, stale version. The follow-up cleanup (Task 7b),
scoped to exactly one file with a narrow, fully-specified task, ran
cleanly with no drift. Narrower allowed-file lists correlate directly
with less wandering when a session is under pressure to make
something pass.

## Killed approach (superseded, kept for context)
Task 1a's original plan — scraping Wikipedia's S&P 500 constituent
table via `pandas.read_html()` — failed with an HTTP 403 (Wikipedia
blocks generic scraping user agents). This was fully superseded by
switching to a static, actively-maintained CSV from
`datasets/s-and-p-500-companies-financials` on GitHub, which also
already includes market cap, removing the need for a separate
per-ticker yfinance loop entirely. No action needed here; noted only
so the abandoned direction doesn't get rediscovered later.

## On reserving the OOS holdout before, not after, parameter exploration
`sma_crossover_sp500top50`'s Phase 1 window sweep (T in {20,50,100,200})
used the entire available historical range (2022-01-01 to the
2026-07-31 train/test cutoff) to pick the best-performing window. That
leaves no untouched historical stretch to serve as a genuine Phase 2
out-of-sample test — the sweep itself already "used up" all of it. The
only truly unseen data remaining is the short post-cutoff window,
which is barely above the ~30-day floor already flagged elsewhere as
producing near-meaningless Sharpe estimates.

For future hypotheses: decide the in-sample/out-of-sample historical
split BEFORE running any parameter sweep, and keep the OOS slice
completely untouched until Gate 2 — not just "whatever data arrives
after today." A parameter sweep that spans the entire available
history is really an unusually thorough Gate-1-only exercise, not a
substitute for Gate 2.

## On the daily-rebalancing bug's real lesson
The bug itself (`hold_until_signal_change()`, added 2026-09-08) is
already covered in Task 7's fix commit message. The broader lesson:
a wiring bug between two individually-correct, individually-tested
functions (`compute_target_weights()` producing a value that persists
across days, `run_backtest()` treating any non-NaN value as "rebalance
today") was invisible to every unit test and only surfaced by running
the real, full pipeline end-to-end and questioning a suspiciously high
trade count rather than accepting it. Isolated unit tests prove a
function does what it claims; they don't prove two correct functions
compose correctly. Both are necessary; neither is sufficient alone.

## Correction to the previous entry above
The prior entry floated "use an earlier historical chunk as a
second-best OOS proxy" as a middle-ground option if the post-cutoff
window proved too short. On reflection, that's wrong and was withdrawn
in the same conversation it was raised: the entire 2022-2026 range was
already folded into the aggregate calculation used to *select* T=200
in the first place. There is no untouched historical slice left to
borrow — any earlier period considered was already part of the
evidence that picked this window. For this specific hypothesis, the
only genuinely clean OOS data is whatever accumulates from here
forward in real time. This is the actual, non-recoverable cost of the
methodology gap already logged above; it is not fixable retroactively,
only avoidable on the next hypothesis by reserving a holdout before
any parameter sweep runs.

## Gate 2, first checkpoint (2026-09-08)
26 trading days post-cutoff, T=200 only. Sharpe 0.13, Sortino 0.20 --
consistent with pure noise at this sample size on their own. But
0 wins out of 22 CLOSED trades (separately from the 50 still-open
positions) is a real, independently-computed data point pointing the
same weak direction, with roughly a 5% chance of occurring by chance
if the in-sample 13% win rate genuinely held. Not enough to kill the
hypothesis, not enough to ignore either. A daily GitHub Action now
extends this window one real trading day at a time
(oos_ledger.csv) so a future review has enough closed trades for an
actual Gate 2 read instead of a 26-day snapshot.

## Full qwen3.5:4b incident log (2026-09-07 to 2026-09-08)

Condensed, actionable versions of these are now in `CLAUDE.md` §10,
read at the start of every session. This is the full narrative for
human reference — what happened, why it mattered, and what changed
as a direct result. Numbered for reference, not chronological within
each number (some overlap in time).

**1. Improvisation-and-oscillation loop (Task 6, first attempt).**
Asked to write a reshape function plus tests, the session added an
unrequested `reset_index()` call, then spent its entire budget
alternating between "fixing" the test to match the broken output and
"fixing" the implementation to match the test — never reverting to
the original, simple spec. Fix: for anything this small, give literal
code to transcribe rather than a spec to implement, and split
"write the function" and "write the tests" into separate sessions so
the model is never negotiating both at once. This worked immediately
(Task 6a/6b) and was reused successfully for the rest of the build.

**2. Fabricated technical explanation (Task 7).** A genuine
vectorbt/plotly import error got "fixed" by setting
`VBT_DISABLE_PLOT = "True"`, described confidently as a known
compatibility setting. That environment variable does not exist in
vectorbt's documentation. Removing it later and re-running the tests
showed they still passed — it was never the fix; the actual fix
(pinning `plotly<7`) was found independently, by testing the import
in a clean environment rather than trusting the session's narrative.

**3. Silent commit failures (Task 3, and again for `runner.py` in
Task 7).** Both sessions reported "committed" in their summary. Both
times, `git log` and `git status` later showed the file had never
actually been committed — in Task 3's case, undetected for four
subsequent tasks, because nothing prompted a `git status` check until
an unrelated review. Fix: treat "committed" as a claim to verify, not
a fact to record — check `git log --oneline -1` after any session
that claims to have committed.

**4. A test suite that never tested the real function (Task 2).**
`fetch_price_history()`'s original test file never imported or called
the actual function — it built its own disconnected synthetic fixture
and tested that instead. All 5 tests passed. The real function had a
missing top-level `pandas` import that made it non-importable from the
moment of its first commit (confirmed later: Python evaluates a
`-> pd.DataFrame` return annotation eagerly at import time on the
installed Python version, so this was a real, load-time `NameError`,
not a hypothetical one). This went undetected through six subsequent
tasks because nothing ever actually imported the module until a much
later independent review did.

**5. Explicit scope boundary violated under pressure (Task 8, the
most serious incident).** The handoff for this task said, in bold
terms, "do not touch any file under `src/`." The session found the
real bug described in #4 above — a correct diagnosis — but then,
rather than reporting it, decided "this is getting too complex, let
me take a much simpler approach," and rewrote the entire batched
yfinance download into a per-ticker loop, reversing a deliberate
design decision from Task 2's original handoff and introducing a new
undefined-variable bug in the rewrite's single-ticker branch. It ran
out of budget mid-rewrite, leaving the file in a broken, uncommitted
state. Recovery required a full manual diff review, a `git restore`,
and rebuilding the fix from scratch in a separate, tightly-scoped
session with "no edits to `src/`, report only" stated explicitly.

**6. A wrong description of correct code (Task 3).** The `compute_sma`
implementation correctly relied on pandas' default `min_periods`
behavior for a fixed-integer rolling window (which equals the window
size), but its own comment claimed the default was 1 — which is only
true for offset/time-based windows, not integer ones. The code worked;
the explanation was wrong. Caught only by independently checking
pandas' actual documented behavior rather than trusting the comment.

**7. A real integration gap invisible to any single unit test.** Two
separate, individually-correct, individually-tested bugs only surfaced
when the full pipeline ran end-to-end for the first time:
- `compute_signal()` initialized its NaN placeholder with `pd.NA`
  instead of `float('nan')`. `pd.isna()` treats them identically, so
  the isolated test passed; `compute_target_weights()`'s
  `.astype(float)` call did not, and only broke when the two functions
  were chained.
- `compute_target_weights()` produces the same weight value on every
  day a signal persists (correct, matches its own spec). But
  `run_backtest()`'s `size_type='targetpercent'` rebalances toward the
  target on every day it sees a non-NaN value, regardless of whether
  that value changed — not only on the day it changes. A position held
  constant for 27 days generated 27 orders, not 1, silently violating
  the strategy's stated design ("rebalanced on signal flips only") and
  inflating turnover/cost drag in every backtest run before this was
  caught. Neither function was individually wrong; they disagreed
  about a convention neither one's unit tests could see.
Neither of these is really a "qwen problem" specifically — they are a
process lesson: isolated unit tests prove a function does what it
claims, they do not prove two correct functions compose correctly.
Both kinds of testing are necessary; neither is sufficient alone. Both
were caught by running the real, full pipeline end-to-end and
questioning a suspicious result (an oscillating test in the first
case, an implausibly high trade count in the second) rather than
accepting a clean-looking pass.

## What actually changed as a result (see CLAUDE.md §10 for the rules)

- Give literal code for anything genuinely small, not a spec to
  design against.
- Split "write the implementation" and "write the tests" into
  separate sessions for anything that previously caused
  implementation-vs-test oscillation.
- Independently verify every "tests pass" and "committed" claim —
  this became standard practice for the rest of the build and caught
  real problems every time it was applied.
- State allowed-files boundaries with an explicit "if you find
  something wrong outside this list, stop and report — do not fix it"
  clause, not just a bare file list.
- Run the real, full pipeline end-to-end at least once before trusting
  a chain of individually-tested functions, and treat a suspicious
  result (implausible counts, values that don't match hand
  calculation) as something to investigate directly rather than a
  detail to gloss over.

# CI & dependency-drift lessons (2026-09-27)

## The pattern: something works locally, breaks only in a clean environment, and is discovered late
Four separate failures this week, on `sma_crossover_sp500top50`'s daily
OOS workflow, all had the same shape: a dependency or an import
assumption held on the machine that already had it installed (or
already invoked commands a particular way), and broke the moment a
genuinely clean environment (GitHub Actions) exercised it:
- `ModuleNotFoundError: vectorbt` — `src/backtest/runner.py` imports
  it directly; `requirements.txt` didn't declare it.
- `vectorbt` import crashing on a `scattermapbox` Plotly trace type
  Plotly's 7.x line removed — an unpinned transitive dependency
  resolved to the newest Plotly on a clean install. (Note: this exact
  incompatibility was already flagged once before, on 2026-09-08 —
  see the entry above about Task 7's `VBT_DISABLE_PLOT` claim — so
  this is at least the second time this specific fragility surfaced.)
- `pandas.to_parquet()` raising `ImportError` for a missing `pyarrow`
  — not a hard pandas dependency, worked locally only because
  something else pulled it in as a transitive package.
- `ModuleNotFoundError: No module named 'src'` in `pytest -q` — local
  test runs (`python -m pytest`, or an editor's runner) add the repo
  root to the import path automatically; plain `pytest -q`, which is
  what CI runs, does not.

## The real root cause of three of the four: a Project-chat overwrite, not three new bugs
Claude Code had already correctly diagnosed and fixed the `vectorbt`/
`plotly` incompatibility *and* the `pyarrow` gap, in two commits on
2026-09-09 (`602a203`, `b99b8fb`) — pinning exact versions
(`vectorbt==1.1.0`, `plotly==6.9.0`, `pyarrow==22.0.0`). The Project
chat then overwrote `requirements.txt` wholesale from its own stale
draft (commit `91a860e`, "Sync tooling policy") without reading the
live file first, silently deleting both fixes. The next three CI/
scheduled-workflow runs failed one at a time as the Project chat
re-discovered — with a wrong guess along the way (assuming `vectorbt`
was still on a 0.x API and capping it `<1.0`, when `1.1.0` was already
verified and in use) — fixes that already existed before it touched
the file.

**Standing rule, now in `CLAUDE.md` §4:** before replacing any shared
file (`requirements.txt`, `CLAUDE.md`, any config both sides touch)
wholesale, read the live version from the repo first. A local Claude
Code session may have already fixed something the Project chat
doesn't know about; a blind overwrite deletes it silently, with no
error until the next CI or scheduled run.

## What actually changed as a result
- Added `.github/workflows/ci_tests.yml`: installs `requirements.txt`
  fresh and runs the full `pytest` suite on every push to `main` (and
  on `pull_request`, and via manual dispatch) — not just on
  `daily_oos_update.yml`'s once-a-day schedule. This is the structural
  fix: a broken dependency or import now surfaces within about a
  minute of committing, in the commit's own CI status, instead of up
  to a day later inside a scheduled job nobody is watching in real
  time. It also means every *future* strategy's new dependencies get
  the same check automatically, with no bespoke test to write per
  strategy — it rides on whatever test file `CLAUDE.md` §5 already
  requires for new signal/money-math code.
- Added `pytest.ini` (`[pytest]` / `pythonpath = .`) so `pytest -q`
  resolves `src.*` imports identically to however local runs already
  worked, removing the local/CI invocation-style gap entirely.
- Verified the new CI workflow actually fails on a real problem (not
  just passes when everything's fine): pushed a throwaway test file
  containing one deliberately-failing assertion, confirmed the Actions
  tab showed a red status with that exact assertion in the log, then
  deleted the file and confirmed it went green again. Worth repeating
  this drill once after any future change to the CI workflow itself
  (not for every ordinary code change) — a CI check that has never
  been seen to fail is unverified, however reassuring a string of
  green runs looks.

# Small-model sessions & input-validation lessons (2026-09-27)

## 2026-09-27 — Small-model sessions: never let the model derive expected test values
The first reconstruct_membership session hit the 64k output limit. Cause: the handoff asked qwen3.5:4b to invent test inputs and work out expected outputs by hand-tracing a backward-walk algorithm; it lost track, then kept editing its expected values to match its own code instead of checking its code against the spec. Also, exact dtype checks (`object`, `datetime64[ns]`) break across pandas versions.
Rule from now on: (1) implementation and tests are separate sessions; (2) the Project chat supplies literal inputs AND literal expected outputs for every test, verified before the handoff is written; (3) expected values are fixed — a failing test is reported, never "fixed" by editing the expectation; (4) dtype checks use pandas.api.types (is_string_dtype, is_datetime64_any_dtype, is_bool_dtype); (5) every handoff states a one-fix-then-stop budget rule and bans scratch files. Re-run in sessions 1a/1b/1c: all passed first time.
Note: this is a repeat of incident #1 in the 2026-09-08 log above (improvisation-and-oscillation loop). The fix — separate implementation/test sessions, literal specs — was already known; the Project chat simply didn't apply it when writing the first reconstruct_membership handoff. That was a planning error on the Project-chat side, not a new model failure. The Project chat should re-read this file before writing any handoff for a new module.

## 2026-09-27 — Data functions must fail loudly on bad input
Review of reconstruct_membership found two silent failures: a NaT in the change log's date column made that change row vanish in the date-window filter, and a blank/None ticker in the current list became a fake ticker ("nan") in the output. Neither raised an error. Separately, the model had added `errors="coerce"` to date parsing unprompted, which would have hidden bad dates the same way.
Rule from now on (codified in CLAUDE.md §5): no silent coercion, fill, drop or skip on inputs; data/feature functions validate dtypes, missing values and blank keys and raise ValueError. Fixed in sessions 1d (removed coerce) and 1e (added validation + 5 tests).
