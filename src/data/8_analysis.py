import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
INPUT_FILE = "data/processed/master_dataset_analysis.csv"
OUTPUT_DIR = "reports/figures"

def main():
    print(f"--- Generating Visual Analysis from {INPUT_FILE} ---")
    
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: File not found at {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)
    df["QuarterEnd"] = pd.to_datetime(df["QuarterEnd"])
    df = df.sort_values("QuarterEnd")
    
    # Auto-detect date range for titles
    start_year = df["QuarterEnd"].dt.year.min()
    end_year = df["QuarterEnd"].dt.year.max()
    date_range_str = f"{start_year}-{end_year}"
    
    print(f"📅 Data Range Detected: {date_range_str}")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- CHART 1: Cost Distribution (No KDE, with Mean) ---
    print("Generating Cost Distribution Chart...")
    plt.figure(figsize=(10, 6))
    
    # Histogram (No KDE)
    sns.histplot(df["Y_Cost_Per_Ton"], kde=False, bins=15, color="green", edgecolor="black", label="Frequency")
    
    # Add Mean Line
    mean_cost = df["Y_Cost_Per_Ton"].mean()
    plt.axvline(mean_cost, color='red', linestyle='dashed', linewidth=2, label=f'Mean Cost: ${mean_cost:.0f}')
    
    plt.title(f"Distribution of Nucor Production Cost ({date_range_str})", fontsize=14)
    plt.xlabel("Cost Per Ton ($)", fontsize=12)
    plt.ylabel("Quarterly Frequency", fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.legend() # Shows the labels
    
    save_path_dist = os.path.join(OUTPUT_DIR, "cost_distribution.png")
    plt.savefig(save_path_dist)
    print(f"✅ Saved: {save_path_dist}")
    plt.close()

    # --- CHART 2: The Driver (Time Series) ---
    print("Generating Time Series Driver Chart...")
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    dates = df["QuarterEnd"]
    
    # Plot Target (Cost Per Ton) on Left Axis
    color = 'tab:red'
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Nucor Cost Per Ton ($)', color=color, fontsize=12, fontweight='bold')
    ax1.plot(dates, df["Y_Cost_Per_Ton"], color=color, linewidth=3, label='Nucor Cost ($/Ton)')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    
    # Plot Scrap Price on Right Axis
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Market Scrap Price ($/Ton)', color=color, fontsize=12, fontweight='bold')
    ax2.plot(dates, df["X1_Scrap_Price"], color=color, linestyle='--', linewidth=2, label='Market Scrap Price ($/Ton)')
    ax2.tick_params(axis='y', labelcolor=color)
    
    # Add vertical lines for years
    for year in df["QuarterEnd"].dt.year.unique():
        ax1.axvline(pd.Timestamp(f"{year}-01-01"), color='gray', linestyle=':', alpha=0.3)

    # Unified Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=True, facecolor='white', framealpha=0.9)

    plt.title(f"Scrap Price vs. Production Cost ({date_range_str})", fontsize=16)
    fig.tight_layout()
    
    save_path_ts = os.path.join(OUTPUT_DIR, "timeseries_scrap_vs_cost.png")
    plt.savefig(save_path_ts)
    print(f"✅ Saved: {save_path_ts}")
    plt.close()
    
    print("\n🚀 Visual Analysis Complete!")

if __name__ == "__main__":
    main()