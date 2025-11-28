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
LAGS = [1]  # Standard Forecasting (Predict t using t-1)
TEST_SIZE = 8 # Last 2 years for testing

# Columns to Drop (Metadata & Leakage)
# Ensure we drop these so the model only sees Features + Lagged Target
DROP_COLS = [
    "Quarter_Label", "ReportType", "AccessionNumber", "PeriodEndDate", "QuarterEnd",
    "Cost_of_products_sold", "Net_sales", "Inventories_net", "Tons_Shipped", 
    "Gross_Margin_Pct", "Inventory_Turnover", "Inventories_millions", 
    "Net_sales_millions", "COGS_millions", "Tons_Shipped_thousands",
    "Inventories_Previous", "Average_Inventory", "Quarter"
]

def load_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cannot find {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Ensure Date is index
    if "QuarterEnd" in df.columns:
        df["QuarterEnd"] = pd.to_datetime(df["QuarterEnd"])
        df = df.sort_values("QuarterEnd").set_index("QuarterEnd")
        
    return df

def create_lagged_features(df, target, lags=[1]):
    """
    Creates lagged features for forecasting.
    """
    df_lagged = df.copy()
    
    # Use only numeric columns for features
    feature_cols = [c for c in df.columns if c not in DROP_COLS and c != target]
    
    for col in feature_cols:
        for lag in lags:
            df_lagged[f"{col}_lag{lag}"] = df_lagged[col].shift(lag)
            
    # Drop current features (t) to prevent leakage
    # We keep only Target(t) and Features(t-1)
    df_lagged = df_lagged.drop(columns=feature_cols)
    
    # Drop columns in DROP_COLS if they exist
    cols_to_remove = [c for c in DROP_COLS if c in df_lagged.columns]
    df_lagged = df_lagged.drop(columns=cols_to_remove)

    return df_lagged.dropna()

def evaluate_model(name, model, X_train, y_train, X_test, y_test):
    # Train
    model.fit(X_train, y_train)
    
    # Predict
    y_pred = model.predict(X_test)
    
    # Metrics
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    print(f"\n📊 {name} Results:")
    print(f"   MAE:  ${mae:.2f}")
    print(f"   RMSE: ${rmse:.2f}")
    print(f"   MAPE: {mape:.1f}%")
    print(f"   R²:   {r2:.3f}")
    
    return y_pred, r2

def main():
    print("--- Starting Regression Forecasting Pipeline ---")
    
    # 1. Load & Preprocess
    df = load_data(INPUT_FILE)
    df_model = create_lagged_features(df, TARGET, lags=LAGS)
    
    print(f"Modeling Data Shape: {df_model.shape}")
    
    # 2. Split Train/Test (Time Series Split)
    # We simulate a real forecast: Train on past, Test on recent future
    train_size = len(df_model) - TEST_SIZE
    
    X = df_model.drop(columns=[TARGET])
    y = df_model[TARGET]
    
    X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
    y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]
    
    print(f"Train Range: {X_train.index.min().date()} to {X_train.index.max().date()}")
    print(f"Test Range:  {X_test.index.min().date()} to {X_test.index.max().date()}")

    # 3. Define Models
    models = {
        "Linear Regression": Pipeline([('scaler', StandardScaler()), ('model', LinearRegression())]),
        "Ridge (L2)": Pipeline([('scaler', StandardScaler()), ('model', Ridge(alpha=10.0))]),
        "Lasso (L1)": Pipeline([('scaler', StandardScaler()), ('model', Lasso(alpha=5.0))])
    }
    
    # 4. Run & Compare
    results = pd.DataFrame(index=X_test.index)
    results['Actual'] = y_test
    
    plt.figure(figsize=(12, 6))
    plt.plot(y_test.index, y_test, label='Actual', color='black', linewidth=3, marker='o')
    
    for name, model in models.items():
        pred, r2 = evaluate_model(name, model, X_train, y_train, X_test, y_test)
        results[name] = pred
        plt.plot(y_test.index, pred, label=f'{name} (R²={r2:.2f})', linestyle='--')

    # 5. Visualization
    plt.title(f"Model Comparison: Forecasting Steel Production Cost (Horizon: {TEST_SIZE} Quarters)")
    plt.ylabel("Cost Per Ton ($)")
    plt.xlabel("Quarter")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_path = os.path.join(OUTPUT_DIR, "regression_forecast_comparison.png")
    plt.savefig(save_path)
    print(f"\n✅ Comparison Plot saved to: {save_path}")
    
    # 6. Save Predictions
    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    csv_path = os.path.join(PREDICTIONS_DIR, "regression_predictions.csv")
    results.to_csv(csv_path)
    print(f"✅ Predictions saved to: {csv_path}")

if __name__ == "__main__":
    main()