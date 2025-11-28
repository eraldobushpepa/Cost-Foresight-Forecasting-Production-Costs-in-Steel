import pandas as pd
import matplotlib.pyplot as plt

# 1. Load Data
# Ensure these files are in the same directory
df_segments = pd.read_csv('data/interim/nucor_financials/nucor_segments_final.csv')
df_general = pd.read_csv('data/processed/master_dataset_general.csv')

# 2. Process Financials (Sales & COGS)
df_segments['PeriodEndDate'] = pd.to_datetime(df_segments['PeriodEndDate'])
df_segments['Year'] = df_segments['PeriodEndDate'].dt.year

# CRITICAL: Filter for 10-Q (Quarterly) reports only.
# We sum the quarters to get the Annual Total. 
# If we included 10-K rows, we would double-count the data.
df_q = df_segments[df_segments['ReportType'] == '10-Q'].copy()
annual_financials = df_q.groupby('Year')[['NetSalesExternal_Total', 'COGS_Total']].sum()

# 3. Process Operational Metrics (Inventory Turnover)
# We take the average turnover across the year
annual_inv = df_general.groupby('Year')['X12_Inventory_Turnover'].mean()

# 4. Merge Dataframes
df_table = annual_financials.join(annual_inv, how='inner')

# 5. Calculate Accounting KPIs
# COGS Ratio = Cost / Sales
df_table['COGS Ratio (%)'] = (df_table['COGS_Total'] / df_table['NetSalesExternal_Total']) * 100

# Gross Margin = (Sales - Cost) / Sales
df_table['Gross Margin (%)'] = ((df_table['NetSalesExternal_Total'] - df_table['COGS_Total']) / df_table['NetSalesExternal_Total']) * 100

# 6. Formatting for the Report
# Rename columns to be professional
df_table.rename(columns={
    'NetSalesExternal_Total': 'Net Sales ($M)',
    'COGS_Total': 'COGS ($M)',
    'X12_Inventory_Turnover': 'Inv. Turnover (x)'
}, inplace=True)

# Select and Reorder columns
cols = ['Net Sales ($M)', 'COGS ($M)', 'COGS Ratio (%)', 'Gross Margin (%)', 'Inv. Turnover (x)']
df_table = df_table[cols]

# Round to 2 decimal places
df_table = df_table.round(2)

# Reset index so "Year" becomes a column in the plot
df_display = df_table.reset_index()

# 7. Render the Table as an Image
fig, ax = plt.subplots(figsize=(10, 6))
ax.axis('off') # Hide the graph axes

# Create the table
table = pd.plotting.table(
    ax, 
    df_display, 
    loc='center', 
    cellLoc='center',
    colWidths=[0.15] * len(df_display.columns)
)

# Styling for the report
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5) # Make rows taller for readability

# Add a header color (Nucor-style blue/grey)
for key, cell in table.get_celld().items():
    row, col = key
    if row == 0: # Header row
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('#40466e')

# Save
plt.title('Nucor Annual Financial Summary (2015-2025)', fontsize=14, fontweight='bold', y=0.95)
plt.tight_layout()
plt.savefig('reports/figures/nucor_annual_financial_summary.png', dpi=300, bbox_inches='tight')

print("✅ Table generated and saved as 'nucor_annual_financial_summary.png'")
print(df_display)