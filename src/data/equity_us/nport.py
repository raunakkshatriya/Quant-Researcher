"""Read SEC Form N-PORT filings of an S&P 500 index fund (IVV) into clean tables.

Primary source for point-in-time S&P 500 membership (CLAUDE.md §3, decided
2026-09-28). Parts:
- parse_nport_holdings(): pure — one N-PORT XML string -> (meta, holdings).
- save_nport_filings() / select_snapshots(): file saving + one-snapshot-per-date.
- fetch_nport_filing_list(): network (edgartools), thin wrapper.
"""

from pathlib import Path

import pandas as pd
from lxml import etree

_MISSING_CUSIPS = {"N/A", "000000000"}


def _strip_namespaces(root):
    for el in root.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return root


def _text(el, path):
    if el is None:
        return None
    value = el.findtext(path)
    if value is None:
        return None
    value = value.strip()
    return value if value != "" else None


def _float_or_none(value):
    return None if value is None else float(value)


def parse_nport_holdings(xml_text):
    """Parse one N-PORT (NPORT-P or NPORT-P/A) XML document.

    Pure function: no network, no file I/O, no datetime.now().

    Input:
        xml_text: str, the full XML of one filing (UTF-8 text).

    Returns (meta, holdings):
        meta: dict with keys rep_pd_date (pd.Timestamp, the holdings date),
            series_id (str or None), series_name (str or None).
        holdings: DataFrame, one row per position, in file order, RangeIndex.
            Columns: name (str), title (str or missing), cusip (str or
            missing; "N/A"/"000000000" become missing), isin (str or missing),
            asset_category (str, e.g. "EC" = common equity, "STIV" = cash
            fund, "DE" = derivative), balance (float), units (str),
            value_usd (float), pct_value (float, PERCENT of net assets, so
            0.385 means 0.385%), is_derivative (bool).
            Every position is kept — filtering to common equity is the
            caller's job, so nothing is dropped silently here.

    Raises ValueError if repPdDate is missing, the file has no positions, a
    position has no asset category, or a common-equity (EC) position has no
    name, no value_usd, or neither an ISIN nor a CUSIP.
    """
    root = _strip_namespaces(etree.fromstring(xml_text.encode("utf-8")))
    gen = root.find(".//genInfo")
    rep_pd_date = _text(gen, "repPdDate")
    if rep_pd_date is None:
        raise ValueError("N-PORT file has no genInfo/repPdDate")
    meta = {
        "rep_pd_date": pd.Timestamp(rep_pd_date),
        "series_id": _text(gen, "seriesId"),
        "series_name": _text(gen, "seriesName"),
    }

    rows = []
    for inv in root.iter("invstOrSec"):
        asset_cond = inv.find("assetConditional")
        if asset_cond is not None:
            asset_category = asset_cond.get("assetCat")
        else:
            asset_category = _text(inv, "assetCat")
        if asset_category is None:
            raise ValueError(f"position {_text(inv, 'name')!r} has no asset category")
        cusip = _text(inv, "cusip")
        if cusip in _MISSING_CUSIPS:
            cusip = None
        isin_el = inv.find("identifiers/isin")
        isin = isin_el.get("value") if isin_el is not None else None
        if isin is not None and isin.strip() == "":
            isin = None
        rows.append({
            "name": _text(inv, "name"),
            "title": _text(inv, "title"),
            "cusip": cusip,
            "isin": isin,
            "asset_category": asset_category,
            "balance": _float_or_none(_text(inv, "balance")),
            "units": _text(inv, "units"),
            "value_usd": _float_or_none(_text(inv, "valUSD")),
            "pct_value": _float_or_none(_text(inv, "pctVal")),
            "is_derivative": inv.find("derivativeInfo") is not None,
        })
    if len(rows) == 0:
        raise ValueError("N-PORT file has no invstOrSec positions")

    holdings = pd.DataFrame(rows, columns=[
        "name", "title", "cusip", "isin", "asset_category", "balance",
        "units", "value_usd", "pct_value", "is_derivative",
    ])
    holdings["is_derivative"] = holdings["is_derivative"].astype(bool)

    equity = holdings[holdings["asset_category"] == "EC"]
    if equity["name"].isna().any():
        raise ValueError("a common-equity position has no name")
    if equity["value_usd"].isna().any():
        raise ValueError("a common-equity position has no valUSD")
    if (equity["isin"].isna() & equity["cusip"].isna()).any():
        raise ValueError("a common-equity position has neither an ISIN nor a CUSIP")

    return meta, holdings


MANIFEST_COLUMNS = ["accession_no", "form", "filing_date", "rep_pd_date",
                    "file_name", "n_positions", "n_equity"]


def save_nport_filings(filings, out_dir, prefix):
    """Save each filing's raw XML under out_dir and return a manifest.

    Files are named f"{prefix}_{accession_no}.xml". A file that already exists
    is read from disk and NOT downloaded again, so re-running only fetches new
    filings. Every saved file is parsed once to record its holdings date.

    Inputs:
        filings: iterable of objects with attributes form, filing_date,
            accession_no and a method xml() returning the XML text (e.g. the
            edgartools Filings object from fetch_nport_filing_list()).
        out_dir: str or Path; created if missing.
        prefix: str, e.g. "IVV".

    Returns a DataFrame with columns accession_no (str), form (str),
    filing_date (datetime64[ns]), rep_pd_date (datetime64[ns]), file_name
    (str), n_positions (int), n_equity (int, rows with asset_category "EC").
    Sorted by (rep_pd_date, filing_date), RangeIndex.

    Raises ValueError if a filing returns no XML or the same accession number
    appears twice.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    for filing in filings:
        accession_no = str(filing.accession_no)
        if accession_no in seen:
            raise ValueError(f"accession number {accession_no} appears twice")
        seen.add(accession_no)
        path = out_dir / f"{prefix}_{accession_no}.xml"
        if path.exists():
            xml_text = path.read_text(encoding="utf-8")
        else:
            xml_text = filing.xml()
            if not xml_text:
                raise ValueError(f"filing {accession_no} returned no XML")
            path.write_text(xml_text, encoding="utf-8")
        meta, holdings = parse_nport_holdings(xml_text)
        rows.append({
            "accession_no": accession_no,
            "form": str(filing.form),
            "filing_date": pd.Timestamp(str(filing.filing_date)),
            "rep_pd_date": meta["rep_pd_date"],
            "file_name": path.name,
            "n_positions": len(holdings),
            "n_equity": int((holdings["asset_category"] == "EC").sum()),
        })
    manifest = pd.DataFrame(rows, columns=MANIFEST_COLUMNS)
    manifest["filing_date"] = pd.to_datetime(manifest["filing_date"]).astype("datetime64[ns]")
    manifest["rep_pd_date"] = pd.to_datetime(manifest["rep_pd_date"]).astype("datetime64[ns]")
    manifest["n_positions"] = manifest["n_positions"].astype(int)
    manifest["n_equity"] = manifest["n_equity"].astype(int)
    return manifest.sort_values(["rep_pd_date", "filing_date"]).reset_index(drop=True)


def select_snapshots(manifest):
    """Keep one filing per holdings date: the latest-filed one.

    An amendment (NPORT-P/A) is filed after the original, so it wins.
    Pure function. Input and output have the MANIFEST_COLUMNS schema; output
    is sorted by rep_pd_date with RangeIndex.

    Raises ValueError if a column is missing, or two filings share both the
    same rep_pd_date and the same filing_date (can't tell which is newer).
    """
    for col in MANIFEST_COLUMNS:
        if col not in manifest.columns:
            raise ValueError(f"manifest is missing column {col!r}")
    if manifest.duplicated(["rep_pd_date", "filing_date"]).any():
        raise ValueError("two filings share the same rep_pd_date and filing_date")
    ordered = manifest.sort_values(["rep_pd_date", "filing_date"])
    latest = ordered.drop_duplicates("rep_pd_date", keep="last")
    return latest.reset_index(drop=True)


def fetch_nport_filing_list(fund_ticker):
    """Return the edgartools Filings list of NPORT-P (and NPORT-P/A) filings
    for one fund series, e.g. fund_ticker="IVV".

    Network call (SEC EDGAR) — needs the EDGAR_IDENTITY environment variable.
    Thin wrapper, not unit-tested; save_nport_filings() is tested with fakes.
    """
    from edgar import Fund

    return Fund(fund_ticker).get_filings(series_only=True, form="NPORT-P")
