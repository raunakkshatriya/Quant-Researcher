# Hypothesis: SMA(T) Price-Crossover, S&P 500 Top 50 by Market Cap

**Source:** Kakushadze & Serur (2018), *151 Trading Strategies*, Sec 3.11
("Single moving average")

## Signal
For each stock independently: compute a T-day simple moving average of
closing price. Go long (or cover short) when price > SMA(T); go short
(or cover long) when price < SMA(T). No cross-sectional interaction
between stocks — 50 independent single-stock signals, aggregated into
one equal-weighted portfolio.

## In-sample design
- T swept over {20, 50, 100, 200} trading days
- Direction: long/short (both legs) as primary variant
- Position sizing: equal-weight, ~2% target per name, rebalanced on
  signal flips only

## Universe
Top 50 S&P 500 constituents by market capitalization, one-time
snapshot (date stamped when Task 2 runs). Survivorship-biased by
construction — today's top 50, not the top 50 as of backtest start.
Flagged, not fixed, for Phase 1; revisit before Phase 2 if it looks
like it's inflating results.

## What would kill this hypothesis
- In-sample Sharpe doesn't clear the Gate 1 bar after realistic costs
- Result is driven by 1-2 names rather than broad-based across the 50
- Result is fully explained by market beta rather than the crossover
  signal itself

## Status
Freshly proposed 2026-09-07 (superseding a prior attempt at this same
hypothesis, reset — see project chat history for why).
