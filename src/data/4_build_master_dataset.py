import pandas as pd
import os

# --- CONFIGURATION ---
# Relative paths because this script is in src/data/
RAW_DIR = "data/raw"
INTERIM_DIR = "data/interim"
PROCESSED_DIR = "data/processed"

def main():
    print("--- Building Master Dataset ---")
    
    try:
        # 1. Load Nucor data
        nucor_path = os.path.join(INTERIM_DIR, "nucor_04_METRICS.csv")
        df_nucor = pd.read_csv(nucor_path)
        print(f"Loaded Nucor Data: {df_nucor.shape}")
        
        # --- DATE setup ---
        # Snap Nucor dates to Standard Calendar quarter end
        df_nucor["TempDate"] = pd.to_datetime(df_nucor["PeriodEndDate"])
        
        # Shift back 15 days (April 4 -> March 20) to catch the correct quarter
        df_nucor["TempDate"] = df_nucor["TempDate"] - pd.Timedelta(days=15)
        
        # Convert to Quarter End
        df_nucor["QuarterEnd"] = df_nucor["TempDate"].dt.to_period("Q").dt.to_timestamp("Q", how="end").dt.normalize()
        
        # Drop tempdate and quarter
        df_nucor = df_nucor.drop(columns=["TempDate", "Quarter"])


        # 2. Load External Features
        external_path = os.path.join(INTERIM_DIR, "external_features_quarterly.csv")
        df_external = pd.read_csv(external_path)
        print(f"Loaded External Data: {df_external.shape}")

        # Index Check
        if "QuarterEnd" not in df_external.columns:
            print("⚠️ 'QuarterEnd' not found in columns. Resetting index...")
            df_external.index.name = "QuarterEnd"
            df_external = df_external.reset_index()

        # --- DATE FIX FOR EXTERNAL ---
        df_external["QuarterEnd"] = pd.to_datetime(df_external["QuarterEnd"])
        df_external["QuarterEnd"] = df_external["QuarterEnd"].dt.to_period("Q").dt.to_timestamp("Q", how="end").dt.normalize()

        # 3. The merge
        print("Merging...")
        df_master = pd.merge(df_nucor, df_external, on="QuarterEnd", how="inner")
        
        # Rename target for consistency
        if "Cost_Per_Ton" in df_master.columns:
            df_master = df_master.rename(columns={"Cost_Per_Ton": "Y_Cost_Per_Ton"})

        # 4. Save
        output_path = os.path.join(PROCESSED_DIR, "master_dataset.csv")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df_master.to_csv(output_path, index=False)
        
        print(f"✅ SUCCESS! Full Master Dataset saved to: {output_path}")
        print(f"Final Shape: {df_master.shape}")
        print("Columns included:")
        print(df_master.columns.tolist())

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()