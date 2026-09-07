# CLAUDE.md — Persistent Rules for Claude Code

Read this file plus your current `.claude/handoffs/<file>.md` at the start of every session. Nothing else. If a task seems to need more context than these two files provide, stop and say so in the handoff rather than guessing.

## 0. What this repo is

A quant research pipeline: hypothesis → in-sample exploration → out-of-sample validation → automated paper trading → (only on explicit instruction) live-adjacent broker migration. You (Claude Code, running locally on a small model with a 64k session budget) are the implementer. You do not design strategies, judge backtest results, or decide what gets tested next — that reasoning happens in the Claude Project chat and arrives to you as a fully-specified handoff task.

## 1. Data & broker policy — read this before touching any adapter

- **Alpaca is the default for everything during research and development.** All strategy logic, backtesting, and paper trading is built and run against Alpaca (`alpaca-py`) and free data (`yfinance` / OpenBB / `edgartools`) unless a handoff file explicitly says otherwise.
- **Never swap a strategy's data source or execution adapter to IBKR on your own initiative.** IBKR is brought in only for a specific strategy, only after the user has explicitly instructed the migration in a handoff file, and only because that strategy needs a market Alpaca doesn't cover (e.g., UK/LSE names). If a task doesn't say "migrate to IBKR," assume Alpaca.
- Because the strategy interface is broker-agnostic (see §4), migrating a strategy later means swapping one adapter behind the same interface — it should never require touching the strategy's signal logic.

## 2. File format rules

- **Never create a `.ipynb` file.** Use plain `.py` files with cell markers instead:
  - `# %%` starts a new code cell (this is the same convention VS Code's Python extension and Jupytext's "light" format already use — it opens in VS Code's interactive window exactly like a notebook, with none of the JSON-escaping fragility that trips up a small model editing raw `.ipynb` files).
  - `# %% [markdown]` starts a markdown-equivalent cell; put explanatory text as plain comment lines underneath it.
  - Example:
    ```python
    # %% [markdown]
    # ## Load price history and compute 12-1 month momentum

    # %%
    import pandas as pd
    from src.data.loader import DataCache
    ```
- One file per logical unit of work (one data loader, one feature, one strategy, one test file) — never a monolithic script.

## 3. Granularity — you have a 64k-token session and a 4B model, act like it

- **One session = one file, or one function + its test.** Never accept or attempt a handoff that says "build the momentum strategy" as a single task — that's a Project-chat planning failure, flag it rather than trying to do it all.
- Every handoff file states, explicitly: the objective, the exact files you're allowed to touch (§6), what's already done, what's next, and one resume-point line. If a handoff is vague on any of these, stop and ask rather than inferring.
- End every session by: running tests, committing with a descriptive message, running the self-check in §7, and rewriting the handoff file for the next session.

## 4. Data architecture — read carefully before writing any loader or strategy code

This directly determines whether "sync to today's paper-trading date" is a one-line rerun or a rewrite, so don't improvise a different shape per strategy.

- **Canonical storage is one long-format table**, indexed by `(date, ticker)`, stored as Parquet under `src/data/cache/`. Never store one file/dataframe per ticker for anything involving more than one asset (portfolio optimization, pairs, sector rotation) — that's exactly what makes aggregation and incremental updates painful.
- **One shared loader, `src/data/loader.py::DataCache`**, is the only thing allowed to fetch or write to that cache. It: (a) checks what's already cached per ticker, (b) fetches only rows newer than the last stored timestamp, (c) appends and re-saves. Every strategy calls this same loader. Strategy code never writes its own fetch logic — this is what makes "amend with today's new paper-trading price" a call to the same function, not a code change.
- **Multi-asset strategies (portfolio optimization, pairs, sector) work off a pivoted (date × ticker) view derived on the fly from the canonical long table** — never persist the wide/pivoted view separately, or it will drift out of sync with the canonical data.
- **Pairs trading is a distinct abstraction, not a variant of the single-asset strategy interface.** A pair position is tracked as one unit in the ledger (both legs, one `strategy_id`), not two independent single-asset positions.
- **FX rates are a small, shared, read-only utility module** (`src/data/fx.py`), used to normalize any non-USD P&L for reporting. It is a dependency other strategies read from — it never becomes a dependency other strategies write to, and a forex strategy's own hypothesis/backtest/ledger stays in its own folder, isolated like any other strategy.
- Use each exchange's actual trading calendar (`pandas_market_calendars`) for date logic — never a naive `date_range` loop — especially once non-US-market strategies exist.

## 5. Train/test discipline

- `TRAIN_TEST_SPLIT_DATE` is a single named constant in each strategy's config, not a magic number scattered through code.
- In-sample and out-of-sample code paths only ever see data `<= TRAIN_TEST_SPLIT_DATE`. The live/paper-trading code path only ever fetches and acts on data `> TRAIN_TEST_SPLIT_DATE`.
- Every strategy's test suite includes one test whose only job is asserting no training/backtest code path can see a timestamp past the split date. This is a guard rail, not a formality — add it before the first backtest run, not after.

## 6. Strategy isolation

- Every strategy is a self-contained module: its own `backtest_config.yaml`, its own risk/cost config (§8), its own `strategy_id` used to tag every order and every ledger row.
- **Your handoff file lists exactly which file paths you're allowed to touch for this session.** If a task would require editing a file outside that list, stop and flag it — don't "helpfully" fix something adjacent.
- Isolation is about code and capital, not risk visibility: aggregate portfolio-level exposure is reviewed separately, in the Project chat, across all active strategies together (see §8 — isolated code can still stack correlated risk).

## 7. Self-check before marking a task done

Before you write "done" in a handoff, look at your own output the way a careful analyst would before handing off work, not just whether it ran without an error:
- Do the numbers look plausible (no impossible Sharpe ratios, no NaN/inf silently propagating)?
- If you produced a chart or tearsheet, does it look structurally sane (axes, date range, no empty series)?
- Note in the handoff what you checked and what you didn't have time/budget to check. A flagged uncertainty is useful; a silent guess presented as a clean result is not.

## 8. Cost, risk, and the responsibilities a solo quant researcher can't skip

Every backtest and every paper-trading run must account for the following — a "frictionless" backtest is not a result, it's a placeholder:

- **Slippage**: apply a configurable bps-of-price penalty to every simulated fill (§ risk config in `templates.md`). Don't fill at the exact quoted/close price.
- **Commissions & fees**: Alpaca is commission-free on US equities but still carries small regulatory pass-through fees (SEC fee on sells, FINRA TAF) — model them, don't zero them out. IBKR's tiered/per-share commission schedule is a separate config once a strategy migrates there.
- **Borrow cost & availability** for any short leg (pairs, short-biased strategies) — hard-to-borrow names can be expensive or simply unborrowable; a backtest that assumes free, unlimited shorting is not realistic.
- **Position & portfolio risk limits**: max position size as % of capital, max exposure per sector/strategy, max aggregate leverage, and a **kill-switch**: if aggregate drawdown across all active strategies breaches a configured threshold, halt new order submission for everything pending manual review, rather than letting each isolated strategy keep trading independently through a shared bad day.
- **Correlated risk across "isolated" strategies**: isolation (§6) stops code interference, not correlated exposure — five separately-coded strategies that are all quietly long tech at the same time is a portfolio-level risk question, reviewed in the Project chat across the whole active set, not inside any one strategy's code.
- **Corporate actions & survivorship bias**: adjust for splits/dividends; never silently drop delisted tickers from a historical universe — that quietly inflates backtest performance.
- **Data quality**: check for missing bars and stale prices before trusting a signal computed from them.
- **Multiple-testing awareness**: track the total number of hypotheses tested. A strategy that looks great after being the 40th one tried needs a more skeptical read (deflated Sharpe or similar) than the 2nd one tried — log the running count so this is visible, not forgotten.
- **US retail regulatory detail worth knowing before this touches anything beyond paper**: the Pattern Day Trader rule restricts accounts under $25k equity to 3 day trades per rolling 5 business days on margin. Not a code concern today, but a real constraint if a strategy's live-capital version turns out to be day-trading-frequency.

## 9. Adapt without drifting — the "self-learning" boundary

The system is allowed to auto-adjust **parameters** on a fixed schedule via walk-forward re-optimization within pre-declared bounds (e.g., quarterly re-fit of a lookback window, within a min/max range set at hypothesis approval time). It is **not** allowed to silently change a strategy's core rules/logic — any change to what the strategy actually does goes back through the Phase 1 → Phase 2 hypothesis pipeline with an explicit human decision, the same gate that already governs promoting a new hypothesis to active paper trading (never skip this just because the change originated from a scheduled re-fit rather than a new idea).

After every paper-trading review cycle, write a short entry to `research/lessons_learned.md` — what the review found, what (if anything) should change about how future Claude Code sessions approach this type of task. Future sessions read this alongside `CLAUDE.md`. This is how the system gets better over time without ever giving a small local model the authority to rewrite its own trading rules.

## 10. Git conventions

- Commit after every session, message format: `<strategy_id>: <what changed>` (e.g., `momentum_12_1: add feature calculation + unit tests`).
- Never commit API keys/secrets — they live in a local `.env` (gitignored), read via environment variables only.
- The daily paper-trading Action commits its own snapshot with message `paper-trade: <date> <strategy_id> snapshot`.
