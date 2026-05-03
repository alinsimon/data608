# =============================================================================
# Assignment 6: Food Security & Nutrition in the US
# Analysis – Two Questions for a Political Audience
#
# Question 1: How tightly does poverty drive food insecurity, malnutrition,
#             and starvation across US states?
#
# Question 2: What actually happens to food-insecure children when they grow up?
#             Do they escape the cycle, or does hunger follow them into adulthood?
#
# 5 interactive charts, saved as standalone HTML files.
# All data comes from Assignment6_DataSource.py outputs in /data/.
# =============================================================================

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths and output folder
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Colour palette — consistent across all charts
# ---------------------------------------------------------------------------
RED        = "#c0392b"    # hunger / high food insecurity
ORANGE     = "#e67e22"    # elevated risk
YELLOW     = "#f1c40f"    # moderate
GREEN      = "#27ae60"    # low food insecurity / good outcome
BLUE       = "#2980b9"    # male / general data series
PINK       = "#e91e8c"    # female
DARK_GREY  = "#2c3e50"    # text / axis labels
LIGHT_GREY = "#ecf0f1"    # background

# Shared Plotly layout defaults
BASE_LAYOUT = dict(
    font=dict(family="Arial, sans-serif", size=14, color=DARK_GREY),
    paper_bgcolor="white",
    plot_bgcolor="#f9f9f9",
    margin=dict(t=100, b=80, l=80, r=60),
)

# Lookup table: 2-digit FIPS code → 2-letter state abbreviation
# Needed to join Census FIPS data with ERS state abbreviation data
FIPS_TO_ABBR = {
    "01":"AL","02":"AK","04":"AZ","05":"AR","06":"CA","08":"CO","09":"CT",
    "10":"DE","11":"DC","12":"FL","13":"GA","15":"HI","16":"ID","17":"IL",
    "18":"IN","19":"IA","20":"KS","21":"KY","22":"LA","23":"ME","24":"MD",
    "25":"MA","26":"MI","27":"MN","28":"MS","29":"MO","30":"MT","31":"NE",
    "32":"NV","33":"NH","34":"NJ","35":"NM","36":"NY","37":"NC","38":"ND",
    "39":"OH","40":"OK","41":"OR","42":"PA","44":"RI","45":"SC","46":"SD",
    "47":"TN","48":"TX","49":"UT","50":"VT","51":"VA","53":"WA","54":"WV",
    "55":"WI","56":"WY",
}
ABBR_TO_STATE = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"Dist. of Columbia",
    "FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois",
    "IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan",
    "MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana",
    "NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey",
    "NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota",
    "OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania",
    "RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
    "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
    "US":"U.S. total",
}

# Education level labels from CPS PEEDUCA codes
# Values -1 mean "not applicable" (respondent too young to have education data)
EDUC_LABELS = {
    31: "< 1st grade",
    32: "1st–4th grade",
    33: "5th–6th grade",
    34: "7th–8th grade",
    35: "9th grade",
    36: "10th grade",
    37: "11th grade",
    38: "12th, no diploma",
    39: "High school / GED",
    40: "Some college",
    41: "Associate (vocational)",
    42: "Associate (academic)",
    43: "Bachelor's degree",
    44: "Master's degree",
    45: "Professional degree",
    46: "Doctoral degree",
}

# Grouped education labels for cleaner chart display
EDUC_GROUPS = {
    31: "No schooling",
    32: "No schooling",
    33: "Elementary",
    34: "Middle school",
    35: "Some high school",
    36: "Some high school",
    37: "Some high school",
    38: "Some high school",
    39: "HS diploma / GED",
    40: "Some college",
    41: "Associate degree",
    42: "Associate degree",
    43: "Bachelor's degree",
    44: "Graduate degree",
    45: "Graduate degree",
    46: "Graduate degree",
}

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Loading data …")

# CPS microdata: one row per person, 2023 survey
cps = pd.read_csv(DATA_DIR / "cps_foodsec_2023.csv", dtype=str)
for col in ["HRFS12M1", "PESEX", "PRTAGE", "HHSUPWGT", "GESTFIPS", "HRPOOR",
            "PEEDUCA", "HESP1"]:
    cps[col] = pd.to_numeric(cps[col], errors="coerce")

# Food insecurity flag: HRFS12M1=2 (low) or 3 (very low)
cps["food_insecure"]      = cps["HRFS12M1"].isin([2, 3])
cps["very_low_food_sec"]  = cps["HRFS12M1"] == 3          # "starvation level"
cps["below_poverty"]      = cps["HRPOOR"] == 1            # below 185% poverty line
cps["on_snap"]            = cps["HESP1"]  == 1
cps["sex_label"]          = cps["PESEX"].map({1: "Male", 2: "Female"})
cps["state_abbr"]         = cps["GESTFIPS"].astype("Int64").astype(str).str.zfill(2).map(FIPS_TO_ABBR)

# Age groups matching the DataSource aggregation
age = cps["PRTAGE"]
cps["age_group"] = pd.cut(
    age,
    bins=[0, 5, 18, 35, 65, 120],
    labels=["Under 5", "5-17", "18-34", "35-64", "65+"],
    right=False,
)

# Only keep adults (18+) for the education analysis — children don't have
# meaningful education attainment data in CPS
cps_adults = cps[cps["PRTAGE"] >= 18].copy()
cps_adults["educ_group"] = cps_adults["PEEDUCA"].map(EDUC_GROUPS)

# ACS 2022 poverty by state (one row per state)
acs = pd.read_csv(DATA_DIR / "acs_poverty_by_state_2022.csv")
acs["state_abbr"] = acs["state"].astype(str).str.zfill(2).map(FIPS_TO_ABBR)

# ERS official 3-year rolling state food insecurity rates
ers_state_raw = pd.read_csv(DATA_DIR / "ers_foodsecurity-state-2024.csv")
ers_state_raw.columns = ers_state_raw.columns.str.strip()
# The year column uses an en-dash (–) encoded as \x96; keep just the end year
# e.g. "2022–2024" → end_year = 2024
ers_state_raw["end_year"] = (
    ers_state_raw["Year"].str.replace("\x96", "–")
                         .str.split("–").str[-1]
                         .astype(int)
)
# Most recent 3-year period available
ers_state = ers_state_raw[ers_state_raw["end_year"] == ers_state_raw["end_year"].max()].copy()
ers_state.rename(columns={
    "State": "state_abbr",
    "Food insecurity prevalence": "fi_rate",
    "Very low food security prevalence": "vl_rate",
}, inplace=True)
ers_state["state_name"] = ers_state["state_abbr"].map(ABBR_TO_STATE)
# Remove the national total row for state-level comparisons
ers_state_only = ers_state[ers_state["state_abbr"] != "U.S. total"].copy()

# ERS national food insecurity by income-to-poverty ratio
ers_hh = pd.read_csv(DATA_DIR / "ers_foodsecurity-all-households-2024.csv")
ers_hh["Food insecure-percent"] = pd.to_numeric(
    ers_hh["Food insecure-percent"], errors="coerce"
)
ers_hh["Very low food security-percent"] = pd.to_numeric(
    ers_hh["Very low food security-percent"], errors="coerce"
)

# ERS national food insecurity by education / employment (for trajectory story)
ers_educ_raw = pd.read_csv(DATA_DIR / "ers_foodsecurity-educ-emp-dis-2024.csv")
ers_educ_raw["Food insecure-percent"] = pd.to_numeric(
    ers_educ_raw["Food insecure-percent"], errors="coerce"
)
ers_educ_raw["Very low food security-percent"] = pd.to_numeric(
    ers_educ_raw["Very low food security-percent"], errors="coerce"
)

# CPS-based national food insecurity rate by age group (weighted)
agg_path = DATA_DIR / "food_insecurity_by_state_sex_age.csv"
agg_df = pd.read_csv(agg_path)
agg_df["GESTFIPS"] = pd.to_numeric(agg_df["GESTFIPS"], errors="coerce")
agg_df["state_abbr"] = agg_df["GESTFIPS"].astype("Int64").astype(str).str.zfill(2).map(FIPS_TO_ABBR)

print("  All data loaded.\n")


# =============================================================================
# CHART 1 — Poverty Drives Hunger: State-Level Correlation
#
# Each dot is a state. X = poverty rate (ACS 2022). Y = food insecurity rate
# (ERS official 3-year average). We overlay a regression line to show how
# tightly these two variables move together.
#
# Message to lawmakers: "This is not random. The states with the most poverty
# are exactly the states with the most hunger."
# =============================================================================
print("Building Chart 1 — Poverty vs Food Insecurity by State …")

# Merge ACS poverty data with ERS food insecurity data on state abbreviation
merged = acs.merge(ers_state_only[["state_abbr","fi_rate","vl_rate","state_name"]],
                   on="state_abbr", how="inner")
merged = merged.dropna(subset=["poverty_rate_pct", "fi_rate"])

# Linear regression
slope, intercept, r_val, p_val, _ = stats.linregress(
    merged["poverty_rate_pct"], merged["fi_rate"]
)
r2 = r_val ** 2
x_line = np.linspace(merged["poverty_rate_pct"].min(),
                     merged["poverty_rate_pct"].max(), 100)
y_line = slope * x_line + intercept

# Colour dots by how far above/below the trend line each state sits
residuals = merged["fi_rate"] - (slope * merged["poverty_rate_pct"] + intercept)
merged["dot_color"] = pd.cut(
    residuals,
    bins=[-999, -1.5, 1.5, 999],
    labels=["Better than expected", "Near trend", "Worse than expected"],
)
color_map = {
    "Better than expected": GREEN,
    "Near trend":           ORANGE,
    "Worse than expected":  RED,
}

fig1 = go.Figure()

# One trace per colour group so we get a legend
for label, color in color_map.items():
    subset = merged[merged["dot_color"] == label]
    fig1.add_trace(go.Scatter(
        x=subset["poverty_rate_pct"],
        y=subset["fi_rate"],
        mode="markers+text",
        marker=dict(size=12, color=color, opacity=0.85,
                    line=dict(width=1, color="white")),
        text=subset["state_abbr"],
        textposition="top center",
        textfont=dict(size=9, color=DARK_GREY),
        name=label,
        customdata=subset[["NAME", "poverty_rate_pct", "fi_rate", "vl_rate"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Poverty rate: %{customdata[1]:.1f}%<br>"
            "Food insecure: %{customdata[2]:.1f}%<br>"
            "Very low food security: %{customdata[3]:.1f}%"
            "<extra></extra>"
        ),
    ))

# Regression trend line
fig1.add_trace(go.Scatter(
    x=x_line, y=y_line,
    mode="lines",
    line=dict(color=DARK_GREY, width=2, dash="dash"),
    name=f"Trend line  (R² = {r2:.2f})",
    hoverinfo="skip",
))

# Annotation showing the R² and a plain-language interpretation
fig1.add_annotation(
    x=0.97, y=0.05, xref="paper", yref="paper",
    text=(f"<b>R² = {r2:.2f}</b><br>"
          f"A state's poverty rate explains<br>"
          f"<b>{r2*100:.0f}%</b> of the variation in its<br>"
          f"food insecurity rate."),
    showarrow=False,
    bgcolor="white",
    bordercolor=DARK_GREY,
    borderwidth=1,
    borderpad=8,
    align="left",
    font=dict(size=12),
)

fig1.update_layout(
    **BASE_LAYOUT,
    title=dict(
        text="<b>Poverty Drives Hunger: How Poverty Rate Predicts Food Insecurity by State</b><br>"
             "<sup>Each dot is a state — the higher the poverty rate, the higher the food insecurity rate</sup>",
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="State Poverty Rate (ACS 2022, %)", gridcolor=LIGHT_GREY),
    yaxis=dict(title="Food Insecurity Rate (ERS 3-yr avg, %)", gridcolor=LIGHT_GREY),
    legend=dict(x=0.01, y=0.99, bordercolor=LIGHT_GREY, borderwidth=1),
    hovermode="closest",
)

out1 = HTML_DIR / "A6_01_poverty_vs_food_insecurity.html"
fig1.write_html(str(out1), include_plotlyjs="cdn")
print(f"  Saved → {out1.name}\n")


# =============================================================================
# CHART 2 — The Steeper the Poverty, the Worse the Hunger
#
# Using ERS national data, shows food insecurity rates for households at
# different income-to-poverty ratio brackets. Moves from "barely surviving"
# (<100% poverty) through "working poor" to "comfortably above poverty".
#
# Message: "The problem isn't just being poor — it gets dramatically worse
# the deeper you fall below the poverty line."
# =============================================================================
print("Building Chart 2 — Food Insecurity by Income-to-Poverty Ratio …")

# Pull the income bracket rows from ERS (most recent year)
income_cats = [
    "Under 1.00",   # below poverty line
    "Under 1.30",   # 30% above poverty
    "Under 1.85",   # 85% above poverty (SNAP eligibility threshold)
    "1.85 and over", # above SNAP threshold
]
income_rows = (
    ers_hh[
        (ers_hh["Category"] == "Household income-to-poverty ratio") &
        (ers_hh["Subcategory"].isin(income_cats))
    ]
    .sort_values("Year", ascending=False)
    .drop_duplicates("Subcategory")
    .set_index("Subcategory")
    .reindex(income_cats)
)

bracket_labels = [
    "Below poverty line\n(<100%)",
    "Near poverty\n(<130%)",
    "Low income\n(<185%)\n← SNAP eligibility",
    "Above 185%\npoverty",
]
fi_pcts  = income_rows["Food insecure-percent"].values
vl_pcts  = income_rows["Very low food security-percent"].values
bar_colors = [RED, ORANGE, YELLOW, GREEN]

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    name="Food insecure (low + very low)",
    x=bracket_labels,
    y=fi_pcts,
    marker_color=bar_colors,
    opacity=0.9,
    text=[f"{v:.1f}%" for v in fi_pcts],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Food insecure: %{y:.1f}%<extra></extra>",
))

fig2.add_trace(go.Bar(
    name="Very low food security (starvation risk)",
    x=bracket_labels,
    y=vl_pcts,
    marker_color=[DARK_GREY]*4,
    opacity=0.6,
    text=[f"{v:.1f}%" for v in vl_pcts],
    textposition="inside",
    textfont=dict(color="white"),
    hovertemplate="<b>%{x}</b><br>Very low food security: %{y:.1f}%<extra></extra>",
))

# Reference line — national average food insecurity rate
national_avg = ers_hh[
    (ers_hh["Category"] == "All households") &
    (ers_hh["Subcategory"].isna())
].sort_values("Year", ascending=False).iloc[0]["Food insecure-percent"]

fig2.add_hline(
    y=national_avg,
    line_dash="dot",
    line_color=BLUE,
)
# Place the label in the open whitespace above the 4th bar (right side of chart)
fig2.add_annotation(
    xref="paper", yref="y",
    x=0.99, y=national_avg,
    text=f"National average: {national_avg:.1f}%",
    showarrow=False,
    xanchor="right", yanchor="bottom",
    font=dict(color=BLUE, size=12),
)

fig2.update_layout(
    **BASE_LAYOUT,
    title=dict(
        text="<b>The Deeper the Poverty, the Worse the Hunger</b><br>"
             "<sup>Food insecurity rate by household income level — national data</sup>",
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Household Income Relative to Poverty Line"),
    yaxis=dict(title="Share of Households (%)", gridcolor=LIGHT_GREY,
               range=[0, max(fi_pcts) * 1.2]),
    barmode="overlay",
    legend=dict(x=0.60, y=0.98),
    hovermode="closest",
)

out2 = HTML_DIR / "A6_02_food_insecurity_by_income_bracket.html"
fig2.write_html(str(out2), include_plotlyjs="cdn")
print(f"  Saved → {out2.name}\n")


# =============================================================================
# CHART 3 — Children Bear the Heaviest Burden
#
# National food insecurity rates by age group, split by sex.
# Uses the weighted CPS 2023 microdata aggregated in DataSource.
#
# Message: "Children — especially children under 5 — face the highest rates
# of food insecurity. This is not a background statistic. These are the
# formative years that shape a person's entire life."
# =============================================================================
print("Building Chart 3 — Food Insecurity by Age Group and Sex …")

# Compute national weighted food insecurity rates by age group + sex
# (we aggregate across all states from the state×sex×age file)
national_age = (
    agg_df.groupby(["age_group", "sex_label"], observed=True)
    .agg(total=("total_weighted", "sum"), insecure=("insecure_weighted", "sum"))
    .reset_index()
)
national_age["fi_rate"] = (national_age["insecure"] / national_age["total"] * 100).round(2)

age_order = ["Under 5", "5-17", "18-34", "35-64", "65+"]
national_age["age_group"] = pd.Categorical(
    national_age["age_group"], categories=age_order, ordered=True
)
national_age = national_age.sort_values("age_group")

fig3 = go.Figure()

for sex, color, offset in [("Female", PINK, -0.2), ("Male", BLUE, 0.2)]:
    sub = national_age[national_age["sex_label"] == sex]
    sub = sub.sort_values("age_group")
    fig3.add_trace(go.Bar(
        name=sex,
        x=sub["age_group"].astype(str),
        y=sub["fi_rate"],
        marker_color=color,
        opacity=0.85,
        text=[f"{v:.1f}%" for v in sub["fi_rate"]],
        textposition="outside",
        hovertemplate=f"<b>{sex}</b><br>Age: %{{x}}<br>Food insecure: %{{y:.1f}}%<extra></extra>",
    ))

# School-age children (5-17) have the highest rate — find the peak bar for the annotation
_peak_group = national_age.loc[national_age["fi_rate"].idxmax()]
_peak_rate   = _peak_group["fi_rate"]
_peak_age    = str(_peak_group["age_group"])

# Annotation pointing at the tallest bar
fig3.add_annotation(
    x=_peak_age,
    y=_peak_rate + 0.5,
    text=f"<b>School-age children (5-17)<br>face the highest food insecurity — {_peak_rate:.1f}%</b>",
    showarrow=True, arrowhead=2, ax=90, ay=-45,
    font=dict(size=12, color=RED), arrowcolor=RED,
)

fig3.update_layout(
    **BASE_LAYOUT,
    title=dict(
        text="<b>Children and Young Adults Bear the Heaviest Burden of Food Insecurity</b><br>"
             "<sup>National food insecurity rate by age group, 2023 CPS Food Security Supplement</sup>",
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Age Group"),
    yaxis=dict(title="Food Insecurity Rate (%)", gridcolor=LIGHT_GREY,
               range=[0, national_age["fi_rate"].max() * 1.25]),
    barmode="group",
    legend=dict(x=0.80, y=0.98),
)

out3 = HTML_DIR / "A6_03_food_insecurity_by_age_group.html"
fig3.write_html(str(out3), include_plotlyjs="cdn")
print(f"  Saved → {out3.name}\n")


# =============================================================================
# CHART 4 — Does Childhood Food Insecurity Follow You Into Adulthood?
#
# Scatter: state child food insecurity rate (ages 5–17) on the X axis,
# state young adult food insecurity rate (ages 18–34) on the Y axis.
# One dot per state.
#
# Message: "The states where children go hungry are the same states where
# young adults go hungry a decade later. Hunger is a cycle — it doesn't
# disappear when a child turns 18."
# =============================================================================
print("Building Chart 4 — Child vs Young Adult Food Insecurity by State …")

# Compute state-level food insecurity rate for each age group
# Combine male + female together for each state × age group
state_age_national = (
    agg_df.groupby(["GESTFIPS", "state_abbr", "age_group"], observed=True)
    .agg(total=("total_weighted", "sum"), insecure=("insecure_weighted", "sum"))
    .reset_index()
)
state_age_national["fi_rate"] = (
    state_age_national["insecure"] / state_age_national["total"] * 100
).round(2)

# Pivot so we have one row per state with columns for each age group
pivot = (
    state_age_national.pivot(index=["GESTFIPS", "state_abbr"],
                              columns="age_group", values="fi_rate")
    .reset_index()
)
pivot.columns.name = None
pivot = pivot.rename(columns={"5-17": "child_fi", "18-34": "young_adult_fi"})
pivot = pivot.dropna(subset=["child_fi", "young_adult_fi"])

# Merge in state names
pivot["state_name"] = pivot["state_abbr"].map(ABBR_TO_STATE)

# Regression line for child → young adult correlation
slope4, intercept4, r4, p4, _ = stats.linregress(
    pivot["child_fi"], pivot["young_adult_fi"]
)
r2_4 = r4 ** 2
x4 = np.linspace(pivot["child_fi"].min(), pivot["child_fi"].max(), 100)
y4 = slope4 * x4 + intercept4

fig4 = go.Figure()

fig4.add_trace(go.Scatter(
    x=pivot["child_fi"],
    y=pivot["young_adult_fi"],
    mode="markers+text",
    marker=dict(
        size=13,
        color=pivot["child_fi"],
        colorscale=[[0, GREEN], [0.5, ORANGE], [1, RED]],
        showscale=False,
        line=dict(width=1, color="white"),
    ),
    text=pivot["state_abbr"],
    textposition="top center",
    textfont=dict(size=9),
    customdata=pivot[["state_name", "child_fi", "young_adult_fi"]].values,
    hovertemplate="<b>%{customdata[0]}</b><br>Children (5-17) food insecure: %{customdata[1]:.1f}%<br>Young adults (18-34) food insecure: %{customdata[2]:.1f}%<extra></extra>",
    name="States",
))

fig4.add_trace(go.Scatter(
    x=x4, y=y4,
    mode="lines",
    line=dict(color=DARK_GREY, width=2, dash="dash"),
    name=f"Trend line (R² = {r2_4:.2f})",
    hoverinfo="skip",
))

fig4.add_annotation(
    x=0.03, y=0.97, xref="paper", yref="paper",
    text=(f"<b>R² = {r2_4:.2f}</b><br>"
          f"States where children go hungry<br>"
          f"are the <b>same states</b> where<br>"
          f"young adults go hungry."
    ),
    showarrow=False,
    bgcolor="white",
    bordercolor=DARK_GREY,
    borderwidth=1,
    borderpad=8,
    align="left",
    font=dict(size=12),
)

# Diagonal reference — "if child rate equalled young adult rate"
max_val = max(pivot["child_fi"].max(), pivot["young_adult_fi"].max())
fig4.add_trace(go.Scatter(
    x=[0, max_val], y=[0, max_val],
    mode="lines",
    line=dict(color=LIGHT_GREY, width=1, dash="dot"),
    name="Equal rates (reference)",
    hoverinfo="skip",
))

# Label the equal-rates diagonal directly on the chart
fig4.add_annotation(
    x=max_val * 0.72, y=max_val * 0.72,
    text="Equal rates",
    showarrow=False,
    font=dict(size=10, color="#aaa"),
    textangle=-45,
    xanchor="center",
)

fig4.update_layout(
    **BASE_LAYOUT,
    title=dict(
        text="<b>Hunger Follows Children Into Adulthood</b><br>"
             "<sup>States where children (5-17) face high food insecurity also have "
             "high young adult (18-34) food insecurity — 2023 CPS data</sup>",
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Child Food Insecurity Rate — Ages 5-17 (%)", gridcolor=LIGHT_GREY),
    yaxis=dict(title="Young Adult Food Insecurity Rate — Ages 18-34 (%)",
               gridcolor=LIGHT_GREY),
    legend=dict(x=0.65, y=0.05),
    hovermode="closest",
)

out4 = HTML_DIR / "A6_04_child_to_adult_insecurity.html"
fig4.write_html(str(out4), include_plotlyjs="cdn")
print(f"  Saved → {out4.name}\n")


# =============================================================================
# CHART 5 — Education Level and Adult Food Insecurity: The Cycle Revealed
#
# Bar chart from ERS data: food insecurity rate by highest education level.
# Shows how adults with less education face dramatically higher food insecurity —
# and since childhood hunger is one of the biggest predictors of lower
# educational attainment, this chart completes the story.
#
# Message: "Food-insecure children are more likely to drop out, less likely
# to graduate college, and end up in exactly this chart — food insecure
# adults. The cycle is self-reinforcing unless we intervene early."
# =============================================================================
print("Building Chart 5 — Food Insecurity by Education Level …")

educ_rows = (
    ers_educ_raw[
        (ers_educ_raw["Subcategory"] == "Education") &
        ers_educ_raw["Food insecure-percent"].notna()
    ]
    .sort_values("Year", ascending=False)
    .drop_duplicates("Sub-subcategory")
    .copy()
)

# Canonical order: least educated to most educated
educ_order = [
    "Less than high school",
    "High School",
    "Some College",
    "College or more",
]
educ_rows = educ_rows[educ_rows["Sub-subcategory"].isin(educ_order)]
educ_rows["Sub-subcategory"] = pd.Categorical(
    educ_rows["Sub-subcategory"], categories=educ_order, ordered=True
)
educ_rows = educ_rows.sort_values("Sub-subcategory")

educ_labels_short = [
    "Less than\nhigh school",
    "High school\ngrad / GED",
    "Some college",
    "College\nor more",
]
fi_educ = educ_rows["Food insecure-percent"].values
vl_educ = educ_rows["Very low food security-percent"].values
educ_colors = [RED, ORANGE, YELLOW, GREEN]

fig5 = go.Figure()

fig5.add_trace(go.Bar(
    name="Food insecure (any level)",
    x=educ_labels_short,
    y=fi_educ,
    marker_color=educ_colors,
    opacity=0.9,
    text=[f"{v:.1f}%" for v in fi_educ],
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Food insecure: %{y:.1f}%<extra></extra>"
    ),
))

fig5.add_trace(go.Bar(
    name="Very low food security (starvation risk)",
    x=educ_labels_short,
    y=vl_educ,
    marker_color=[DARK_GREY]*4,
    opacity=0.55,
    text=[f"{v:.1f}%" for v in vl_educ],
    textposition="inside",
    textfont=dict(color="white"),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Very low food security: %{y:.1f}%<extra></extra>"
    ),
))

fig5.add_hline(
    y=national_avg,
    line_dash="dot",
    line_color=BLUE,
)
# Label placed in the open whitespace above the college bar on the right
fig5.add_annotation(
    xref="paper", yref="y",
    x=0.99, y=national_avg,
    text=f"National average: {national_avg:.1f}%",
    showarrow=False,
    xanchor="right", yanchor="bottom",
    font=dict(color=BLUE, size=12),
)

# Show how much higher the least-educated group is vs most-educated
ratio = fi_educ[0] / fi_educ[-1]
fig5.add_annotation(
    x=0.01, y=1.05, xref="paper", yref="paper",
    text=(
        f"Adults without a high school diploma are<br>"
        f"<b>{ratio:.1f}×</b> more likely to be food insecure<br>"
        f"than college graduates."
    ),
    showarrow=False,
    xanchor="left", yanchor="top",
    bgcolor="#fff8e1",
    bordercolor=ORANGE,
    borderwidth=1.5,
    borderpad=8,
    font=dict(size=12),
)

fig5.update_layout(
    **BASE_LAYOUT,
    title=dict(
        text="<b>Less Education, More Hunger — The Cycle Adults Can't Escape</b><br>"
             "<sup>Food insecurity rate by highest education level completed — national ERS data</sup>",
        x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Highest Education Level Completed"),
    yaxis=dict(title="Share of Households Food Insecure (%)",
               gridcolor=LIGHT_GREY, range=[0, max(fi_educ) * 1.3]),
    barmode="overlay",
    legend=dict(x=0.55, y=0.78),
)

out5 = HTML_DIR / "A6_05_food_insecurity_by_education.html"
fig5.write_html(str(out5), include_plotlyjs="cdn")
print(f"  Saved → {out5.name}\n")


# =============================================================================
# CHART 6 — The Full Story: A Summary Dashboard for Lawmakers
#
# Four-panel overview combining the key findings into one slide:
#   Top-left:  Poverty → Food insecurity state scatter (small version)
#   Top-right: Food insecurity by income bracket (bar)
#   Bot-left:  Food insecurity by age group (bar)
#   Bot-right: Education attainment vs food insecurity (bar)
#
# This is the chart you hand to a legislator who only has 5 minutes.
# =============================================================================
print("Building Chart 6 — Summary Dashboard …")

fig6 = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "① Poverty rate → food insecurity rate by state",
        "② Hunger intensifies as income falls below poverty line",
        "③ Children face the highest food insecurity rates",
        "④ Less education = more food insecurity — the adult cycle",
    ),
    vertical_spacing=0.16,
    horizontal_spacing=0.10,
)

# Panel 1 — state scatter (smaller, no text labels)
fig6.add_trace(go.Scatter(
    x=merged["poverty_rate_pct"],
    y=merged["fi_rate"],
    mode="markers",
    marker=dict(size=7, color=merged["poverty_rate_pct"],
                colorscale=[[0, GREEN], [1, RED]], opacity=0.8),
    hovertext=merged["NAME"],
    hovertemplate="<b>%{hovertext}</b><br>Poverty: %{x:.1f}%<br>Food insecure: %{y:.1f}%<extra></extra>",
    showlegend=False,
), row=1, col=1)
fig6.add_trace(go.Scatter(
    x=x_line, y=y_line, mode="lines",
    line=dict(color=DARK_GREY, dash="dash", width=1.5),
    showlegend=False, hoverinfo="skip",
), row=1, col=1)

# Panel 2 — income bracket bars
fig6.add_trace(go.Bar(
    x=["<100%", "<130%", "<185%", "≥185%"],
    y=fi_pcts,
    marker_color=bar_colors,
    showlegend=False,
    hovertemplate="<b>%{x}</b><br>Food insecure: %{y:.1f}%<extra></extra>",
), row=1, col=2)

# Panel 3 — age group bars (combined sexes)
age_combined = (
    national_age.groupby("age_group", observed=True)
    .apply(lambda g: pd.Series({
        "fi_rate": (g["insecure"].sum() / g["total"].sum() * 100).round(2)
    }))
    .reset_index()
)
age_combined["age_group"] = pd.Categorical(
    age_combined["age_group"], categories=age_order, ordered=True
)
age_combined = age_combined.sort_values("age_group")

fig6.add_trace(go.Bar(
    x=age_combined["age_group"].astype(str),
    y=age_combined["fi_rate"],
    marker_color=[RED, RED, ORANGE, ORANGE, GREEN],
    showlegend=False,
    hovertemplate="<b>%{x}</b><br>Food insecure: %{y:.1f}%<extra></extra>",
), row=2, col=1)

# Panel 4 — education bars
fig6.add_trace(go.Bar(
    x=educ_labels_short,
    y=fi_educ,
    marker_color=educ_colors,
    showlegend=False,
    hovertemplate="<b>%{x}</b><br>Food insecure: %{y:.1f}%<extra></extra>",
), row=2, col=2)

fig6.update_layout(
    font=dict(family="Arial, sans-serif", size=13, color=DARK_GREY),
    paper_bgcolor="white",
    plot_bgcolor="#f9f9f9",
    title=dict(
        text="<b>Food Insecurity in America: A Summary for Policymakers</b><br>"
             "<sup>Four charts — one message: poverty creates hunger, hunger traps children, "
             "and that trap follows them into adulthood</sup>",
        x=0.5, xanchor="center",
        font=dict(size=16),
    ),
    margin=dict(t=120, b=80, l=60, r=60),
    height=750,
)
fig6.update_xaxes(tickfont=dict(size=10))
fig6.update_yaxes(gridcolor=LIGHT_GREY)

out6 = HTML_DIR / "A6_06_summary_dashboard.html"
fig6.write_html(str(out6), include_plotlyjs="cdn")
print(f"  Saved → {out6.name}\n")


# =============================================================================
# Done
# =============================================================================
print("=" * 60)
print("All 6 charts saved to:", HTML_DIR)
print("=" * 60)
print()
print("Chart summary:")
print(f"  A6_01 — Poverty vs Food Insecurity by State (scatter, R²={r2:.2f})")
print(f"  A6_02 — Food Insecurity by Income Bracket (bar)")
print(f"  A6_03 — Food Insecurity by Age Group & Sex (bar)")
print(f"  A6_04 — Child → Young Adult Insecurity by State (scatter, R²={r2_4:.2f})")
print(f"  A6_05 — Food Insecurity by Education Level (bar)")
print(f"  A6_06 — Summary Dashboard (4-panel overview)")
print()
print("Key findings:")
print(f"  • Poverty rate explains {r2*100:.0f}% of variation in state food insecurity")
print(f"  • Households below the poverty line: {fi_pcts[0]:.1f}% food insecure "
      f"vs {fi_pcts[3]:.1f}% above 185% poverty")
print(f"  • Child→young adult correlation R²={r2_4:.2f}: "
      f"hungry children become hungry adults")
print(f"  • Education multiplier: "
      f"{fi_educ[0]:.1f}% insecure (no HS) vs {fi_educ[3]:.1f}% (college grad)")
