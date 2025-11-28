import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# --- CONFIGURATION ---
INPUT_FILE = "data/processed/master_dataset_model.csv"
OUTPUT_DIR = "reports/figures"
PREDICTIONS_DIR = "data/processed"
TARGET = "Y_Cost_Per_Ton"

# Hyperparameters
LAGS = [1]  # Forecasting (Lag 1)
TEST_SIZE = 8 # Last 2 years for testing (2024-2025)

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
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    print(f"\n📊 {name} Results:")
    print(f"   MAE:  ${mae:.2f} | RMSE: ${rmse:.2f} | MAPE: {mape:.1f}% | R²: {r2:.3f}")
    return y_pred, r2

def main():
    print("--- Standard Forecasting Pipeline ---")
    df = load_data(INPUT_FILE)
    df_model = create_lagged_features(df, TARGET, lags=LAGS)
    
    train_size = len(df_model) - TEST_SIZE
    X = df_model.drop(columns=[TARGET])
    y = df_model[TARGET]
    
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
    
    print(f"Train: {X_train.index.min().date()} - {X_train.index.max().date()}")
    print(f"Test:  {X_test.index.min().date()} - {X_test.index.max().date()}")

    models = {
        "Linear Regression": Pipeline([('scaler', StandardScaler()), ('model', LinearRegression())]),
        "Ridge (L2)": Pipeline([('scaler', StandardScaler()), ('model', Ridge(alpha=10.0))]),
        "Lasso (L1)": Pipeline([('scaler', StandardScaler()), ('model', Lasso(alpha=5.0))])
    }
    
    results = pd.DataFrame(index=X_test.index)
    results['Actual'] = y_test
    
    plt.figure(figsize=(12, 6))
    plt.plot(y_test.index, y_test, label='Actual', color='black', linewidth=3, marker='o')
    
    for name, model in models.items():
        pred, r2 = evaluate_model(name, model, X_train, y_train, X_test, y_test)
        results[name] = pred
        plt.plot(y_test.index, pred, label=f'{name} (R²={r2:.2f})', linestyle='--')

    plt.title(f"Forecast (Standard): 2024-2025 Prediction")
    plt.legend()
    plt.grid(True, alpha=0.3)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(os.path.join(OUTPUT_DIR, "regression_forecast_standard.png"))
    print("✅ Done.")

if __name__ == "__main__":
    main()