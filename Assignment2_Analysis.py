# Assignment 2 – Did the Federal Reserve Do Its Job?
#
# This script takes the economic data we pulled earlier and turns it into visual stories
# that help us answer: "Has the Fed actually fulfilled the mandate Congress gave it?"
#
# What we're looking at:
# The Fed has two main jobs (dual mandate):
#   1. Keep inflation low and stable (around 2% is their sweet spot)
#   2. Keep unemployment low (help people find jobs)
#
# Their main lever? The Federal Funds Rate (basically the interest rate they control).
# Think of it like this: when inflation heats up, they raise rates to cool things down.
# When unemployment spikes, they lower rates to give the economy a boost.
#
# We're using Plotly for these charts - nice interactive visualizations
# (Assignment 1 used matplotlib/seaborn, so we're switching it up)

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path

# Setting up our file paths
DATA_DIR = Path(__file__).parent / "data"
HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(exist_ok=True)

# Clean, simple theme for all our charts
THEME = "plotly_white"

# Color scheme - keeping it consistent and intuitive
COLOR_PALETTE = {
    'inflation': '#E74C3C',      # Red = hot (inflation)
    'unemployment': '#3498DB',    # Blue = cool (unemployment)
    'fed_rate': '#2ECC71',        # Green = money (Fed rate)
    'good': '#27AE60',            # Success indicators
    'bad': '#C0392B',             # Warning signs
    'neutral': '#95A5A6'          # Neutral stuff
}

# Grab all the economic data we saved earlier
# Returns one nice DataFrame with everything: CPI, unemployment, and Fed rate
def load_data():
    print("Loading economic data from CSV files...")
    
    # Pull in our combined dataset
    data_path = DATA_DIR / "macro_data.csv"
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # Drop any rows with missing values - keeps things clean
    df = df.dropna()
    
    print(f"Loaded {len(df)} months of data ({df['date'].min().year} to {df['date'].max().year})")
    print(f"\nData columns: {', '.join(df.columns)}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    return df

# Let's poke around the data and see what stands out
# This helps us find the interesting moments to highlight in our visualizations
def explore_data(df):

    print("\n" + "="*60)
    print("DATA EXPLORATION")
    print("="*60)
    
    print("\nBasic Statistics:")
    print(df[['CPI', 'unemployment_rate', 'fed_funds_rate', 'CPI_YoY_pct']].describe())
    
    # Let's find the most dramatic moments in the data
    print("\n" + "-"*60)
    print("General Overview:")
    print("-"*60)
    
    # Highest inflation
    max_inflation = df.loc[df['CPI_YoY_pct'].idxmax()]
    print(f"\nHighest Inflation: {max_inflation['CPI_YoY_pct']:.2f}% in {max_inflation['date'].strftime('%B %Y')}")
    
    # Lowest inflation
    min_inflation = df.loc[df['CPI_YoY_pct'].idxmin()]
    print(f"Lowest Inflation:  {min_inflation['CPI_YoY_pct']:.2f}% in {min_inflation['date'].strftime('%B %Y')}")
    
    # Highest unemployment
    max_unemp = df.loc[df['unemployment_rate'].idxmax()]
    print(f"\nHighest Unemployment: {max_unemp['unemployment_rate']:.1f}% in {max_unemp['date'].strftime('%B %Y')}")
    
    # Lowest unemployment
    min_unemp = df.loc[df['unemployment_rate'].idxmin()]
    print(f"Lowest Unemployment:  {min_unemp['unemployment_rate']:.1f}% in {min_unemp['date'].strftime('%B %Y')}")
    
    # Highest Fed rate
    max_fed = df.loc[df['fed_funds_rate'].idxmax()]
    print(f"\nHighest Fed Funds Rate: {max_fed['fed_funds_rate']:.2f}% in {max_fed['date'].strftime('%B %Y')}")
    
    # Lowest Fed rate
    min_fed = df.loc[df['fed_funds_rate'].idxmin()]
    print(f"Lowest Fed Funds Rate:  {min_fed['fed_funds_rate']:.2f}% in {min_fed['date'].strftime('%B %Y')}")
    
    # Phillips Curve analysis - is there a tradeoff between inflation and unemployment?
    print("\n" + "-"*60)
    print("Phillips Curve Analysis:")
    print("-"*60)
    correlation = df['unemployment_rate'].corr(df['CPI_YoY_pct'])
    print(f"\nCorrelation between unemployment and inflation: {correlation:.3f}")
    
    if abs(correlation) < 0.3:
        strength = "weak"
    elif abs(correlation) < 0.7:
        strength = "moderate"
    else:
        strength = "strong"
    
    direction = "negative (inverse)" if correlation < 0 else "positive"
    print(f"Interpretation: {strength.capitalize()} {direction} relationship")
    print(f"\nWhat this means: A {strength} {direction} correlation suggests")
    print(f"the classic Phillips Curve tradeoff {'does exist but is not absolute' if abs(correlation) > 0.3 else 'is very weak'}.")
    print(f"The Fed {'can sometimes' if abs(correlation) < 0.7 else 'rarely can'} achieve both low inflation AND low unemployment.")
    
    return df


def create_dual_mandate_overview(df):
    """
    First chart: showing both of the Fed's goals side by side.
    Sometimes these two goals work against each other - this chart makes it easy
    to spot when the Fed had to make tough choices.
    
    What makes this chart work:
    - Shows the complete picture of both mandates over time
    - Easy to see when they moved in opposite directions
    - Simple layout that anyone can understand
    """
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Inflation Over Time (CPI Year-over-Year %)", 
                       "Unemployment Rate Over Time"),
        vertical_spacing=0.12,
        row_heights=[0.5, 0.5]
    )
    
    # Plot inflation over time
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['CPI_YoY_pct'],
            name='Inflation Rate',
            line=dict(color=COLOR_PALETTE['inflation'], width=2),
            fill='tozeroy',
            fillcolor='rgba(231, 76, 60, 0.1)',
            hovertemplate='%{x|%B %Y}<br>Inflation: %{y:.2f}%<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add the Fed's 2% target line - this is their unofficial goal for inflation
    fig.add_hline(y=2, line_dash="dash", line_color="gray", 
                  annotation_text="Fed's 2% Target", row=1, col=1)
    
    # Plot unemployment over time
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['unemployment_rate'],
            name='Unemployment Rate',
            line=dict(color=COLOR_PALETTE['unemployment'], width=2),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.1)',
            hovertemplate='%{x|%B %Y}<br>Unemployment: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Clean up the layout - keep it simple and clear
    fig.update_layout(
        title={
            'text': "The Fed's Dual Mandate Challenge: Inflation vs Unemployment (2002-2026)",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        template=THEME,
        height=700,
        showlegend=False,
        hovermode='x unified'
    )
    
    fig.update_xaxes(title_text="Year", row=2, col=1)
    fig.update_yaxes(title_text="Inflation (%)", row=1, col=1)
    fig.update_yaxes(title_text="Unemployment (%)", row=2, col=1)
    
    # Save it as an interactive HTML file you can open in a browser
    output_path = HTML_DIR / "dual_mandate_overview.html"
    fig.write_html(str(output_path))
    print(f"Saved: {output_path}")
    
    return fig


def create_fed_response_analysis(df):
    """
    This is where it gets interesting: how did the Fed actually respond?
    We're plotting their actions (interest rates) against what was happening
    in the economy. Did they make the right calls?
    
    What makes this useful:
    - Shows all three metrics accurately on one chart
    - You can see the Fed's decision-making process unfold
    - Easy to connect cause and effect
    """
    fig = go.Figure()
    
    # Start with the Fed Funds Rate - this is what the Fed controls
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['fed_funds_rate'],
            name='Fed Funds Rate',
            line=dict(color=COLOR_PALETTE['fed_rate'], width=3),
            yaxis='y1',
            hovertemplate='%{x|%B %Y}<br>Fed Rate: %{y:.2f}%<extra></extra>'
        )
    )
    
    # Add inflation as a dotted line for comparison
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['CPI_YoY_pct'],
            name='Inflation',
            line=dict(color=COLOR_PALETTE['inflation'], width=2, dash='dot'),
            yaxis='y2',
            hovertemplate='%{x|%B %Y}<br>Inflation: %{y:.2f}%<extra></extra>'
        )
    )
    
    # Add unemployment as a dashed line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['unemployment_rate'],
            name='Unemployment',
            line=dict(color=COLOR_PALETTE['unemployment'], width=2, dash='dash'),
            yaxis='y2',
            hovertemplate='%{x|%B %Y}<br>Unemployment: %{y:.1f}%<extra></extra>'
        )
    )
    
    # Set up dual y-axes so we can compare different scales
    fig.update_layout(
        title={
            'text': "How Did the Fed Respond? Interest Rates vs Economic Indicators",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        xaxis=dict(title="Year"),
        yaxis=dict(
            title=dict(text="Federal Funds Rate (%)", font=dict(color=COLOR_PALETTE['fed_rate'])),
            tickfont=dict(color=COLOR_PALETTE['fed_rate'])
        ),
        yaxis2=dict(
            title=dict(text="Inflation & Unemployment (%)", font=dict(color="#34495E")),
            tickfont=dict(color="#34495E"),
            overlaying='y',
            side='right'
        ),
        template=THEME,
        height=600,
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    output_path = HTML_DIR / "fed_response_analysis.html"
    fig.write_html(str(output_path))
    print(f"Saved: {output_path}")
    
    return fig


def create_crisis_periods_annotation(df):
    """
    Let's highlight the big moments - the crises that really tested the Fed.
    Shaded regions make it super obvious when things got wild.
    
    Why this works:
    - Draws your eye to the most important periods
    - Crystal clear what happened and when
    - Doesn't clutter things up - just the major events
    """
    # The three big crises we're highlighting
    crises = [
        {'name': '2008 Financial Crisis', 'start': '2008-09-01', 'end': '2009-06-01', 'color': 'rgba(231, 76, 60, 0.2)', 'y_pos': 13},
        {'name': 'COVID-19 Pandemic', 'start': '2020-03-01', 'end': '2020-12-01', 'color': 'rgba(155, 89, 182, 0.2)', 'y_pos': 13.5},
        {'name': '2022 Inflation Surge', 'start': '2021-06-01', 'end': '2023-06-01', 'color': 'rgba(243, 156, 18, 0.2)', 'y_pos': 8}
    ]
    
    fig = go.Figure()
    
    # Show all three metrics together
    fig.add_trace(go.Scatter(x=df['date'], y=df['CPI_YoY_pct'], name='Inflation', 
                            line=dict(color=COLOR_PALETTE['inflation'], width=2)))
    fig.add_trace(go.Scatter(x=df['date'], y=df['unemployment_rate'], name='Unemployment',
                            line=dict(color=COLOR_PALETTE['unemployment'], width=2)))
    fig.add_trace(go.Scatter(x=df['date'], y=df['fed_funds_rate'], name='Fed Rate',
                            line=dict(color=COLOR_PALETTE['fed_rate'], width=2)))
    
    # Shade the crisis periods and add nice labels
    for crisis in crises:
        fig.add_vrect(
            x0=crisis['start'], x1=crisis['end'],
            fillcolor=crisis['color'], opacity=0.5,
            layer="below", line_width=0
        )
        # Add a clean label in the middle of each crisis period
        fig.add_annotation(
            x=pd.Timestamp(crisis['start']) + (pd.Timestamp(crisis['end']) - pd.Timestamp(crisis['start'])) / 2,
            y=crisis['y_pos'],
            text=f"<b>{crisis['name']}</b>",
            showarrow=False,
            font=dict(size=11, color='#2C3E50'),
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#34495E',
            borderwidth=1,
            borderpad=4
        )
    
    fig.update_layout(
        title={
            'text': "Economic Crises and Fed Response: A 25-Year Timeline",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        xaxis_title="Year",
        yaxis_title="Percentage (%)",
        template=THEME,
        height=600,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    output_path = HTML_DIR / "crisis_periods.html"
    fig.write_html(str(output_path))
    print(f"Saved: {output_path}")
    
    return fig


def create_scatter_analysis(df):
    """
    The big question: can the Fed have its cake and eat it too?
    This scatter plot shows if low inflation and low unemployment can happen together,
    or if the Fed has to pick one or the other.
    
    Why this chart matters:
    - Shows the classic economic tradeoff in action
    - Super straightforward - no confusion about what you're looking at
    - Tells you right away if the Fed's goals conflict
    """
    # Color the points by year so we can see how things changed over time
    df['year'] = df['date'].dt.year
    
    fig = px.scatter(
        df,
        x='unemployment_rate',
        y='CPI_YoY_pct',
        color='year',
        size='fed_funds_rate',
        hover_data=['date'],
        title="The Inflation-Unemployment Tradeoff: Phillips Curve in Action?",
        labels={
            'unemployment_rate': 'Unemployment Rate (%)',
            'CPI_YoY_pct': 'Inflation Rate (%)',
            'year': 'Year',
            'fed_funds_rate': 'Fed Rate'
        },
        color_continuous_scale='Viridis'
    )
    
    # Add reference lines to show the "ideal" zone
    fig.add_hline(y=2, line_dash="dash", line_color="gray", 
                  annotation_text="2% Inflation Target")
    fig.add_vline(x=4, line_dash="dash", line_color="gray",
                  annotation_text="~4% Historical Avg Unemployment")
    
    fig.update_layout(
        template=THEME,
        height=600,
        title={'x': 0.5, 'xanchor': 'center', 'font': {'size': 18, 'color': '#2C3E50'}}
    )
    
    output_path = HTML_DIR / "inflation_unemployment_relationship.html"
    fig.write_html(str(output_path))
    print(f"Saved: {output_path}")
    
    return fig


def main():
    """
    Bringing it all together:
    1. Load up our data
    2. Dig through it to find the interesting bits
    3. Create charts that tell the story
    """
    print("="*60)
    print("ASSIGNMENT 2 - FEDERAL RESERVE MANDATE ANALYSIS")
    print("="*60)
    
    # First, grab our data
    df = load_data()
    
    # Then, poke around to see what's interesting
    df = explore_data(df)
    
    # Finally, make some killer visualizations
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60 + "\n")
    
    create_dual_mandate_overview(df)
    create_fed_response_analysis(df)
    create_crisis_periods_annotation(df)
    create_scatter_analysis(df)
    
    print("\n" + "="*60)
    print("All visualizations created successfully!")
    print(f"📁 Check the '{HTML_DIR}' folder for interactive HTML files")
    print("="*60)
    
    return df


if __name__ == "__main__":
    data = main()
