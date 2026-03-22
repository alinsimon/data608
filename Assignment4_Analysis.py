# Assignment 4: Data Practitioner Salary Visualization
# Question: "How much do we get paid?"
# Audience: Data Scientists, Data Engineers, Data Analysts, Business Analysts, Data Architects, etc.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
import warnings
from matplotlib.colors import LinearSegmentedColormap
warnings.filterwarnings('ignore')

# Use a seaborn dark-grid style for a clean, polished look
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory if it doesn't exist
Path("html").mkdir(exist_ok=True)

# ============================================================================
# LOAD DATA
# ============================================================================
print("Loading salary data...")
df = pd.read_csv('data/BLS_data_practitioner_salaries_by_state.csv')

# Pull out the national-level rows and rank roles by salary, highest first
national_data = df[df['Area'] == 'National'].copy()
national_data = national_data.sort_values('Annual_Mean_Wage', ascending=False)

print(f"\nRoles analyzed: {len(national_data)}")
print(f"Salary range: ${national_data['Annual_Mean_Wage'].min():,.0f} - ${national_data['Annual_Mean_Wage'].max():,.0f}")


# ============================================================================
# VISUALIZATION 1: National salary comparison by role
# ============================================================================
# Sorted from highest to lowest so the top earners stand out immediately.
# Horizontal bars work better here since the role names are long.

print("\n[1/3] Creating primary visualization: Role comparison...")

# Prepare data for horizontal bar chart
roles = national_data['Role'].tolist()
salaries = national_data['Annual_Mean_Wage'].tolist()
employment = national_data['Employment'].tolist()

# Top 2 roles get bold blue; everything else fades to gray
colors = []
for i in range(len(salaries)):
    if i == 0:  # Highest paying
        colors.append('#1f77b4')  # Bold blue for emphasis
    elif i == 1:  # Second highest
        colors.append('#4a90c4')  # Slightly lighter blue
    else:  # All others - muted gray scale
        colors.append('#a8a8a8')

# Create figure with optimal dimensions
fig, ax = plt.subplots(figsize=(12, 7))

# Create horizontal bars
y_pos = np.arange(len(roles))
bars = ax.barh(y_pos, salaries, color=colors, height=0.7)

# Give the top 2 bars a dark outline so they stand out even more
for i, bar in enumerate(bars):
    if i < 2:  # Top 2 highest paying roles
        bar.set_edgecolor("#0e3b5c")
        bar.set_linewidth(2)

# Label every bar with the actual dollar amount so readers don't have to squint at the axis
for i, (bar, salary) in enumerate(zip(bars, salaries)):
    # Long bars get white text inside; short bars get dark text outside
    if i < 2:
        label_x = salary - 5000
        label_color = 'white'
        fontsize = 14
        fontweight = 'bold'
    else:
        label_x = salary + 3000
        label_color = '#333333'
        fontsize = 12
        fontweight = 'normal'
    
    ax.text(label_x, i, f'${salary:,.0f}', 
            va='center', ha='right' if i < 2 else 'left',
            color=label_color, fontsize=fontsize, fontweight=fontweight)

# Clean up the axes
ax.set_yticks(y_pos)
ax.set_yticklabels(roles, fontsize=13, fontweight='bold')
ax.set_xlabel('Annual Mean Wage (USD)', fontsize=13, fontweight='bold')
ax.set_xlim(0, max(salaries) * 1.15)

# Drop the top and right borders — less visual noise
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')

# Show dollar amounts on the x-axis
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# No gridlines — the value labels on each bar do the job
ax.grid(False)

# Title states the actual finding rather than just describing the chart
title_text = "Software Developers and Data Architects Lead \n $143K - $145K Average Salaries"
subtitle_text = "National average salaries for data practitioners (2024 BLS data)"

ax.text(0.5, 1.12, title_text, transform=ax.transAxes, 
        fontsize=15, fontweight='bold', ha='center', va='top')
ax.text(0.5, 1.04, subtitle_text, transform=ax.transAxes,
        fontsize=11, color='#666666', ha='center', va='top')


plt.tight_layout()
plt.savefig('images/Assignment4_salary_by_role.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: images/Assignment4_salary_by_role.png")
plt.close()



# ============================================================================
# VISUALIZATION 2: Geographic salary variation for top roles
# ============================================================================
# Focuses on the top 3 highest-paying roles to keep the state comparison clean.

print("\n[2/3] Creating secondary visualization: Geographic variation...")

# Select top 3 roles
top_roles = national_data.head(3)['Role'].tolist()

# State-level data only — strip out the national aggregate row
state_data = df[
    (df['Role'].isin(top_roles)) & 
    (df['State_Code'] != '00') &  # Exclude national
    (df['State_Code'].notna())
].copy()

# Average the three top-role salaries per state into a single number for ranking
state_avg = state_data.groupby('Area').agg({
    'Annual_Mean_Wage': 'mean',
    'State_Code': 'first'
}).reset_index()

state_avg = state_avg.sort_values('Annual_Mean_Wage', ascending=True)  # Ascending so the highest state ends up at the top of the horizontal chart

# Show only the top 15 and bottom 15 — the extremes tell the story without overwhelming the chart
top_15_states_data = state_avg.tail(15)  # Highest salaries
bottom_15_states_data = state_avg.head(15)  # Lowest salaries
comparison_states = pd.concat([bottom_15_states_data, top_15_states_data])

# Re-sort ascending so California (the top earner) lands at the top of the chart
comparison_states = comparison_states.sort_values('Annual_Mean_Wage', ascending=True)

# Create visualization showing the range
states_list = comparison_states['Area'].tolist()
state_salaries = comparison_states['Annual_Mean_Wage'].tolist()

# California (position 29, the top) gets bold green; next 4 get lighter green;
# bottom 5 get red; the middle group fades to gray
colors_geographic = []
for i in range(len(state_salaries)):
    if i >= 29:  # Highest paying state (California at top) - DOMINANT
        colors_geographic.append('#2ca02c')  # Bold green for emphasis
    elif i >= 25:  # Top 5 states - secondary emphasis
        colors_geographic.append('#5cb85c')  # Lighter green
    elif i < 5:  # Bottom 5 states (Puerto Rico at bottom) - warning color
        colors_geographic.append('#d9534f')  # Red for lowest
    else:  # All others - muted
        colors_geographic.append('#b0b0b0')  # Gray

# Taller figure so 30 states have enough room to breathe
fig, ax = plt.subplots(figsize=(14, 12))

y_pos = np.arange(len(states_list))
bars = ax.barh(y_pos, state_salaries, color=colors_geographic, height=0.75)

# Bold outline on California, lighter outline on the next 4 states
for i, bar in enumerate(bars):
    if i >= 29:  # Top state (California at top) gets bold border
        bar.set_edgecolor('#1a6e1a')
        bar.set_linewidth(3)
    elif i >= 25:  # Top 5 get subtle border
        bar.set_edgecolor('#4ca64c')
        bar.set_linewidth(1.5)

# California gets white text inside its bar; everyone else gets dark text outside
for i, (bar, salary) in enumerate(zip(bars, state_salaries)):
    if i >= 29:  # Top state (California) - white text inside bar
        label_x = salary - 5000
        label_color = 'white'
        fontsize = 13
        fontweight = 'bold'
    else:  # Others - outside bar
        label_x = salary + 2000
        label_color = '#333333'
        fontsize = 11
        fontweight = 'bold' if i >= 25 else 'normal'
    
    ax.text(label_x, i, f'${salary:,.0f}', 
            va='center', ha='right' if i >= 29 else 'left',
            color=label_color, fontsize=fontsize, fontweight=fontweight)

# Bold y-axis labels so state names are easy to scan
ax.set_yticks(y_pos)
# Build the label list — California gets its own styling applied after
state_labels_styled = []
for i, state in enumerate(states_list):
    state_labels_styled.append(state)
        
ax.set_yticklabels(state_labels_styled, fontsize=12, fontweight='bold')
# Color California's y-axis label green to match its bar
ytick_labels = ax.get_yticklabels()
if ytick_labels and len(ytick_labels) == 30:
    ytick_labels[29].set_color('#2ca02c')  # California is at index 29 (top)
    ytick_labels[29].set_fontweight('extra bold')
    ytick_labels[29].set_fontsize(13)
ax.set_xlabel('Average Annual Salary (USD)', fontsize=12, fontweight='bold')
ax.set_xlim(0, max(state_salaries) * 1.12)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')

ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax.grid(False)

# Title names the winning state and its average salary up front
highest_state = comparison_states.iloc[-1]['Area']  # Last in ascending sort = highest
lowest_state = comparison_states.iloc[0]['Area']  # First in ascending sort = lowest
highest_salary = state_salaries[-1]  # Last element = highest
lowest_salary = state_salaries[0]  # First element = lowest

geo_title = f"{highest_state} Leads Data Practitioner Salaries\n${highest_salary:,.0f} Average for Top Roles"
geo_subtitle = f"Average salary for Software Developers, Data Architects, and Data Scientists by state"

ax.text(0.5, 1.08, geo_title, transform=ax.transAxes,
        fontsize=15, fontweight='bold', ha='center', va='top')
ax.text(0.5, 1.02, geo_subtitle, transform=ax.transAxes,
        fontsize=10, color='#666666', ha='center', va='top')

# Callout box showing the percentage gap between the best and worst states
salary_gap = ((highest_salary / lowest_salary) - 1) * 100
ax.text(0.02, 0.98, f"{highest_state} pays {salary_gap:.0f}% more than {lowest_state}",
        transform=ax.transAxes, fontsize=10, color='#2ca02c', style='italic',
        bbox=dict(boxstyle='round,pad=0.6', facecolor='#e8f5e9', edgecolor='#2ca02c', linewidth=1.5))

# Dashed line separating the bottom 15 (positions 0-14) from the top 15 (positions 15-29)
ax.axhline(y=14.5, color='#333333', linestyle='--', linewidth=2, alpha=0.6)
# Label sits just inside the lower group, arrow points further down into it
ax.text(max(state_salaries) * 0.5, 13, 'Bottom 15 States ↓', 
        ha='center', fontsize=13, fontweight='bold', color='white',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#d62728', edgecolor='white', linewidth=1.5, alpha=0.9))
# Label sits just inside the upper group, arrow points further up into it
ax.text(max(state_salaries) * 0.5, 16, 'Top 15 States ↑', 
        ha='center', fontsize=13, fontweight='bold', color='white',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#2ca02c', edgecolor='white', linewidth=1.5, alpha=0.9))

plt.tight_layout()
plt.savefig('images/Assignment4_salary_by_state.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: images/Assignment4_salary_by_state.png")
plt.close()



# ============================================================================
# VISUALIZATION 3: State × role salary heatmap
# ============================================================================
# Shows the full salary landscape across the top 10 states and all 7 roles.
# California's dominance and the Software Developer premium both stand out clearly.

print("\n[3/3] Creating focused visualization: California's salary dominance...")

# Get top 10 states for cleaner display (not 15)
state_role_data = df[
    (df['State_Code'] != '00') &
    (df['State_Code'].notna())
].copy()

print(f"  - State role data records: {len(state_role_data)}")

# Calculate average salary per state across all roles
state_overall = state_role_data.groupby('Area')['Annual_Mean_Wage'].mean().reset_index()
state_overall = state_overall.sort_values('Annual_Mean_Wage', ascending=False)
top_10_states = state_overall.head(10)['Area'].tolist()

print(f"  - Top 10 states identified: {len(top_10_states)}")

# Filter to top 10 states
matrix_data = state_role_data[state_role_data['Area'].isin(top_10_states)].copy()

print(f"  - Matrix data records: {len(matrix_data)}")

# Pivot to create matrix
salary_matrix = matrix_data.pivot_table(
    index='Area',
    columns='Role',
    values='Annual_Mean_Wage',
    aggfunc='mean'
)

print(f"  - Salary matrix shape: {salary_matrix.shape}")

# Reorder states by average salary (descending)
salary_matrix['avg'] = salary_matrix.mean(axis=1)
salary_matrix = salary_matrix.sort_values('avg', ascending=False)
salary_matrix = salary_matrix.drop('avg', axis=1)

# Reorder roles by average salary (descending)
role_order = national_data['Role'].tolist()
salary_matrix = salary_matrix[role_order]

print(f"  - Creating focused heatmap with emphasized top cell...")

# Create figure with better proportions
fig, ax = plt.subplots(figsize=(16, 10))

# Calculate value range for color normalization
vmin = salary_matrix.min().min()
vmax = salary_matrix.max().max()
vmean = salary_matrix.values.mean()  # used to decide whether cell text should be white or dark

# Find which cell has the highest salary — that's the one we'll highlight
max_value = salary_matrix.max().max()
max_state = salary_matrix.max(axis=1).idxmax()
max_role = salary_matrix.max().idxmax()
max_row = list(salary_matrix.index).index(max_state)
max_col = list(salary_matrix.columns).index(max_role)

# Custom colormap: near-white for low salaries, dark blue for high ones.
# Colorblind-friendly and perceptually smooth so the gradient stays honest.
colors_list = ['#f5f5f5', '#d4f1e8', '#a8ddb5', '#7bccc4', '#4eb3d3', '#2b8cbe', '#08589e']
custom_cmap = LinearSegmentedColormap.from_list('professional_green', colors_list, N=256)

im = ax.imshow(salary_matrix.values, cmap=custom_cmap, aspect='auto',
               vmin=vmin, vmax=vmax, interpolation='nearest')

# White lines between cells so the grid reads clearly
for i in range(len(salary_matrix.index) + 1):
    ax.axhline(i - 0.5, color='white', linewidth=2)
for j in range(len(salary_matrix.columns) + 1):
    ax.axvline(j - 0.5, color='white', linewidth=2)

# Red border around the peak cell (California × Software Developer) so the eye goes there first
from matplotlib.patches import Rectangle
emphasis_rect = Rectangle((max_col - 0.5, max_row - 0.5), 1, 1, 
                          linewidth=5, edgecolor='#d73027', facecolor='none', zorder=10)
ax.add_patch(emphasis_rect)

# Write the salary in every cell; special styling for the peak cell, the California row, and the Software Developer column
for i, state in enumerate(salary_matrix.index):
    for j, role in enumerate(salary_matrix.columns):
        value = salary_matrix.iloc[i, j]
        
        if pd.notna(value):
            text = f'${value:,.0f}'
            
            # Peak cell: white text on red background so it's impossible to miss
            if i == max_row and j == max_col:
                text_color = 'white'
                weight = 'bold'
                fontsize = 13
                bbox_props = dict(boxstyle='round,pad=0.4', facecolor='#d73027', 
                                edgecolor='none', alpha=0.8)
            # California row: bold text to reinforce its leadership across all roles
            elif i == 0:
                text_color = 'white' if value > vmean else '#2d2d2d'
                weight = 'bold'
                fontsize = 11
                bbox_props = None
            # Software Developer column: bold for the same reason
            elif j == 0:
                text_color = 'white' if value > vmean else '#2d2d2d'
                weight = 'bold'
                fontsize = 11
                bbox_props = None
            # All other cells: white text on dark backgrounds, dark text on light ones
            else:
                normalized_value = (value - vmin) / (vmax - vmin)
                text_color = 'white' if normalized_value > 0.5 else '#404040'
                weight = 'normal'
                fontsize = 10
                bbox_props = None
            
            ax.text(j, i, text, ha='center', va='center', 
                   color=text_color, fontsize=fontsize, weight=weight,
                   bbox=bbox_props, zorder=11)

ax.set_xticks(np.arange(len(salary_matrix.columns)))
ax.set_yticks(np.arange(len(salary_matrix.index)))

# Wrap role names onto two lines so the column headers don't crowd each other
role_labels = [
    'Software\nDeveloper',
    'Data\nArchitect',
    'Data\nScientist',
    'Business\nAnalyst',
    'Data\nAnalyst',
    'Database\nAdmin',
    'Operations\nResearch'
]

ax.set_xticklabels(role_labels, fontsize=12, weight='bold', color='#2d2d2d')
ax.set_yticklabels(salary_matrix.index, fontsize=12, fontweight='bold', color='#2d2d2d')

# Make California's row label red so it matches the highlighted cell
ytick_labels = ax.get_yticklabels()
if ytick_labels:
    ytick_labels[0].set_color('#d73027')
    ytick_labels[0].set_fontweight('extra bold')
    ytick_labels[0].set_fontsize(13)

# Same treatment for the Software Developer column label
xtick_labels = ax.get_xticklabels()
if xtick_labels:
    xtick_labels[0].set_color('#d73027')
    xtick_labels[0].set_fontweight('extra bold')
    xtick_labels[0].set_fontsize(13)

# Hide the tick marks — labels are enough
ax.tick_params(which='both', length=0)

# Move column labels above the chart so they sit right above the data
ax.xaxis.tick_top()
ax.xaxis.set_label_position('top')

# Add a color scale on the right so readers can map cell colors to salary values
cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.02, aspect=30)
cbar.set_label('Annual Mean Wage', fontsize=12, weight='bold', 
               rotation=270, labelpad=25, color='#2d2d2d')
cbar.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
cbar.ax.tick_params(labelsize=10, colors='#2d2d2d')
# Light gray border to define the color scale's edges
cbar.outline.set_edgecolor('#cccccc')
cbar.outline.set_linewidth(1)

# Title names California and the exact peak salary — the main takeaway up front
title = f"California Dominates: {max_role}s Earn ${max_value:,.0f}"
subtitle = f"Top 10 states × all data roles • Darker blue = higher salary"

fig.text(0.5, 0.97, title, fontsize=18, weight='bold', ha='center', va='top', color='#1a1a1a')
fig.text(0.5, 0.945, subtitle, fontsize=11, color='#666666', ha='center', va='top', style='italic')

# Compute the salary gap between the highest and lowest cells in case we want to annotate it later
min_value_in_matrix = salary_matrix.min().min()
gap = ((max_value / min_value_in_matrix) - 1) * 100


plt.tight_layout(rect=[0, 0.02, 1, 0.93])
plt.savefig('images/Assignment4_salary_heatmap.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("  ✓ Saved: images/Assignment4_salary_heatmap.png")
plt.close()



# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("\n" + "="*80)
print("VISUALIZATION SUMMARY")
print("="*80)
print("\nVISUALIZATION 1: Role Comparison (Primary)")
print("  Purpose: Show WHO earns the most")
print("  Emphasis: Top 2 roles highlighted in bold blue")
print("  Insight: Software Developers ($145K) and Data Architects ($143K) lead")
print("  Title: 'Software Developers and Data Architects Lead: $145K and $143K Average Salaries'")
print("  Files: images/Assignment4_salary_by_role.png")

print("\nVISUALIZATION 2: Geographic Variation (Secondary)")
print("  Purpose: Show WHERE top roles pay the most")
print("  Emphasis: Color gradient (green=high, red=low)")
print(f"  Insight: {salary_gap:.0f}% salary gap between top and bottom states")
print("  Title: 'Location Matters: [Highest State] vs [Lowest State]'")
print("  Files: images/Assignment4_salary_by_state.png")

print("\nVISUALIZATION 3: Complete Matrix (Bonus for Analysts)")
print("  Purpose: Full detail for all role×state combinations")
print("  Emphasis: Heatmap with RdYlGn color scale")
print("  Insight: Comprehensive view of salary landscape")
print("  Files: images/Assignment4_salary_heatmap.png")

print("\nKEY FINDINGS:")
print(f"  • Highest paying role: {national_data.iloc[0]['Role']} (${national_data.iloc[0]['Annual_Mean_Wage']:,.0f})")
print(f"  • Lowest paying role: {national_data.iloc[-1]['Role']} (${national_data.iloc[-1]['Annual_Mean_Wage']:,.0f})")
print(f"  • Salary spread: {((national_data.iloc[0]['Annual_Mean_Wage'] / national_data.iloc[-1]['Annual_Mean_Wage'] - 1) * 100):.1f}%")
print(f"  • Highest paying state: {state_overall.iloc[0]['Area']} (${state_overall.iloc[0]['Annual_Mean_Wage']:,.0f} avg)")
print(f"  • Lowest paying state: {state_overall.iloc[-1]['Area']} (${state_overall.iloc[-1]['Annual_Mean_Wage']:,.0f} avg)")

print("\nDESIGN PRINCIPLES APPLIED:")
print("  ✓ Emphasis: Bold colors for top-paying roles, muted for others")
print("  ✓ Salience: Sorted data with highest values at top")
print("  ✓ Pre-conscious Processing: Horizontal bars, color coding, position")
print("  ✓ Context: Titles with insights, annotations explaining significance")
print("  ✓ Clarity: Minimal gridlines, clear labels, no decorative elements")

print("\n" + "="*80)
print("ANALYSIS COMPLETE - View PNG/PDF files in images/ folder")
print("="*80)

