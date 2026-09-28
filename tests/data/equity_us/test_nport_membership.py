import pandas as pd
import pytest
from pandas.api import types as ptypes
from src.data.equity_us.nport_membership import load_equity_snapshots, snapshots_to_intervals

XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport"><formData>
<genInfo><seriesId>S000004310</seriesId><repPdDate>{date}</repPdDate></genInfo>
<invstOrSecs>{positions}</invstOrSecs></formData></edgarSubmission>"""

EQUITY = ('<invstOrSec><name>{name}</name><cusip>{cusip}</cusip><identifiers><isin value="{isin}"/></identifiers>'
          '<balance>1</balance><units>NS</units><valUSD>{value}</valUSD><pctVal>{pct}</pctVal><assetCat>EC</assetCat></invstOrSec>')
CASH = ('<invstOrSec><name>BlackRock Funds III</name><cusip>066922477</cusip><identifiers><isin value="US0669224778"/></identifiers>'
        '<balance>1</balance><units>NS</units><valUSD>10</valUSD><pctVal>0.1</pctVal><assetCat>STIV</assetCat></invstOrSec>')


def fmt(v):
    if v is pd.NaT:
        return "NaT"
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return v


def as_rows(df):
    return [tuple(fmt(v) for v in row) for row in df.itertuples(index=False)]


def write_snapshot_files(tmp_path):
    oracle = EQUITY.format(name="Oracle Corp.", cusip="68389X105", isin="US68389X1054", value="300", pct="0.3")
    eaton = EQUITY.format(name="Eaton Corp. plc", cusip="N/A", isin="IE00B8KQN827", value="200", pct="0.2")
    (tmp_path / "IVV_a.xml").write_text(XML.format(date="2025-12-31", positions=oracle + eaton + CASH), encoding="utf-8")
    (tmp_path / "IVV_b.xml").write_text(XML.format(date="2026-03-31", positions=oracle + CASH), encoding="utf-8")
    return pd.DataFrame({
        "rep_pd_date": pd.to_datetime(["2025-12-31", "2026-03-31"]),
        "file_name": ["IVV_a.xml", "IVV_b.xml"],
    })


def make_snapshots(pairs):
    return pd.DataFrame({
        "rep_pd_date": pd.to_datetime([d for d, _ in pairs]),
        "isin": [i for _, i in pairs],
    })


D1, D2, D3, D4 = "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"


# ---------- load_equity_snapshots ----------

def test_load_keeps_equity_only(tmp_path):
    snapshots = write_snapshot_files(tmp_path)
    out = load_equity_snapshots(snapshots, tmp_path)
    assert list(out.columns) == ["rep_pd_date", "isin", "cusip", "name", "value_usd", "pct_value"]
    assert as_rows(out) == [
        ("2025-12-31", "IE00B8KQN827", None, "Eaton Corp. plc", 200.0, 0.2),
        ("2025-12-31", "US68389X1054", "68389X105", "Oracle Corp.", 300.0, 0.3),
        ("2026-03-31", "US68389X1054", "68389X105", "Oracle Corp.", 300.0, 0.3),
    ]


def test_load_date_mismatch_raises(tmp_path):
    snapshots = write_snapshot_files(tmp_path)
    snapshots.loc[1, "rep_pd_date"] = pd.Timestamp("2026-06-30")
    with pytest.raises(ValueError):
        load_equity_snapshots(snapshots, tmp_path)


def test_load_empty_raises(tmp_path):
    empty = pd.DataFrame({"rep_pd_date": pd.to_datetime([]), "file_name": []})
    with pytest.raises(ValueError):
        load_equity_snapshots(empty, tmp_path)


# ---------- snapshots_to_intervals ----------

def test_intervals_all_patterns():
    snaps = make_snapshots([
        (D1, "A"), (D2, "A"), (D3, "A"), (D4, "A"),
        (D1, "B"), (D2, "B"),
        (D2, "C"), (D3, "C"), (D4, "C"),
        (D1, "E"), (D3, "E"), (D4, "E"),
        (D3, "F"),
    ])
    out = snapshots_to_intervals(snaps)
    assert list(out.columns) == ["isin", "date_added", "date_removed", "start_censored"]
    assert as_rows(out) == [
        ("A", D1, "NaT", True),
        ("B", D1, D3, True),
        ("C", D2, "NaT", False),
        ("E", D1, D2, True),
        ("E", D3, "NaT", False),
        ("F", D3, D4, False),
    ]


def test_intervals_unsorted_input_same_result():
    snaps = make_snapshots([(D2, "B"), (D1, "A"), (D1, "B"), (D2, "A")])
    assert as_rows(snapshots_to_intervals(snaps)) == [
        ("A", D1, "NaT", True),
        ("B", D1, "NaT", True),
    ]


def test_intervals_dtypes():
    out = snapshots_to_intervals(make_snapshots([(D1, "A"), (D2, "B")]))
    assert ptypes.is_string_dtype(out["isin"])
    assert ptypes.is_datetime64_any_dtype(out["date_added"])
    assert ptypes.is_datetime64_any_dtype(out["date_removed"])
    assert ptypes.is_bool_dtype(out["start_censored"])


def test_intervals_duplicate_pair_raises():
    with pytest.raises(ValueError):
        snapshots_to_intervals(make_snapshots([(D1, "A"), (D1, "A")]))


def test_intervals_blank_isin_raises():
    with pytest.raises(ValueError):
        snapshots_to_intervals(make_snapshots([(D1, "A"), (D1, "  ")]))


def test_intervals_missing_date_raises():
    snaps = pd.DataFrame({"rep_pd_date": pd.to_datetime([D1, None]), "isin": ["A", "B"]})
    with pytest.raises(ValueError):
        snapshots_to_intervals(snaps)


def test_intervals_empty_raises():
    with pytest.raises(ValueError):
        snapshots_to_intervals(make_snapshots([]))
