import pandas as pd
import numpy as np
import os
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.metadata import SingleTableMetadata

# adapted to notebook synthetic_data.ipynb
# --- CONFIGURATION ---
INPUT_FILE = "data/processed/master_dataset_model.csv" # Use the model-ready file
OUTPUT_FILE = "data/processed/synthetic_dataset.csv"
N_SAMPLES = 200 # How many synthetic quarters to generate (e.g. 50 years of data)
LAG_MAX = 4     # Generate lags up to 1 year

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure QuarterEnd is datetime
    if "QuarterEnd" in df.columns:
        df["QuarterEnd"] = pd.to_datetime(df["QuarterEnd"])
        
    return df

def generate_synthetic_data(df, n_samples):
    print(f"--- Learning Data Patterns from {len(df)} rows ---")
    
    # 1. Setup Metadata
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df)
    
    # Update QuarterEnd to be treated as a datetime context, or drop it for synthesis
    # SDV handles datetimes well, but for pure correlation learning, sometimes dropping date is safer
    # Let's keep it to see if it learns the trend.
    
    # 2. Train Synthesizer
    # GaussianCopula is great for capturing correlations between numerical columns
    synthesizer = GaussianCopulaSynthesizer(metadata)
    synthesizer.fit(df)
    
    # 3. Generate
    print(f"--- Generating {n_samples} synthetic rows ---")
    synthetic_data = synthesizer.sample(num_rows=n_samples)
    
    # 4. Post-Process (Sort by generated date)
    if "QuarterEnd" in synthetic_data.columns:
        synthetic_data = synthetic_data.sort_values("QuarterEnd").reset_index(drop=True)
        
    return synthetic_data

def main():
    print("--- Starting Synthetic Data Generation ---")
    
    try:
        # 1. Load Real Data
        df_real = load_data(INPUT_FILE)
        
        # 2. Generate Synthetic Data
        # We drop 'QuarterEnd' before training because we want to generate random scenarios,
        # not necessarily tied to specific historical dates.
        # However, if you want a time-series extension, you handle dates differently.
        # For this simple version, let's drop Date and just learn the math relationships.
        
        df_for_training = df_real.drop(columns=["QuarterEnd"])
        
        df_synthetic = generate_synthetic_data(df_for_training, N_SAMPLES)
        
        # 3. Add Fake Dates (Future)
        last_date = df_real["QuarterEnd"].max()
        future_dates = pd.date_range(start=last_date, periods=N_SAMPLES + 1, freq='QE')[1:]
        df_synthetic["QuarterEnd"] = future_dates
        
        # --- REORDER COLUMNS (Target First, Date Second) ---
        cols = df_synthetic.columns.tolist()
        
        # Move Target to front
        if "Y_Cost_Per_Ton" in cols:
            cols.insert(0, cols.pop(cols.index("Y_Cost_Per_Ton")))
            
        # Move Date to second position
        if "QuarterEnd" in cols:
            cols.insert(1, cols.pop(cols.index("QuarterEnd")))
            
        df_synthetic = df_synthetic[cols]

        # 4. Save
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        df_synthetic.to_csv(OUTPUT_FILE, index=False)
        
        print(f"✅ SUCCESS! Generated {len(df_synthetic)} rows.")
        print(f"   Saved to: {OUTPUT_FILE}")
        print(df_synthetic.head())

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()