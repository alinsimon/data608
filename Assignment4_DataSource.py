#Assignment 4: Data Source Preparation
#I have introduced the term "Data Practitioner" as a generic job descriptor because we have so many different job role titles 
#for individuals whose work activities overlap including Data Scientist, Data Engineer, Data Analyst, Business Analyst, Data Architect, etc.
#For this story we will answer the question, "How much do we get paid?" Your analysis and data visualizations 
# must address the variation in average salary based on role descriptor and state.
#Notes:
#1)You will need to identify reliable sources for salary data and assemble the data sets that you will need.
#2)Your visualization(s) must show the most salient information (variation in average salary by role and by state).
#3)For this Story you must use a code library and code that you have written in R, Python or Java Script (additional coding in other languages is allowed).
#4)Post generation enhancements to you generated visualization will be allowed (e.g. Addition of kickers and labels).
#5)This assignment is due at the end of week eight of the semester.

import pandas as pd
import numpy as np
from pathlib import Path

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------
DATA_DIR = Path("data")

# Target data practitioner occupations from BLS OEWS
# BLS uses SOC (Standard Occupational Classification) codes
TARGET_OCCUPATIONS = {
    "152051": "Data Scientist",
    "151243": "Data Architect",
    "151242": "Database Administrator",
    "131111": "Business Analyst",  # Management Analysts
    "152031": "Operations Research Analyst",
    "151211": "Data Analyst",  # Computer Systems Analysts (closest proxy)
    "151252": "Software Developer",  # For comparison
}

print("=" * 80)
print("BLS OEWS DATA PROCESSING - DATA PRACTITIONER SALARIES")
print("=" * 80)

# -------------------------------------------------------
# Step 1: Load reference/mapping files
# -------------------------------------------------------
print("\n[1/6] Loading BLS reference files...")

# Helper function to clean column names
def clean_columns(df):
    df.columns = [col.strip() for col in df.columns]
    return df

# Load occupation codes and names
occupation_df = pd.read_csv(
    DATA_DIR / "BLS_Employment_Wage_oe.occupation",
    sep="\t",
    dtype=str
)
occupation_df = clean_columns(occupation_df)
print(f"  - Loaded {len(occupation_df):,} occupations")

# Load area codes (states and metros)
area_df = pd.read_csv(
    DATA_DIR / "BLS_Employment_Wage_oe.area",
    sep="\t",
    dtype=str
)
area_df = clean_columns(area_df)
print(f"  - Loaded {len(area_df):,} areas")

# Load data type codes (wage/employment metrics)
datatype_df = pd.read_csv(
    DATA_DIR / "BLS_Employment_Wage_oe.datatype",
    sep="\t",
    dtype=str
)
datatype_df = clean_columns(datatype_df)
print(f"  - Loaded {len(datatype_df):,} data types")

# Load industry codes
industry_df = pd.read_csv(
    DATA_DIR / "BLS_Employment_Wage_oe.industry",
    sep="\t",
    dtype=str
)
industry_df = clean_columns(industry_df)
print(f"  - Loaded {len(industry_df):,} industries")

# -------------------------------------------------------
# Step 2: Load series metadata (series_id definitions)
# -------------------------------------------------------
print("\n[2/6] Loading BLS series metadata...")
# Note: This file can be large, so we'll read it in chunks if needed
try:
    series_df = pd.read_csv(
        DATA_DIR / "BLS_Employment_Wage_oe.series",
        sep="\t",
        dtype=str
    )
    series_df = clean_columns(series_df)
    print(f"  - Loaded {len(series_df):,} series")
except Exception as e:
    print(f"  - Warning: Could not load series file directly: {e}")
    print(f"  - Will construct series IDs manually")
    series_df = None

# -------------------------------------------------------
# Step 3: Filter series for target occupations
# -------------------------------------------------------
print("\n[3/6] Filtering for target occupations and states...")

if series_df is not None:
    # Filter series for:
    # - Target occupations
    # - State-level data (not metro areas)
    # - All industries combined (industry_code = '000000')
    # - Non-seasonal (seasonal = 'U' for unadjusted)
    target_occ_codes = list(TARGET_OCCUPATIONS.keys())
    
    filtered_series = series_df[
        (series_df['occupation_code'].isin(target_occ_codes)) &
        (series_df['industry_code'] == '000000') &  # All industries
        (series_df['seasonal'] == 'U')  # Unadjusted/non-seasonal
    ].copy()
    
    # Get both state-level and national data
    # State codes: 2-digit FIPS codes (01-56)
    # National code: 0000000
    filtered_series = filtered_series[
        (filtered_series['areatype_code'].isin(['S', 'N']))  # State or National
    ].copy()
    
    print(f"  - Filtered to {len(filtered_series):,} relevant series")
    series_ids_to_load = filtered_series['series_id'].tolist()
else:
    # Manual construction of series IDs (if series file couldn't be loaded)
    print("  - Manually constructing series IDs...")
    series_ids_to_load = None

# -------------------------------------------------------
# Step 4: Load actual data points
# -------------------------------------------------------
print("\n[4/6] Loading BLS data file (this may take a moment)...")

# Read the data file
data_df = pd.read_csv(
    DATA_DIR / "BLS_Employment_Wage_oe.data.1.AllData",
    sep="\t",
    dtype=str
)
data_df = clean_columns(data_df)
print(f"  - Loaded {len(data_df):,} total data points")

# Filter to only the series we need (if we have series list)
if series_ids_to_load:
    data_df = data_df[data_df['series_id'].isin(series_ids_to_load)].copy()
    print(f"  - Filtered to {len(data_df):,} relevant data points")

# Convert year and value to numeric
data_df['year'] = pd.to_numeric(data_df['year'], errors='coerce')
data_df['value'] = pd.to_numeric(data_df['value'], errors='coerce')

# Keep only annual data (period = 'A01' represents annual data in OEWS)
data_df = data_df[data_df['period'] == 'A01'].copy()
print(f"  - {len(data_df):,} annual data points")

# Keep recent years only (last 5 years)
max_year = data_df['year'].max()
data_df = data_df[data_df['year'] >= max_year - 4].copy()
print(f"  - Years: {data_df['year'].min():.0f} to {data_df['year'].max():.0f}")

# -------------------------------------------------------
# Step 5: Merge with reference data to add labels
# -------------------------------------------------------
print("\n[5/6] Merging data with reference tables...")

# Merge with series metadata to get dimensions
if series_df is not None:
    data_merged = data_df.merge(
        filtered_series[['series_id', 'occupation_code', 'industry_code', 'area_code', 'datatype_code']],
        on='series_id',
        how='left'
    )
else:
    # If series file wasn't loaded, extract codes from series_id
    # BLS OEWS series_id format: OEUSSSSSSSSIIIIIIOOOOOOTT
    # OE = prefix
    # U = Unadjusted  
    # SSSSSSS = Area code (7 digits)
    # IIIIII = Industry code (6 digits)
    # OOOOOO = Occupation code (6 digits)
    # TT = Data type code (2 digits)
    data_merged = data_df.copy()
    data_merged['area_code'] = data_merged['series_id'].str[3:10]
    data_merged['industry_code'] = data_merged['series_id'].str[10:16]
    data_merged['occupation_code'] = data_merged['series_id'].str[16:22]
    data_merged['datatype_code'] = data_merged['series_id'].str[22:24]

# Filter for target occupations
data_merged = data_merged[
    data_merged['occupation_code'].isin(TARGET_OCCUPATIONS.keys())
].copy()

# Add readable occupation names
data_merged['Role'] = data_merged['occupation_code'].map(TARGET_OCCUPATIONS)

# Add area/state names
area_lookup = area_df.set_index('area_code')['area_name'].to_dict()
data_merged['Area'] = data_merged['area_code'].map(area_lookup)

# Add state codes
state_lookup = area_df.set_index('area_code')['state_code'].to_dict()
data_merged['State_Code'] = data_merged['area_code'].map(state_lookup)

# Add data type descriptions
datatype_lookup = datatype_df.set_index('datatype_code')['datatype_name'].to_dict()
data_merged['Metric'] = data_merged['datatype_code'].map(datatype_lookup)

print(f"  - Merged data: {len(data_merged):,} records")

# -------------------------------------------------------
# Step 6: Create flat wide-format dataframe
# -------------------------------------------------------
print("\n[6/6] Creating flat dataframe...")

# Pivot to wide format: one row per Role/State/Year with columns for each metric
salary_flat = data_merged.pivot_table(
    index=['Role', 'Area', 'State_Code', 'year'],
    columns='Metric',
    values='value',
    aggfunc='first'
).reset_index()

# Flatten column names
salary_flat.columns.name = None

# Rename columns for easier use
column_rename = {
    'Employment': 'Employment',
    'Hourly mean wage': 'Hourly_Mean_Wage',
    'Annual mean wage': 'Annual_Mean_Wage',
    'Hourly median wage': 'Hourly_Median_Wage',
    'Annual median wage': 'Annual_Median_Wage',
    'Hourly 10th percentile wage': 'Hourly_P10_Wage',
    'Hourly 25th percentile wage': 'Hourly_P25_Wage',
    'Hourly 75th percentile wage': 'Hourly_P75_Wage',
    'Hourly 90th percentile wage': 'Hourly_P90_Wage',
    'Annual 10th percentile wage': 'Annual_P10_Wage',
    'Annual 25th percentile wage': 'Annual_P25_Wage',
    'Annual 75th percentile wage': 'Annual_P75_Wage',
    'Annual 90th percentile wage': 'Annual_P90_Wage',
}
salary_flat = salary_flat.rename(columns=column_rename)

# Sort by year (descending), role, and area
salary_flat = salary_flat.sort_values(
    ['year', 'Role', 'Area'],
    ascending=[False, True, True]
).reset_index(drop=True)

# -------------------------------------------------------
# Display summary statistics
# -------------------------------------------------------
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total records: {len(salary_flat):,}")
print(f"Roles: {salary_flat['Role'].nunique()}")
print(f"Areas: {salary_flat['Area'].nunique()}")
print(f"Years: {sorted(salary_flat['year'].unique())}")

print("\nSample data:")
# Display available columns
display_cols = ['Role', 'Area', 'year']
if 'Annual_Mean_Wage' in salary_flat.columns:
    display_cols.append('Annual_Mean_Wage')
if 'Employment' in salary_flat.columns:
    display_cols.append('Employment')
    
if len(salary_flat) > 0:
    print(salary_flat.head(20)[display_cols])
else:
    print("No data available")
    print("\nAvailable columns:", list(salary_flat.columns))

# -------------------------------------------------------
# Save to CSV
# -------------------------------------------------------
output_file = "data/BLS_data_practitioner_salaries_by_state.csv"
salary_flat.to_csv(output_file, index=False)
print(f"\n✓ Data saved to: {output_file}")

if len(salary_flat) > 0 and 'Annual_Mean_Wage' in salary_flat.columns:
    print("\nMean annual salary by role (most recent year):")
    latest_year = salary_flat['year'].max()
    national_data = salary_flat[
        (salary_flat['year'] == latest_year) & 
        (salary_flat['Area'] == 'National')
    ]
    
    if len(national_data) > 0:
        salary_summary = national_data[
            [col for col in ['Role', 'Annual_Mean_Wage', 'Employment'] if col in national_data.columns]
        ].sort_values('Annual_Mean_Wage', ascending=False)
        print(salary_summary)
    else:
        print("  (No national-level data available)")


print("\n" + "=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)

