# Handoff — equity_us_shared — 3d: snapshot script (write only, do not run)

## Objective
Create a small script that downloads the Wikipedia page once, saves the raw HTML to data/reference/, parses it, runs reconstruct_membership, and prints a summary for review. Write it only; the user runs it.

## Allowed files
- scripts/fetch_sp500_snapshot.py   (create; create the scripts/ folder if it does not exist. Do NOT create scripts/__init__.py)
Nothing else. No scratch or debug scripts.

## Budget rules for this session
- Transcribe the code below exactly.
- Do NOT run the script (it makes a real network request and needs the user's contact details in USER_AGENT first).
- The only command you run is the import check at the end. If it fails, you may make ONE fix; if it still fails, write the error in the self-check and stop.

## File content — write exactly this

```python
"""Download today's Wikipedia S&P 500 page, save it, and print a review summary.

Run from the repo root:
    python -m scripts.fetch_sp500_snapshot

Writes:
    data/reference/sp500_wikipedia_<YYYY-MM-DD>.html   (raw page, commit it)
    data/reference/sp500_anomalies_<YYYY-MM-DD>.csv    (for Project-chat review)
"""

from datetime import date
from pathlib import Path

import pandas as pd

from src.data.equity_us.sp500_membership import reconstruct_membership
from src.data.equity_us.sp500_wikipedia import (
    USER_AGENT,
    fetch_sp500_wikipedia_html,
    parse_sp500_wikipedia_html,
)

RECONSTRUCT_START = pd.Timestamp("2015-01-01")


def main():
    today = pd.Timestamp(date.today())
    out_dir = Path("data/reference")
    out_dir.mkdir(parents=True, exist_ok=True)

    html = fetch_sp500_wikipedia_html(USER_AGENT)
    html_path = out_dir / f"sp500_wikipedia_{today:%Y-%m-%d}.html"
    html_path.write_text(html, encoding="utf-8")

    current, changes = parse_sp500_wikipedia_html(html)
    membership, anomalies = reconstruct_membership(
        current[["ticker"]],
        changes[["date", "added_ticker", "removed_ticker"]],
        today,
        RECONSTRUCT_START,
    )
    anomalies_path = out_dir / f"sp500_anomalies_{today:%Y-%m-%d}.csv"
    anomalies.to_csv(anomalies_path, index=False)

    in_window = changes[changes["date"] >= RECONSTRUCT_START]
    print(f"Saved raw HTML:            {html_path}")
    print(f"Current constituents:      {len(current)}")
    print(f"Change rows (all):         {len(changes)}  ({changes['date'].min():%Y-%m-%d} to {changes['date'].max():%Y-%m-%d})")
    print(f"Change rows since {RECONSTRUCT_START:%Y-%m-%d}: {len(in_window)}")
    print(f"Membership intervals:      {len(membership)}")
    print(f"Anomalies since {RECONSTRUCT_START:%Y-%m-%d}:   {len(anomalies)}  (saved to {anomalies_path})")
    print()
    with pd.option_context("display.max_rows", None, "display.width", 200):
        print(anomalies.to_string())


if __name__ == "__main__":
    main()
```

## Done so far
sp500_wikipedia.py has parse + fetch with 11 tests; 38 tests passing.

## This session's task
Create the file. Then run exactly this one command from the repo root and nothing else:
    python -c "import scripts.fetch_sp500_snapshot; print('import ok')"
Fill in the self-check and stop.

## Resume point
If out of budget: the next session finishes transcribing the file.

## Session self-check
(fill in before finishing, per CLAUDE.md §7)
