import pandas as pd
import numpy as np

np.random.seed(42)

# 1. Create quarterly date range (2015–2024)
dates = pd.date_range(start='2015-01-01', end='2024-12-31', freq='QE')

n = len(dates)

# 2. Generate core features with realistic patterns

# Scrap price: volatile but upward drift
scrap = 250 + np.cumsum(np.random.normal(0, 5, n))

# Electricity price: small trend + seasonality
electricity = 50 + 0.5*np.arange(n) + 3*np.sin(np.linspace(0, 8*np.pi, n))

# Natural gas: volatile energy-style
natural_gas = 3 + 0.2*np.arange(n) + np.random.normal(0, 0.3, n)

# Diesel price
diesel = 3 + 0.02*np.arange(n) + np.random.normal(0, 0.1, n)

# Rail freight price index
rail = 120 + 0.7*np.arange(n) + np.random.normal(0, 1.5, n)

# Natural disaster count (integer)
disasters = np.random.poisson(lam=3, size=n)

# Wage index (slow upward trend)
wage = 20 + 0.1*np.arange(n)

# Scrap exports (seasonal-ish)
exports = 300 + 20*np.sin(np.linspace(0, 6*np.pi, n)) + np.random.normal(0, 15, n)

# USD Index
usd = 90 + np.random.normal(0, 2, n)

# Graphite electrode price (very volatile)
electrodes = 200 + np.cumsum(np.random.normal(0, 10, n))

# Economic Policy Uncertainty Index
epu = 100 + 5*np.sin(np.linspace(0, 4*np.pi, n)) + np.random.normal(0, 10, n)

# 3. Generate Nucor-style accounting data

# Total tons shipped — increases slowly, seasonal bump
tons = 6000 + 50*np.arange(n) + 200*np.sin(np.linspace(0, 6*np.pi, n))

# Cost of products sold — driven by scrap + electricity + random
cogs = (scrap*5 + electricity*20 + natural_gas*50) * (tons/10000) \
       + np.random.normal(0, 50000, n)

# Net Sales — markup over COGS
sales = cogs * (1.10 + np.random.normal(0, 0.02, n))

# Derived metrics
cost_per_ton = cogs / tons
sales_per_ton = sales / tons
gross_margin_per_ton = sales_per_ton - cost_per_ton

# Inventory for turnover: random but stable
inventory = 200000 + np.random.normal(0, 20000, n)

inventory_turnover = cogs / inventory

# 4. Build final dataset

df_quarterly = pd.DataFrame({
    "Date": dates,
    "Scrap_Price": scrap,
    "Electricity_Price": electricity,
    "Natural_Gas_Price": natural_gas,
    "Diesel_Price": diesel,
    "Rail_Price": rail,
    "Disaster_Event_Count": disasters,
    "Avg_Hourly_Wage": wage,
    "US_Scrap_Exports": exports,
    "US_Dollar_Index": usd,
    "Graphite_Electrode_Price": electrodes,
    "Economic_Policy_Uncertainty_Index": epu,
    "Total_Tons_Shipped": tons,
    "Cost_of_Products_Sold": cogs,
    "Net_Sales": sales,
    "Cost_Per_Ton": cost_per_ton,
    "Sales_Per_Ton": sales_per_ton,
    "Gross_Margin_Per_Ton": gross_margin_per_ton,
    "Inventory": inventory,
    "Inventory_Turnover": inventory_turnover
})

df_quarterly.to_csv("toy_quarterly_data.csv", index=False)

df_quarterly.head()
