import pandas as pd
from functools import reduce
import os

# --- CONFIGURATION ---
standard_config = [
    {"file": "PPI_Ferrous_Metal_Scrap.csv", "date": "observation_date", "val": "PCU33123312", "name": "X1_Scrap_Price", "skip": 0},
    {"file": "EIA_Electricity_Price_Monthly.csv", "date": "Month", "val": "industrial cents per kilowatthour", "name": "X2_Electricity_Price", "skip": 4},
    {"file": "EIA_Natural_Gas_Price_Monthly.csv", "date": "Month", "val": "Henry Hub Natural Gas Spot Price Dollars per Million Btu", "name": "X3_Natural_Gas_Price", "skip": 4},
    {"file": "EIA_Diesel_Price_Monthly.csv", "date": "Month", "val": "U.S. No 2 Diesel Ultra Low Sulfur (0-15 ppm) Retail Prices Dollars per Gallon", "name": "X4_Diesel_Price", "skip": 4},
    {"file": "BLS_rail_price_monthly.csv", "date": "observation_date", "val": "PCU48214821", "name": "X5_Rail_Price", "skip": 0},
    {"file": "hourly_wage_monthly.csv", "date": "observation_date", "val": "CES0500000003", "name": "X7_Hourly_Wage", "skip": 0},
    {"file": "Graphite_Electrode_Price.csv", "date": "observation_date", "val": "PCU3359913359910", "name": "X10_Graphite_Price", "skip": 0},
    {"file": "PPI_All_Commodities.csv.csv", "date": "observation_date", "val": "PPIACO", "name": "X_PPI_All_Commodities", "skip": 0}
]

dfs_to_merge = []

print("--- Processing Standard Monthly Files ---")
for cfg in standard_config:
    try:
        df = pd.read_csv(f"data/external/{cfg['file']}", skiprows=cfg["skip"])
        df["Date"] = pd.to_datetime(df[cfg["date"]], errors='coerce')
        df = df.dropna(subset=["Date"]).set_index("Date")
        df_q = df[[cfg["val"]]].resample("QE").mean() # Using 'QE' for Quarter End
        df_q.columns = [cfg["name"]]
        df_q.index.name = "QuarterEnd"
        dfs_to_merge.append(df_q)
        print(f"✅ Processed {cfg['name']}")
    except Exception as e:
        print(f"❌ Error on {cfg['file']}: {e}")

print("--- Processing Daily Data ---")
try:
    df_dollar = pd.read_csv("data/external//US_Dollar_Index.csv")
    df_dollar["Date"] = pd.to_datetime(df_dollar["observation_date"], errors='coerce')
    df_dollar = df_dollar.dropna(subset=["Date"]).set_index("Date")
    df_dollar["DTWEXBGS"] = pd.to_numeric(df_dollar["DTWEXBGS"], errors='coerce')
    df_dollar_q = df_dollar[["DTWEXBGS"]].resample("QE").mean()
    df_dollar_q.columns = ["X9_US_Dollar_Index"]
    df_dollar_q.index.name = "QuarterEnd"
    dfs_to_merge.append(df_dollar_q)
    print("✅ Processed X9_US_Dollar_Index")
except Exception as e:
    print(f"❌ Error on US Dollar: {e}")

print("--- Processing Event Data ---")
try:
    df_noaa = pd.read_csv("data/external/NOAA_disasters_clean.csv")
    df_noaa["Date"] = pd.to_datetime(df_noaa["Begin Date"], errors='coerce')
    df_noaa = df_noaa.dropna(subset=["Date"])
    df_noaa["Quarter"] = df_noaa["Date"].dt.to_period("Q")
    df_noaa_q = df_noaa.groupby("Quarter").agg({"CPI-Adjusted Cost": "sum", "Name": "count"})
    df_noaa_q.index = df_noaa_q.index.to_timestamp(freq="Q")
    df_noaa_q.index.name = "QuarterEnd"
    df_noaa_q.columns = ["X6_Disaster_Cost_Sum", "X6_Disaster_Event_Count"]
    dfs_to_merge.append(df_noaa_q)
    print("✅ Processed X6_Disaster_Event_Count")
except Exception as e:
    print(f"❌ Error on NOAA: {e}")

print("--- Processing Policy Uncertainty (X12) ---")
try:
    df_policy = pd.read_csv("data/external/US_Policy_Uncertainty_Data.csv")
    # FIX: Force numeric to drop footer text
    df_policy["Year"] = pd.to_numeric(df_policy["Year"], errors='coerce')
    df_policy = df_policy.dropna(subset=["Year"])
    df_policy["Date"] = pd.to_datetime(dict(year=df_policy.Year, month=df_policy.Month, day=1))
    df_policy = df_policy.set_index("Date")
    df_policy_q = df_policy[["News_Based_Policy_Uncert_Index"]].resample("QE").mean()
    df_policy_q.columns = ["X12_Economic_Policy_Uncertainty"]
    df_policy_q.index.name = "QuarterEnd"
    dfs_to_merge.append(df_policy_q)
    print("✅ Processed X12_Economic_Policy_Uncertainty")
except Exception as e:
    print(f"❌ Error on Policy Uncertainty: {e}")

print("--- Merging All External Features ---")
df_external = reduce(lambda left, right: pd.merge(left, right, on='QuarterEnd', how='outer'), dfs_to_merge)
df_external = df_external.sort_index()

# Save
output_path = "data/interim/external_features_quarterly.csv"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_external.to_csv(output_path)
print(f"🎉 Success! External features saved to: {output_path}")