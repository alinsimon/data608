
# Assignment 2 – Has the Federal Reserve Fulfilled Its Mandate?
#
# Congress gave the Federal Reserve two main jobs: keep inflation low and keep unemployment low.
# This script helps us see how well they've done over the past 25 years (2001–2026).
#
# We're going to look at three key datasets:
#   1. Consumer Price Index (CPI) - tracks how prices of everyday things change over time
#   2. Unemployment Rate - shows what percentage of people who want jobs can't find them
#   3. Federal Funds Rate - the main interest rate the Fed uses to control the economy
#
# Where we're getting the data from:
#   - CPI & Unemployment: Bureau of Labor Statistics (BLS) API
#     Series IDs: CUUR0000SA0 (CPI), LNS14000000 (Unemployment)
#     Endpoint: https://api.bls.gov/publicAPI/v2/timeseries/data/
#     Files created: data/cpi.csv, data/unemployment_rate.csv
#
#   - Fed Funds Rate: Federal Reserve Economic Data (FRED) API
#     Series ID: FEDFUNDS
#     Endpoint: https://api.stlouisfed.org/fred/series/observations
#     File created: data/fed_funds_rate.csv
#
#   - Combined Dataset: All three datasets merged together
#     File created: data/macro_data.csv



# Important notes:
#   - You'll need free API keys
#   - BLS API only gives us 20 years at a time, so we split into: 2001–2015 and 2016–2026
#   - Once we fetch the data, we save it to CSV files so we don't have to keep calling the APIs
#
# Get your API keys here:
#   BLS:  https://data.bls.gov/registrationEngine/
#   FRED: https://fred.stlouisfed.org/docs/api/api_key.html


import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load our API keys from the .env file (keeps them secure and out of the code)
load_dotenv()

BLS_API_KEY  = os.getenv("BLS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Quick check: do we have our API keys set up?
if not BLS_API_KEY or BLS_API_KEY == "YOUR_BLS_API_KEY_HERE":
    print("⚠️  Heads up: BLS_API_KEY isn't set yet. We can still try unauthenticated requests, "
          "but they're limited to 10-year windows.")
if not FRED_API_KEY or FRED_API_KEY == "YOUR_FRED_API_KEY_HERE":
    raise EnvironmentError(
        "We need the FRED_API_KEY to continue. Please register at "
        "https://fred.stlouisfed.org/docs/api/api_key.html and add it to your .env file"
    )

# Set up our data folder (this is where we'll save all the CSV files)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# We want 25 years of data total
START_YEAR = 2001
END_YEAR   = 2026

# BLS API can only handle 20 years at a time, so we split our requests
BLS_QUERY_WINDOWS = [
    (2001, 2015),   # First 15 years
    (2016, 2026),   # Last 10 years
]

BLS_ENDPOINT  = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
FRED_ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"

# The specific data series we need (these are like catalog numbers for the data)
CPI_SERIES_ID          = "CUUR0000SA0"   # Consumer Price Index for all urban consumers
UNEMPLOYMENT_SERIES_ID = "LNS14000000"   # Civilian unemployment rate
FED_FUNDS_SERIES_ID    = "FEDFUNDS"      # Federal Funds effective rate


# This function talks to the BLS API and gets data for a specific time window
def _bls_single_request(series_ids: list[str],
                        yr_start: int,
                        yr_end: int) -> dict:
    """
    Makes one request to BLS to get data for the years we specify.
    The API needs our key and can only give us up to 20 years at once.
    """
    payload: dict = {
        "seriesid":        series_ids,
        "startyear":       str(yr_start),
        "endyear":         str(yr_end),
        "registrationkey": BLS_API_KEY,
    }
    headers = {"Content-type": "application/json"}

    print(f"  → Requesting data from BLS for {yr_start}–{yr_end}...")
    response = requests.post(
        BLS_ENDPOINT,
        data=json.dumps(payload),
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()

    if result.get("status") != "REQUEST_SUCCEEDED":
        messages = result.get("message", [])
        raise RuntimeError(f"BLS API error ({yr_start}–{yr_end}): {messages}")

    return result


def fetch_bls_series(series_ids: list[str]) -> dict[str, pd.DataFrame]:
    """
    Gets all 25 years of data from BLS (2001-2026) for the series we want.
    
    Since BLS only lets us grab 20 years at a time, we make two separate requests
    and then combine them. Returns a dictionary with a DataFrame for each series.
    """
    all_data: dict[str, list] = {s: [] for s in series_ids}

    for (yr_start, yr_end) in BLS_QUERY_WINDOWS:
        result = _bls_single_request(series_ids, yr_start, yr_end)

        for series in result["Results"]["series"]:
            sid  = series["seriesID"]
            rows = []
            for d in series["data"]:
                if d["period"].startswith("M"):   # we only want monthly data
                    # BLS sometimes returns '-' for missing data, so we need to handle that
                    try:
                        value = float(d["value"])
                        rows.append({
                            "date": pd.Timestamp(
                                f"{d['year']}-{d['period'].replace('M', '').zfill(2)}-01"
                            ),
                            "value": value,
                        })
                    except (ValueError, TypeError):
                        # Skip entries with invalid values like '-'
                        continue
            all_data[sid].extend(rows)

        time.sleep(0.5)   # be nice to the API - don't overwhelm it

    # Now turn all that raw data into nice, clean DataFrames
    dataframes: dict[str, pd.DataFrame] = {}
    for sid, rows in all_data.items():
        df = (
            pd.DataFrame(rows)
            .drop_duplicates(subset="date")
            .sort_values("date")
            .reset_index(drop=True)
        )
        dataframes[sid] = df

    return dataframes


# This function grabs data from the FRED API (for the Fed Funds Rate)
def fetch_fred_series(series_id: str,
                      start_date: str,
                      end_date: str) -> pd.DataFrame:
    """
    Gets Federal Reserve data from FRED for the date range we specify.
    Returns it as a nice DataFrame with dates and values.
    """
    params = {
        "series_id":         series_id,
        "api_key":           FRED_API_KEY,
        "file_type":         "json",
        "frequency":         "m",           # monthly frequency
        "observation_start": start_date,
        "observation_end":   end_date,
    }
    print(f"  → Requesting {series_id} from FRED ({start_date} to {end_date})...")

    response = requests.get(FRED_ENDPOINT, params=params, timeout=30)
    response.raise_for_status()
    result = response.json()

    if "observations" not in result:
        raise RuntimeError(f"FRED API error for {series_id}: {result}")

    df = pd.DataFrame(result["observations"])[["date", "value"]]
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = (
        df.dropna(subset=["value"])
          .sort_values("date")
          .reset_index(drop=True)
    )
    return df


# The main part of our script - this is where everything happens!
def main():
    print("=" * 60)
    print("Assignment 2 – Calling the APIs and preparing our dataset")
    print("=" * 60)

    start_date_str = f"{START_YEAR}-01-01"
    end_date_str   = f"{END_YEAR}-12-31"

    # Where we'll save our data files
    cpi_path = DATA_DIR / "cpi.csv"
    unemp_path = DATA_DIR / "unemployment_rate.csv"
    fed_path = DATA_DIR / "fed_funds_rate.csv"

    # Step 1 & 2: Get CPI and Unemployment Rate
    # First, let's see if we already have this data saved locally
    if cpi_path.exists() and unemp_path.exists():
        print("\n[1-2/3] Found existing CPI & Unemployment files. Loading them up...")
        cpi_df = pd.read_csv(cpi_path)
        cpi_df['date'] = pd.to_datetime(cpi_df['date'])
        print(f"CPI loaded from {cpi_path}  ({len(cpi_df)} rows)")
        
        unemp_df = pd.read_csv(unemp_path)
        unemp_df['date'] = pd.to_datetime(unemp_df['date'])
        print(f"Unemployment Rate loaded from {unemp_path}  ({len(unemp_df)} rows)")
    else:
        # Don't have the files yet, so let's grab them from BLS
        print("\n[1-2/3] Fetching CPI & Unemployment Rate from BLS (this might take a moment)...")
        print(f"   → Getting years {BLS_QUERY_WINDOWS[0][0]}–{BLS_QUERY_WINDOWS[0][1]} first")
        print(f"   → Then years {BLS_QUERY_WINDOWS[1][0]}–{BLS_QUERY_WINDOWS[1][1]}")
        bls_data = fetch_bls_series(
            series_ids=[CPI_SERIES_ID, UNEMPLOYMENT_SERIES_ID]
        )

        cpi_df = bls_data[CPI_SERIES_ID].rename(columns={"value": "CPI"})
        cpi_df.to_csv(cpi_path, index=False)
        print(f"CPI saved → {cpi_path}  ({len(cpi_df)} rows)")

        unemp_df = bls_data[UNEMPLOYMENT_SERIES_ID].rename(columns={"value": "unemployment_rate"})
        unemp_df.to_csv(unemp_path, index=False)
        print(f"Unemployment Rate saved → {unemp_path}  ({len(unemp_df)} rows)")
    # Step 3: Get the Federal Funds Rate
    # Same deal - check if we have it already
    if fed_path.exists():
        print("\n[3/3] Found Fed Funds Rate file. Loading it...")
        fed_df = pd.read_csv(fed_path)
        fed_df['date'] = pd.to_datetime(fed_df['date'])
        print(f"Fed Funds Rate loaded from {fed_path}  ({len(fed_df)} rows)")
    else:
        # Need to get it from FRED
        print("\n[3/3] Fetching Fed Funds Rate from FRED...")
        fed_df = fetch_fred_series(FED_FUNDS_SERIES_ID, start_date_str, end_date_str)
        fed_df = fed_df.rename(columns={"value": "fed_funds_rate"})
        fed_df.to_csv(fed_path, index=False)
        print(f"Fed Funds Rate saved → {fed_path}  ({len(fed_df)} rows)")

    # Step 4: Combine everything into one master dataset
    print("\nCombining all three datasets together...")
    merged = (cpi_df
              .merge(unemp_df, on="date", how="outer")
              .merge(fed_df,   on="date", how="outer")
              .sort_values("date")
              .reset_index(drop=True))

    # Let's also calculate the year-over-year inflation rate while we're at it
    merged["CPI_YoY_pct"] = merged["CPI"].pct_change(periods=12) * 100

    merged_path = DATA_DIR / "macro_data.csv"
    merged.to_csv(merged_path, index=False)
    print(f"Saved combined dataset → {merged_path} ({len(merged)} rows)")

    print("\nHere's a quick look at the most recent data:")
    print(merged.tail(12).to_string(index=False))
    print("\nDData collection complete!")


if __name__ == "__main__":
    main()


