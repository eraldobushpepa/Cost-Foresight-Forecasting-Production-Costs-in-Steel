import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.ticker as mtick

# 1. Load Data
file_path = 'data/interim/nucor_financials/nucor_segments_final.csv'
df = pd.read_csv(file_path)

# 2. Preprocessing
df['PeriodEndDate'] = pd.to_datetime(df['PeriodEndDate'])
df = df.sort_values('PeriodEndDate')

# Filter for Quarterly (10-Q) data only
q_df = df[df['ReportType'] == '10-Q'].copy()

# 3. Calculate ONLY Total Gross Margin %
# Formula: (Net Sales Total - COGS Total) / Net Sales Total * 100
q_df['Gross_Margin_Total'] = ((q_df['NetSalesExternal_Total'] - q_df['COGS_Total']) / q_df['NetSalesExternal_Total']) * 100

# 4. Plot
plt.figure(figsize=(12, 6))

# Plot ONLY the Total Consolidated Margin
sns.lineplot(data=q_df, x='PeriodEndDate', y='Gross_Margin_Total', 
             color='darkgreen', linewidth=2, marker='o')

# Formatting
plt.title('Nucor Quarterly Gross Margin % (2015-2025)', fontsize=14)
plt.ylabel('Gross Margin %', fontsize=12)
plt.xlabel('Date', fontsize=12)

plt.grid(True, alpha=0.3)

# Format Y-axis as percentage
plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter())

# Save and Show
plt.tight_layout()
plt.savefig('reports/figures/nucor_total_gross_margin_clean.png', dpi=300)
plt.show()