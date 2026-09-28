import pandas as pd
import pytest
from lxml import etree
from pandas.api import types as ptypes
from src.data.equity_us.nport import parse_nport_holdings

FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="http://www.sec.gov/edgar/nport" xmlns:com="http://www.sec.gov/edgar/common" xmlns:ncom="http://www.sec.gov/edgar/nportcommon">
<headerData><submissionType>NPORT-P</submissionType></headerData>
<formData>
<genInfo><regName>iShares Trust</regName><seriesName>iShares Core S&amp;P 500 ETF</seriesName><seriesId>S000004310</seriesId><repPdEnd>2027-03-31</repPdEnd><repPdDate>2026-06-30</repPdDate></genInfo>
<invstOrSecs>
<invstOrSec><name>Oracle Corp.</name><lei>1Z4GXXU7ZHVWFCD8TV52</lei><title>Oracle Corp.</title><cusip>68389X105</cusip><identifiers><isin value="US68389X1054"/></identifiers><balance>13929497.00000000</balance><units>NS</units><curCd>USD</curCd><valUSD>3420553645.65000000</valUSD><pctVal>0.385141560120</pctVal><payoffProfile>Long</payoffProfile><assetCat>EC</assetCat><issuerCat>CORP</issuerCat><invCountry>US</invCountry></invstOrSec>
<invstOrSec><name>Eaton Corp. plc</name><lei>549300VDIGTMXUNT7H71</lei><title>Eaton Corp. plc</title><cusip>N/A</cusip><identifiers><isin value="IE00B8KQN827"/><other otherDesc="Inhouse AssetID" value="SB8KQN824"/></identifiers><balance>2500000.00000000</balance><units>NS</units><curCd>USD</curCd><valUSD>900000000.00000000</valUSD><pctVal>0.101000000000</pctVal><payoffProfile>Long</payoffProfile><assetCat>EC</assetCat><issuerCat>CORP</issuerCat><invCountry>IE</invCountry></invstOrSec>
<invstOrSec><name>BlackRock Funds III</name><lei>N/A</lei><title>BlackRock Cash Funds: Treasury, SL Agency Shares</title><cusip>066922477</cusip><identifiers><isin value="US0669224778"/></identifiers><balance>1025979283.84000000</balance><units>NS</units><curCd>USD</curCd><valUSD>1025979283.84000000</valUSD><pctVal>0.115521433944</pctVal><payoffProfile>Long</payoffProfile><assetCat>STIV</assetCat><issuerCat>RF</issuerCat><invCountry>US</invCountry></invstOrSec>
<invstOrSec><name>N/A</name><lei>N/A</lei><title>S&amp;P 500 E-Mini Index</title><cusip>N/A</cusip><identifiers><other otherDesc="Inhouse Asset ID" value="ESU6"/></identifiers><balance>200.00000000</balance><units>NC</units><curCd>USD</curCd><valUSD>13915610.94000000</valUSD><pctVal>0.001566845798</pctVal><payoffProfile>N/A</payoffProfile><assetCat>DE</assetCat><issuerCat>OTHER</issuerCat><invCountry>US</invCountry><derivativeInfo><futrDeriv derivCat="FUT"/></derivativeInfo></invstOrSec>
<invstOrSec><name>Hologic, Inc.</name><lei>549300DW2HDK2LFFB779</lei><title>Hologic, Inc., CVR</title><cusip>436CVR021</cusip><identifiers><isin value="US436CVR0216"/></identifiers><balance>100.00000000</balance><units>NS</units><curCd>USD</curCd><valUSD>28433.88000000</valUSD><pctVal>0.000003201548</pctVal><payoffProfile>Long</payoffProfile><assetConditional assetCat="OTHER" desc="Contingent value right"/><issuerCat>CORP</issuerCat><invCountry>US</invCountry></invstOrSec>
</invstOrSecs>
</formData>
</edgarSubmission>"""


def fmt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return v


def as_rows(df):
    return [tuple(fmt(v) for v in row) for row in df.itertuples(index=False)]


def test_meta():
    meta, _ = parse_nport_holdings(FIXTURE)
    assert meta == {
        "rep_pd_date": pd.Timestamp("2026-06-30"),
        "series_id": "S000004310",
        "series_name": "iShares Core S&P 500 ETF",
    }


def test_holdings_rows():
    _, holdings = parse_nport_holdings(FIXTURE)
    assert list(holdings.columns) == ["name", "title", "cusip", "isin", "asset_category", "balance",
                                      "units", "value_usd", "pct_value", "is_derivative"]
    assert as_rows(holdings) == [
        ("Oracle Corp.", "Oracle Corp.", "68389X105", "US68389X1054", "EC", 13929497.0, "NS", 3420553645.65, 0.38514156012, False),
        ("Eaton Corp. plc", "Eaton Corp. plc", None, "IE00B8KQN827", "EC", 2500000.0, "NS", 900000000.0, 0.101, False),
        ("BlackRock Funds III", "BlackRock Cash Funds: Treasury, SL Agency Shares", "066922477", "US0669224778", "STIV", 1025979283.84, "NS", 1025979283.84, 0.115521433944, False),
        ("N/A", "S&P 500 E-Mini Index", None, None, "DE", 200.0, "NC", 13915610.94, 0.001566845798, True),
        ("Hologic, Inc.", "Hologic, Inc., CVR", "436CVR021", "US436CVR0216", "OTHER", 100.0, "NS", 28433.88, 0.000003201548, False),
    ]


def test_dtypes():
    _, holdings = parse_nport_holdings(FIXTURE)
    assert ptypes.is_float_dtype(holdings["value_usd"])
    assert ptypes.is_float_dtype(holdings["pct_value"])
    assert ptypes.is_bool_dtype(holdings["is_derivative"])


def test_missing_rep_pd_date_raises():
    with pytest.raises(ValueError):
        parse_nport_holdings(FIXTURE.replace("<repPdDate>2026-06-30</repPdDate>", ""))


def test_no_positions_raises():
    start = FIXTURE.index("<invstOrSecs>")
    end = FIXTURE.index("</invstOrSecs>") + len("</invstOrSecs>")
    with pytest.raises(ValueError):
        parse_nport_holdings(FIXTURE[:start] + FIXTURE[end:])


def test_equity_without_any_identifier_raises():
    bad = FIXTURE.replace('<identifiers><isin value="IE00B8KQN827"/>', "<identifiers>")
    with pytest.raises(ValueError):
        parse_nport_holdings(bad)


def test_equity_without_value_raises():
    with pytest.raises(ValueError):
        parse_nport_holdings(FIXTURE.replace("<valUSD>3420553645.65000000</valUSD>", ""))


def test_invalid_xml_raises():
    with pytest.raises(etree.XMLSyntaxError):
        parse_nport_holdings("<edgarSubmission><unclosed>")
