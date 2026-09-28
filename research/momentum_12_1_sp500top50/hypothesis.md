# momentum_12_1_sp500top50 — cross-sectional 12-1 momentum, same 50 stocks as the SMA baseline

Proposed 2026-09-28. Stage A (paper-faithful) per `quant-project-clarifications.md` §9.2.
`n_hypotheses_tested_before_this` = 1.

## Economic rationale
Stocks with the highest returns over the past 3–12 months tend to keep
outperforming the weakest ones over the following months (Jegadeesh & Titman,
1993; replicated across decades and markets). The usual explanation is
behavioural: investors under-react to news, then pile in. The most recent
month is skipped because over one month prices tend to reverse instead.

## What is tested
At each month-end, rank the stocks in
`research/sma_crossover_sp500top50/universe_snapshot.csv` — the same 50 the SMA
baseline trades, unchanged until the user says otherwise — by their return from
12 months ago to 1 month ago. Long the top decile (5 stocks), short the bottom
decile (5 stocks), +10% / −10% each (100% gross, dollar-neutral), hold one
month, repeat. Prices: `adj_close` (dividends included).

## Split, fixed before any backtest
- In-sample: 2016-01-01 → 2023-12-31. The paper's own grid J ∈ {3, 6, 9, 12}
  months is swept here only (4 settings — multiple testing is counted).
- Historical holdout: 2024-01-01 → 2026-07-31, untouched until gate 2.
- Forward OOS: from 2026-08-01, extended daily by
  `.github/workflows/daily_oos_update_momentum.yml` with J = 12 (the
  pre-registered primary setting), exactly like the SMA's daily ledger.

## Known limitations, stated plainly
- **Universe chosen with hindsight.** The 50 stocks are the largest on
  2026-09-08. Backtest years before that use companies known to have become
  the biggest — survivorship bias, which flatters in-sample and holdout
  results. The daily forward ledger is the unbiased part. (Same caveat as the
  SMA baseline; kept deliberately so the two are compared on the same stocks.)
- **Universe differs from the paper**, which used all NYSE/AMEX stocks.
- Signal and trade both use the month-end close (same convention as the SMA
  pipeline) — slightly optimistic; the one-month skip limits the effect.
- Costs: 5 bps slippage per trade (runner default). Short borrow cost is not
  yet modelled in the engine — recorded in `risk_and_costs.yaml`, to be added
  before gate 2.

## What would count as support at gate 1
- Long-short return positive over the in-sample period, not driven by one year.
- Sharpe clearly above zero for J = 12, and the J grid not showing one
  isolated good number (4 settings were tried).
Gate decisions are made in the Project chat, not by a threshold in code.

## Correlated risk
Same stocks as the SMA baseline, and both are trend-following — overlap is
likely, especially in semiconductors. The two ledgers are compared at every
review before either goes to paper trading.
