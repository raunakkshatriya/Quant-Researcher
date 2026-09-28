"""ONE-OFF EXPLORATION — not pipeline code, no tests, safe to delete later.

Purpose: look at the REAL structure of iShares Core S&P 500 ETF (IVV) N-PORT
filings on SEC EDGAR before any parser is written (lessons_learned 2026-09-28:
verify structure against raw data, not a rendering).

Before running (PowerShell, venv active, repo root):
    $env:EDGAR_IDENTITY = "Your Name your.email@example.com"
    python -m scripts.explore_nport_ivv

The identity is sent to the SEC as the User-Agent (SEC fair-access policy).
It lives only in this terminal session — it is never written to any file.

Writes one raw filing to data/reference/nport_raw/ and prints a summary.
"""

import os
import sys
from collections import Counter
from pathlib import Path

from lxml import etree


def strip_namespaces(root):
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def summarize_nport_xml(xml_text):
    """Return a dict describing one N-PORT XML document. Pure, no network."""
    root = strip_namespaces(etree.fromstring(xml_text.encode("utf-8")))
    gen = root.find(".//genInfo")
    rows = []
    for inv in root.iter("invstOrSec"):
        asset_cond = inv.find("assetConditional")
        asset_cat = asset_cond.get("assetCat") if asset_cond is not None else inv.findtext("assetCat")
        ticker_el = inv.find("identifiers/ticker")
        isin_el = inv.find("identifiers/isin")
        rows.append({
            "name": inv.findtext("name"),
            "title": inv.findtext("title"),
            "cusip": inv.findtext("cusip"),
            "ticker": ticker_el.get("value") if ticker_el is not None else None,
            "isin": isin_el.get("value") if isin_el is not None else None,
            "assetCat": asset_cat,
            "valUSD": inv.findtext("valUSD"),
            "pctVal": inv.findtext("pctVal"),
            "has_derivativeInfo": inv.find("derivativeInfo") is not None,
        })
    return {
        "seriesName": gen.findtext("seriesName") if gen is not None else None,
        "seriesId": gen.findtext("seriesId") if gen is not None else None,
        "repPdEnd": gen.findtext("repPdEnd") if gen is not None else None,
        "repPdDate": gen.findtext("repPdDate") if gen is not None else None,
        "n_positions": len(rows),
        "asset_categories": Counter(r["assetCat"] for r in rows),
        "n_missing_ticker": sum(1 for r in rows if not r["ticker"]),
        "n_missing_cusip": sum(1 for r in rows if not r["cusip"] or r["cusip"] in ("000000000", "N/A")),
        "n_derivatives": sum(1 for r in rows if r["has_derivativeInfo"]),
        "sample": rows[:5],
        "non_EC_rows": [r for r in rows if r["assetCat"] != "EC"][:10],
        "top_level_tags_of_first_position": (
            [c.tag for c in next(root.iter("invstOrSec"))] if rows else []
        ),
    }


def main():
    if not os.environ.get("EDGAR_IDENTITY"):
        sys.exit('Set EDGAR_IDENTITY first, e.g.  $env:EDGAR_IDENTITY = "Your Name your.email@example.com"')

    from edgar import Fund

    fund = Fund("IVV")
    print("Fund object:", repr(fund))
    filings = fund.get_filings(series_only=True, form="NPORT-P")
    print(f"NPORT-P filings found for this series: {len(filings)}")
    if len(filings) == 0:
        sys.exit("No filings found — paste this output back to the Project chat.")

    index_df = filings.to_pandas()
    print("Filing index columns:", index_df.columns.tolist())
    print(index_df.to_string(max_rows=80))

    latest = filings[0]
    print(f"\nLatest filing: form={latest.form} filed={latest.filing_date} accession={latest.accession_no}")
    xml_text = latest.xml()
    if not xml_text:
        sys.exit("Latest filing returned no XML — paste this output back.")

    out_dir = Path("data/reference/nport_raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"IVV_{latest.accession_no}.xml"
    out_path.write_text(xml_text, encoding="utf-8")
    print(f"Saved raw XML: {out_path}  ({len(xml_text):,} characters)")

    s = summarize_nport_xml(xml_text)
    print("\n--- Summary of latest filing ---")
    for key in ["seriesName", "seriesId", "repPdEnd", "repPdDate", "n_positions",
                "n_missing_ticker", "n_missing_cusip", "n_derivatives"]:
        print(f"{key}: {s[key]}")
    print("asset categories:", dict(s["asset_categories"]))
    print("tags inside first position:", s["top_level_tags_of_first_position"])
    print("\nFirst 5 positions:")
    for r in s["sample"]:
        print("  ", r)
    print("\nUp to 10 positions that are NOT common equity (assetCat != EC):")
    for r in s["non_EC_rows"]:
        print("  ", r)


if __name__ == "__main__":
    main()
