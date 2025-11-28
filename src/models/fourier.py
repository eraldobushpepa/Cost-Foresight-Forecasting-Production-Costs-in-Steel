import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score

# --- CONFIGURATION ---
INPUT_FILE = "data/processed/master_dataset_model.csv"
OUTPUT_IMG = "reports/figures/fourier_forecast.png"
TARGET = "Y_Cost_Per_Ton"

# FIX: Stop looking at data after 2024 so we can "Forecast" 2025
TRAIN_CUTOFF = "2025-12-31" 

CYCLE_PERIOD = 12 # 3-year market cycle
FUTURE_STEPS = 4  # Forecast 4 quarters (2025)

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find {filepath}")
    df = pd.read_csv(filepath)
    df["QuarterEnd"] = pd.to_datetime(df["QuarterEnd"])
    df = df.sort_values("QuarterEnd").set_index("QuarterEnd")
    
    # APPLY CUTOFF
    df = df[df.index <= TRAIN_CUTOFF]
    print(f"✅ Loaded Data (Cutoff {TRAIN_CUTOFF}): {df.shape}")
    return df

def add_fourier_features(df, period=12, k=2):
    df_fourier = df.copy()
    t = np.arange(len(df))
    for i in range(1, k + 1):
        df_fourier[f'sin_{i}'] = np.sin(2 * np.pi * i * t / period)
        df_fourier[f'cos_{i}'] = np.cos(2 * np.pi * i * t / period)
    return df_fourier

def create_lagged_features(df, target, lags=[1]):
    df_final = df.copy()
    df_final[f"{target}_lag1"] = df_final[target].shift(1)
    
    # Keep only numeric columns
    numeric_cols = [c for c in df_final.columns if df_final[c].dtype in ['float64', 'int64']]
    df_final = df_final[numeric_cols]
    return df_final.dropna()

def train_predict_future(df, target, steps=4):
    X = df.drop(columns=[target])
    y = df[target]
    
    model = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('regressor', Ridge(alpha=1.0))
    ])
    model.fit(X, y)
    
    # Predict Future
    last_row = X.iloc[[-1]].copy()
    predictions = []
    current_lag_val = y.iloc[-1]
    
    # For Fourier features, we need to extend time 't'
    # We estimate 't' continues incrementing
    # (This is a simplified assumption for the demo)
    
    for i in range(steps):
        # Update Lag
        if f"{target}_lag1" in last_row.columns:
            last_row[f"{target}_lag1"] = current_lag_val
            
        pred = model.predict(last_row)[0]
        predictions.append(pred)
        current_lag_val = pred
        
    return predictions

def main():
    print("--- Starting Fourier Forecasting ---")
    
    # 1. Load (With Cutoff)
    df = load_data(INPUT_FILE)
    
    # 2. Feature Engineering
    df_fourier = add_fourier_features(df, period=CYCLE_PERIOD)
    df_model = create_lagged_features(df_fourier, TARGET, lags=[0])
    
    # 3. Validate
    X = df_model.drop(columns=[TARGET])
    y = df_model[TARGET]
    tscv = TimeSeriesSplit(n_splits=5)
    model = Pipeline([('scaler', StandardScaler()), ('regressor', Ridge())])
    
    r2_scores = []
    for train_idx, test_idx in tscv.split(X):
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        score = model.score(X.iloc[test_idx], y.iloc[test_idx])
        r2_scores.append(score)
    print(f"Average R² (Validation): {np.mean(r2_scores):.2f}")
    
    # 4. Forecast 2025
    future_preds = train_predict_future(df_model, TARGET, steps=FUTURE_STEPS)
    
    # 5. Plot
    plt.figure(figsize=(12, 6))
    
    # History
    plt.plot(df.index, df[TARGET], label='Historical Cost (2015-2024)', color='black', linewidth=2)
    
    # Forecast
    last_date = df.index[-1]
    future_dates = pd.date_range(start=last_date, periods=FUTURE_STEPS + 1, freq='QE')[1:]
    
    plt.plot(future_dates, future_preds, label='Fourier Forecast (2025)', color='green', linestyle='--', marker='o')
    
    plt.title(f"Fourier Cycle Forecasting (Validation R²: {np.mean(r2_scores):.2f})")
    plt.xlabel("Year")
    plt.ylabel("Cost Per Ton ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs(os.path.dirname(OUTPUT_IMG), exist_ok=True)
    plt.savefig(OUTPUT_IMG)
    print(f"✅ Forecast Plot saved to {OUTPUT_IMG}")

if __name__ == "__main__":
    main()