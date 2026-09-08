# Quant-Researcher

A personal, end-to-end algorithmic trading research pipeline: hypothesis → in-sample exploration → out-of-sample validation → (once earned) paper trading. Built by orchestrating Claude (planning, judgment calls, code review) with Claude Code (implementation) against a real repo.

**This is an educational research project, not investment advice.** Every result below is either a backtest against historical data or a paper-trading simulation — no real capital is or has been at risk. Decisions about risking real capital are not automated by anything in this repo.

## What this actually demonstrates

Not "an AI that trades." The interesting part is the *process*: a disciplined hypothesis pipeline with real gates, a small local model doing implementation work under tight, explicit guardrails, and — critically — real bugs that got caught by independent verification rather than trusted self-reports. `research/lessons_learned.md` and `CLAUDE.md` §10 document those incidents directly, including ones that briefly broke the pipeline (an unverified environment-variable "fix," a test suite that never called the function it claimed to test, a rebalancing bug that inflated trade counts 9x). Keeping that record is the point, not a footnote — the killed assumptions and caught bugs are as much the result as the Sharpe ratios below.

## Current strategy status

| Strategy | Universe | Gate 1 (in-sample) | Gate 2 (out-of-sample) | Status |
|---|---|---|---|---|
| `sma_crossover_sp500top50` | Top 50 S&P 500 by market cap | **Sharpe 1.32**, max DD 17.7% (T=200, 2022-01-01 to 2026-07-31) | Sharpe 0.13 (first checkpoint, 26 trading days — too short to be conclusive; see caveats) | Testing OOS — accumulating daily |

Full detail, all four swept windows, and every caveat (multiple-testing inflation, unmodeled borrow cost, a real methodology gap in how the OOS holdout was scoped) are in [`research/hypothesis_log.csv`](research/hypothesis_log.csv).

**The out-of-sample test extends automatically, one real trading day at a time**, via a scheduled GitHub Action ([`.github/workflows/daily_oos_update.yml`](.github/workflows/daily_oos_update.yml)) that appends to `research/sma_crossover_sp500top50/oos_ledger.csv` (created on the workflow's first run — not present in the repo until then). This is a backtest re-scored against real data as it arrives — not live broker paper trading (no Alpaca integration exists yet; that's separate, later work).

## Repo structure

```
src/
  data/          data loaders (S&P 500 universe, price history) — shared, not per-strategy
  features/      indicators (currently: SMA)
  strategies/     signal + position-sizing logic, one file per strategy
  backtest/       reshape utilities + the vectorbt-based backtest runner
research/
  hypothesis_log.csv     one row per hypothesis, updated at each gate
  lessons_learned.md     process lessons — read alongside CLAUDE.md
  <strategy_id>/          hypothesis, config, and results per strategy
tests/            mirrors src/ — every function in src/ has a real, verified test
CLAUDE.md          persistent rules for the local Claude Code agent
```

## Quickstart

```bash
pip install -r requirements.txt
python -m pytest -v          # 33 tests, all independently verified — see lessons_learned.md for why that phrasing matters here
python research/sma_crossover_sp500top50/run_is_exploration.py 200   # re-run the in-sample backtest for a given SMA window
```

## Methodology

The hypothesis → explore → refine → out-of-sample flowchart and the full division of labor between planning and implementation are documented in `CLAUDE.md`. Every strategy gets its own isolated folder, its own risk/cost config, and its own row in the hypothesis log — killed hypotheses stay in the log, they don't get deleted.
