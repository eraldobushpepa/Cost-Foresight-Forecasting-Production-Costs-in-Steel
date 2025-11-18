import pandas as pd
import os
import re
import numpy as np

# --- CONFIGURATION ---
INPUT_FILE = "data/interim/nucor_financials/nucor_01_RAW_EXTRACT.csv"
OUTPUT_FILE = "data/interim/nucor_04_METRICS.csv"

def extract_tons(text):
    if pd.isna(text): return None
    text = str(text)
    # Look for "24,334" or "24,334,000"
    # We prioritize "tons" or "were" to avoid random years like "2015"
    patterns = [r'([\d,]+)\s+tons', r'were\s+([\d,]+)', r'to\s+([\d,]+)']
    for p in patterns:
        match = re.search(p, text)
        if match:
            try: return float(match.group(1).replace(",", ""))
            except: pass
    return None

def normalize_financials(val):
    if pd.isna(val): return val
    if val < 100_000: return val * 1_000_000
    if val < 1_000_000_000: return val * 1_000
    return val

def get_fiscal_quarter(date):
    m = date.month
    if m in [1, 2, 3, 4]: return 1
    if m in [5, 6, 7]: return 2
    if m in [8, 9, 10]: return 3
    return 4

def calculate_q4_data(df):
    print("--- Calculating Q4 from 10-K Data ---")
    
    # MANUAL BACKUPS
    manual_annual_tons = {
        2015: 22748000,
        2016: 24334000,
        2017: 26489000,
        2018: 27899000,
        2019: 26532000
    }
    
    # MANUAL FINANCIALS (Cost, Sales)
    manual_financials = {
        2024: (25821000000, 30734000000),
        2023: (28441000000, 34714000000),
        2022: (31267000000, 41512000000),
        2021: (27283000000, 36484000000),
        2020: (19304000000, 20140000000),
        2019: (20806000000, 22589000000),
        2018: (21838000000, 25067000000),
        2017: (18502000000, 20252000000),
        2016: (14909000000, 16208000000),
        2015: (15184000000, 16439000000)
    }

    processed_rows = []
    
    for year, group in df.groupby("Year"):
        annual = group[group["ReportType"] == "10-K"]
        quarterly = group[group["ReportType"] == "10-Q"]
        
        for _, row in quarterly.iterrows():
            processed_rows.append(row)
            
        if not annual.empty and len(quarterly) == 3:
            ann_row = annual.iloc[0].copy()
            
            # 1. Financials bckup
            if pd.isna(ann_row["Cost_of_products_sold"]) and year in manual_financials:
                ann_row["Cost_of_products_sold"] = manual_financials[year][0]
            if pd.isna(ann_row["Net_sales"]) and year in manual_financials:
                ann_row["Net_sales"] = manual_financials[year][1]
                
            # 2. Tonnage logic (aggressive backup)
            annual_tons = ann_row["Tons_Shipped"]
            
            # Convert '18846' -> '18,846,000' if needed
            if pd.notna(annual_tons) and annual_tons < 100_000:
                annual_tons *= 1000

            # STRICT CHECK: If annual tons < 20M, it's likely wrong (segment data). Use Backup.
            # Nucor ships >20M tons/year.
            if (pd.isna(annual_tons) or annual_tons < 20_000_000) and year in manual_annual_tons:
                annual_tons = manual_annual_tons[year]
                print(f"   ℹ️ Used Manual Backup Tonnage for {year}: {annual_tons:,.0f}")

            # 3. Calc Q4
            if pd.notna(ann_row["Cost_of_products_sold"]) and pd.notna(annual_tons):
                q4_cost = ann_row["Cost_of_products_sold"] - quarterly["Cost_of_products_sold"].sum()
                q4_sales = ann_row["Net_sales"] - quarterly["Net_sales"].sum()
                q4_tons = annual_tons - quarterly["Tons_Shipped"].sum()
                
                q4_row = ann_row.copy()
                q4_row["ReportType"] = "Calculated_Q4"
                q4_row["Cost_of_products_sold"] = q4_cost
                q4_row["Net_sales"] = q4_sales
                q4_row["Tons_Shipped"] = q4_tons
                q4_row["Inventories_net"] = ann_row["Inventories_net"]
                q4_row["PeriodEndDate"] = f"{year}-12-31"
                
                processed_rows.append(q4_row)
                print(f"   -> Generated Q4 for {year} (Tons: {q4_tons:,.0f})")
            else:
                print(f"   ⚠️ Skipped Q4 for {year} (Missing Data)")

    return pd.DataFrame(processed_rows)

def main():
    print("--- Processing Nucor Financials ---")
    try:
        df = pd.read_csv(INPUT_FILE)
        
        # 1. Clean
        df["Tons_Shipped"] = df["Total_tons_shipped_text"].apply(extract_tons)
        cols_to_fix = ["Cost_of_products_sold", "Net_sales", "Inventories_net"]
        for col in cols_to_fix:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].apply(normalize_financials)
            
        # 2. Q4 Logic
        df_quarterly = calculate_q4_data(df)
        
        # 3. Dates + quarters
        df_quarterly["PeriodEndDate"] = pd.to_datetime(df_quarterly["PeriodEndDate"])
        df_quarterly["Quarter"] = df_quarterly["PeriodEndDate"].apply(get_fiscal_quarter)
        df_quarterly["Quarter_Label"] = "Q" + df_quarterly["Quarter"].astype(str)
        
        # 4. Metrics
        df_quarterly["Cost_Per_Ton"] = df_quarterly["Cost_of_products_sold"] / df_quarterly["Tons_Shipped"]
        df_quarterly["Gross_Margin_Pct"] = ((df_quarterly["Net_sales"] - df_quarterly["Cost_of_products_sold"]) / df_quarterly["Net_sales"]) * 100
        
        df_quarterly = df_quarterly.sort_values("PeriodEndDate")
        df_quarterly["Inventories_Previous"] = df_quarterly["Inventories_net"].shift(1)
        
        # Manual fix 2015 Q1
        mask_2015_q1 = df_quarterly["PeriodEndDate"] == "2015-04-04"
        if mask_2015_q1.any():
             df_quarterly.loc[mask_2015_q1, "Inventories_Previous"] = 2_745_032_000
        
        df_quarterly["Inventories_Previous"] = df_quarterly["Inventories_Previous"].fillna(df_quarterly["Inventories_net"])
        df_quarterly["Average_Inventory"] = (df_quarterly["Inventories_net"] + df_quarterly["Inventories_Previous"]) / 2
        df_quarterly["Inventory_Turnover"] = df_quarterly["Cost_of_products_sold"] / df_quarterly["Average_Inventory"]
        
        # Formatting
        df_quarterly["Net_sales_millions"] = df_quarterly["Net_sales"] / 1_000_000
        df_quarterly["COGS_millions"] = df_quarterly["Cost_of_products_sold"] / 1_000_000
        df_quarterly["Inventories_millions"] = df_quarterly["Inventories_net"] / 1_000_000
        df_quarterly["Tons_Shipped_thousands"] = df_quarterly["Tons_Shipped"] / 1_000

        # 5. Output
        df_final = df_quarterly.dropna(subset=["Cost_Per_Ton"])
        df_final = df_final[(df_final["Cost_Per_Ton"] > 300) & (df_final["Cost_Per_Ton"] < 5000)]
        
        if "Total_tons_shipped_text" in df_final.columns:
            df_final = df_final.drop(columns=["Total_tons_shipped_text"])
            
        cols_order = ["Year", "Quarter_Label", "PeriodEndDate", "ReportType", "Cost_Per_Ton", "Gross_Margin_Pct", "Inventory_Turnover", "Net_sales_millions", "COGS_millions", "Tons_Shipped_thousands"]
        final_cols = cols_order + [c for c in df_final.columns if c not in cols_order]
        df_final = df_final[final_cols]

        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df_final.to_csv(OUTPUT_FILE, index=False)
        
        print(f"✅ SUCCESS! Processed Metrics saved to: {OUTPUT_FILE}")
        print(f"Total Rows: {len(df_final)}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()