# Assignment 6 – Food Security & Nutrition in the US
#
# Reading the UN Food and Agriculture report on global food security might make
# you think hunger is someone else's problem — happening far away, not here.
# This assignment asks you to look closer to home and examine food insecurity
# right here in the United States.
#
# What we need to do:
#   - Find data on food security and nutrition broken down by state, gender
#     (men, women), and age group (children, adults, seniors).
#   - Demonstrate correlations that exist between level of poverty and food insecurity, malnutrition and starvation
#   - indicate what happens to the children as they mature into adults. Will they become fully functional citizens or will they require continued support?
#   - Build visualizations that the story for a political audience that you were lobbying to address the issue of food insecurity in the US.

# -----------------------------------------------------------------------
# Where does the data come from?
# -----------------------------------------------------------------------
#
# 1. Census Bureau — CPS Food Security Supplement (our main data source)
#
#    Every December the Census Bureau surveys roughly 40,000 households
#    and asks them directly about food insecurity. This is THE official
#    US measurement of hunger. Each record tells us the person's state,
#    age, sex, whether their household was food insecure, and whether
#    they were living near or below the poverty line.
#
#    The columns we care about:
#      GESTFIPS  — which state the person lives in
#      PESEX     — gender: 1 = Male, 2 = Female
#      PRTAGE    — age (0 to 90)
#      HRFS12M1  — was the household food insecure over the past year?
#                   1 = fine, 2 = low food security, 3 = very low food security
#      HRFS12MC  — same question but specifically for children in the house
#      HRFS12M8  — same question but specifically for adults in the house
#      HRPOOR    — is the household below 185% of the poverty line?
#                   1 = yes (low income), 2 = no
#      HHSUPWGT  — statistical weight to make the sample represent the US population
#      HESP1     — did the household receive SNAP (food stamps) this past year?
#      HESP8     — did anyone receive WIC food assistance this past month?
#      PEEDUCA   — highest education level (helps us trace child outcomes into adulthood)
#
#    Download the full file (compressed CSV, ~50 MB):
#      https://www2.census.gov/programs-surveys/cps/datasets/{year}/supp/dec{yy}pub.csv
#    Or use the Census API:
#      https://api.census.gov/data/{year}/cps/foodsec/dec
#    No API key needed, though registering for one is free and avoids rate limits.
#    More info: https://www.ers.usda.gov/data-products/food-security-in-the-united-states/
#
#
# 2. USDA ERS — Ready-made state-level food insecurity rates
#
#    The USDA Economic Research Service takes the CPS data and publishes
#    clean, pre-calculated food insecurity rates for every state. They use
#    three-year averages to make the numbers more reliable for smaller states.
#    This is a great sanity check against our own calculations.
#
#    Download (a ZIP file with several CSV tables inside):
#      https://www.ers.usda.gov/media/799/food-security-csv-data-files.zip
#    Includes national trends, breakdowns by demographic group, and state rates.
#    Interactive version: https://www.ers.usda.gov/topics/food-nutrition-assistance/food-security-in-the-us/interactive-charts-and-highlights/
#
#
# 3. Census Bureau — ACS Poverty Data by State, Sex, and Age
#
#    The American Community Survey gives us detailed poverty numbers for
#    every state, broken down by gender and age group. We use this to
#    show the connection between poverty rates and food insecurity rates.
#
#    We pull from table B17001, which counts how many people in each state
#    are below the poverty line, split by male/female and age bracket.
#    API: https://api.census.gov/data/{year}/acs/acs1
#    No API key needed.
#
#
# 4. USDA ERS — Food Environment Atlas
#
#    This dataset adds broader context at the state and county level:
#    how many people use SNAP, how many use WIC, what share of the
#    population lives in a food desert, and health outcomes like
#    obesity and diabetes rates. It helps paint the full picture of
#    what food insecurity looks like on the ground.
#
#    Download (Excel file):
#      https://www.ers.usda.gov/media/5570/food-environment-atlas-csv-files.zip
#
#
# How do we track what happens to food-insecure kids as they grow up?
#
#    The CPS microdata lets us compare food insecurity rates across age
#    groups within the same states — children (under 18), young adults
#    (18–34), working-age adults (35–64), and seniors (65+). Combined
#    with the PEEDUCA education variable, we can explore whether kids
#    who grew up in food-insecure households ended up less educated and
#    still struggling as adults.
# -----------------------------------------------------------------------

import io
import os
import zipfile

import pandas as pd
import requests
import dotenv

dotenv.load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

# Which year of the CPS Food Security Survey to download.
# The survey runs every December; 2023 data became available in mid-2024.
CPS_YEAR = 2023

# Numeric FIPS codes for all 50 states + DC (territories are excluded).
# These are used when we query the Census API one state at a time.
STATE_FIPS = [
    "01","02","04","05","06","08","09","10","11","12","13","15","16","17","18",
    "19","20","21","22","23","24","25","26","27","28","29","30","31","32","33",
    "34","35","36","37","38","39","40","41","42","44","45","46","47","48","49",
    "50","51","53","54","55","56",
]

# The specific columns we want to keep from the CPS raw file.
# The full file has hundreds of columns; we only need these.
CPS_VARS = [
    "GESTFIPS",   # which state
    "PESEX",      # gender: 1=Male, 2=Female
    "PRTAGE",     # person's age
    "HRFS12M1",   # food security over the past year: 1=secure, 2=low, 3=very low
    "HRFS12MD",   # more detailed version: 1=high, 2=marginal, 3=low, 4=very low
    "HRFS12MC",   # food security specifically for children in the household
    "HRFS12M8",   # food security specifically for adults in the household
    "HRPOOR",     # is the household below 185% of the poverty line? 1=yes, 2=no
    "HHSUPWGT",   # statistical weight for the household (needed for accurate totals)
    "PWSSWGT",    # statistical weight for the individual person
    "HESP1",      # did they receive SNAP (food stamps) this year? 1=yes, 2=no
    "HESP8",      # did they receive WIC food assistance this month? 1=yes, 2=no
    "PEEDUCA",    # highest education level reached (useful for the child→adult story)
    "PRFAMTYP",   # type of family unit (single parent, married couple, etc.)
]

# ACS Table B17001 — poverty counts by state, broken down by sex and age.
# These column codes are how the Census API names each data point.
ACS_POVERTY_VARS = [
    "NAME",
    "B17001_001E",   # total number of people the poverty question was asked of
    "B17001_002E",   # total people below the poverty line
    "B17001_003E",   # men below the poverty line (all ages combined)
    "B17001_004E",   # men below poverty: under 5 years old
    "B17001_005E",   # men below poverty: age 5
    "B17001_006E",   # men below poverty: ages 6-11
    "B17001_007E",   # men below poverty: ages 12-14
    "B17001_008E",   # men below poverty: ages 15-17
    "B17001_009E",   # men below poverty: ages 18-24
    "B17001_010E",   # men below poverty: ages 25-34
    "B17001_011E",   # men below poverty: ages 35-44
    "B17001_012E",   # men below poverty: ages 45-54
    "B17001_013E",   # men below poverty: ages 55-64
    "B17001_014E",   # men below poverty: ages 65-74
    "B17001_015E",   # men below poverty: age 75 and older
    "B17001_017E",   # women below the poverty line (all ages combined)
    "B17001_018E",   # women below poverty: under 5 years old
    "B17001_019E",   # women below poverty: age 5
    "B17001_020E",   # women below poverty: ages 6-11
    "B17001_021E",   # women below poverty: ages 12-14
    "B17001_022E",   # women below poverty: ages 15-17
    "B17001_023E",   # women below poverty: ages 18-24
    "B17001_024E",   # women below poverty: ages 25-34
    "B17001_025E",   # women below poverty: ages 35-44
    "B17001_026E",   # women below poverty: ages 45-54
    "B17001_027E",   # women below poverty: ages 55-64
    "B17001_028E",   # women below poverty: ages 65-74
    "B17001_029E",   # women below poverty: age 75 and older
]


# -----------------------------------------------------------------------
# Helper functions (internal plumbing — not meant to be called directly)
# -----------------------------------------------------------------------

def _census_api_url(year: int, dataset: str, variables: list[str],
                    geo: str = "us:1", api_key: str = "") -> str:
    """Assembles a Census API request URL from the pieces we provide."""
    var_str = ",".join(variables)
    key_part = f"&key={api_key}" if api_key else ""
    return (f"https://api.census.gov/data/{year}/{dataset}"
            f"?get={var_str}&for={geo}{key_part}")


def _fetch_census_json(url: str) -> list[list]:
    """Calls the Census API and returns the data as a list of rows. The first row is always the column headers."""
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_cps_food_security(year: int = CPS_YEAR,
                             output_path: str | None = None) -> pd.DataFrame:
    """
    Downloads the CPS Food Security Supplement microdata from the Census Bureau.

    We grab the bulk compressed file (the whole country in one download) rather
    than querying the API, because the API caps responses at 50,000 rows and
    the full dataset is much larger than that. If the bulk download fails for
    any reason, we automatically fall back to the API and query each state one
    at a time.

    year        -- which December survey to pull (default is 2023)
    output_path -- where to save the resulting CSV (optional)

    Returns a DataFrame with one row per person and the columns listed in CPS_VARS.
    """
    two_digit = str(year)[2:]  # the file name uses a 2-digit year, e.g. "23" for 2023
    url = (f"https://www2.census.gov/programs-surveys/cps/datasets/"
           f"{year}/supp/dec{two_digit}pub.csv")

    raw_path = os.path.join(DATA_DIR, f"cps_foodsec_{year}_raw.csv")
    csv_path = output_path or os.path.join(DATA_DIR, f"cps_foodsec_{year}.csv")

    if os.path.exists(csv_path):
        print(f"  [skip] {os.path.basename(csv_path)} already exists.")
        return pd.read_csv(csv_path, dtype=str)

    # Download the full file (it's a plain CSV, about 175 MB)
    if not os.path.exists(raw_path):
        print(f"  Downloading CPS Food Security Supplement {year} …")
        print(f"    {url}")
        try:
            r = requests.get(url, stream=True, timeout=600)
            r.raise_for_status()
            with open(raw_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
            size_mb = os.path.getsize(raw_path) / (1024 * 1024)
            print(f"    Downloaded {size_mb:.1f} MB → {raw_path}")
        except Exception as exc:
            print(f"    ERROR downloading bulk file: {exc}")
            print("    Falling back to Census JSON API (state-by-state)…")
            return _fetch_cps_via_api(year, csv_path)

    # Read the CSV and strip it down to only the columns we actually need
    print(f"  Reading and filtering columns …")
    try:
        df = pd.read_csv(raw_path, dtype=str, encoding="latin-1", low_memory=False)
    except Exception as exc:
        print(f"    ERROR reading file: {exc}")
        return _fetch_cps_via_api(year, csv_path)

    # The raw file can have mixed-case column names depending on the year, so normalize them
    df.columns = [c.upper() for c in df.columns]
    available = [v for v in CPS_VARS if v in df.columns]
    missing = [v for v in CPS_VARS if v not in df.columns]
    if missing:
        print(f"    Note: some expected columns weren't in the file: {missing}")
    df = df[available].copy()

    df.to_csv(csv_path, index=False)
    print(f"    Saved {len(df):,} records → {csv_path}")
    return df


def _fetch_cps_via_api(year: int, csv_path: str) -> pd.DataFrame:
    """
    Backup method: pulls CPS Food Security data from the Census API one state at a time.
    We do it this way because the API only returns 50,000 rows per request, which isn't
    enough for the full national dataset in one shot.
    """
    print(f"  Fetching CPS FSS {year} via Census API (state by state) …")
    # GESTFIPS (state code) comes back automatically from the geographic filter, so we don't request it separately
    base_vars = [v for v in CPS_VARS if v != "GESTFIPS"]
    var_str = ",".join(base_vars)
    key_part = f"&key={CENSUS_API_KEY}" if CENSUS_API_KEY else ""
    all_rows = []

    for fips in STATE_FIPS:
        url = (f"https://api.census.gov/data/{year}/cps/foodsec/dec"
               f"?get={var_str}&for=state:{fips}{key_part}")
        try:
            rows = _fetch_census_json(url)
            if len(rows) > 1:
                headers = rows[0]
                for row in rows[1:]:
                    all_rows.append(dict(zip(headers, row)))
        except Exception as exc:
            print(f"    WARN: state {fips} failed — {exc}")

    if not all_rows:
        print("    ERROR: No data retrieved from API.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    # The API returns the geographic filter column as "state" — rename it to match our standard column name
    if "state" in df.columns and "GESTFIPS" not in df.columns:
        df.rename(columns={"state": "GESTFIPS"}, inplace=True)

    df.to_csv(csv_path, index=False)
    print(f"    Saved {len(df):,} records → {csv_path}")
    return df


def download_ers_state_food_security(output_dir: str = DATA_DIR) -> dict[str, pd.DataFrame]:
    """
    Downloads the USDA ERS food security data package — a ZIP file containing
    several ready-to-use CSV tables with official state-level food insecurity
    rates, national trends, and demographic breakdowns.

    These are the numbers that show up in government reports and news articles.
    We use them to validate our own calculations from the CPS microdata.

    Returns a dictionary where each key is a table name and the value is a
    DataFrame. Each table is also saved as its own CSV file.
    Source: https://www.ers.usda.gov/topics/food-nutrition-assistance/food-security-in-the-us/interactive-charts-and-highlights/
    """
    zip_url = "https://www.ers.usda.gov/media/799/food-security-csv-data-files.zip"
    zip_path = os.path.join(output_dir, "ers_food_security_csvs.zip")
    tables: dict[str, pd.DataFrame] = {}

    # Don't re-download if we already have it
    state_file = os.path.join(output_dir, "ers_food_security_by_state.csv")
    if os.path.exists(state_file):
        print(f"  [skip] ERS state-level file already exists.")
        tables["state"] = pd.read_csv(state_file)
        return tables

    if not os.path.exists(zip_path):
        print(f"  Downloading USDA ERS Food Security CSV data …")
        print(f"    {zip_url}")
        try:
            r = requests.get(zip_url, timeout=120)
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                f.write(r.content)
            print(f"    Downloaded {os.path.getsize(zip_path)/1024:.0f} KB → {zip_path}")
        except Exception as exc:
            print(f"    ERROR: {exc}")
            return tables

    # Unzip and save each CSV table inside
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if not name.lower().endswith(".csv"):
                    continue
                with zf.open(name) as f:
                    content = f.read().decode("latin-1")
                try:
                    df = pd.read_csv(io.StringIO(content))
                    # Use the original file name (without extension) as the table key
                    key = os.path.splitext(os.path.basename(name))[0].lower()
                    tables[key] = df
                    out_path = os.path.join(output_dir, f"ers_{key}.csv")
                    df.to_csv(out_path, index=False)
                    print(f"    Extracted {name} → {os.path.basename(out_path)} "
                          f"({len(df)} rows)")
                except Exception as exc:
                    print(f"    WARN: could not parse {name}: {exc}")
    except Exception as exc:
        print(f"    ERROR extracting ZIP: {exc}")

    return tables


def fetch_acs_poverty_by_state(year: int = 2022,
                                output_path: str | None = None) -> pd.DataFrame:
    """
    Pulls poverty rates by state from the Census American Community Survey,
    broken down by sex and age group.

    We use this to show the relationship between poverty and food insecurity
    across states — the higher the poverty rate, the worse the food insecurity
    tends to be. The ACS covers all 50 states plus DC.

    year        -- which ACS year to use (the 1-year ACS is available for all states)
    output_path -- where to save the CSV (optional)

    Returns a DataFrame with one row per state and poverty counts by age and sex.
    """
    csv_path = output_path or os.path.join(DATA_DIR, f"acs_poverty_by_state_{year}.csv")
    if os.path.exists(csv_path):
        print(f"  [skip] {os.path.basename(csv_path)} already exists.")
        return pd.read_csv(csv_path)

    var_str = ",".join(ACS_POVERTY_VARS)
    key_part = f"&key={CENSUS_API_KEY}" if CENSUS_API_KEY else ""
    url = (f"https://api.census.gov/data/{year}/acs/acs1"
           f"?get={var_str}&for=state:*{key_part}")
    print(f"  Fetching ACS {year} poverty data by state …")
    print(f"    {url}")
    try:
        rows = _fetch_census_json(url)
        headers = rows[0]
        df = pd.DataFrame(rows[1:], columns=headers)

        # The API returns everything as strings, so convert the count columns to numbers
        est_cols = [c for c in df.columns if c.endswith("E") and c != "NAME"]
        for col in est_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Calculate overall poverty rate and child poverty totals for easy use in analysis
        df["poverty_rate_pct"] = (
            df["B17001_002E"] / df["B17001_001E"] * 100
        ).round(2)
        df["child_poverty_male"] = (
            df[["B17001_004E","B17001_005E","B17001_006E",
                "B17001_007E","B17001_008E"]].sum(axis=1)
        )
        df["child_poverty_female"] = (
            df[["B17001_018E","B17001_019E","B17001_020E",
                "B17001_021E","B17001_022E"]].sum(axis=1)
        )
        df["child_poverty_total"] = df["child_poverty_male"] + df["child_poverty_female"]
        df["child_poverty_rate_pct"] = (
            df["child_poverty_total"] /
            df[["B17001_004E","B17001_005E","B17001_006E","B17001_007E","B17001_008E",
                "B17001_018E","B17001_019E","B17001_020E","B17001_021E","B17001_022E"]
               ].sum(axis=1) * 100
        ).round(2)

        df.to_csv(csv_path, index=False)
        print(f"    Saved {len(df)} states → {csv_path}")
        return df
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return pd.DataFrame()


def fetch_ers_food_environment_atlas(output_path: str | None = None) -> pd.DataFrame:
    """
    Downloads the USDA ERS Food Environment Atlas, which gives us state and
    county-level context around food insecurity: how many people use SNAP
    or WIC, how many live in food deserts, and health outcomes like obesity
    and diabetes that are linked to poor nutrition.

    This helps tell the broader story — food insecurity doesn't just mean
    going hungry, it shapes long-term health outcomes.
    Source: https://www.ers.usda.gov/data-products/food-environment-atlas/
    """
    out_csv = output_path or os.path.join(DATA_DIR, "ers_food_environment_atlas.csv")
    if os.path.exists(out_csv):
        print(f"  [skip] {os.path.basename(out_csv)} already exists.")
        return pd.read_csv(out_csv)

    # The Atlas is distributed as a ZIP containing a single CSV file
    zip_url = "https://www.ers.usda.gov/media/5570/food-environment-atlas-csv-files.zip?v=25727"
    print(f"  Downloading USDA ERS Food Environment Atlas …")
    print(f"    {zip_url}")
    try:
        r = requests.get(zip_url, timeout=120)
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            with zf.open("StateAndCountyData.csv") as f:
                df = pd.read_csv(f, dtype=str, encoding="latin-1", low_memory=False)
        df.to_csv(out_csv, index=False)
        print(f"    Saved {len(df)} rows → {out_csv}")
        return df
    except Exception as exc:
        print(f"    ERROR: {exc}")
        return pd.DataFrame()


def build_age_groups(df: pd.DataFrame, age_col: str = "PRTAGE") -> pd.DataFrame:
    """
    Adds an 'age_group' column to the CPS data so we can compare food insecurity
    across life stages. The groups are:
        Under 5   — infants and toddlers
        5-17      — school-age children
        18-34     — young adults (the same kids, grown up)
        35-64     — working-age adults
        65+       — seniors

    These buckets are standard in US policy analysis and let us tell the story
    of what happens to food-insecure children as they age into adulthood.
    """
    age = pd.to_numeric(df[age_col], errors="coerce")
    bins   = [0,  5, 18, 35, 65, 120]
    labels = ["Under 5", "5-17", "18-34", "35-64", "65+"]
    df = df.copy()
    df["age_group"] = pd.cut(age, bins=bins, labels=labels, right=False)
    return df


def aggregate_food_insecurity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rolls up the raw CPS person records into a summary table showing
    food insecurity rates broken down by state, gender, and age group.

    This is the core output we need for the analysis visualizations —
    one rate per combination of (state, Male/Female, age group).
    The rates are weighted using the household supplement weight so
    they accurately represent the full US population.
    """
    df = df.copy()
    df = build_age_groups(df)

    # Make sure the key columns are numbers, not strings
    for col in ["HRFS12M1", "PESEX", "HHSUPWGT", "GESTFIPS"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Anyone with HRFS12M1 of 2 or 3 is food insecure (2=low, 3=very low)
    df["is_food_insecure"] = df["HRFS12M1"].isin([2, 3]).astype(int)

    df["sex_label"] = df["PESEX"].map({1: "Male", 2: "Female"})

    # Use the household weight if available so numbers reflect the real population
    wgt_col = "HHSUPWGT" if "HHSUPWGT" in df.columns else None

    group_cols = ["GESTFIPS", "sex_label", "age_group"]

    if wgt_col:
        df[wgt_col] = pd.to_numeric(df[wgt_col], errors="coerce").fillna(1)
        grouped = df.groupby(group_cols, observed=True).apply(
            lambda g: pd.Series({
                "total_weighted": g[wgt_col].sum(),
                "insecure_weighted": (g["is_food_insecure"] * g[wgt_col]).sum(),
            })
        ).reset_index()
        grouped["food_insecure_rate_pct"] = (
            grouped["insecure_weighted"] / grouped["total_weighted"] * 100
        ).round(2)
    else:
        grouped = df.groupby(group_cols, observed=True).agg(
            total_weighted=("is_food_insecure", "count"),
            insecure_weighted=("is_food_insecure", "sum"),
        ).reset_index()
        grouped["food_insecure_rate_pct"] = (
            grouped["insecure_weighted"] / grouped["total_weighted"] * 100
        ).round(2)

    return grouped


# -----------------------------------------------------------------------
# Run this script directly to download all the data files we need.
# -----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("Assignment 6 – Food Security Data Download")
    print("=" * 70)

    # --- 1. CPS Food Security Supplement microdata ---
    print("\n[1] CPS Food Security Supplement microdata")
    cps_df = fetch_cps_food_security(year=CPS_YEAR)

    if not cps_df.empty:
        # Aggregate to state × sex × age for analysis script
        print("  Aggregating by state × sex × age group …")
        agg_path = os.path.join(DATA_DIR, "food_insecurity_by_state_sex_age.csv")
        if not os.path.exists(agg_path):
            agg_df = aggregate_food_insecurity(cps_df)
            agg_df.to_csv(agg_path, index=False)
            print(f"  Saved aggregated data ({len(agg_df)} rows) → {agg_path}")
        else:
            print(f"  [skip] Aggregated file already exists.")

    # --- 2. USDA ERS state-level food security rates ---
    print("\n[2] USDA ERS pre-computed state-level food security rates")
    ers_tables = download_ers_state_food_security()

    # --- 3. Census ACS poverty by state (for correlation analysis) ---
    print("\n[3] Census ACS 1-year poverty by state, sex, and age")
    acs_df = fetch_acs_poverty_by_state(year=2022)

    # --- 4. USDA ERS Food Environment Atlas (SNAP, WIC, food access) ---
    print("\n[4] USDA ERS Food Environment Atlas")
    atlas_df = fetch_ers_food_environment_atlas()

    # --- Summary ---
    print("\n" + "=" * 70)
    print("Download complete. Files saved to:", DATA_DIR)
    print("=" * 70)
    print("\nKey output files for Assignment 6 Analysis:")
    print(f"  • data/cps_foodsec_{CPS_YEAR}.csv")
    print(f"    → CPS microdata: state, sex, age, food security, poverty, SNAP/WIC")
    print(f"  • data/food_insecurity_by_state_sex_age.csv")
    print(f"    → Aggregated food insecurity rates by state × sex × age group")
    print(f"  • data/acs_poverty_by_state_2022.csv")
    print(f"    → State poverty rates by sex and age (for correlation)")
    print(f"  • data/ers_*.csv")
    print(f"    → USDA ERS official state-level food insecurity rates and trends")
    print(f"  • data/ers_food_environment_atlas.csv")
    print(f"    → SNAP/WIC participation, food access, obesity by state")
    print("\nVariable reference:")
    print("  HRFS12M1: 1=Food Secure  2=Low Food Security  3=Very Low Food Security")
    print("  PESEX:    1=Male  2=Female")
    print("  HRPOOR:   1=Below 185% poverty  2=Above 185% poverty")
    print("  HESP1:    1=Received SNAP in past year  2=No")
