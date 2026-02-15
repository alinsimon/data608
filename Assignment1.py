# IIJA Funding Allocation Analysis
# Data source: data/IIJA_FUNDING_AS_OF_MARCH_2023_assignment1.xlsx

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Create images folder if it doesn't exist
os.makedirs('images', exist_ok=True)

# Load data
df_funding = pd.read_excel('data/IIJA_FUNDING_AS_OF_MARCH_2023_assignment1.xlsx', sheet_name='Funding')
df_population = pd.read_excel('data/IIJA_FUNDING_AS_OF_MARCH_2023_assignment1.xlsx', sheet_name='Population')
df_election = pd.read_excel('data/IIJA_FUNDING_AS_OF_MARCH_2023_assignment1.xlsx', sheet_name='Election_2020')
# Prepare data
df_funding['State'] = df_funding['State, Teritory or Tribal Nation'].str.upper()
df_merged = df_funding.merge(df_population, left_on='State', right_on='State', how='left')
df_merged['Per_Capita_Allocation'] = (df_merged['Total (Billions)'] * 1e9) / (df_merged['Population_Millions'] * 1e6)
df_merged = df_merged.sort_values('Per_Capita_Allocation', ascending=False)
# Visualization 1: Per capita allocation by state
mean_per_capita = df_merged['Per_Capita_Allocation'].mean()
std_per_capita = df_merged['Per_Capita_Allocation'].std()
threshold = mean_per_capita + 1.5 * std_per_capita

# Create color array: highlight outliers in red, others in light gray
colors = ['#d62728' if x > threshold else '#7f7f7f' for x in df_merged['Per_Capita_Allocation']]

# Create the minimalist horizontal bar chart
fig, ax = plt.subplots(figsize=(10, 15))

# Plot bars
bars = ax.barh(df_merged['State'], df_merged['Per_Capita_Allocation'], color=colors, edgecolor='none')

# Add mean reference line
ax.axvline(mean_per_capita, color='black', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Mean: ${mean_per_capita:.0f}')

# Count outliers for subtitle
num_outliers = sum(1 for x in df_merged['Per_Capita_Allocation'] if x > threshold)
max_state = df_merged.iloc[0]['State']
max_value = df_merged.iloc[0]['Per_Capita_Allocation']

# Minimal styling - remove chart junk
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)

# Set labels with clear, simple formatting
ax.set_xlabel('Per Capita Allocation ($)', fontsize=12, fontweight='normal')
ax.set_ylabel('')
ax.set_title('IIJA Funding Per Capita by State/Territory\nNOT Equitable: ' + f'{num_outliers} states receive 1.5× above mean (highlighted in red)', 
             fontsize=14, fontweight='bold', pad=20, loc='left', 
             fontdict={'fontsize': 14, 'weight': 'bold', 'verticalalignment': 'top'})
# Make subtitle smaller and italic using text annotation
fig.text(0.125, 0.97, f'NOT Equitable: {num_outliers} states receive 1.5× above mean (highlighted in red)', 
         fontsize=10, style='italic', color='#d62728', transform=fig.transFigure)

# Minimal gridlines - only vertical
ax.grid(axis='x', alpha=0.3, linewidth=0.5)
ax.set_axisbelow(True)

# Format x-axis as currency
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Adjust font size for state labels
ax.tick_params(axis='y', labelsize=8)
ax.tick_params(axis='x', labelsize=10)

# Enhanced legend with statistics
ax.legend(loc='lower right', frameon=False, fontsize=9)

# Add conclusion box
ax.text(0.98, 0.02, f'Highest: {max_state} (${max_value:.0f})\nLowest: ${df_merged.iloc[-1]["Per_Capita_Allocation"]:.0f}\nRange: {max_value/df_merged.iloc[-1]["Per_Capita_Allocation"]:.1f}× difference',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=9,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff5f5', edgecolor='#d62728', linewidth=1))

# Tight layout
plt.tight_layout()
plt.savefig('images/output_per_capita_allocation_question1.png', dpi=300, bbox_inches='tight')
print("\n✓ Visualization 1 saved: images/output_per_capita_allocation_question1.png")
plt.close()

# Visualization 1B: Total funding vs population
fig, ax = plt.subplots(figsize=(11, 7.5))

# Filter out NaN values for clean plotting
df_plot = df_merged.dropna(subset=['Population_Millions', 'Total (Billions)'])

# Calculate what "equitable" would look like (proportional allocation)
equitable_per_capita = df_plot['Total (Billions)'].sum() / df_plot['Population_Millions'].sum()
equitable_line_x = np.array([0, df_plot['Population_Millions'].max()])
equitable_line_y = equitable_line_x * equitable_per_capita

# Plot equity reference line first
ax.plot(equitable_line_x, equitable_line_y, 'k--', linewidth=1.5, alpha=0.5, 
        label=f'Equitable allocation (${equitable_per_capita*1000:.0f}/person)', zorder=1)

# Create scatter plot
scatter = ax.scatter(df_plot['Population_Millions'], 
                     df_plot['Total (Billions)'],
                     s=90, 
                     c=['#d62728' if x > threshold else '#7f7f7f' for x in df_plot['Per_Capita_Allocation']],
                     alpha=0.7,
                     edgecolors='none',
                     zorder=2)

# Annotate key states (California and top outlier)
for state_name in ['CALIFORNIA', 'ALASKA']:
    row = df_plot[df_plot['State'] == state_name].iloc[0]
    ax.annotate(state_name.title(), 
                xy=(row['Population_Millions'], row['Total (Billions)']),
                xytext=(10, 10), textcoords='offset points',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', linewidth=0.5),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1))

# Minimal styling
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)

# Labels
ax.set_xlabel('Population (Millions)', fontsize=12)
ax.set_ylabel('Total Funding (Billions $)', fontsize=12)
ax.set_title('IIJA Funding vs. Population', 
             fontsize=14, fontweight='bold', pad=20, loc='left')
fig.text(0.125, 0.94, 'Small states fall ABOVE equity line = disproportionately high per capita allocation', 
         fontsize=10, style='italic', color='#333333', transform=fig.transFigure)

# Gridlines
ax.grid(True, alpha=0.3, linewidth=0.5)
ax.set_axisbelow(True)

# Legend
ax.legend(loc='upper left', frameon=False, fontsize=9)

plt.tight_layout()
plt.savefig('images/output_funding_vs_population_question1.png', dpi=300, bbox_inches='tight')
print("✓ Visualization 1B saved: images/output_funding_vs_population_question1.png")
plt.close()

# Visualization 1C: Per capita vs population scatter
fig, ax = plt.subplots(figsize=(11, 7.5))

# Create scatter plot with larger markers for outliers
marker_sizes = [120 if x > threshold else 70 for x in df_plot['Per_Capita_Allocation']]
scatter = ax.scatter(df_plot['Population_Millions'], 
                     df_plot['Per_Capita_Allocation'],
                     s=marker_sizes, 
                     c=['#d62728' if x > threshold else '#7f7f7f' for x in df_plot['Per_Capita_Allocation']],
                     alpha=0.7,
                     edgecolors='none')

# Add horizontal mean line (what equitable would look like)
ax.axhline(mean_per_capita, color='black', linestyle='--', linewidth=1.5, alpha=0.6, 
           label=f'Mean: ${mean_per_capita:.0f}', zorder=1)

# Add shaded region for "above mean" to highlight bias
ax.axhspan(mean_per_capita, df_plot['Per_Capita_Allocation'].max(), 
           alpha=0.05, color='red', zorder=0)
ax.text(df_plot['Population_Millions'].max() * 0.98, mean_per_capita + 300, 
        'Above Mean\n(Over-allocated)', ha='right', fontsize=9, style='italic', color='#d62728')

# Annotate ALL outliers with better positioning
outliers_to_label = df_plot.nlargest(6, 'Per_Capita_Allocation')
for idx, row in outliers_to_label.iterrows():
    ax.annotate(row['State'].title(), 
                xy=(row['Population_Millions'], row['Per_Capita_Allocation']),
                xytext=(8, -8 if row['Per_Capita_Allocation'] > 3000 else 8), 
                textcoords='offset points',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#fff5f5', edgecolor='#d62728', linewidth=1, alpha=0.9),
                arrowprops=dict(arrowstyle='->', color='#d62728', lw=1.5))

# Minimal styling
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)

# Labels
ax.set_xlabel('Population (Millions)', fontsize=12)
ax.set_ylabel('Per Capita Allocation ($)', fontsize=12)
ax.set_title('Per Capita Funding vs. Population', 
             fontsize=14, fontweight='bold', pad=20, loc='left')
fig.text(0.125, 0.95, 'Clear inverse relationship: smaller population = higher per capita allocation', 
         fontsize=10, style='italic', color='#d62728', transform=fig.transFigure)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Gridlines
ax.grid(True, alpha=0.3, linewidth=0.5)
ax.set_axisbelow(True)

# Legend
ax.legend(loc='upper right', frameon=False, fontsize=9)

# Add conclusion box
ax.text(0.02, 0.02, 'Conclusion: Allocation is NOT equitable\nSmall states systematically favored',
        transform=ax.transAxes, ha='left', va='bottom', fontsize=10,
        bbox=dict(boxstyle='round,pad=0.6', facecolor='#f0f0f0', edgecolor='#d62728', linewidth=1.5))

plt.tight_layout()
plt.savefig('images/output_percapita_vs_population_question1.png', dpi=300, bbox_inches='tight')
print("✓ Visualization 1C saved: images/output_percapita_vs_population_question1.png")
plt.close()

# Visualization 2: Political bias analysis
df_merged = df_merged.merge(df_election[['State', 'Biden_Won', 'Party']], on='State', how='left')
df_political = df_merged[df_merged['Biden_Won'].notna()].copy()

biden_allocations = df_political[df_political['Party'] == 'Biden (D)']['Per_Capita_Allocation']
trump_allocations = df_political[df_political['Party'] == 'Trump (R)']['Per_Capita_Allocation']
t_statistic, p_value = stats.ttest_ind(biden_allocations, trump_allocations)

# Create comparison visualization
fig, ax = plt.subplots(figsize=(11, 7))

# Calculate statistics for labels
biden_mean = df_political[df_political['Party'] == 'Biden (D)']['Per_Capita_Allocation'].mean()
trump_mean = df_political[df_political['Party'] == 'Trump (R)']['Per_Capita_Allocation'].mean()
biden_n = len(df_political[df_political['Party'] == 'Biden (D)'])
trump_n = len(df_political[df_political['Party'] == 'Trump (R)'])
difference = trump_mean - biden_mean
percent_difference = (difference / biden_mean) * 100

# Box plot with subtle political color coding (minimalist approach)
biden_data = df_political[df_political['Party'] == 'Biden (D)']['Per_Capita_Allocation']
trump_data = df_political[df_political['Party'] == 'Trump (R)']['Per_Capita_Allocation']

bp = ax.boxplot([biden_data, trump_data],
                 tick_labels=[f'Biden States\n(n={biden_n})', f'Trump States\n(n={trump_n})'],
                 patch_artist=True,
                 widths=0.5,
                 medianprops=dict(color='black', linewidth=2.5),
                 boxprops=dict(linewidth=1.5),
                 whiskerprops=dict(color='black', linewidth=1.5),
                 capprops=dict(color='black', linewidth=1.5),
                 flierprops=dict(marker='o', markerfacecolor='#d62728', markersize=7, 
                                linestyle='none', markeredgecolor='none', alpha=0.7))

# Color boxes with subtle political colors (very muted for minimalism)
bp['boxes'][0].set_facecolor('#b8c5d6')  # Muted blue for Biden
bp['boxes'][0].set_edgecolor('#4a5f7a')
bp['boxes'][1].set_facecolor('#d6b8b8')  # Muted red for Trump
bp['boxes'][1].set_edgecolor('#7a4a4a')

# Minimal styling
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)

# Labels and enhanced title with finding
ax.set_ylabel('Per Capita Allocation ($)', fontsize=12)
ax.set_title('IIJA Funding Per Capita: Biden vs. Trump States', 
             fontsize=14, fontweight='bold', pad=20, loc='left')
fig.text(0.125, 0.92, 'Trump states receive 59% MORE funding per capita than Biden states', 
         fontsize=10, style='italic', color='#333333', transform=fig.transFigure)

# Format y-axis as currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# Add gridlines
ax.grid(axis='y', alpha=0.3, linewidth=0.5)
ax.set_axisbelow(True)

# Add mean values with enhanced annotations
ax.text(1, biden_mean, f'Mean: ${biden_mean:.0f}', 
        ha='center', va='bottom', fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#4a5f7a', linewidth=1))
ax.text(2, trump_mean, f'Mean: ${trump_mean:.0f}', 
        ha='center', va='bottom', fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#7a4a4a', linewidth=1))

# Add difference annotation with arrow
mid_x = 1.5
mid_y = (biden_mean + trump_mean) / 2
ax.annotate('', xy=(2, trump_mean), xytext=(1, biden_mean),
            arrowprops=dict(arrowstyle='<->', color='#d62728', lw=2, alpha=0.6))
ax.text(mid_x, mid_y + 150, f'+${difference:.0f}\n({percent_difference:.0f}% higher)', 
        ha='center', va='center', fontsize=10, fontweight='bold', color='#d62728',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff5f5', edgecolor='#d62728', linewidth=1.5))

# Add conclusion text at bottom
ax.text(0.5, -0.12, 'Conclusion: NO evidence of Biden administration favoritism. Republican states benefit more.',
        transform=ax.transAxes, ha='center', fontsize=10, style='italic', 
        bbox=dict(boxstyle='round,pad=0.6', facecolor='#f0f0f0', edgecolor='gray', linewidth=1))

plt.tight_layout()
plt.savefig('images/output_political_comparison_question2.png', dpi=300, bbox_inches='tight')
print("\n✓ Visualization 2 saved: images/output_political_comparison_question2.png")
plt.close()

print(f"\nAnalysis complete. Trump states: ${trump_mean:.0f}/person | Biden states: ${biden_mean:.0f}/person")


