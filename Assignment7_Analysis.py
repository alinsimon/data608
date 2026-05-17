# =============================================================================
# Assignment 7: Critical Minerals Supply Chain Analysis
# Analysis & Visualization
#
# This creates six interactive visualizations that tell a clear story about
# US critical mineral vulnerabilities. After getting feedback on Assignment 6
# about charts being "difficult to interpret," I focused on making these
# super clear with dynamic controls and lots of annotations.
#
# What I improved:
#   - Every chart has one focused message
#   - Added dropdowns, sliders, and filters so you can explore the data
#   - Lots of annotations and explanatory text right on the charts
#   - Used intuitive colors (red=danger, green=safe)
#   - Designed the layout to guide your eye to the key insights
# =============================================================================

import warnings
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# We're loading data from CSV files (same approach as Assignment 6)
# Just make sure you've run Assignment7_Datasource.py first

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Set up our file paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(exist_ok=True)

# Load our datasets
df_minerals = pd.read_csv(DATA_DIR / "critical_minerals_catalog.csv")
df_sources = pd.read_csv(DATA_DIR / "mineral_sources_by_country.csv")
df_reliability = pd.read_csv(DATA_DIR / "source_reliability_scores.csv")
df_risk = pd.read_csv(DATA_DIR / "mineral_supply_risk_analysis.csv")

# ---------------------------------------------------------------------------
# Color scheme: using intuitive colors where red means danger and green means safe
# ---------------------------------------------------------------------------
CRITICAL_RED = "#d62728"
HIGH_RISK = "#ff7f0e"
MEDIUM_RISK = "#ffbb78"
LOW_RISK = "#98df8a"
SECURE_GREEN = "#2ca02c"

COMPETITOR_COLOR = "#d62728"  # Red for China, Russia
NEUTRAL_COLOR = "#ffbb78"     # Orange for most countries
ALLY_COLOR = "#2ca02c"        # Green for US allies

CHINA_COLOR = "#d62728"
RUSSIA_COLOR = "#8B0000"
ALLY_COLORS = "#2ca02c"

BACKGROUND = "#f9f9f9"
TEXT_COLOR = "#2c3e50"

# Base styling that all our charts will use
BASE_LAYOUT = dict(
    font=dict(family="Arial, sans-serif", size=13, color=TEXT_COLOR),
    paper_bgcolor="white",
    plot_bgcolor=BACKGROUND,
    margin=dict(t=120, b=80, l=80, r=80),
)

# Combine our datasets so we have everything in one place
df_full = df_sources.merge(
    df_reliability[['country', 'relationship', 'overall_score']], 
    on='country', 
    how='left'
)
df_full = df_full.merge(
    df_minerals[['mineral', 'category', 'strategic_importance']], 
    on='mineral', 
    how='left'
)


# =============================================================================
# CHART 1: Supply Chain Vulnerability Matrix (Interactive)
# This is the key chart that shows which minerals are in the danger zone
# =============================================================================
def create_vulnerability_matrix():
    """
    Creates an interactive scatter plot showing import reliance vs. source reliability.
    
    What you can do:
    - Use the dropdown to filter by mineral category
    - Drag the slider to focus on higher-risk minerals
    
    The story: Minerals in the top-left corner are in trouble—we import a lot
    of them and they come from unreliable sources.
    """
    
    # Bring in the category info for each mineral
    df_plot = df_risk.merge(df_minerals[['mineral', 'category']], on='mineral', how='left')
    
    # Build our category list for the dropdown
    categories = ['All Categories'] + sorted(df_plot['category'].dropna().unique().tolist())
    
    # Assign colors based on risk level
    risk_colors = {
        'Critical': CRITICAL_RED,
        'High': HIGH_RISK,
        'Medium': MEDIUM_RISK,
        'Low': LOW_RISK
    }
    
    fig = go.Figure()
    
    # Start with traces for the "All Categories" view
    for risk_cat in ['Low', 'Medium', 'High', 'Critical']:
        subset = df_plot[df_plot['risk_category'] == risk_cat]
        
        # Only show labels for the most important minerals to avoid clutter
        show_labels = risk_cat in ['Critical', 'High']
        
        fig.add_trace(go.Scatter(
            x=subset['avg_source_reliability'],
            y=subset['us_import_reliance_pct'],
            mode='markers+text' if show_labels else 'markers',
            name=f"{risk_cat} Risk",
            legendgroup=risk_cat,
            showlegend=True,  # Keep the legend visible for all risk levels
            marker=dict(
                size=14 if risk_cat in ['Critical', 'High'] else 10,
                color=risk_colors[risk_cat],
                line=dict(width=1.5, color='white'),
                opacity=0.85
            ),
            text=subset['mineral'],
            textposition='top center',
            textfont=dict(size=9, color=TEXT_COLOR, family='Arial Black'),
            hovertemplate=(
                "<b>%{text}</b><br>" +
                "Category: " + subset['category'].astype(str) + "<br>" +
                "Import Reliance: %{y:.0f}%<br>" +
                "Source Reliability: %{x:.1f}/10<br>" +
                "Risk Score: " + subset['composite_risk_score'].apply(lambda x: f"{x:.1f}").astype(str) + "<br>" +
                "<extra></extra>"
            ),
            visible=True
        ))
    
    # Now add traces for each individual category (hidden at first)
    for category in categories[1:]:
        for risk_cat in ['Low', 'Medium', 'High', 'Critical']:
            subset = df_plot[(df_plot['category'] == category) & 
                           (df_plot['risk_category'] == risk_cat)]
            
            # Show labels only for Critical and High risk minerals to reduce clutter
            show_labels = risk_cat in ['Critical', 'High']
            
            fig.add_trace(go.Scatter(
                x=subset['avg_source_reliability'],
                y=subset['us_import_reliance_pct'],
                mode='markers+text' if show_labels else 'markers',
                name=f"{risk_cat} Risk",
                legendgroup=risk_cat,
                showlegend=True,  # The legendgroup setting prevents duplicate labels in the legend
                marker=dict(
                    size=14 if risk_cat in ['Critical', 'High'] else 10,
                    color=risk_colors[risk_cat],
                    line=dict(width=1.5, color='white'),
                    opacity=0.85
                ),
                text=subset['mineral'],
                textposition='top center',
                textfont=dict(size=9, color=TEXT_COLOR, family='Arial Black'),
                hovertemplate=(
                    "<b>%{text}</b><br>" +
                    f"Category: {category}<br>" +
                    "Import Reliance: %{y:.0f}%<br>" +
                    "Source Reliability: %{x:.1f}/10<br>" +
                    "Risk Score: " + subset['composite_risk_score'].apply(lambda x: f"{x:.1f}").astype(str) + "<br>" +
                    "<extra></extra>"
                ),
                visible=False
            ))
    
    # Shade the danger zone (top-left): high imports from unreliable sources
    fig.add_shape(
        type="rect",
        x0=0, x1=5, y0=70, y1=100,
        fillcolor="rgba(214, 39, 40, 0.08)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_annotation(
        x=1.3, y=92,
        text="<b>High-Risk Quadrant</b><br><i>High import reliance + Low source reliability</i>",
        showarrow=False,
        font=dict(size=11, color=CRITICAL_RED),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(214, 39, 40, 0.3)",
        borderwidth=1,
        borderpad=6
    )
    
    # Shade the safe zone (bottom-right): low imports from reliable sources
    fig.add_shape(
        type="rect",
        x0=6.5, x1=10, y0=0, y1=35,
        fillcolor="rgba(44, 160, 44, 0.08)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_annotation(
        x=8.7, y=9.5,
        text="<b>Low-Risk Quadrant</b><br><i>Low import dependence + Reliable sources</i>",
        showarrow=False,
        font=dict(size=11, color=SECURE_GREEN),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="rgba(44, 160, 44, 0.3)",
        borderwidth=1,
        borderpad=6
    )
    
    # Build the category dropdown menu
    buttons = []
    traces_per_category = 4  # Four risk levels: Low, Medium, High, Critical
    
    # First button shows everything
    all_visible = [True] * traces_per_category + [False] * (len(fig.data) - traces_per_category)
    
    buttons.append(
        dict(
            label="All Categories",
            method="update",
            args=[{"visible": all_visible},
                  {"title": {
                      "text": "<b>US Critical Minerals: Supply Chain Vulnerability Matrix</b>",
                      "x": 0.5,
                      "xanchor": "center"
                  }}]
        )
    )
    
    # The rest of the buttons are for individual categories
    # (Remember: first 4 traces are "All Categories", then come the individual ones)
    for idx, category in enumerate(categories[1:]):
        visible = [False] * len(fig.data)
        # Skip past the "All Categories" traces to get to this category's data
        start_idx = traces_per_category + (idx * traces_per_category)
        for i in range(start_idx, start_idx + traces_per_category):
            if i < len(visible):
                visible[i] = True
        
        buttons.append(
            dict(
                label=category,
                method="update",
                args=[{"visible": visible},
                      {"title": {
                          "text": f"<b>US Critical Minerals: Supply Chain Vulnerability Matrix</b>",
                          "x": 0.5,
                          "xanchor": "center"
                      }}]
            )
        )
    
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text="<b>US Critical Minerals: Supply Chain Vulnerability Matrix</b>",
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="<b>Average Source Reliability Score</b><br>(10=Very Reliable Ally, 0=High-Risk Source)",
            range=[0, 10],
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            zeroline=True,
            zerolinecolor='rgba(150,150,150,0.5)'
        ),
        yaxis=dict(
            title="<b>US Import Reliance (%)</b><br>(% of apparent consumption from imports)",
            range=[0, 105],
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            zeroline=True,
            zerolinecolor='rgba(150,150,150,0.5)'
        ),
        legend=dict(
            title="<b>Risk Category</b>",
            x=0.98,
            y=0.98,
            xanchor='right',
            yanchor='top',
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#1e3c72",
            borderwidth=1
        ),
        updatemenus=[
            dict(
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.02,  # moved further left
                xanchor="left",
                y=1.21,
                yanchor="top",
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#1e3c72",
                borderwidth=2
            )
        ],
        annotations=[
            dict(
                text="<b>How to Read:</b> Top-left quadrant = Critical Risk (high import reliance + unreliable sources).<br>Use category dropdown to filter minerals.",
                x=0.01,
                xref="paper",
                y=0.98,
                yref="paper",
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font=dict(size=10, color=TEXT_COLOR),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgba(30,60,114,0.3)",
                borderwidth=1,
                borderpad=8
            ),
            dict(
                text="<b>Filter by Category:</b>",
                x=0.02,
                xref="paper",
                y=1.15,
                yref="paper",
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font=dict(size=12, color=TEXT_COLOR)
            )
        ] + list(fig.layout.annotations),  # Keep existing annotations (quadrant labels)
        hovermode='closest',
        height=700
    )
    
    output_file = HTML_DIR / "A7_01_vulnerability_matrix.html"
    fig.write_html(output_file)
    print(f"   ✓ Created vulnerability matrix (DYNAMIC): {output_file.name}")
    return fig


# =============================================================================
# CHART 2: China Dependency (Interactive)
# Shows just how dominant China is in critical mineral supply chains
# =============================================================================
def create_china_dependency_chart():
    """
    Creates an interactive bar chart of minerals by China exposure.
    
    What you can do:
    - Use the slider to filter by different dependency thresholds
    
    The story: China controls a scary percentage of many critical minerals
    """
    
    # Sort by China exposure (highest concern first)
    all_minerals = df_risk.sort_values('china_exposure_pct', ascending=False)
    
    # Match each risk level to its color
    colors_map = {
        'Critical': CRITICAL_RED,
        'High': HIGH_RISK,
        'Medium': MEDIUM_RISK,
        'Low': LOW_RISK
    }
    
    fig = go.Figure()
    
    # We'll create different views based on threshold: 0%, 25%, 50%, 75%
    thresholds = [0, 25, 50, 75]
    
    for threshold in thresholds:
        subset = all_minerals[all_minerals['china_exposure_pct'] >= threshold].head(25)
        
        colors = subset['risk_category'].map(colors_map)
        
        fig.add_trace(go.Bar(
            y=subset['mineral'],
            x=subset['china_exposure_pct'],
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(width=0.5, color='white')
            ),
            text=subset['china_exposure_pct'].apply(lambda x: f"{x:.0f}%"),
            textposition='outside',
            textfont=dict(size=11),
            hovertemplate=(
                "<b>%{y}</b><br>" +
                "China's Share: %{x:.1f}%<br>" +
                "Risk Category: " + subset['risk_category'].astype(str) + "<br>" +
                "<extra></extra>"
            ),
            visible=(threshold == 0)  # Start with the 0% threshold visible
        ))
    
    # Mark the 50% and 75% thresholds on the chart
    fig.add_vline(
        x=50, 
        line_dash="dash", 
        line_color="gray",
        annotation_text="50% threshold",
        annotation_position="top"
    )
    
    fig.add_vline(
        x=75, 
        line_dash="dash", 
        line_color=CRITICAL_RED,
        annotation_text="75% critical threshold",
        annotation_position="top"
    )
    
    # Build the slider that lets you adjust the threshold
    steps = []
    for i, threshold in enumerate(thresholds):
        subset_count = len(all_minerals[all_minerals['china_exposure_pct'] >= threshold])
        above_50 = len(all_minerals[(all_minerals['china_exposure_pct'] >= max(threshold, 50))])
        
        step = dict(
            method="update",
            args=[
                {"visible": [j == i for j in range(len(thresholds))]},
                {"title": {
                    "text": f"<b>China's Dominance in Critical Mineral Supply Chains</b><br>" +
                            f"<sub>Showing minerals with ≥{threshold}% China dependency " +
                            f"({subset_count} minerals meet this threshold)</sub>",
                    "x": 0.5,
                    "xanchor": "center"
                }}
            ],
            label=f"≥{threshold}%"
        )
        steps.append(step)
    
    sliders = [dict(
        active=0,
        yanchor="top",
        y=1.18,
        xanchor="left",
        x=0.15,
        currentvalue=dict(
            prefix="Show minerals with China dependency: ",
            visible=True,
            xanchor="left",
            font=dict(size=12)
        ),
        pad={"t": 50, "b": 10},
        len=0.6,
        steps=steps
    )]
    
    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=13, color=TEXT_COLOR),
        paper_bgcolor="white",
        plot_bgcolor=BACKGROUND,
        title=dict(
            text=(
                "<b>China's Dominance in Critical Mineral Supply Chains</b><br>"
                "<sub>Showing minerals with ≥0% China dependency (43 minerals meet this threshold)</sub>"
            ),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="<b>China's Share of US Imports or Global Production (%)</b>",
            range=[0, 105],
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="",
            showgrid=False
        ),
        sliders=sliders,
        height=900,
        showlegend=False,
        margin=dict(t=180, b=80, l=180, r=80)
    )
    
    output_file = HTML_DIR / "A7_02_china_dependency.html"
    fig.write_html(output_file)
    print(f"   ✓ Created China dependency chart (DYNAMIC): {output_file.name}")
    return fig


# =============================================================================
# CHART 3: Source Concentration by Category
# Which mineral categories have concentrated supply chains?
# =============================================================================
def create_source_diversification():
    """
    Box plot showing how concentrated supply chains are for each mineral category.
    
    The story: Rare earths and platinum group metals are highly concentrated
    (meaning just a few countries control most of the supply).
    """
    
    # Count how many sources each mineral has
    source_counts = df_sources.groupby(['mineral']).size().reset_index(name='num_sources')
    
    # Calculate the HHI (concentration index) for each mineral
    category_data = []
    for mineral in df_sources['mineral'].unique():
        sources = df_sources[df_sources['mineral'] == mineral]
        hhi = (sources['production_share'] ** 2).sum()
        category = df_minerals[df_minerals['mineral'] == mineral]['category'].iloc[0]
        num_sources = len(sources)
        
        category_data.append({
            'mineral': mineral,
            'category': category,
            'hhi': hhi,
            'num_sources': num_sources,
            'concentration_level': 'High' if hhi > 0.25 else 'Medium' if hhi > 0.15 else 'Low'
        })
    
    df_concentration = pd.DataFrame(category_data)
    
    # Build the box plot, one box per category
    fig = go.Figure()
    
    categories = df_concentration['category'].unique()
    category_colors = {
        'Rare Earth': CRITICAL_RED,
        'PGM': HIGH_RISK,
        'Energy & Battery': HIGH_RISK,
        'Technology': MEDIUM_RISK,
        'Industrial': LOW_RISK,
        'Agriculture': LOW_RISK
    }
    
    for cat in categories:
        subset = df_concentration[df_concentration['category'] == cat]
        
        fig.add_trace(go.Box(
            y=subset['hhi'],
            name=cat,
            marker=dict(color=category_colors.get(cat, NEUTRAL_COLOR)),
            boxmean='sd',
            hovertemplate=(
                "<b>%{fullData.name}</b><br>" +
                "HHI: %{y:.3f}<br>" +
                "<extra></extra>"
            )
        ))
    
    # Draw a line showing where "high concentration" starts
    fig.add_hline(
        y=0.25,
        line_dash="dash",
        line_color=CRITICAL_RED,
        annotation_text="High Concentration Threshold (HHI=0.25)",
        annotation_position="right"
    )
    
    fig.add_annotation(
        x=6, y=0.7,
        text=(
            "<b>Interpreting HHI Values</b><br><br>"
            "Concentrated supply chains exhibit:<br>"
            "• Higher vulnerability to single-source disruption<br>"
            "• Reduced supplier substitutability<br>"
            "• Increased market power concentration"
        ),
        showarrow=False,
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="gray",
        borderwidth=1,
        borderpad=10,
        font=dict(size=10),
        align='left'
    )
    
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text=(
                "<b>Supply Chain Concentration by Mineral Category</b><br>"
                "<sub>Herfindahl-Hirschman Index (HHI): Higher values = fewer suppliers dominate the market</sub>"
            ),
            x=0.5,
            xanchor='center'
        ),
        yaxis=dict(
            title="<b>Supply Concentration (HHI)</b><br>(0=Many equal suppliers, 1=Single monopoly)",
            range=[0, 0.9],
            showgrid=True,
            gridcolor='lightgray'
        ),
        xaxis=dict(
            title="<b>Mineral Category</b>",
            showgrid=False
        ),
        showlegend=False,
        height=600
    )
    
    output_file = HTML_DIR / "A7_03_source_concentration.html"
    fig.write_html(output_file)
    print(f"   ✓ Created source concentration chart: {output_file.name}")
    return fig


# =============================================================================
# CHART 4: Geopolitical Sources (Interactive)
# Shows which minerals come from allies vs. competitors
# =============================================================================
def create_geopolitical_source_map():
    """
    Creates a stacked bar chart showing import sources by relationship type.
    
    What you can do:
    - Use the toggle buttons to show/hide allies, neutrals, or competitors
    
    The story: Some minerals (like rare earths) come mostly from China and Russia,
    while others have better geographic diversity.
    """
    
    # Calculate what percentage comes from allies, neutrals, and competitors
    relationship_data = []
    
    for mineral in df_full['mineral'].unique():
        sources = df_full[df_full['mineral'] == mineral]
        
        ally_share = sources[sources['relationship'] == 'Ally']['us_imports_from'].sum()
        neutral_share = sources[sources['relationship'] == 'Neutral']['us_imports_from'].sum()
        competitor_share = sources[sources['relationship'] == 'Competitor']['us_imports_from'].sum()
        
        category = df_minerals[df_minerals['mineral'] == mineral]['category'].iloc[0]
        import_reliance = df_risk[df_risk['mineral'] == mineral]['us_import_reliance_pct'].iloc[0]
        
        relationship_data.append({
            'mineral': mineral,
            'category': category,
            'import_reliance': import_reliance,
            'ally_share': ally_share * 100,
            'neutral_share': neutral_share * 100,
            'competitor_share': competitor_share * 100
        })
    
    df_relationships = pd.DataFrame(relationship_data)
    
    # Sort by competitor share (most concerning first)
    df_relationships = df_relationships.sort_values('competitor_share', ascending=True)
    
    # Take top 25 minerals by import reliance
    df_top = df_relationships.nlargest(25, 'import_reliance')
    df_top = df_top.sort_values('competitor_share')
    
    fig = go.Figure()
    
    # Stacked horizontal bars
    fig.add_trace(go.Bar(
        y=df_top['mineral'],
        x=df_top['competitor_share'],
        name='Competitor (China, Russia)',
        orientation='h',
        marker=dict(
            color=COMPETITOR_COLOR,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate="<b>%{y}</b><br>Competitor sources: %{x:.1f}%<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=df_top['mineral'],
        x=df_top['neutral_share'],
        name='Neutral Country',
        orientation='h',
        marker=dict(
            color=NEUTRAL_COLOR,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate="<b>%{y}</b><br>Neutral sources: %{x:.1f}%<extra></extra>"
    ))
    
    fig.add_trace(go.Bar(
        y=df_top['mineral'],
        x=df_top['ally_share'],
        name='Allied Country',
        orientation='h',
        marker=dict(
            color=ALLY_COLOR,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate="<b>%{y}</b><br>Allied sources: %{x:.1f}%<extra></extra>"
    ))
    
    # Add annotation for minerals with high competitor dependence
    high_competitor = df_top[df_top['competitor_share'] > 50]
    
    # Add reference line at 50% threshold
    fig.add_vline(
        x=50,
        line_dash="dash",
        line_color="rgba(214, 39, 40, 0.4)",
        line_width=2,
        layer="below"
    )
    
    fig.add_annotation(
        x=50, y=26,
        text=(
            f"<b>{len(high_competitor)} minerals show >50%"
            f"competitor-source concentration"
            f"<i>Geopolitical relationship classification"
            f"indicates reliability under stress scenarios</i>"
        ),
        showarrow=False,
        arrowhead=2,
        arrowcolor=CRITICAL_RED,
        ax=-100, ay=-60,
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor=CRITICAL_RED,
        borderwidth=1,
        borderpad=10,
        font=dict(size=10, color=TEXT_COLOR),
        align='left'
    )
    
    # Create toggle buttons for showing/hiding relationship types
    fig.update_layout(
        font=dict(family="Arial, sans-serif", size=13, color=TEXT_COLOR),
        paper_bgcolor="white",
        plot_bgcolor=BACKGROUND,
        title=dict(
            text=(
                "<b>Critical Mineral Sources: Allies vs. Competitors vs. Neutrals</b><br>"
                "<sub>Share of US imports by geopolitical relationship — Top 25 minerals by import dependence</sub>"
            ),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="<b>Share of US Imports (%)</b>",
            range=[0, 100],
            showgrid=True,
            gridcolor='rgba(200,200,200,0.3)',
            zeroline=False
        ),
        yaxis=dict(
            title="",
            showgrid=False
        ),
        barmode='stack',
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(
                        label="Show All",
                        method="update",
                        args=[{"visible": [True, True, True]}]
                    ),
                    dict(
                        label="Competitors Only",
                        method="update",
                        args=[{"visible": [True, False, False]}]
                    ),
                    dict(
                        label="Allies Only",
                        method="update",
                        args=[{"visible": [False, False, True]}]
                    ),
                    dict(
                        label="Compare Competitors vs Allies",
                        method="update",
                        args=[{"visible": [True, False, True]}]
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.02,
                xanchor="left",
                y=-0.08,
                yanchor="top",
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#1e3c72",
                borderwidth=2
            )
        ],
        annotations=[
            dict(
                text="<b>View Options:</b>",
                x=0.02,
                xref="paper",
                y=-0.05,
                yref="paper",
                showarrow=False,
                xanchor="left",
                yanchor="top",
                font=dict(size=12, color=TEXT_COLOR)
            )
        ] + list(fig.layout.annotations),  # Keep existing annotations
        height=900,
        margin=dict(t=120, b=120, l=180, r=80)
    )
    
    output_file = HTML_DIR / "A7_04_geopolitical_sources.html"
    fig.write_html(output_file)
    print(f"   ✓ Created geopolitical sources chart: {output_file.name}")
    return fig


# =============================================================================
# CHART 5: Strategic Dashboard — The Executive Summary
# Multi-panel view showing key metrics
# =============================================================================
def create_strategic_dashboard():
    """
    Comprehensive dashboard with key insights
    """
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Risk Category Distribution",
            "Top 10 Highest-Risk Minerals",
            "Import Reliance Distribution",
            "Competitor Exposure by Category"
        ),
        specs=[
            [{"type": "pie"}, {"type": "bar"}],
            [{"type": "histogram"}, {"type": "bar"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # Panel 1: Risk category pie chart
    risk_counts = df_risk['risk_category'].value_counts()
    risk_order = ['Critical', 'High', 'Medium', 'Low']
    risk_counts = risk_counts.reindex(risk_order)
    
    fig.add_trace(
        go.Pie(
            labels=risk_counts.index,
            values=risk_counts.values,
            marker=dict(colors=[CRITICAL_RED, HIGH_RISK, MEDIUM_RISK, LOW_RISK]),
            textinfo='label+percent',
            textfont=dict(size=12),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Panel 2: Top 10 highest-risk minerals
    top_10_risk = df_risk.nlargest(10, 'composite_risk_score').sort_values('composite_risk_score')
    
    fig.add_trace(
        go.Bar(
            y=top_10_risk['mineral'],
            x=top_10_risk['composite_risk_score'],
            orientation='h',
            marker=dict(
                color=top_10_risk['composite_risk_score'],
                colorscale=[[0, LOW_RISK], [0.4, MEDIUM_RISK], [0.7, HIGH_RISK], [1, CRITICAL_RED]],
                showscale=False
            ),
            text=top_10_risk['composite_risk_score'].apply(lambda x: f"{x:.1f}"),
            textposition='outside',
            hovertemplate="<b>%{y}</b><br>Risk Score: %{x:.2f}/10<extra></extra>"
        ),
        row=1, col=2
    )
    
    # Panel 3: Import reliance histogram
    fig.add_trace(
        go.Histogram(
            x=df_risk['us_import_reliance_pct'],
            nbinsx=20,
            marker=dict(
                color=HIGH_RISK,
                line=dict(color='white', width=1)
            ),
            hovertemplate="Import Reliance: %{x:.0f}%<br>Count: %{y}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Panel 4: Competitor exposure by category
    category_competitor = df_full.groupby('category').apply(
        lambda x: x[x['relationship'] == 'Competitor']['production_share'].sum() * 100
    ).sort_values()
    
    fig.add_trace(
        go.Bar(
            y=category_competitor.index,
            x=category_competitor.values,
            orientation='h',
            marker=dict(color=COMPETITOR_COLOR),
            text=category_competitor.apply(lambda x: f"{x:.0f}%"),
            textposition='outside',
            hovertemplate="<b>%{y}</b><br>Competitor share: %{x:.1f}%<extra></extra>"
        ),
        row=2, col=2
    )
    
    # Update axes
    fig.update_xaxes(title_text="Risk Score (0-10)", row=1, col=2, showgrid=True, gridcolor='lightgray')
    fig.update_xaxes(title_text="US Import Reliance (%)", row=2, col=1, showgrid=True, gridcolor='lightgray')
    fig.update_xaxes(title_text="Competitor Share (%)", row=2, col=2, showgrid=True, gridcolor='lightgray')
    
    fig.update_yaxes(title_text="", row=1, col=2)
    fig.update_yaxes(title_text="Number of Minerals", row=2, col=1, showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(title_text="", row=2, col=2)
    
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(
            text=(
                "<b>US Critical Minerals: Strategic Supply Chain Dashboard</b><br>"
                "<sub>Comprehensive overview of vulnerabilities, dependencies, and strategic risks</sub>"
            ),
            x=0.5,
            xanchor='center',
            y=0.98
        ),
        showlegend=False,
        height=900
    )
    
    output_file = HTML_DIR / "A7_05_strategic_dashboard.html"
    fig.write_html(output_file)
    print(f"   ✓ Created strategic dashboard: {output_file.name}")
    return fig


# =============================================================================
# CHART 6: Critical Minerals Reference Catalog — PRIMARY ASSIGNMENT DELIVERABLE
# Interactive table showing all minerals with key data
#
# THIS IS THE MAIN DELIVERABLE: A reference catalog of source countries for
# each critical mineral with reliability judgments under stressed circumstances
# (war, economic crisis, trade conflict). Charts 1-5 provide supporting analysis.
# =============================================================================
def create_reference_catalog():
    """
    Interactive table — THE reference catalog requested in assignment.
    
    Shows for each of 43 critical minerals:
    - Category and strategic uses
    - Top 3 source countries with geopolitical relationship (Ally/Neutral/Competitor)
    - US import reliance percentage
    - Composite risk score (accounts for reliability under stress)
    - Risk category assessment
    """
    
    # Prepare comprehensive data
    # Select only needed columns from df_risk to avoid duplicate columns
    catalog = df_minerals[['mineral', 'category', 'uses', 'strategic_importance', 'us_import_reliance_pct']].merge(
        df_risk[['mineral', 'composite_risk_score', 'risk_category', 'china_exposure_pct']], 
        on='mineral', 
        how='left'
    )
    catalog = catalog.sort_values(['risk_category', 'composite_risk_score'], ascending=[True, False])
    
    # Get top 3 sources for each mineral
    def get_top_sources(mineral):
        sources = df_sources[df_sources['mineral'] == mineral].nlargest(3, 'production_share')
        source_list = []
        for _, row in sources.iterrows():
            rel = df_reliability[df_reliability['country'] == row['country']]['relationship'].iloc[0]
            source_list.append(f"{row['country']} ({rel})")
        return "<br>".join(source_list)
    
    catalog['top_sources'] = catalog['mineral'].apply(get_top_sources)
    
    # Color code by risk
    risk_colors_text = {
        'Critical': '#ffffff',
        'High': '#ffffff',
        'Medium': '#000000',
        'Low': '#000000'
    }
    risk_colors_bg = {
        'Critical': CRITICAL_RED,
        'High': HIGH_RISK,
        'Medium': MEDIUM_RISK,
        'Low': LOW_RISK
    }
    
    fig = go.Figure(data=[go.Table(
        columnwidth=[80, 60, 120, 180, 50, 50, 60],
        header=dict(
            values=[
                '<b>Mineral</b>',
                '<b>Category</b>',
                '<b>Primary Uses</b>',
                '<b>Top 3 Sources<br>(Relationship)</b>',
                '<b>Import<br>Reliance</b>',
                '<b>Risk<br>Score</b>',
                '<b>Risk<br>Level</b>'
            ],
            fill_color='#2c3e50',
            font=dict(color='white', size=12),
            align='left',
            height=40
        ),
        cells=dict(
            values=[
                catalog['mineral'],
                catalog['category'],
                catalog['uses'],
                catalog['top_sources'],
                catalog['us_import_reliance_pct'].apply(lambda x: f"{x}%"),
                catalog['composite_risk_score'].apply(lambda x: f"{x:.1f}"),
                catalog['risk_category']
            ],
            fill_color=[
                'white',
                'white',
                'white',
                'white',
                'white',
                'white',
                [risk_colors_bg.get(risk, 'white') for risk in catalog['risk_category']]
            ],
            font=dict(
                color=[
                    TEXT_COLOR,
                    TEXT_COLOR,
                    TEXT_COLOR,
                    TEXT_COLOR,
                    TEXT_COLOR,
                    TEXT_COLOR,
                    [risk_colors_text.get(risk, TEXT_COLOR) for risk in catalog['risk_category']]
                ],
                size=11
            ),
            align='left',
            height=30
        )
    )])
    
    fig.update_layout(
        title=dict(
            text=(
                "<b>Critical Minerals Reference Catalog</b><br>"
                "<sub>Complete USGS 2022 list with sources, import reliance, and reliability assessment</sub>"
            ),
            x=0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        margin=dict(t=100, b=20, l=20, r=20),
        height=1200
    )
    
    output_file = HTML_DIR / "A7_06_reference_catalog.html"
    fig.write_html(output_file)
    print(f"   ✓ Created reference catalog: {output_file.name}")
    return fig


# =============================================================================
# Main Execution
# =============================================================================
def main():
    print("=" * 70)
    print("Assignment 7: Critical Minerals Supply Chain Analysis")
    print("Creating Visualizations")
    print("=" * 70)
    
    print("\n[1/6] Creating vulnerability matrix...")
    create_vulnerability_matrix()
    
    print("\n[2/6] Creating China dependency analysis...")
    create_china_dependency_chart()
    
    print("\n[3/6] Creating source concentration analysis...")
    create_source_diversification()
    
    print("\n[4/6] Creating geopolitical source map...")
    create_geopolitical_source_map()
    
    print("\n[5/6] Creating strategic dashboard...")
    create_strategic_dashboard()
    
    print("\n[6/6] Creating reference catalog...")
    create_reference_catalog()
    
    print("\n" + "=" * 70)
    print("Analysis complete! 6 interactive charts created in html/")
    print("=" * 70)
    print("\nKey findings:")
    print(f"  • {len(df_risk[df_risk['risk_category'].isin(['Critical', 'High'])])} minerals face critical or high supply chain risk")
    print(f"  • {len(df_risk[df_risk['china_exposure_pct'] > 50])} minerals depend heavily on China (>50% exposure)")
    print(f"  • {len(df_risk[df_risk['us_import_reliance_pct'] == 100])} minerals have 100% import reliance")
    print("\nReady for Assignment7_Presentation.py to compile the final report.")
    print("=" * 70)


if __name__ == "__main__":
    main()
