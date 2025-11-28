import pandas as pd
import os
import re

# adapted to notebook master_dataset_refining.ipynb
# --- CONFIGURATION ---
INPUT_FILE = "data/processed/master_dataset.csv"
OUTPUT_ANALYSIS = "data/processed/master_dataset_analysis.csv" 
OUTPUT_MODEL = "data/processed/master_dataset_modelling.csv"       

CUTOFF_DATE = "2025-12-31"

def get_x_num(col_name):
    """
    Helper to sort columns numerically (X1, X2... X10) instead of alphabetically (X1, X10, X2).
    """
    match = re.search(r'X(\d+)_', col_name)
    if match:
        return int(match.group(1))
    return 999 # Put non-numbered columns last

def main():
    print(f"--- Finalizing Dataset: {INPUT_FILE} ---")
    
    try:
        if not os.path.exists(INPUT_FILE):
             raise FileNotFoundError(f"Cannot find {INPUT_FILE}")
        
        df = pd.read_csv(INPUT_FILE)

        # 1. BASIC CLEANUP
        df["QuarterEnd"] = pd.to_datetime(df["QuarterEnd"])
        df = df.sort_values("QuarterEnd")
        df = df.drop_duplicates(subset=["QuarterEnd"], keep="last")

        # 2. TIME FILTER
        if CUTOFF_DATE:
            df = df[df["QuarterEnd"] <= CUTOFF_DATE]

        # 3. FILL MISSING VALUES
        print("Filling gaps...")
        cols_zero_fill = ["X6_Disaster_Cost_Sum", "X6_Disaster_Event_Count"]
        for col in cols_zero_fill:
            if col in df.columns: df[col] = df[col].fillna(0)

        if "Inventory_Turnover" in df.columns:
            df["Inventory_Turnover"] = df["Inventory_Turnover"].ffill().bfill()

        feature_cols = [c for c in df.columns if c.startswith("X") and c not in cols_zero_fill]
        for col in feature_cols:
            if df[col].isna().sum() > 0:
                df[col] = df[col].interpolate(method='linear').ffill().bfill()
        
        # 4. SAVE ANALYSIS VERSION (Full Data)
        cols = df.columns.tolist()
        if "Quarter_Label" in cols: cols.insert(0, cols.pop(cols.index("Quarter_Label")))
        if "Year" in cols: cols.insert(0, cols.pop(cols.index("Year")))
        
        df = df[cols]
        df.to_csv(OUTPUT_ANALYSIS, index=False)
        print(f"✅ Saved ANALYSIS dataset to: {OUTPUT_ANALYSIS}")

        # 5. CREATE & SAVE MODEL VERSION (Lean Data & REORDERED)
        # Find all X columns
        x_cols = [c for c in df.columns if c.startswith("X")]
        
        # --- REORDERING MAGIC ---
        # Sort them nicely: X1, X2, ... X10, X11...
        x_cols = sorted(x_cols, key=get_x_num)
        
        # Define exact order: Date -> Target -> Sorted Features
        target = "Y_Cost_Per_Ton"
        model_cols = [target, "QuarterEnd"] + x_cols
        
        # Filter valid columns only
        final_model_cols = [c for c in model_cols if c in df.columns]
        
        # Remove specific columns if needed (e.g. X6 count vs sum)
        if "X6_Disaster_Event_Count" in final_model_cols:
            final_model_cols.remove("X6_Disaster_Event_Count")

        # Create Final DataFrame
        df_model = df[final_model_cols].copy()
        
        df_model.to_csv(OUTPUT_MODEL, index=False)
        print(f"✅ Saved MODEL dataset to: {OUTPUT_MODEL}")
        print(f"   Columns Ordered: {df_model.columns.tolist()}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()