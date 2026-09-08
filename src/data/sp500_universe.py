"""
S&P 500 top-50 universe snapshot builder.

Builds a static one-time snapshot of the S&P 500's top 50 companies by market cap.
This snapshot serves as the initial universe for strategy backtesting and paper trading.
"""

import pandas as pd
from pathlib import Path
from datetime import date

# Snapshot date - this is today, 2026-09-08 (per CLAUDE.md)
SNAPSHOT_DATE = "2026-09-08"

# Cache directory for raw CSV data
CACHE_DIR = Path("src/data/.cache")


def _fetch_constituents_csv() -> pd.DataFrame:
    """Fetch S&P 500 constituents financials CSV from public source.

    The CSV may contain rows with null/missing Market Cap values due to
    Yahoo Finance not reporting a value for some companies. These are dropped
    before ranking.

    Returns:
        pd.DataFrame with columns: Symbol, Name, Sector, Market Cap

    Raises:
        FileNotFoundError: If cache file doesn't exist and network fetch fails.
        Exception: On any other error fetching data.
    """
    url = (
        "https://raw.githubusercontent.com/datasets/s-and-p-500-"
        "companies-financials/main/data/constituents-financials.csv"
    )

    cache_path = CACHE_DIR / "sp500_financials_raw.csv"

    if not cache_path.exists():
        df = pd.read_csv(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)
    else:
        df = pd.read_csv(cache_path)

    return df


def build_sp500_top50_snapshot() -> pd.DataFrame:
    """Build and save the S&P 500 top-50 universe snapshot.

    Fetches a public S&P 500 constituents CSV, filters out rows with
    missing market cap values, ranks by market cap descending, and
    returns the top 50 companies. Also saves the result to a CSV file.

    Returns:
        pd.DataFrame: Exactly 50 rows, sorted by market_cap_usd descending,
            columns: ticker, company_name, sector, market_cap_usd, snapshot_date

    Raises:
        Exception: On any error during fetching or processing.
    """
    # Fetch the raw CSV data (using cache if available)
    df_raw = _fetch_constituents_csv()

    # Drop rows with null/missing Market Cap values
    df_clean = df_raw.dropna(subset=["Market Cap"])

    # Extract ticker - clean by replacing "." with "-" for yfinance compatibility
    # e.g., "BRK.B" -> "BRK-B", "AAPL.O" -> "AAPL-O" (though yfinance uses just symbol)
    df_clean["ticker"] = df_clean["Symbol"].str.replace(r"\.", "-", regex=True)

    # Extract market cap - convert to numeric, handling any currency symbols if present
    market_cap_str = df_clean["Market Cap"].astype(str).str.strip("$")
    df_clean["market_cap_usd"] = pd.to_numeric(market_cap_str, errors="coerce")

    # Drop any remaining rows that failed to convert to numeric (edge case)
    df_clean = df_clean.dropna(subset=["market_cap_usd"])

    # Sort by market cap descending and take top 50
    df_top50 = df_clean.nlargest(50, "market_cap_usd")

    # Select and rename columns to match expected output schema
    result = df_top50[["Symbol", "Name", "Sector", "Market Cap"]].copy()
    result = result.rename(columns={
        "Symbol": "ticker",
        "Name": "company_name",
        "Sector": "sector",
        "Market Cap": "market_cap_usd"
    })
    # Add snapshot_date column with ISO format (today's date for all rows)
    result["snapshot_date"] = SNAPSHOT_DATE

    # Ensure exactly 50 rows
    assert len(result) == 50, f"Expected 50 rows, got {len(result)}"

    # Verify sorted descending by market_cap_usd
    assert result["market_cap_usd"].is_monotonic_decreasing, \
        "Results should be sorted by market_cap_usd descending"

    # Ensure no dots in ticker (yfinance-compatible)
    for idx, row in result.iterrows():
        assert "." not in str(row["ticker"]), \
            f"Ticker {row['ticker']} contains a literal '.' character"

    # Write to CSV file
    output_path = Path("research/sma_crossover_sp500top50/universe_snapshot.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)

    return result
