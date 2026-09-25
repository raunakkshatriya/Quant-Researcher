# Hypothesis Backlog

Seeded 2026-09-09 from the job-market scan (`claude/job_market_strategy_scan_2026-09.md`
in the Claude Project, also published as an artifact — see the Project chat
for the link) — see `quant-project-clarifications.md` §9 for the
methodology decisions made alongside this seeding.

## In progress
- `sma_crossover_sp500top50` (Stage A) — implemented 2026-09-09, IS backtest not yet run locally. See `research/sma_crossover_sp500top50/`.

## Queued, in the job-market scan's priority order
- [ ] Cross-sectional equity momentum / factor ranking — extends the SMA-crossover work; matches the most-requested skill across postings.
- [ ] Statistical arbitrage / cointegrated pairs — abstraction already specced in `quant-project-clarifications.md` §Q16 (cointegration test, spread z-score, pair-as-one-position ledger).
- [ ] Sector rotation / relative strength — grouping layer over the momentum signal; needs the pivoted (date × ticker) view per `PROJECT_INSTRUCTIONS.md`.
- [ ] Commodities & cross-asset trend-following / risk parity — direct match to a live Neuberger Berman posting found in the scan; needs continuous-futures roll handling (open question, not yet resolved).
- [ ] FX systematic macro (carry / momentum) — reuses the FX-rate utility already scoped in `quant-project-clarifications.md` §Q17/§Q19.
- [ ] Execution research: VWAP/TWAP & slippage signals — closest match to the AmplifyME project already on the CV; needs intraday data (Alpaca free tier or a daily-bar proxy as a first cut).
- [ ] News / alternative-data sentiment signal — the free-data rebuild of the original Twitter-sentiment doc (RSS/yfinance news/Reddit API in place of the dead Twitter API).
- [ ] Lightweight crypto systematic (BTC/ETH momentum) — optional, only if also targeting crypto-native firms.

## Deferred by design
- [ ] Equity volatility relative value (autocallables / vol surface) — no free historical options data identified; theory worth knowing for interviews, not a near-term build. See scan artifact for detail. **Update 2026-09-12 (Quantpedia survey):** the specific autocallable/vol-surface version stays deferred, but Quantpedia's "Exploiting Term Structure of VIX Futures" strategy doesn't need an options chain at all — it trades the VIX futures curve, approximable with free `yfinance` data on VXX/SVXY/UVXY (imperfect proxies for the futures curve itself, a caveat to resolve before scoping). Worth reconsidering as a *different*, buildable vol strategy under this same item when its turn comes, rather than staying deferred outright — see `claude/quantpedia_additions_2026-09.md` in the Project.

## In progress (older items, from the original four source documents, still queued)
- [ ] Equal-weight rebalancing vs. cap-weight concentration risk — source: original "Algorithmic Trading" doc
- [ ] Value composite from EDGAR fundamentals, 6-month horizon — source: original "Algorithmic Trading" doc. Quantpedia's own "Best Performing Value Strategies" series is a good reference to pull from when this gets scoped — not a new backlog item, this one's already queued.
- [ ] K-Means regime clustering — source: original "Algorithmic Trading with ML" doc

## Queued, from Quantpedia survey (2026-09-12) — after all of the above

Cross-checked against every item above (both the job-market-scan queue and the older items) to avoid duplicates — see `claude/quantpedia_additions_2026-09.md` in the Project for the full dedup reasoning and citations. These four are additions, not restatements: each is mechanically distinct from everything already queued.

- [ ] Betting-against-beta / low-volatility factor (equities) — long low-beta, short high-beta, a well-documented anomaly distinct from momentum, value, or sector rotation. No new data source: rolling beta/volatility from the existing `yfinance` price history is enough.
- [ ] Short-term reversal (equities and/or futures) — short-horizon mean reversion, the mechanical opposite of the momentum hypothesis already queued. Flag at scoping time: if run on the same universe/timeframe as cross-sectional momentum, check the two signals' correlation before running both live — that's the correlated-risk review the methodology already reserves for the Project chat, not a reason to skip either one.
- [ ] Turn-of-the-month / calendar seasonality effects (equities, sector ETFs) — the simplest of this batch to build: no new data source, no new infrastructure, just a calendar-conditioned long/flat signal on data we already pull.
- [ ] Post-earnings announcement drift (PEAD) — well-documented, 50+ years of research behind it. Real data-feasibility caveat, flag before scoping: the textbook version needs analyst consensus EPS estimates to compute the earnings "surprise," which free EDGAR data alone doesn't provide. A scoping decision is needed on whether to proxy surprise from YoY reported-EPS change instead (a real but different, weaker version of the effect) before this becomes a handoff.

Not added (already covered by an existing item, see dedup reasoning in the Project doc): FX carry trade, asset-class trend-following / time-series momentum, sector or multi-asset momentum rotation, value composites. Considered and deliberately left out for now (too fresh / not yet proven, or no asset class currently in scope): a bond/rates momentum-and-carry genre — worth a dedicated look only if this project ever adds fixed income to its asset mix.

## Killed
(move items here with the phase they were killed at and why — this list is as valuable on the GitHub showcase as anything that survived)
