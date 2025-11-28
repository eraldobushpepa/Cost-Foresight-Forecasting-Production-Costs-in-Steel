import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# --- CONFIGURATION ---
REAL_FILE = "data/processed/master_dataset_model.csv"
SYNTHETIC_FILE = "data/processed/synthetic_dataset.csv"
OUTPUT_DIR = "reports/figures"
PREDICTIONS_DIR = "data/processed"
TARGET = "Y_Cost_Per_Ton"

# Hyperparameters
LAGS = [1]  # Forecasting (Lag 1)
TEST_SIZE = 8 # Last 2 years of REAL data for testing

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find {filepath}")
    df = pd.read_csv(filepath)
    if "QuarterEnd" in df.columns:
        df["QuarterEnd"] = pd.to_datetime(df["QuarterEnd"])
        df = df.sort_values("QuarterEnd").set_index("QuarterEnd")
    return df

def create_lagged_features(df, target, lags=[1]):
    df_lagged = df.copy()
    feature_cols = [c for c in df.columns]
    
    for col in feature_cols:
        for lag in lags:
            df_lagged[f"{col}_lag{lag}"] = df_lagged[col].shift(lag)
            
    drop_cols = [c for c in df.columns if c != target]
    df_lagged = df_lagged.drop(columns=drop_cols)
    
    return df_lagged.dropna()

def evaluate_model(name, model, X_train, y_train, X_test, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n📊 {name} Results (Tested on REAL Data):")
    print(f"   MAE:  ${mae:.2f}")
    print(f"   R²:   {r2:.3f}")
    
    return y_pred, r2

def main():
    print("--- Starting Augmented Regression Forecasting ---")
    
    # 1. Load Both Datasets
    df_real = load_data(REAL_FILE)
    df_synth = load_data(SYNTHETIC_FILE)
    
    print(f"Real Data: {df_real.shape}")
    print(f"Synthetic Data: {df_synth.shape}")

    # 2. Feature Engineering (Apply separately to avoid leakage)
    df_real_model = create_lagged_features(df_real, TARGET, lags=LAGS)
    df_synth_model = create_lagged_features(df_synth, TARGET, lags=LAGS)
    
    # 3. Split Real Data (Train vs Test)
    train_size = len(df_real_model) - TEST_SIZE
    
    real_train = df_real_model.iloc[:train_size]
    real_test  = df_real_model.iloc[train_size:]
    
    print(f"Real Train: {len(real_train)} | Real Test: {len(real_test)}")

    # 4. Augment Training Data (Real Train + All Synthetic)
    # We stack them together to create a massive training set
    augmented_train = pd.concat([real_train, df_synth_model])
    
    X_train = augmented_train.drop(columns=[TARGET])
    y_train = augmented_train[TARGET]
    
    X_test = real_test.drop(columns=[TARGET])
    y_test = real_test[TARGET]
    
    print(f"Augmented Training Set: {X_train.shape} rows")

    # 5. Define Models
    models = {
        "Linear Regression": Pipeline([('scaler', StandardScaler()), ('model', LinearRegression())]),
        "Ridge (Augmented)": Pipeline([('scaler', StandardScaler()), ('model', Ridge(alpha=10.0))]),
        "Lasso (Augmented)": Pipeline([('scaler', StandardScaler()), ('model', Lasso(alpha=5.0))])
    }
    
    # 6. Run & Compare
    plt.figure(figsize=(12, 6))
    plt.plot(y_test.index, y_test, label='Actual (Real)', color='black', linewidth=3, marker='o')
    
    for name, model in models.items():
        pred, r2 = evaluate_model(name, model, X_train, y_train, X_test, y_test)
        plt.plot(y_test.index, pred, label=f'{name} (R²={r2:.2f})', linestyle='--')

    plt.title(f"Augmented Forecasting: Trained on Real+Synthetic ({len(X_train)} rows), Tested on Real ({TEST_SIZE} Qs)")
    plt.ylabel("Cost Per Ton ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_path = os.path.join(OUTPUT_DIR, "regression_augmented_forecast.png")
    plt.savefig(save_path)
    print(f"\n✅ Augmented Plot saved to: {save_path}")

if __name__ == "__main__":
    main()