import pandas as pd
import os

# --- CONFIGURATION ---
RAW_DIR = "data/raw"
INTERIM_DIR = "data/interim"
PROCESSED_DIR = "data/processed"

def main():
    print("--- Building Master Dataset ---")
    
    try:
        # 1. Load Nucor Data
        nucor_path = os.path.join(INTERIM_DIR, "nucor_04_METRICS.csv")
        df_nucor = pd.read_csv(nucor_path)
        
        # Date Fix
        df_nucor["TempDate"] = pd.to_datetime(df_nucor["PeriodEndDate"])
        df_nucor["TempDate"] = df_nucor["TempDate"] - pd.Timedelta(days=15)
        df_nucor["QuarterEnd"] = df_nucor["TempDate"].dt.to_period("Q").dt.to_timestamp("Q", how="end").dt.normalize()
        df_nucor = df_nucor.drop(columns=["TempDate"])

        # 2. Load External Features
        external_path = os.path.join(INTERIM_DIR, "external_features_quarterly.csv")
        df_external = pd.read_csv(external_path)

        if "QuarterEnd" not in df_external.columns:
            df_external.index.name = "QuarterEnd"
            df_external = df_external.reset_index()

        df_external["QuarterEnd"] = pd.to_datetime(df_external["QuarterEnd"])
        df_external["QuarterEnd"] = df_external["QuarterEnd"].dt.to_period("Q").dt.to_timestamp("Q", how="end").dt.normalize()

        # 3. The Merge
        df_master = pd.merge(df_nucor, df_external, on="QuarterEnd", how="inner")
        
        # --- FINAL RENAMING FOR CONSISTENCY ---
        rename_map = {
            "Cost_Per_Ton": "Y_Cost_Per_Ton",
            "Inventory_Turnover": "X12_Inventory_Turnover"
        }
        df_master = df_master.rename(columns=rename_map)

        # 4. Save
        output_path = os.path.join(PROCESSED_DIR, "master_dataset_general.csv")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_master.to_csv(output_path, index=False)
        
        print(f"✅ SUCCESS! Full Master Dataset saved to: {output_path}")
        print("Columns included:")
        print(df_master.columns.tolist())

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    main()