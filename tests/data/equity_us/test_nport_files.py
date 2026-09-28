import pandas as pd
import pytest
from src.data.equity_us.nport import save_nport_filings, select_snapshots

MINI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport"><formData>
<genInfo><seriesId>S000004310</seriesId><repPdDate>{date}</repPdDate></genInfo>
<invstOrSecs>
<invstOrSec><name>Oracle Corp.</name><cusip>68389X105</cusip><identifiers><isin value="US68389X1054"/></identifiers><balance>1</balance><units>NS</units><valUSD>100</valUSD><pctVal>0.5</pctVal><assetCat>EC</assetCat></invstOrSec>
<invstOrSec><name>BlackRock Funds III</name><cusip>066922477</cusip><identifiers><isin value="US0669224778"/></identifiers><balance>1</balance><units>NS</units><valUSD>10</valUSD><pctVal>0.1</pctVal><assetCat>STIV</assetCat></invstOrSec>
</invstOrSecs></formData></edgarSubmission>"""


class FakeFiling:
    def __init__(self, form, filing_date, accession_no, xml_text):
        self.form = form
        self.filing_date = filing_date
        self.accession_no = accession_no
        self._xml = xml_text
        self.xml_calls = 0

    def xml(self):
        self.xml_calls += 1
        return self._xml


def fmt(v):
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    return v


def as_rows(df):
    return [tuple(fmt(v) for v in row) for row in df.itertuples(index=False)]


def make_filings():
    return [
        FakeFiling("NPORT-P", "2026-05-28", "0002071691-26-012459", MINI_XML.format(date="2026-03-31")),
        FakeFiling("NPORT-P/A", "2026-07-13", "0002071691-26-015790", MINI_XML.format(date="2026-03-31")),
        FakeFiling("NPORT-P", "2026-02-25", "0002071691-26-004238", MINI_XML.format(date="2025-12-31")),
    ]


def test_save_writes_files_and_manifest(tmp_path):
    manifest = save_nport_filings(make_filings(), tmp_path, "IVV")
    assert list(manifest.columns) == ["accession_no", "form", "filing_date", "rep_pd_date",
                                      "file_name", "n_positions", "n_equity"]
    assert as_rows(manifest) == [
        ("0002071691-26-004238", "NPORT-P", "2026-02-25", "2025-12-31", "IVV_0002071691-26-004238.xml", 2, 1),
        ("0002071691-26-012459", "NPORT-P", "2026-05-28", "2026-03-31", "IVV_0002071691-26-012459.xml", 2, 1),
        ("0002071691-26-015790", "NPORT-P/A", "2026-07-13", "2026-03-31", "IVV_0002071691-26-015790.xml", 2, 1),
    ]
    assert (tmp_path / "IVV_0002071691-26-004238.xml").exists()


def test_existing_file_is_not_downloaded_again(tmp_path):
    save_nport_filings(make_filings(), tmp_path, "IVV")
    second = make_filings()
    save_nport_filings(second, tmp_path, "IVV")
    assert [f.xml_calls for f in second] == [0, 0, 0]


def test_empty_xml_raises(tmp_path):
    bad = [FakeFiling("NPORT-P", "2026-02-25", "0002071691-26-004238", "")]
    with pytest.raises(ValueError):
        save_nport_filings(bad, tmp_path, "IVV")


def test_duplicate_accession_raises(tmp_path):
    f = make_filings()[0]
    with pytest.raises(ValueError):
        save_nport_filings([f, f], tmp_path, "IVV")


def test_select_snapshots_keeps_latest_filed(tmp_path):
    manifest = save_nport_filings(make_filings(), tmp_path, "IVV")
    snapshots = select_snapshots(manifest)
    assert as_rows(snapshots) == [
        ("0002071691-26-004238", "NPORT-P", "2026-02-25", "2025-12-31", "IVV_0002071691-26-004238.xml", 2, 1),
        ("0002071691-26-015790", "NPORT-P/A", "2026-07-13", "2026-03-31", "IVV_0002071691-26-015790.xml", 2, 1),
    ]


def test_select_snapshots_ambiguous_raises(tmp_path):
    manifest = save_nport_filings(make_filings(), tmp_path, "IVV")
    manifest.loc[2, "filing_date"] = manifest.loc[1, "filing_date"]
    with pytest.raises(ValueError):
        select_snapshots(manifest)


def test_select_snapshots_missing_column_raises(tmp_path):
    manifest = save_nport_filings(make_filings(), tmp_path, "IVV")
    with pytest.raises(ValueError):
        select_snapshots(manifest.drop(columns=["rep_pd_date"]))
