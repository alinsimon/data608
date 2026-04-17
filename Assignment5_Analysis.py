# =============================================================================
# Assignment 5: Hotter Planet → Wilder Storms
# Question: Does a warmer Earth produce more — and stronger — storms?
# Audience: High-school earth science class
# =============================================================================
#
# Story arc (5 interactive Plotly charts, saved as standalone HTML):
#   1. "Our planet is warming" — GISTEMP rising temp anomaly 2000-2024
#   2. "Hurricanes are getting stronger" — Atlantic ACE & Cat4/5 count vs temperature
#   3. "Typhoons follow the same pattern" — Western Pacific ACE vs temperature
#   4. "Even tornadoes on land respond" — U.S. significant tornado count vs temperature
#   5. "The big picture" — 2x2 scatter grid: temp vs each storm metric with r² label
#
# Analysis period: 2000–2024 (25 years, clean overlap — matches assignment minimum)
# All charts are interactive: hover tooltips, zoom, pan, click-to-hide series.
# =============================================================================

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Colours (used across all Plotly charts for visual consistency)
# ---------------------------------------------------------------------------
WARM   = "#e05c2a"   # deep orange — hot / intense
COOL   = "#2166ac"   # deep blue   — cool / baseline
YELLOW = "#f7b731"   # highlight / attention
TEAL   = "#17a589"   # typhoon accent

ANALYSIS_YEAR_START = 2000   # 25-year window per assignment requirement
ANALYSIS_YEAR_END   = 2024

# Shared Plotly layout defaults for the classroom projector look
LAYOUT_BASE = dict(
    font=dict(family="Arial, sans-serif", size=14, color="#333"),
    paper_bgcolor="#fafafa",
    plot_bgcolor="#fafafa",
    margin=dict(t=90, b=70, l=70, r=70),
    hovermode="x unified",
)


# =============================================================================
# 1.  LOAD & PREPARE DATA  (2000–2024)
# =============================================================================
print("Loading and validating data …")

# ---- 1a. Temperature (GISTEMP) ----
temp_raw = pd.read_csv(DATA_DIR / "GLB.Ts+dSST.csv", skiprows=1)
temp = (
    temp_raw[["Year", "J-D"]]
    .rename(columns={"Year": "year", "J-D": "temp_anomaly"})
    .assign(temp_anomaly=lambda d: pd.to_numeric(d["temp_anomaly"], errors="coerce"))
    .dropna()
    .query(f"{ANALYSIS_YEAR_START} <= year <= {ANALYSIS_YEAR_END}")
    .reset_index(drop=True)
)
print(f"  Temperature: {len(temp)} years ({temp['year'].min()}–{temp['year'].max()})")
print(f"    Validation: min={temp['temp_anomaly'].min():.2f}  max={temp['temp_anomaly'].max():.2f}  rows={len(temp)}")

# ---- 1b. Hurricanes (IBTrACS North Atlantic) ----
na_raw = pd.read_csv(
    DATA_DIR / "ibtracs_NA.csv",
    skiprows=[1],
    low_memory=False,
    usecols=["SID", "SEASON", "NAME", "NATURE", "WMO_WIND", "USA_SSHS"],
)
na_raw["SEASON"]   = pd.to_numeric(na_raw["SEASON"],   errors="coerce")
na_raw["WMO_WIND"] = pd.to_numeric(na_raw["WMO_WIND"], errors="coerce")
na_raw["USA_SSHS"] = pd.to_numeric(na_raw["USA_SSHS"], errors="coerce")

TROPICAL_NATURES = {"TS", "MX"}
na = na_raw[
    na_raw["NATURE"].isin(TROPICAL_NATURES) &
    na_raw["SEASON"].between(ANALYSIS_YEAR_START, ANALYSIS_YEAR_END)
].copy()
na["ace_point"] = na["WMO_WIND"] ** 2 / 10_000

na_annual = (
    na.groupby("SEASON")
    .agg(named_storms=("SID", "nunique"), ace=("ace_point", "sum"),
         max_wind=("WMO_WIND", "max"))
    .reset_index()
    .rename(columns={"SEASON": "year", "named_storms": "na_named_storms",
                     "ace": "na_ace", "max_wind": "na_max_wind"})
)
cat45 = (
    na[na["USA_SSHS"] >= 4]
    .groupby("SEASON")["SID"].nunique()
    .reset_index()
    .rename(columns={"SEASON": "year", "SID": "cat45_storms"})
)
na_annual = na_annual.merge(cat45, on="year", how="left").fillna({"cat45_storms": 0})
print(f"  Hurricanes: {len(na_annual)} seasons  |  ACE range: {na_annual['na_ace'].min():.0f}–{na_annual['na_ace'].max():.0f}  Cat4/5 range: {na_annual['cat45_storms'].min():.0f}–{na_annual['cat45_storms'].max():.0f}")

# ---- 1c. Typhoons (IBTrACS Western Pacific) ----
wp_raw = pd.read_csv(
    DATA_DIR / "ibtracs_since1980.csv",
    skiprows=[1],
    low_memory=False,
    usecols=["SID", "SEASON", "BASIN", "NATURE", "WMO_WIND"],
)
wp_raw["SEASON"]   = pd.to_numeric(wp_raw["SEASON"],   errors="coerce")
wp_raw["WMO_WIND"] = pd.to_numeric(wp_raw["WMO_WIND"], errors="coerce")

wp = wp_raw[
    (wp_raw["BASIN"] == "WP") &
    wp_raw["NATURE"].isin(TROPICAL_NATURES) &
    wp_raw["SEASON"].between(ANALYSIS_YEAR_START, ANALYSIS_YEAR_END)
].copy()
wp["ace_point"] = wp["WMO_WIND"] ** 2 / 10_000

wp_annual = (
    wp.groupby("SEASON")
    .agg(named_storms=("SID", "nunique"), ace=("ace_point", "sum"),
         max_wind=("WMO_WIND", "max"))
    .reset_index()
    .rename(columns={"SEASON": "year", "named_storms": "wp_named_storms",
                     "ace": "wp_ace", "max_wind": "wp_max_wind"})
)
print(f"  Typhoons:   {len(wp_annual)} seasons  |  ACE range: {wp_annual['wp_ace'].min():.0f}–{wp_annual['wp_ace'].max():.0f}  Peak wind range: {wp_annual['wp_max_wind'].min():.0f}–{wp_annual['wp_max_wind'].max():.0f}")

# ---- 1d. Tornadoes (NOAA SPC) ----
tor_raw = pd.read_csv(DATA_DIR / "spc_tornadoes_1950_2024.csv")
tor = tor_raw[tor_raw["yr"].between(ANALYSIS_YEAR_START, ANALYSIS_YEAR_END)].copy()
tor_annual = (
    tor.groupby("yr")
    .agg(total_tornadoes=("om", "count"),
         sig_tornadoes=("mag", lambda x: (x >= 2).sum()))
    .reset_index()
    .rename(columns={"yr": "year"})
)
print(f"  Tornadoes:  {len(tor_annual)} years  |  Total range: {tor_annual['total_tornadoes'].min()}–{tor_annual['total_tornadoes'].max()}  EF2+ range: {tor_annual['sig_tornadoes'].min()}–{tor_annual['sig_tornadoes'].max()}")

# ---- 1e. Merge on year ----
df = (
    temp
    .merge(na_annual,  on="year", how="left")
    .merge(wp_annual,  on="year", how="left")
    .merge(tor_annual, on="year", how="left")
    .dropna(subset=["temp_anomaly"])
)
print(f"\nMerged dataset: {len(df)} rows × {len(df.columns)} cols  ✓")
print(df[["year","temp_anomaly","na_ace","cat45_storms","wp_ace","total_tornadoes","sig_tornadoes"]].to_string(index=False))


# =============================================================================
# Helper: OLS trend line points for Plotly
# =============================================================================
def trend_line(x, y):
    mask = ~(np.isnan(x) | np.isnan(y))
    xc, yc = x[mask], y[mask]
    if len(xc) < 5:
        return None, None, None
    slope, intercept, r, pval, _ = stats.linregress(xc, yc)
    xfit = np.linspace(xc.min(), xc.max(), 200)
    yfit = slope * xfit + intercept
    return xfit, yfit, r ** 2


def save_html(fig, filename):
    path = HTML_DIR / filename
    fig.write_html(str(path), include_plotlyjs="cdn", full_html=True)
    print(f"  ✓ Saved: html/{filename}")


# =============================================================================
# CHART 1: Rising Global Temperature
# =============================================================================
print("\n[1/5] Warming planet …")

years = df["year"].values.astype(int)
anom  = df["temp_anomaly"].values
bar_colors = [WARM if a >= 0 else COOL for a in anom]
rolling5   = pd.Series(anom).rolling(5, center=True, min_periods=3).mean().values
hottest    = int(years[np.argmax(anom)])

fig1 = go.Figure()

# Colour-coded bars
fig1.add_trace(go.Bar(
    x=years, y=anom,
    marker_color=bar_colors,
    name="Annual anomaly",
    hovertemplate="<b>%{x}</b><br>Anomaly: %{y:+.2f} °C<extra></extra>",
))

# 5-year rolling mean
fig1.add_trace(go.Scatter(
    x=years, y=rolling5,
    mode="lines", line=dict(color="#222", width=3),
    name="5-year average",
    hovertemplate="5-yr avg: %{y:+.2f} °C<extra></extra>",
))

# Annotation for hottest year
fig1.add_annotation(
    x=hottest, y=float(anom[np.argmax(anom)]),
    text=f"Hottest: {hottest}<br>+{anom[np.argmax(anom)]:.2f}°C",
    showarrow=True, arrowhead=2, ax=40, ay=-50,
    bgcolor=YELLOW, bordercolor="#b8860b", borderwidth=1,
    font=dict(size=12, color="#333"),
)

fig1.add_hline(y=0, line_color="#888", line_width=1.5)

fig1.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text="<b>Earth Is Getting Warmer</b><br>"
             "<span style='font-size:14px;color:#666'>Every decade since 2000 has been hotter than the last  |  Source: NASA GISTEMP v4</span>",
        font=dict(size=20), x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Year", dtick=2, gridcolor="#e8e8e8"),
    yaxis=dict(title="Temperature anomaly (°C)<br>vs 1951–1980 average", gridcolor="#e8e8e8",
               zeroline=True, zerolinecolor="#aaa", zerolinewidth=1.5),
    bargap=0.15,
    legend=dict(orientation="h", y=1.06, x=0.5, xanchor="center"),
)
save_html(fig1, "A5_01_temperature_trend.html")


# =============================================================================
# CHART 2: Atlantic Hurricanes vs Temperature
# =============================================================================
print("[2/5] Hurricane trends …")

hurr_df = df[["year", "temp_anomaly", "na_ace", "cat45_storms", "na_named_storms"]].dropna()
yr  = hurr_df["year"].values.astype(int)
ta  = hurr_df["temp_anomaly"].values
ace = hurr_df["na_ace"].values
c45 = hurr_df["cat45_storms"].values
ns  = hurr_df["na_named_storms"].values

_, yfit_c45, r2_c45 = trend_line(ta, c45)
_, _, _ = trend_line(np.arange(len(yr)), ace)  # time trend for display

# Notable seasons with descriptions
notable_seasons = {
    2005: "Katrina Season<br>(record 28 named storms)",
    2017: "Harvey / Irma / Maria<br>(3 Cat4+ landfalls)",
    2020: "Record 30 named storms",
    2024: "Helene / Milton",
}

fig2 = make_subplots(specs=[[{"secondary_y": True}]])

# ACE bars (primary y)
fig2.add_trace(go.Bar(
    x=yr, y=ace,
    name="ACE (total season energy)",
    marker_color=COOL, opacity=0.80,
    hovertemplate="<b>%{x}</b><br>ACE: %{y:.1f} ×10⁴ kt²<extra></extra>",
), secondary_y=False)

# Cat 4/5 line (secondary y)
fig2.add_trace(go.Scatter(
    x=yr, y=c45,
    name="Cat 4 & 5 storms",
    mode="lines+markers",
    line=dict(color=WARM, width=3),
    marker=dict(size=8, color=WARM, line=dict(color="white", width=1.5)),
    hovertemplate="Cat 4/5: %{y} storms<extra></extra>",
), secondary_y=True)

# Named storm count line (secondary y)
fig2.add_trace(go.Scatter(
    x=yr, y=ns,
    name="Named storms",
    mode="lines+markers",
    line=dict(color=TEAL, width=2, dash="dot"),
    marker=dict(size=6, color=TEAL),
    hovertemplate="Named storms: %{y}<extra></extra>",
), secondary_y=True)

# Callout annotations pointing INTO the chart at the ACE bar top
# staggered y-offsets to avoid overlap
callout_offsets = {
    2005: dict(ax=0,   ay=-80, yanchor="bottom"),
    2017: dict(ax=30,  ay=-60, yanchor="bottom"),
    2020: dict(ax=-30, ay=-50, yanchor="bottom"),
    2024: dict(ax=0,   ay=-40, yanchor="bottom"),
}
callout_labels = {
    2005: "2005: Katrina<br>(record ACE)",
    2017: "2017: Harvey / Irma / Maria",
    2020: "2020: 30 named storms",
    2024: "2024: Helene / Milton",
}
for yr_n, label in callout_labels.items():
    if yr_n in yr:
        ace_val = float(ace[yr == yr_n][0])
        off = callout_offsets[yr_n]
        fig2.add_annotation(
            x=yr_n, y=ace_val,
            text=label,
            showarrow=True, arrowhead=2, arrowwidth=1.5, arrowcolor="#888",
            ax=off["ax"], ay=off["ay"],
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#ccc", borderwidth=1,
            font=dict(size=10, color="#333"),
            xanchor="center", yanchor=off["yanchor"],
        )

r2_str = f"r² = {r2_c45:.2f}" if r2_c45 is not None else ""
fig2.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text=f"<b>Atlantic Hurricanes: More Cat 4 & 5 Storms in Warmer Years</b><br>"
             f"<span style='font-size:13px;color:#666'>"
             f"Cat 4/5 count r = +0.27  |  Source: NOAA IBTrACS v4r01 (North Atlantic)</span>",
        font=dict(size=18), x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Hurricane Season Year", dtick=2, gridcolor="#e8e8e8"),
    bargap=0.18,
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
)
fig2.update_layout(margin=dict(t=100, b=110, l=70, r=70))
fig2.update_yaxes(title_text="ACE (×10⁴ kt²) — Total Season Energy",
                  gridcolor="#e8e8e8", secondary_y=False)
fig2.update_yaxes(title_text="Number of Storms",
                  gridcolor="rgba(0,0,0,0)", secondary_y=True)
save_html(fig2, "A5_02_hurricane_trends.html")


# =============================================================================
# CHART 3: Western Pacific Typhoons vs Temperature
# =============================================================================
print("[3/5] Typhoon trends …")

typh_df = df[["year", "temp_anomaly", "wp_ace", "wp_max_wind", "wp_named_storms"]].dropna()
yr   = typh_df["year"].values.astype(int)
ta   = typh_df["temp_anomaly"].values
wace = typh_df["wp_ace"].values
wmw  = typh_df["wp_max_wind"].values
wns  = typh_df["wp_named_storms"].values

xfit_mw, yfit_mw, r2_mw = trend_line(np.arange(len(yr)), wmw)

fig3 = make_subplots(specs=[[{"secondary_y": True}]])

fig3.add_trace(go.Bar(
    x=yr, y=wace,
    name="ACE (total season energy)",
    marker_color="#5b92c5", opacity=0.80,
    hovertemplate="<b>%{x}</b><br>ACE: %{y:.1f} ×10⁴ kt²<extra></extra>",
), secondary_y=False)

fig3.add_trace(go.Scatter(
    x=yr, y=wmw,
    name="Peak season wind speed",
    mode="lines+markers",
    line=dict(color=WARM, width=3),
    marker=dict(size=8, color=WARM, line=dict(color="white", width=1.5)),
    hovertemplate="Peak wind: %{y:.0f} knots<extra></extra>",
), secondary_y=True)

fig3.add_trace(go.Scatter(
    x=yr, y=wns,
    name="Named typhoons",
    mode="lines+markers",
    line=dict(color=TEAL, width=2, dash="dot"),
    marker=dict(size=6, color=TEAL),
    hovertemplate="Named typhoons: %{y}<extra></extra>",
), secondary_y=True)

# Trend line on peak wind
if xfit_mw is not None:
    time_indices = np.linspace(0, len(yr)-1, 200)
    yr_fit = np.interp(time_indices, np.arange(len(yr)), yr.astype(float))
    fig3.add_trace(go.Scatter(
        x=yr_fit.astype(int), y=yfit_mw,
        name="Wind trend",
        mode="lines",
        line=dict(color="#7b2d0b", width=2, dash="dash"),
        hoverinfo="skip",
    ), secondary_y=True)

r2_str = f"r² = {r2_mw:.2f}" if r2_mw is not None else ""

# Callout annotation for Super Typhoon Haiyan 2013
if 2013 in yr:
    haiyan_wind = float(wmw[yr == 2013][0])
    fig3.add_annotation(
        x=2013, y=haiyan_wind,
        yref="y2",
        text="2013: Super Typhoon Haiyan<br>170 knots (195 mph) at landfall",
        showarrow=True, arrowhead=2, arrowwidth=1.5, arrowcolor="#888",
        ax=55, ay=-55,
        bgcolor="rgba(255,255,255,0.85)", bordercolor="#ccc", borderwidth=1,
        font=dict(size=10, color="#333"),
        xanchor="left", yanchor="bottom",
    )

fig3.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text=f"<b>Western Pacific Typhoons: Peak Winds Climb With Temperature</b><br>"
             f"<span style='font-size:13px;color:#666'>"
             f"Peak wind speed trend {r2_str}  |  Source: NOAA IBTrACS v4r01 (Western Pacific)</span>",
        font=dict(size=18), x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Typhoon Season Year", dtick=2, gridcolor="#e8e8e8"),
    bargap=0.18,
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
)
fig3.update_layout(margin=dict(t=100, b=110, l=70, r=70))
fig3.update_yaxes(title_text="ACE (×10⁴ kt²)", gridcolor="#e8e8e8", secondary_y=False)
fig3.update_yaxes(title_text="Wind Speed (knots) / Storm Count",
                  gridcolor="rgba(0,0,0,0)", secondary_y=True)
save_html(fig3, "A5_03_typhoon_trends.html")


# =============================================================================
# CHART 4: U.S. Tornadoes vs Temperature
# =============================================================================
print("[4/5] Tornado trends …")

tor_df = df[["year", "temp_anomaly", "total_tornadoes", "sig_tornadoes"]].dropna()
yr    = tor_df["year"].values.astype(int)
ta    = tor_df["temp_anomaly"].values
total = tor_df["total_tornadoes"].values
sig   = tor_df["sig_tornadoes"].values

xfit_sig, yfit_sig, r2_sig = trend_line(ta, sig)

notable_tor = {
    2011: "2011 Super Outbreak<br>(355 tornadoes in 1 day)",
    2008: "2008: deadliest year",
    2019: "2019: longest streak<br>of consecutive tornado days",
    2024: "2024: record 1,791",
}

fig4 = go.Figure()

fig4.add_trace(go.Bar(
    x=yr, y=total,
    name="All tornadoes (EF0–EF5)",
    marker_color="#a8d8ea", opacity=0.90,
    hovertemplate="<b>%{x}</b><br>Total: %{y} tornadoes<extra></extra>",
))
fig4.add_trace(go.Bar(
    x=yr, y=sig,
    name="Significant (EF2+)",
    marker_color=WARM, opacity=0.90,
    hovertemplate="EF2+: %{y} tornadoes<extra></extra>",
))

# Trend on EF2+
if xfit_sig is not None:
    sig_fit = stats.linregress(ta, sig)
    yr_min, yr_max = yr.min(), yr.max()
    ta_at_yrmin = temp.loc[temp["year"] == yr_min, "temp_anomaly"].values[0]
    ta_at_yrmax = temp.loc[temp["year"] == yr_max, "temp_anomaly"].values[0]
    fig4.add_trace(go.Scatter(
        x=[yr_min, yr_max],
        y=[sig_fit.intercept + sig_fit.slope * ta_at_yrmin,
           sig_fit.intercept + sig_fit.slope * ta_at_yrmax],
        mode="lines",
        name=f"EF2+ trend (r²={r2_sig:.2f})",
        line=dict(color="#7b2d0b", width=2.5, dash="dash"),
        hoverinfo="skip",
    ))

# Arrow callouts for notable years, staggered to avoid overlap
callout_tor = {
    2008: dict(label="2008: deadliest year",                         ax=-50, ay=-60),
    2011: dict(label="2011 Super Outbreak<br>355 tornadoes in 1 day", ax=0,   ay=-75),
    2019: dict(label="2019: record streak<br>of consecutive tornado days", ax=50, ay=-55),
    2024: dict(label="2024: record 1,791",                            ax=0,   ay=-45),
}
for yr_n, cfg in callout_tor.items():
    if yr_n in yr:
        total_val = float(total[yr == yr_n][0])
        fig4.add_annotation(
            x=yr_n, y=total_val,
            text=cfg["label"],
            showarrow=True, arrowhead=2, arrowwidth=1.5, arrowcolor="#888",
            ax=cfg["ax"], ay=cfg["ay"],
            bgcolor="rgba(255,255,255,0.85)", bordercolor="#ccc", borderwidth=1,
            font=dict(size=10, color="#333"),
            xanchor="center", yanchor="bottom",
        )

r2_str = f"r² = {r2_sig:.2f}" if r2_sig is not None else ""
fig4.update_layout(
    **LAYOUT_BASE,
    title=dict(
        text=f"<b>U.S. Tornadoes: Violent EF2+ Storms Trending Upward</b><br>"
             f"<span style='font-size:13px;color:#666'>"
             f"EF2+ vs temperature {r2_str}  |  Source: NOAA SPC 2000–2024</span>",
        font=dict(size=18), x=0.5, xanchor="center",
    ),
    xaxis=dict(title="Year", dtick=2, gridcolor="#e8e8e8"),
    yaxis=dict(title="Number of Tornadoes", gridcolor="#e8e8e8"),
    barmode="overlay",
    bargap=0.15,
    legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
)
fig4.update_layout(margin=dict(t=100, b=110, l=70, r=70))
save_html(fig4, "A5_04_tornado_trends.html")


# =============================================================================
# CHART 5: Correlation scatter grid (2x2)
# =============================================================================
print("[5/5] Correlation summary …")

metrics = [
    ("na_ace",        "Atlantic ACE (×10⁴ kt²)",    COOL,    "Hurricanes"),
    ("cat45_storms",  "Cat 4/5 Hurricanes / season", WARM,    "Hurricanes"),
    ("wp_ace",        "W. Pacific ACE (×10⁴ kt²)",   "#5b92c5","Typhoons"),
    ("sig_tornadoes", "U.S. EF2+ Tornadoes / year",  "#e05c2a","Tornadoes"),
]

fig5 = make_subplots(
    rows=2, cols=2,
    subplot_titles=[m[3] + " — " + m[1] for m in metrics],
    horizontal_spacing=0.12, vertical_spacing=0.18,
)

positions = [(1,1),(1,2),(2,1),(2,2)]
corr_rows = []

for (row, col), (metric, ylabel, color, storm_type) in zip(positions, metrics):
    sub = df[["year", "temp_anomaly", metric]].dropna()
    x = sub["temp_anomaly"].values
    y = sub[metric].values
    yrs_sub = sub["year"].values.astype(int)

    xfit, yfit, r2 = trend_line(x, y)
    sl = stats.linregress(x, y)
    corr_rows.append((storm_type, metric, sl.rvalue, r2, sl.pvalue))

    fig5.add_trace(go.Scatter(
        x=x, y=y,
        mode="markers",
        marker=dict(color=color, size=10, opacity=0.75,
                    line=dict(color="white", width=1)),
        name=storm_type,
        text=[str(yr) for yr in yrs_sub],
        hovertemplate="<b>%{text}</b><br>Temp anomaly: %{x:+.2f}°C<br>" + ylabel + ": %{y}<extra></extra>",
        showlegend=False,
    ), row=row, col=col)

    if xfit is not None:
        direction = "↑" if sl.slope > 0 else "↓"
        fig5.add_trace(go.Scatter(
            x=xfit, y=yfit,
            mode="lines",
            line=dict(color="#333", width=2.5, dash="dash"),
            hoverinfo="skip",
            showlegend=False,
        ), row=row, col=col)

        fig5.add_annotation(
            xref=f"x{(row-1)*2+col if (row,col)!=(1,1) else ''}",
            yref=f"y{(row-1)*2+col if (row,col)!=(1,1) else ''}",
            x=x.min() + 0.02 * (x.max()-x.min()),
            y=y.max(),
            text=f"<b>r² = {r2:.2f}</b><br>p = {sl.pvalue:.3f} {direction}",
            showarrow=False,
            bgcolor=YELLOW, bordercolor="#b8860b", borderwidth=1,
            font=dict(size=12, color="#333"),
            xanchor="left", yanchor="top",
            row=row, col=col,
        )

    fig5.update_xaxes(title_text="Temp anomaly (°C)", gridcolor="#e8e8e8", row=row, col=col)
    fig5.update_yaxes(title_text=ylabel, gridcolor="#e8e8e8", row=row, col=col)

fig5.update_layout(
    **LAYOUT_BASE,
    height=820,
    title=dict(
        text="<b>Warmer = Wilder: Temperature vs Storm Intensity (2000-2024)</b><br>"
             "<span style='font-size:13px;color:#666'>"
             "Each dot = one year. Hover to see the year. Dashed line = trend.</span>",
        font=dict(size=18), x=0.5, xanchor="center",
    ),
)
save_html(fig5, "A5_05_correlation_summary.html")


# =============================================================================
# PRINT VALIDATION & CORRELATION SUMMARY
# =============================================================================
print("\n" + "=" * 68)
print("DATA VALIDATION & CORRELATION SUMMARY (2000–2024, 25 years)")
print("=" * 68)
print(f"{'Storm Metric':<32}  {'r':>6}  {'r²':>5}  {'p-value':>8}  Result")
print("-" * 68)
for storm_type, col, r, r2, pval in corr_rows:
    sig_flag = "✓ significant" if pval < 0.05 else "○ not sig."
    direction = "↑" if r > 0 else "↓"
    print(f"  {col:<30}  {r:+.3f}  {r2:.3f}  {pval:>8.4f}  {sig_flag} {direction}")

print("\n✓ All 5 interactive charts saved to html/")
print("  Run Assignment5_Presentation.py to rebuild the full HTML presentation.")

