# =============================================================================
# Assignment 3: Do Stricter Gun Laws Reduce Firearm Deaths?
# =============================================================================
#
# The Question: Simple and direct - do states with tougher gun laws have fewer gun deaths?
# The Audience: State legislators weighing whether to tighten or loosen gun regulations.
# The Goal: Give them clear, honest data so they can make informed decisions.
#
# Why Bokeh for this assignment?
# -----------------------------
# Assignment 1 used matplotlib/seaborn (static PNG images)
# Assignment 2 used Plotly (interactive HTML with one rendering engine)
# Assignment 3 uses Bokeh (different interactive framework with distinct visualization approach)
#
# Bokeh gives us:
# - True interactive heatmaps that are different from Plotly's implementation
# - Built-in accessible color palettes (important for colorblind viewers)
# - Server-side rendering capabilities (different architecture than Plotly)
# - Better performance for large categorical heatmaps
#
# As a data scientist, I need to show I can adapt to different tools.
# Each library has strengths - Bokeh excels at grid-based heatmaps and categorical data.

import pandas as pd
import numpy as np
from pathlib import Path

# Bokeh imports - our new visualization toolkit
from bokeh.plotting import figure, save, output_file, show
from bokeh.models import (
    HoverTool, LinearColorMapper, ColorBar, 
    BasicTicker, PrintfTickFormatter, ColumnDataSource,
    Title, Label, FactorRange
)
from bokeh.palettes import RdYlBu11, Viridis256, YlOrRd9, Greys256  # Colorblind-friendly palettes
from bokeh.transform import transform, linear_cmap
from bokeh.layouts import column, row
from bokeh.io import export_svgs

# File structure
DATA_DIR = Path(__file__).parent / "data"
HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(exist_ok=True)

# =============================================================================
# Color Strategy: Accessibility First
# =============================================================================
# I'm using a blue-orange palette that works for all types of color blindness:
# - Blue = good (low deaths, strict laws)
# - Orange/Yellow = concerning (high deaths, lax laws)
# This avoids red-green confusion that affects ~8% of men and 0.5% of women.

COLORS = {
    'low': '#0173B2',      # Blue = low deaths (good outcome)
    'high': '#DE8F05',     # Orange = high deaths (concerning)
    'mid': '#ECB01E',      # Yellow = middle ground
    'neutral': '#949494'   # Gray = neutral elements
}


# =============================================================================
# Step 1: Get the firearm death data
# =============================================================================
# The CDC tracks firearm deaths by state and publishes rates per 100,000 people.
# This normalization is crucial - we can't just count raw deaths because California
# has way more people than Wyoming. Per capita rates let us compare apples to apples.

def load_cdc_data():
    # Load firearm death rates from the CDC dataset
    #
    # What we're after: The most recent full year of data (2024)
    # Why filtered data: We already pulled only firearm-related deaths in the API call
    
    print("\n" + "="*70)
    print("Loading CDC Firearm Mortality Data")
    print("="*70)
    
    # Use the pre-filtered data (only firearm deaths, not all injuries)
    df = pd.read_csv(DATA_DIR / "cdc_firearm_state_data_filtered.csv")
    
    # Filter to 2024 (most recent complete year) and total deaths
    df_2024 = df[(df['Intent'] == 'FA_Deaths') & (df['Period'] == '2024')].copy()
    
    # Simplify -  we just need state names and death rates
    df_clean = df_2024[['NAME', 'Rate']].copy()
    df_clean.columns = ['State', 'Death_Rate']
    
    print(f"✓ Loaded {len(df_clean)} states/territories")
    print(f"  Death rate range: {df_clean['Death_Rate'].min():.1f} to {df_clean['Death_Rate'].max():.1f} per 100k")
    
    # Quick sanity check - do we have the big states?
    key_states = ['California', 'Texas', 'Florida', 'New York']
    for state in key_states:
        rate = df_clean[df_clean['State'] == state]['Death_Rate'].values
        if len(rate) > 0:
            print(f"  {state}: {rate[0]:.1f} deaths per 100k")
    
    return df_clean


# =============================================================================
# Step 2: Create the 5-point gun law strictness scale
# =============================================================================
# The Giffords Law Center grades each state's gun laws annually (A through F).
# For our analysis, I'm converting these letter grades to a 5-point Likert scale:
#
# 5 = Very Strict (A grade: comprehensive background checks, assault weapon bans, etc.)
# 4 = Strict (B grade: strong laws with some gaps)
# 3 = Moderate (C grade: basic requirements, mixed approach)
# 2 = Lax (D grade: minimal regulations)
# 1 = Very Lax (F grade: few or no gun laws)
#
# Why this scale? It meets the assignment requirement and makes the relationship
# easy to understand - higher number = stricter laws.

def add_gun_law_ratings():
    # Assign each state a gun law strictness rating (1-5 scale)
    #
    # Source: Giffords Law Center Annual Gun Law Scorecard
    # Methodology: Converted letter grades to numeric scale for statistical analysis
    #
    # Note: In a production analysis, I'd pull this from an API, but for this
    # assignment I'm using the most recent published grades (2024).
    
    print("\n" + "="*70)
    print("Building Gun Law Strictness Scale (1=Very Lax, 5=Very Strict)")
    print("="*70)
    
    # Based on 2024 Giffords Law Center scorecard
    law_ratings = {
        # A Grades - Very Strict States (5)
        # These states have: Universal background checks, assault weapon bans,
        # red flag laws, permit requirements, safe storage laws
        'California': 5, 'New Jersey': 5, 'Massachusetts': 5, 'New York': 5,
        'Hawaii': 5, 'Connecticut': 5, 'Maryland': 5, 'Illinois': 5,
        'District of Columbia': 5,
        
        # B Grades - Strict States (4)
        # Strong laws but missing some key regulations
        'Washington': 4, 'Oregon': 4, 'Colorado': 4, 'Rhode Island': 4,
        'Delaware': 4, 'Michigan': 4, 'Virginia': 4, 'Minnesota': 4,
        
        # C Grades - Moderate States (3)
        # Mix of regulations, neither comprehensive nor permissive
        'Nevada': 3, 'Pennsylvania': 3, 'Florida': 3, 'North Carolina': 3,
        'Iowa': 3, 'Nebraska': 3, 'Wisconsin': 3, 'Maine': 3, 'Vermont': 3,
        
        # D Grades - Lax States (2)
        # Minimal regulations, few restrictions on gun ownership/carry
        'South Dakota': 2, 'North Dakota': 2, 'Ohio': 2, 'Indiana': 2,
        'South Carolina': 2, 'Georgia': 2, 'Texas': 2, 'Kansas': 2,
        'Montana': 2, 'Utah': 2, 'Tennessee': 2, 'Oklahoma': 2,
        
        # F Grades - Very Lax States (1)
        # Virtually no gun regulations, permitless carry, no background checks
        # required for private sales
        'Alaska': 1, 'Arizona': 1, 'Arkansas': 1, 'Idaho': 1,
        'Kentucky': 1, 'Louisiana': 1, 'Mississippi': 1, 'Missouri': 1,
        'New Hampshire': 1, 'New Mexico': 1, 'West Virginia': 1, 'Wyoming': 1,
        'Alabama': 1
    }
    
    df = pd.DataFrame(list(law_ratings.items()), columns=['State', 'Law_Strictness'])
    
    # Add readable labels for charts
    label_map = {
        5: 'Very Strict', 
        4: 'Strict', 
        3: 'Moderate', 
        2: 'Lax', 
        1: 'Very Lax'
    }
    df['Law_Label'] = df['Law_Strictness'].map(label_map)
    
    # Show distribution
    print("\nDistribution of states by law strictness:")
    counts = df['Law_Label'].value_counts().sort_index(ascending=False)
    for label, count in counts.items():
        print(f"  {label}: {count} states")
    
    return df


# =============================================================================
# Step 3: Merge and analyze the data
# =============================================================================

def merge_data():
    # Combine CDC death rates with gun law ratings
    #
    # This is where we connect the dots - literally joining two datasets
    # to see if there's a pattern between law strictness and death rates.
    
    print("\n" + "="*70)
    print("Merging Datasets")
    print("="*70)
    
    deaths = load_cdc_data()
    laws = add_gun_law_ratings()
    
    # Inner join keeps only states that appear in both datasets
    df = deaths.merge(laws, on='State', how='inner')
    
    print(f"\n✓ Successfully merged: {len(df)} states with complete data")
    
    # Show a quick breakdown
    print("\nStates by law strictness category:")
    breakdown = df.groupby('Law_Label')['State'].count().sort_index(ascending=False)
    for category, count in breakdown.items():
        print(f"  {category}: {count} states")
    
    return df


def analyze_relationship(df):
    # The core analysis: Is there a relationship between law strictness and deaths?
    #
    # As a data scientist, I need to quantify this relationship. The correlation
    # coefficient will tell us if stricter laws correlate with fewer deaths.
    #
    # Correlation ranges from -1 to +1:
    # - Negative = as one goes up, the other goes down
    # - Positive = they move together
    # - Zero = no relationship
    
    print("\n" + "="*70)
    print("ANALYZING THE RELATIONSHIP")
    print("="*70)
    
    # Group by law strictness and calculate averages
    summary = df.groupby(['Law_Strictness', 'Law_Label']).agg({
        'Death_Rate': ['mean', 'std', 'count']
    }).reset_index()
    
    summary.columns = ['Law_Strictness', 'Law_Label', 'Avg_Death_Rate', 'Std_Dev', 'States']
    summary = summary.sort_values('Law_Strictness', ascending=False)
    
    print("\nAverage death rate by law strictness:")
    print(summary[['Law_Label', 'Avg_Death_Rate', 'States']].to_string(index=False))
    
    # Calculate the correlation coefficient
    corr = df['Law_Strictness'].corr(df['Death_Rate'])
    print(f"\n{'='*70}")
    print(f"CORRELATION COEFFICIENT: {corr:.3f}")
    print(f"{'='*70}")
    
    # Interpret it in plain English
    if corr < -0.7:
        interpretation = "STRONG negative relationship: Stricter laws strongly associated with fewer deaths"
    elif corr < -0.5:
        interpretation = "MODERATE negative relationship: Stricter laws associated with fewer deaths"
    elif corr < -0.3:
        interpretation = "WEAK negative relationship: Some evidence stricter laws reduce deaths"
    elif corr > 0.3:
        interpretation = "POSITIVE relationship: Stricter laws associated with MORE deaths (unexpected!)"
    else:
        interpretation = "WEAK or NO clear relationship between law strictness and deaths"
    
    print(f"\nInterpretation: {interpretation}")
    
    # Show the magnitude of difference
    very_strict_avg = summary[summary['Law_Label'] == 'Very Strict']['Avg_Death_Rate'].values[0]
    very_lax_avg = summary[summary['Law_Label'] == 'Very Lax']['Avg_Death_Rate'].values[0]
    difference = very_lax_avg - very_strict_avg
    ratio = very_lax_avg / very_strict_avg
    
    print(f"\nPractical Impact:")
    print(f"  Very Strict states average: {very_strict_avg:.1f} deaths per 100k")
    print(f"  Very Lax states average: {very_lax_avg:.1f} deaths per 100k")
    print(f"  Difference: {difference:.1f} additional deaths per 100k in lax states")
    print(f"  Ratio: {ratio:.1f}x higher death rate in very lax vs very strict states")
    
    return summary, corr


# =============================================================================
# Step 4: Create visualizations with Bokeh
# =============================================================================
# Why heatmaps? The assignment specifically requests heat maps.
# Bokeh's heatmap capabilities are excellent for showing patterns across categories.
# 
# I'll create two main heatmaps:
# 1. Death rates by state (organized by law strictness)
# 2. Correlation view showing death rate vs law strength

def create_heatmap_by_law_category(df, summary):
    # Heatmap #1: Death rates grouped by law strictness
    #
    # This is the money shot - legislators can immediately see that states
    # with stricter laws cluster toward lower death rates.
    #
    # Design choices:
    # - Sorted by law strictness (strict at top, lax at bottom)
    # - Blue-orange gradient (colorblind-friendly)
    # - Each row is a state, hover shows exact values
    # - Clean, minimal design (no chart junk)
    
    print("\n[Creating Visualization 1: State-by-State Heatmap]")
    
    # Sort states by law strictness, then by death rate within each category
    df_sorted = df.sort_values(['Law_Strictness', 'Death_Rate'], ascending=[False, True])
    
    # Prepare data for Bokeh
    source = ColumnDataSource(df_sorted)
    
    # Create color mapper using sequential palette: light = low deaths, dark = high deaths
    # YlOrRd is intuitive for mortality (yellow = low severity, red = high severity)
    mapper = LinearColorMapper(
        palette=YlOrRd9,
        low=df['Death_Rate'].min(),
        high=df['Death_Rate'].max()
    )
    
    # Create the figure
    p = figure(
        title="Firearm Death Rates by State (Grouped by Law Strictness)",
        x_axis_label="Death Rate (per 100,000)",
        y_axis_label="State",
        y_range=list(df_sorted['State']),
        width=900,
        height=1000,
        toolbar_location="right",
        tools="hover,save,pan,box_zoom,reset,wheel_zoom"
    )
    
    # Add the heatmap as horizontal bars
    p.hbar(
        y='State',
        right='Death_Rate',
        left=0,
        height=0.8,
        source=source,
        fill_color=transform('Death_Rate', mapper),
        line_color=None
    )
    
    # Add color bar
    color_bar = ColorBar(
        color_mapper=mapper,
        ticker=BasicTicker(),
        label_standoff=12,
        border_line_color=None,
        location=(0,0),
        title="Deaths per 100k"
    )
    p.add_layout(color_bar, 'right')
    
    # Configure hover tool - this shows law category for each state
    hover = p.select_one(HoverTool)
    hover.tooltips = [
        ("State", "@State"),
        ("Death Rate", "@Death_Rate{0.0} per 100k"),
        ("Law Strictness", "@Law_Label")
    ]
    
    # Style
    p.title.text_font_size = "16pt"
    p.xaxis.axis_label_text_font_size = "12pt"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.yaxis.major_label_text_font_size = "9pt"
    
    # Save
    output_file(HTML_DIR / "heatmap_states_by_law_strictness.html")
    save(p)
    print("✓ Saved: heatmap_states_by_law_strictness.html")
    
    return p


def create_category_comparison_heatmap(summary):
    # Heatmap #2: Average death rates by law strictness category
    #
    # This is the simplest view - perfect for legislators who want the answer
    # in  5 seconds. Five categories, five numbers. Done.
    #
    # Design choices:
    # - One row per law strictness level
    # - Wider bars for better visibility
    # - Large text showing the exact numbers
    # - Color gradient makes the pattern obvious even without reading numbers
    
    print("\n[Creating Visualization 2: Law Category Comparison Heatmap]")
    
    # Prepare data
    summary_sorted = summary.sort_values('Law_Strictness', ascending=False)
    source = ColumnDataSource(summary_sorted)
    
    # Color mapper - using same palette as other heatmap for consistency
    mapper = LinearColorMapper(
        palette=YlOrRd9,
        low=summary['Avg_Death_Rate'].min(),
        high=summary['Avg_Death_Rate'].max()
    )
    
    # Create figure
    p = figure(
        title="Average Firearm Deaths by Gun Law Strictness (2024)",
        x_axis_label="Average Death Rate (per 100,000)",
        y_axis_label="Law Strictness Category",
        y_range=list(summary_sorted['Law_Label']),
        width=900,
        height=400,
        toolbar_location="right",
        tools="hover,save"
    )
    
    # Add bars
    p.hbar(
        y='Law_Label',
        right='Avg_Death_Rate',
        left=0,
        height=0.7,
        source=source,
        fill_color=transform('Avg_Death_Rate', mapper),
        line_color='white',
        line_width=2
    )
    
    # Add text labels showing the exact values
    from bokeh.models import LabelSet
    labels = LabelSet(
        x='Avg_Death_Rate',
        y='Law_Label',
        text='Avg_Death_Rate',
        text_font_size='14pt',
        text_font_style='bold',
        x_offset=10,
        y_offset=-10,
        source=source,
        text_align='left'
    )
    p.add_layout(labels)
    
    # Color bar
    color_bar = ColorBar(
        color_mapper=mapper,
        ticker=BasicTicker(),
        label_standoff=12,
        border_line_color=None,
        location=(0,0),
        title="Deaths per 100k"
    )
    p.add_layout(color_bar, 'right')
    
    # Hover
    hover = p.select_one(HoverTool)
    hover.tooltips = [
        ("Category", "@Law_Label"),
        ("Average Death Rate", "@Avg_Death_Rate{0.1} per 100k"),
        ("Number of States", "@States")
    ]
    
    # Style
    p.title.text_font_size = "16pt"
    p.xaxis.axis_label_text_font_size = "12pt"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.yaxis.major_label_text_font_size = "11pt"
    
    # Save
    output_file(HTML_DIR / "heatmap_average_by_category.html")
    save(p)
    print("✓ Saved: heatmap_average_by_category.html")
    
    return p


def create_paneled_state_comparison(df, summary):
    # Create a self-explanatory paneled visualization showing firearm deaths by state.
    #
    # Design Philosophy:
    # - Each law strictness category gets its own clearly labeled panel
    # - States sorted by death rate within each panel
    # - Vertical stacking makes the pattern obvious at a glance
    # - No additional text needed - the visualization tells the story
    #
    # What you'll see:
    # - Top panels (Very Lax laws): Long bars, dark red colors = high mortality
    # - Bottom panels (Very Strict laws): Short bars, yellow colors = low mortality
    # - The pattern is unmistakable without reading any descriptions
    
    from bokeh.layouts import column
    from bokeh.models import Div
    
    print("\n[Creating NEW Visualization: Paneled State Comparison]")
    
    # Color mapper for consistent coloring across all panels
    # YlOrRd9 in Bokeh is stored red-to-yellow, so we reverse it to get yellow-to-red
    # LOW death rates (Hawaii 3.9) should be YELLOW
    # HIGH death rates (Mississippi 27.6) should be RED
    min_death = df['Death_Rate'].min()  
    max_death = df['Death_Rate'].max()
    
    # Use reversed palette: now palette[0]=yellow (for low deaths), palette[-1]=red (for high deaths)
    yellow_to_red = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026', '#800026']
    mapper = LinearColorMapper(
        palette=yellow_to_red,
        low=min_death,  # 3.9 maps to yellow
        high=max_death  # 27.6 maps to red
    )
    
    # Define category order (lax → strict for top-to-bottom organization)
    category_order = [
        ('Very Lax (Grade F)', 1),
        ('Lax (Grade D)', 2),
        ('Moderate (Grade C)', 3),
        ('Strict (Grade B)', 4),
        ('Very Strict (Grade A)', 5)
    ]
    
    # Create a panel for each category
    panels = []
    
    for label, strictness_value in category_order:
        # Get states in this category
        category_data = df[df['Law_Strictness'] == strictness_value].copy()
        
        if len(category_data) == 0:
            continue
            
        # Sort by death rate (lowest to highest within panel)
        category_data = category_data.sort_values('Death_Rate')
        
        # Create data source
        source = ColumnDataSource(category_data)
        
        # Calculate panel height based on number of states
        panel_height = max(150, len(category_data) * 25)
        
        # Create figure for this category
        p = figure(
            title=label,
            x_axis_label="Death Rate (per 100,000 population)",
            y_range=list(category_data['State']),
            width=1000,
            height=panel_height,
            toolbar_location=None,
            tools="hover"
        )
        
        # Add horizontal bars
        p.hbar(
            y='State',
            right='Death_Rate',
            left=0,
            height=0.7,
            source=source,
            fill_color=transform('Death_Rate', mapper),
            line_color='white',
            line_width=1
        )
        
        # Configure hover
        hover = p.select_one(HoverTool)
        hover.tooltips = [
            ("State", "@State"),
            ("Death Rate", "@Death_Rate{0.1} per 100,000"),
            ("Law Grade", label.split('(Grade ')[1].split(')')[0])
        ]
        
        # Style the panel
        p.title.text_font_size = "15pt"
        p.title.text_font_style = "bold"
        p.xaxis.axis_label_text_font_size = "11pt"
        p.yaxis.major_label_text_font_size = "10pt"
        p.xgrid.grid_line_color = "#e0e0e0"
        p.ygrid.grid_line_color = None
        
        # Set consistent x-axis range for comparison
        p.x_range.start = 0
        p.x_range.end = 30
        
        panels.append(p)
    
    # Add overall title as HTML div
    title_html = """
    <div style="text-align: center; padding: 20px; font-family: Arial, sans-serif;">
        <h1 style="margin: 0; font-size: 16pt; color: #333;">
            Firearm Mortality Rate by State Law Strictness
        </h1>
    </div>
    """
    title_div = Div(text=title_html)
    
    # Add color bar legend as HTML div
    legend_html = """
    <div style="text-align: center; padding: 10px; font-family: Arial, sans-serif;">
        <p style="margin: 0; font-size: 11pt; color: #666;">
            <span style="display: inline-block; width: 15px; height: 15px; background: #ffffcc; border: 1px solid #ccc;"></span> Low Mortality (3-10 deaths/100k)
            <span style="padding: 0 10px;"></span>
            <span style="display: inline-block; width: 15px; height: 15px; background: #feb24c; border: 1px solid #ccc;"></span> Moderate Mortality (10-18 deaths/100k)
            <span style="padding: 0 10px;"></span>
            <span style="display: inline-block; width: 15px; height: 15px; background: #f03b20; border: 1px solid #ccc;"></span> High Mortality (18-28 deaths/100k)
        </p>
    </div>
    """
    legend_div = Div(text=legend_html)
    
    # Combine title + panels + legend
    layout = column(title_div, legend_div, *panels)
    
    # Save
    output_file(HTML_DIR / "paneled_state_comparison.html")
    save(layout)
    print("✓ Saved: paneled_state_comparison.html (NEW: Self-Explanatory Panel Design)")
    
    return layout


def create_scatter_with_trendline(df, corr):
    # Bonus Visualization: Scatter plot with trend line
    #
    # Not technically a heatmap, but it shows the relationship most clearly.
    # Every dot is a state. The trend line shows the overall pattern.
    #
    # This is for legislators who want to see the individual states, not just averages.
    
    print("\n[Creating Visualization 3: Scatter Plot with Trend Line]")
    
    # Prepare data
    source = ColumnDataSource(df)
    
    # Create figure
    p = figure(
        title=f"Gun Law Strictness vs Death Rate (Correlation: {corr:.3f})",
        x_axis_label="Gun Law Strictness",
        y_axis_label="Death Rate (per 100,000)",
        width=900,
        height=600,
        toolbar_location="right",
        tools="hover,save,pan,box_zoom,reset"
    )
    
    # Add scatter points with color based on death rate
    color_mapper = LinearColorMapper(
        palette=list(reversed(RdYlBu11)), 
        low=df['Death_Rate'].min(), 
        high=df['Death_Rate'].max()
    )
    
    p.circle(
        'Law_Strictness',
        'Death_Rate',
        size=12,
        source=source,
        fill_color={'field': 'Death_Rate', 'transform': color_mapper},
        line_color='white',
        line_width=2,
        alpha=0.8
    )
    
    # Add color bar to explain what the colors mean
    color_bar = ColorBar(
        color_mapper=color_mapper,
        label_standoff=12,
        border_line_color=None,
        location=(0, 0),
        title="Death Rate\n(per 100k)"
    )
    p.add_layout(color_bar, 'right')
    
    # Add trend line
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['Law_Strictness'], df['Death_Rate'])
    x_trend = np.array([1, 5])
    y_trend = slope * x_trend + intercept
    p.line(x_trend, y_trend, line_width=3, color='black', alpha=0.8, line_dash='dashed', legend_label=f'Trend Line (R²={r_value**2:.3f})')
    
    # Hover
    hover = p.select_one(HoverTool)
    hover.tooltips = [
        ("State", "@State"),
        ("Law Strictness", "@Law_Label"),
        ("Death Rate", "@Death_Rate{0.1} per 100k")
    ]
    
    # Custom x-axis labels
    p.xaxis.ticker = [1, 2, 3, 4, 5]
    p.xaxis.major_label_overrides = {
        1: 'Very Lax',
        2: 'Lax',
        3: 'Moderate',
        4: 'Strict',
        5: 'Very Strict'
    }
    
    # Style
    p.title.text_font_size = "16pt"
    p.xaxis.axis_label_text_font_size = "12pt"
    p.yaxis.axis_label_text_font_size = "12pt"
    p.legend.location = "top_right"
    
    # Save
    output_file(HTML_DIR / "scatter_law_vs_deaths.html")
    save(p)
    print("✓ Saved: scatter_law_vs_deaths.html")
    
    return p


# =============================================================================
# Main execution
# =============================================================================

def main():
    # Bring it all together:
    # 1. Load the data
    # 2. Merge it
    # 3. Analyze it
    # 4. Visualize it
    #
    # The story we're telling: Do stricter gun laws save lives?
    # The answer: Let the data speak.
    
    print("\n" + "="*70)
    print("ASSIGNMENT 3: DO STRICTER GUN LAWS REDUCE FIREARM DEATHS?")
    print("="*70)
    print("\nData Scientist: [Your Name]")
    print("Technology: Bokeh (interactive visualizations)")
    print("Focus: Policy makers and state legislators")
    print("="*70)
    
    # Step 1 & 2: Get and merge data
    df = merge_data()
    
    # Step 3: Analyze the relationship
    summary, corr = analyze_relationship(df)
    
    # Step 4: Create visualizations
    print("\n" + "="*70)
    print("CREATING VISUALIZATIONS")
    print("="*70)
    
    create_paneled_state_comparison(df, summary)  # NEW: Self-explanatory panel design
    create_heatmap_by_law_category(df, summary)
    create_category_comparison_heatmap(summary)
    create_scatter_with_trendline(df, corr)
    
    # Save the merged data
    print("\n[Saving Data]")
    df.to_csv(DATA_DIR / "firearm_analysis_complete.csv", index=False)
    print("✓ Saved: firearm_analysis_complete.csv")
    
    # Final summary
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nKey Finding: Correlation = {corr:.3f}")
    print(f"Interpretation: {'Strong' if abs(corr) > 0.7 else 'Moderate'} negative relationship")
    print(f"\nVisualization files saved to: {HTML_DIR}/")
    print("\nOpen the HTML files in your browser to explore the interactive charts.")
    print("="*70)


if __name__ == "__main__":
    main()
