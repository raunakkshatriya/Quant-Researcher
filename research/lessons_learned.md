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
