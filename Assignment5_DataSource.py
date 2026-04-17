#Historic data indicates that the occurrence and intensity of cyclonic storms (Hurricanes, Typhoons and Tornados) increases with the increased earth temperature. For this assignment you will need to tell this story to a non-technical audience (eg: a high-school earth science class).
#Notes:
#
#Source historic data for a period of at least 25 years on a measure of the earth's temperature.
#
#Source data on the occurrence and intensity of hurricanes, typhoons and tornados for the same historic period.

#Perform the data analysis to establish the correlations between earth temperature and storm occurrence and intensity.

#Tell the story of this data and your analysis using data visualizations and other illustrations (eg: pictures of storm damage) in a presentation that will be accessible to a high-school earth science class.

#This assignment is due at the end of the week ten of the semester.

# =============================================================================
# DATA SOURCES
# =============================================================================
#
# 1. GLOBAL TEMPERATURE — NASA GISS Surface Temperature Analysis (GISTEMP v4)
#    - Provides global mean land-ocean temperature anomalies (°C) vs 1951-1980 baseline
#    - Coverage: 1880 – present (annual + monthly)
#    - File already downloaded: data/GLB.Ts+dSST.csv
#    - Info:  https://data.giss.nasa.gov/gistemp/
#    - Direct download: https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv
#
# 2. HURRICANES — NOAA IBTrACS v4r01, North Atlantic Basin (NA)
#    (International Best Track Archive for Climate Stewardship)
#    - Most complete global tropical cyclone dataset; merges data from all WMO agencies
#    - Columns include: storm name, date, WMO_WIND (max sustained wind knts), WMO_PRES (min pressure mb), USA_SSHS (Saffir-Simpson category)
#    - Coverage: 1851 – present | Named storms: 312+ unique names
#    - File downloaded: data/ibtracs_NA.csv  (54.4 MB)
#    - NOTE: In basin-specific IBTrACS files, the BASIN column is NaN for the primary
#      basin's own storms; the file itself defines the basin (North Atlantic = hurricanes)
#    - Info:  https://www.ncei.noaa.gov/products/international-best-track-archive
#    - Direct download: https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NA.list.v04r01.csv
#
# 3. TYPHOONS — NOAA IBTrACS v4r01, Western Pacific Basin (WP)
#    - Same dataset as above but Western Pacific basin (typhoons)
#    - Columns: same structure as NA file
#    - Coverage: 1980 – present (from ibtracs.since1980.csv, BASIN == 'WP')
#    - File downloaded: data/ibtracs_since1980.csv  (135.8 MB, all non-NA basins)
#    - WP rows: 102,348 | Season range: 1980–2026
#
# 4. TORNADOES — NOAA Storm Prediction Center (SPC) Severe Weather Database
#    - Official U.S. tornado record: date, state, EF/F-scale magnitude (mag col), injuries (inj), fatalities (fat), path length/width
#    - Coverage: 1950 – 2024 | 71,813 tornado events
#    - File downloaded: data/spc_tornadoes_1950_2024.csv  (7.6 MB)
#    - Info:  https://www.spc.noaa.gov/wcm/
#    - Direct download: https://www.spc.noaa.gov/wcm/data/1950-2024_actual_tornadoes.csv
#
# =============================================================================
# ANALYSIS APPROACH
# =============================================================================
#
# - Use the annual temperature anomaly (J-D column) from GISTEMP as the independent variable
# - Derive per-year HURRICANE metrics from ibtracs_NA.csv:
#     * Count of named storms and hurricanes (WMO_WIND >= 64 knts) per season
#     * Average and max WMO_WIND (proxy for intensity)
#     * Accumulated Cyclone Energy (ACE) = sum of (WMO_WIND^2) per 6-hr interval
# - Derive per-year TYPHOON metrics from ibtracs_since1980.csv (BASIN == 'WP'):
#     * Same metrics as above
# - Derive per-year TORNADO metrics from spc_tornadoes_1950_2024.csv:
#     * Total count, count of significant tornadoes (mag >= 2 = EF2+)
# - Align all datasets to year (1980–2024 gives a clean 44-year overlap)
# - Compute Pearson / Spearman correlations and produce scatter + trend plots
# =============================================================================

import os
import requests
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

SOURCES = {
    "gistemp": {
        "url": "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
        "filename": "GLB.Ts+dSST.csv",
        "description": "NASA GISTEMP v4 – Global mean land-ocean temperature anomalies",
    },
    # Hurricanes: North Atlantic basin IBTrACS file
    # NOTE: In basin-specific files the BASIN column is NaN for the primary basin's storms.
    "ibtracs_NA": {
        "url": "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NA.list.v04r01.csv",
        "filename": "ibtracs_NA.csv",
        "description": "NOAA IBTrACS v4r01 – North Atlantic tropical cyclones (hurricanes), 1851–present",
    },
    # Typhoons + other basins (WP = Western Pacific): use BASIN == 'WP' filter
    "ibtracs_since1980": {
        "url": "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.since1980.list.v04r01.csv",
        "filename": "ibtracs_since1980.csv",
        "description": "NOAA IBTrACS v4r01 – All basins since 1980 (filter BASIN=='WP' for typhoons)",
    },
    "tornadoes": {
        "url": "https://www.spc.noaa.gov/wcm/data/1950-2024_actual_tornadoes.csv",
        "filename": "spc_tornadoes_1950_2024.csv",
        "description": "NOAA SPC – U.S. tornado observations 1950–2024 (mag=EF/F scale, -9=unknown)",
    },
}


def download_file(url: str, dest_path: str, description: str) -> bool:
    if os.path.exists(dest_path):
        print(f"  [skip] {os.path.basename(dest_path)} already exists.")
        return True
    print(f"  Downloading: {description}")
    print(f"    {url}")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f"    Saved {size_mb:.1f} MB -> {dest_path}")
        return True
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


if __name__ == "__main__":
    print("=== Assignment 5 – Data Download ===\n")
    for key, source in SOURCES.items():
        dest = os.path.join(DATA_DIR, source["filename"])
        download_file(source["url"], dest, source["description"])
    print("\nDone. All files should be in the data/ folder.")
    print("Note: ibtracs_since1980.csv is large (~142 MB). Be patient on slow connections.")
