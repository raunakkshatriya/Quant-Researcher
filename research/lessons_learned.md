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
