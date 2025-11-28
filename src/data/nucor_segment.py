import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Load Data
df = pd.read_csv('data/interim/nucor_financials/nucor_segments_final.csv')
df['PeriodEndDate'] = pd.to_datetime(df['PeriodEndDate'])
df = df.sort_values('PeriodEndDate')

# Filter for Quarterly (10-Q) data only
q_df = df[df['ReportType'] == '10-Q'].copy()

# 2. Plot
plt.figure(figsize=(12, 6))

# Total Sales
sns.lineplot(data=q_df, x='PeriodEndDate', y='NetSalesExternal_Total', 
             label='Total External Sales', color='black', linewidth=2.5)

# Segment Breakdowns
sns.lineplot(data=q_df, x='PeriodEndDate', y='NetSalesExternal_Mills', 
             label='Steel Mills (Sheet, Plate, Bar)', linestyle='--')
sns.lineplot(data=q_df, x='PeriodEndDate', y='NetSalesExternal_Products', 
             label='Steel Products (Rebar, Joists)', linestyle='--')
sns.lineplot(data=q_df, x='PeriodEndDate', y='NetSalesExternal_Raw', 
             label='Raw Materials (Scrap, DRI)', linestyle='--')

plt.title('Quarterly Net Sales to External Customers by Product Type', fontsize=14)
plt.ylabel('USD (Millions)')
plt.xlabel('Date')
plt.legend(loc='upper left')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('reports/figures/nucor_external_sales_by_type.png', dpi=300)
plt.show()