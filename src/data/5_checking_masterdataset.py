import pandas as pd
import numpy as np
import os

# --- CONFIGURATION ---
# reaad file
FILE_PATH = "data/processed/master_dataset.csv"

def main():
    print(f"--- 🔍 EDA & QUALITY CHECK REPORT: {os.path.basename(FILE_PATH)} ---")
    
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: File not found at {FILE_PATH}")
        return

    df = pd.read_csv(FILE_PATH)
    
    # --- 1. BASIC STRUCTURE ---
    print("\n" + "="*40)
    print("1. DATASET SHAPE & TYPES")
    print("="*40)
    print(f"Rows: {df.shape[0]}")
    print(f"Cols: {df.shape[1]}")
    print("\nColumn Types:")
    print(df.dtypes)

    # --- 2. MISSING VALUES DRILL-DOWN ---
    print("\n" + "="*40)
    print("2. MISSING VALUES ANALYSIS")
    print("="*40)
    
    missing_by_col = df.isna().sum()
    if missing_by_col.sum() == 0:
        print("✅ No missing values found in any column.")
    else:
        print("⚠️ Columns with NaNs:")
        print(missing_by_col[missing_by_col > 0])
        
        print("\n⚠️ Rows with at least ONE missing value:")
        # Calculate missing count per row
        df['nan_count'] = df.isna().sum(axis=1)
        bad_rows = df[df['nan_count'] > 0]
        
        # Show the date, the missing count, and columns that are NaN
        print(bad_rows[['QuarterEnd', 'nan_count']].to_string())
        print(f"\nTotal rows with missing data: {len(bad_rows)}")

    # --- 3. DESCRIPTIVE STATISTICS ---
    print("\n" + "="*40)
    print("3. DESCRIPTIVE STATISTICS (Numerical)")
    print("="*40)
    # Transpose for readability
    desc = df.describe().T
    # Add a "spread" metric (Max - Min)
    desc['Spread'] = desc['max'] - desc['min']
    print(desc[['mean', 'min', '50%', 'max', 'std']].to_string())

    # --- 4. OUTLIER DETECTION (business logic) ---
    print("\n" + "="*40)
    print("4. LOGICAL OUTLIER CHECK")
    print("="*40)
    
    # CHECK A: Cost Per Ton Limits
    # Steel shouldn't be < $300 or > $3000 per ton
    if 'Y_Cost_Per_Ton' in df.columns:
        outliers_cost = df[(df['Y_Cost_Per_Ton'] < 300) | (df['Y_Cost_Per_Ton'] > 3000)]
        if not outliers_cost.empty:
            print(f"\n⚠️ SUSPICIOUS COST PER TON (Count: {len(outliers_cost)}):")
            print(outliers_cost[['QuarterEnd', 'Y_Cost_Per_Ton']].to_string())
        else:
            print("✅ Cost Per Ton looks realistic (300 < x < 3000).")

    # CHECK B: Inventory turnover limits
    # Turnover implies speed. 0 is impossible. > 20 is unlikely for steel.
    if 'Inventory_Turnover' in df.columns:
        outliers_inv = df[(df['Inventory_Turnover'] < 0.5) | (df['Inventory_Turnover'] > 20)]
        if not outliers_inv.empty:
            print(f"\n⚠️ SUSPICIOUS INVENTORY TURNOVER (Count: {len(outliers_inv)}):")
            print(outliers_inv[['QuarterEnd', 'Inventory_Turnover']].to_string())
        else:
            print("✅ Inventory Turnover looks realistic (0.5 < x < 20).")

    # CHECK C: Zero values in prices
    # No market price should be exactly 0
    price_cols = [c for c in df.columns if 'Price' in c]
    for col in price_cols:
        zeros = df[df[col] == 0]
        if not zeros.empty:
             print(f"⚠️ Found ZEROs in {col} (Count: {len(zeros)}) - Check your source!")
    
    # --- 5. TIME CONTINUITY CHECK ---
    print("\n" + "="*40)
    print("5. TIME SERIES CONTINUITY")
    print("="*40)
    if 'QuarterEnd' in df.columns:
        df['QuarterEnd'] = pd.to_datetime(df['QuarterEnd'])
        df = df.sort_values('QuarterEnd')
        
        # Calculate difference between dates
        df['Time_Diff'] = df['QuarterEnd'].diff()
        
        # We expect approx 90-92 days
        gaps = df[df['Time_Diff'].dt.days > 100]
        if not gaps.empty:
            print("\n⚠️ Found Large Time Gaps (Missing Quarters?):")
            print(gaps[['QuarterEnd', 'Time_Diff']].to_string())
        else:
            print("✅ Time series looks continuous (approx 3 months between rows).")
            
        print(f"\nStart Date: {df['QuarterEnd'].min().date()}")
        print(f"End Date:   {df['QuarterEnd'].max().date()}")

if __name__ == "__main__":
    main()