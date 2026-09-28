"""Download every IVV N-PORT filing (only new ones), save the raw XML, and
print a per-snapshot summary for Project-chat review.

Run from the repo root, venv active, after setting your SEC identity for this
terminal session only (never saved to a file):
    $env:EDGAR_IDENTITY = "Your Name your.email@example.com"
    python -m scripts.fetch_nport_ivv

Writes:
    data/reference/nport_raw/IVV_<accession>.xml   (raw filings, commit them)
    data/reference/nport_raw/IVV_manifest.csv      (one row per filing)
"""

import os
import sys
from pathlib import Path

from src.data.equity_us.nport import (
    fetch_nport_filing_list,
    parse_nport_holdings,
    save_nport_filings,
    select_snapshots,
)

OUT_DIR = Path("data/reference/nport_raw")
FUND = "IVV"


def equity_ids(file_name):
    _, holdings = parse_nport_holdings((OUT_DIR / file_name).read_text(encoding="utf-8"))
    equity = holdings[holdings["asset_category"] == "EC"]
    return equity, set(equity["isin"].dropna())


def main():
    if not os.environ.get("EDGAR_IDENTITY"):
        sys.exit('Set EDGAR_IDENTITY first, e.g.  $env:EDGAR_IDENTITY = "Your Name your.email@example.com"')

    filings = fetch_nport_filing_list(FUND)
    manifest = save_nport_filings(filings, OUT_DIR, FUND)
    manifest.to_csv(OUT_DIR / f"{FUND}_manifest.csv", index=False)
    snapshots = select_snapshots(manifest)

    print(f"Filings saved/checked: {len(manifest)}   Snapshots (one per date): {len(snapshots)}")
    print(f"Holdings dates: {snapshots['rep_pd_date'].min():%Y-%m-%d} to {snapshots['rep_pd_date'].max():%Y-%m-%d}")
    print()
    print("rep_pd_date  form       filed       n_equity  no_isin  no_cusip  sum_pct_equity")
    for row in snapshots.itertuples(index=False):
        equity, _ = equity_ids(row.file_name)
        print(f"{row.rep_pd_date:%Y-%m-%d}   {row.form:<9}  {row.filing_date:%Y-%m-%d}  "
              f"{len(equity):>8}  {int(equity['isin'].isna().sum()):>7}  "
              f"{int(equity['cusip'].isna().sum()):>8}  {equity['pct_value'].sum():>14.2f}")

    print()
    dup_dates = manifest[manifest.duplicated("rep_pd_date", keep=False)]
    if len(dup_dates) == 0:
        print("No amended snapshots.")
    for date, group in dup_dates.groupby("rep_pd_date"):
        group = group.sort_values("filing_date")
        first, last = group.iloc[0], group.iloc[-1]
        _, ids_first = equity_ids(first["file_name"])
        _, ids_last = equity_ids(last["file_name"])
        print(f"Amendment for {date:%Y-%m-%d}: {first['form']} ({first['filing_date']:%Y-%m-%d}) -> "
              f"{last['form']} ({last['filing_date']:%Y-%m-%d}); equity ISINs only in original: "
              f"{len(ids_first - ids_last)}, only in amendment: {len(ids_last - ids_first)}")


if __name__ == "__main__":
    main()
