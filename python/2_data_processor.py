import pandas as pd
import re
import numpy as np

# --- ================================== ---
# --- PART 1: QUARTER INFERENCE LOGIC ---
# --- ================================== ---

def infer_quarter_from_dates(row):
    """
    Infers the quarter based on PeriodEndDate when Quarter is missing.
    
    Logic:
    - Q1 ends in March/April (fiscal Q1)
    - Q2 ends in June/July (fiscal Q2)
    - Q3 ends in September/October (fiscal Q3)
    - Q4 ends in December/January (fiscal Q4)
    """
    if pd.notna(row['Quarter']):
        return row['Quarter']  # Already has a quarter, don't change
    
    try:
        period_end = pd.to_datetime(row['PeriodEndDate'])
        month = period_end.month
        
        # Nucor's fiscal quarters based on your data:
        if month in [3, 4]:  # March-April
            return 'Q1'
        elif month in [6, 7]:  # June-July
            return 'Q2'
        elif month in [9, 10]:  # September-October
            return 'Q3'
        elif month in [12, 1]:  # December-January
            return 'Q4'
        else:
            return None
            
    except Exception as e:
        return None


# --- ================================== ---
# --- PART 2: COST SCALING ---
# --- ================================== ---

def scale_financial_value(value):
    """
    Scales financial values if they're not already scaled.
    
    iXBRL (new files) returns full number (e.g., 7,233,000,000).
    HTML (old files) returns unscaled number (e.g., 5,102,283 in thousands).
    """
    if pd.isna(value):
        return np.nan
        
    try:
        value_float = float(value)
    except ValueError:
        return np.nan

    # If the number is less than 100 million, it's "in thousands"
    if value_float < 100_000_000:
        return value_float * 1000
        
    return value_float


# --- ================================== ---
# --- PART 3: TONS EXTRACTION ---
# --- ================================== ---

def extract_tons_number(text):
    """Extracts the first multi-million number from text."""
    if not isinstance(text, str):
        return np.nan
    match = re.search(r'([\d,]{7,})', text) 
    if match:
        tons_str = match.group(1).replace(',', '')
        if len(tons_str) > 5:
            try:
                return int(tons_str)
            except ValueError:
                return np.nan
    return np.nan


def extract_tons_pct(text):
    """
    Extracts percentage change from text.
    Handles "increase", "decrease", and "flat".
    """
    if not isinstance(text, str):
        return np.nan
    
    # Check for "flat"
    if re.search(r'\bflat\b|flat with', text, re.IGNORECASE):
        return 0.0

    # Pattern 1: "13% increase/decrease"
    match = re.search(r'(\d+)%\s+(increase|decrease)', text, re.IGNORECASE)
    if match:
        try:
            pct_val = float(match.group(1)) / 100.0
            if match.group(2).lower() == 'decrease':
                pct_val = -pct_val
            return pct_val
        except Exception:
            return np.nan
    
    # Pattern 2: "increased/decreased 13%"
    match = re.search(r'(increase|decrease)d\s+(\d+)%', text, re.IGNORECASE)
    if match:
        try:
            pct_val = float(match.group(2)) / 100.0
            if match.group(1).lower() == 'decrease':
                pct_val = -pct_val
            return pct_val
        except Exception:
            return np.nan
            
    return np.nan


# --- ================================== ---
# --- PART 4: VALIDATION LOGIC ---
# --- ================================== ---

def validate_financial_data(df):
    """
    Validates financial data for consistency.
    Prints warnings but doesn't remove rows.
    """
    print("\n" + "="*70)
    print("🔍 VALIDATING FINANCIAL DATA")
    print("="*70)
    
    warnings = []
    
    for idx, row in df.iterrows():
        year = row['Year']
        quarter = row['Quarter']
        net_sales = row['Net_sales_millions']
        cogs = row['COGS_millions']
        inventories = row['Inventories_millions']
        
        # Check 1: Net Sales > COGS
        if pd.notna(net_sales) and pd.notna(cogs):
            if net_sales <= cogs:
                warnings.append(f"⚠️  {year} {quarter}: Net Sales (${net_sales:.0f}M) <= COGS (${cogs:.0f}M)")
        
        # Check 2: Gross margin should be reasonable (10-40% typical for steel)
        if pd.notna(net_sales) and pd.notna(cogs) and net_sales > 0:
            gross_margin = (net_sales - cogs) / net_sales * 100
            if gross_margin < 5 or gross_margin > 50:
                warnings.append(f"⚠️  {year} {quarter}: Unusual gross margin: {gross_margin:.1f}%")
        
        # Check 3: Inventory turnover (quarterly COGS / inventory)
        if pd.notna(cogs) and pd.notna(inventories) and inventories > 0:
            turnover = cogs / inventories
            if turnover < 0.5 or turnover > 3.0:
                warnings.append(f"⚠️  {year} {quarter}: Unusual inventory turnover: {turnover:.2f}x")
    
    if warnings:
        print("\n⚠️  Found potential data quality issues:")
        for warning in warnings[:10]:  # Show first 10
            print(f"    {warning}")
        if len(warnings) > 10:
            print(f"    ... and {len(warnings) - 10} more warnings")
    else:
        print("\n✅ All validation checks passed!")
    
    return warnings


# --- ================================== ---
# --- MAIN PROCESSOR ---
# --- ================================== ---

def main_processor():
    
    print("="*70)
    print("--- Starting Enhanced Data Processing (v3) ---")
    print("    Output: 3 separate files (IS, BS, Metrics)")
    print("="*70)
    
    # --- STEP 1: Load raw data ---
    try:
        df = pd.read_csv("nucor_01_RAW_EXTRACT.csv")
        print(f"\n✅ Loaded 'nucor_01_RAW_EXTRACT.csv' ({len(df)} rows)")
    except FileNotFoundError:
        print("\n❌ ERROR: 'nucor_01_RAW_EXTRACT.csv' not found.")
        print("Please run '1_data_extractor_v2.py' first.")
        return

    # --- STEP 2: Infer missing quarters ---
    print("\n" + "="*70)
    print("📅 INFERRING MISSING QUARTERS")
    print("="*70)
    
    missing_quarters_before = df['Quarter'].isna().sum()
    print(f"Missing quarters before inference: {missing_quarters_before}")
    
    if missing_quarters_before > 0:
        print("\nRows with missing quarters:")
        missing_df = df[df['Quarter'].isna()][['Year', 'PeriodEndDate', 'FilingDate', 'Quarter']]
        print(missing_df.to_string(index=False))
        
        df['Quarter_Original'] = df['Quarter']  # Keep original for reference
        df['Quarter'] = df.apply(infer_quarter_from_dates, axis=1)
        
        missing_quarters_after = df['Quarter'].isna().sum()
        inferred_count = missing_quarters_before - missing_quarters_after
        
        if inferred_count > 0:
            print(f"\n✅ Successfully inferred {inferred_count} quarters!")
            print("\nInferred quarters:")
            inferred_df = df[df['Quarter_Original'].isna() & df['Quarter'].notna()][
                ['Year', 'Quarter', 'PeriodEndDate', 'FilingDate']
            ]
            print(inferred_df.to_string(index=False))
        
        if missing_quarters_after > 0:
            print(f"\n⚠️  Still have {missing_quarters_after} missing quarters that couldn't be inferred")
    else:
        print("✅ No missing quarters found!")

    # --- STEP 3: Scale financial values ---
    print("\n" + "="*70)
    print("💰 SCALING FINANCIAL VALUES")
    print("="*70)
    
    df['Cost_of_products_sold_SCALED'] = df['Cost_of_products_sold'].apply(scale_financial_value)
    df['Net_sales_SCALED'] = df['Net_sales'].apply(scale_financial_value)
    df['Inventories_SCALED'] = df['Inventories_net'].apply(scale_financial_value)
    
    # Convert to millions for readability
    df['COGS_millions'] = df['Cost_of_products_sold_SCALED'] / 1_000_000
    df['Net_sales_millions'] = df['Net_sales_SCALED'] / 1_000_000
    df['Inventories_millions'] = df['Inventories_SCALED'] / 1_000_000
    
    print("✅ Financial values scaled to millions")

    # --- STEP 4: Extract tons data ---
    print("\n" + "="*70)
    print("🏭 EXTRACTING TONS DATA")
    print("="*70)
    
    df['Tons_Shipped'] = df['Total_tons_shipped_text'].apply(extract_tons_number)
    df['Tons_Pct_Change_Decimal'] = df['Total_tons_shipped_text'].apply(extract_tons_pct)
    
    tons_found = df['Tons_Shipped'].notna().sum()
    pct_found = df['Tons_Pct_Change_Decimal'].notna().sum()
    print(f"✅ Extracted tons for {tons_found}/{len(df)} rows")
    print(f"✅ Extracted % change for {pct_found}/{len(df)} rows")

    # --- STEP 5: Impute missing percentage changes ---
    print("\n" + "="*70)
    print("📊 IMPUTING MISSING PERCENTAGE CHANGES")
    print("="*70)
    
    # Sort by date for year-over-year calculation
    df = df.sort_values(by='PeriodEndDate', ascending=True)
    
    # Calculate YoY % change by quarter
    df['Calculated_Pct_Change_YoY_Decimal'] = (
        df.groupby('Quarter')['Tons_Shipped'].pct_change(periods=1)
    )
    
    original_missing = df['Tons_Pct_Change_Decimal'].isna().sum()
    
    # Fill missing values
    df['Tons_Pct_Change_Decimal'] = df['Tons_Pct_Change_Decimal'].fillna(
        df['Calculated_Pct_Change_YoY_Decimal']
    )
    
    new_missing = df['Tons_Pct_Change_Decimal'].isna().sum()
    imputed = original_missing - new_missing
    
    if imputed > 0:
        print(f"✅ Imputed {imputed} missing % change values using YoY calculation")
    else:
        print("✅ No missing % change values needed imputation")

    # Convert to whole number percentage
    df['Tons_Pct_Change'] = (
        pd.to_numeric(df['Tons_Pct_Change_Decimal'], errors='coerce') * 100
    ).round(0)

    # --- STEP 6: Validate financial data ---
    validation_warnings = validate_financial_data(df)

    # --- STEP 7: Drop rows with missing critical data ---
    print("\n" + "="*70)
    print("🧹 CLEANING DATA")
    print("="*70)
    
    critical_cols = ['Tons_Shipped', 'COGS_millions', 'Quarter']
    missing_rows_mask = df[critical_cols].isna().any(axis=1)
    rows_to_drop = df[missing_rows_mask]

    if not rows_to_drop.empty:
        print(f"\n⚠️  Dropping {len(rows_to_drop)} row(s) with missing critical data:")
        print(rows_to_drop[['Year', 'Quarter', 'PeriodEndDate']].to_string(index=False))
        df_cleaned = df.dropna(subset=critical_cols)
    else:
        print("\n✅ No rows with missing critical data")
        df_cleaned = df

    # Sort by date (newest first)
    df_cleaned = df_cleaned.sort_values(by='PeriodEndDate', ascending=False)

    # --- STEP 8: Create Income Statement File ---
    print("\n" + "="*70)
    print("📄 CREATING FILE 1: INCOME STATEMENT")
    print("="*70)
    
    income_statement = df_cleaned[[
        'AccessionNumber',
        'PeriodEndDate',
        'FilingDate',
        'Year',
        'Quarter',
        'Net_sales_millions',
        'COGS_millions',
        'Tons_Shipped',
        'Tons_Pct_Change'
    ]].copy()
    
    income_statement_file = "nucor_02_INCOME_STATEMENT.csv"
    income_statement.to_csv(income_statement_file, index=False, encoding='utf-8')
    print(f"✅ Created: {income_statement_file}")
    print(f"   Rows: {len(income_statement)}")
    print(f"   Columns: {', '.join(income_statement.columns)}")

    # --- STEP 9: Create Balance Sheet File ---
    print("\n" + "="*70)
    print("📄 CREATING FILE 2: BALANCE SHEET")
    print("="*70)
    
    balance_sheet = df_cleaned[[
        'AccessionNumber',
        'PeriodEndDate',
        'FilingDate',
        'Year',
        'Quarter',
        'Inventories_millions'
    ]].copy()
    
    balance_sheet_file = "nucor_03_BALANCE_SHEET.csv"
    balance_sheet.to_csv(balance_sheet_file, index=False, encoding='utf-8')
    print(f"✅ Created: {balance_sheet_file}")
    print(f"   Rows: {len(balance_sheet)}")
    print(f"   Columns: {', '.join(balance_sheet.columns)}")

    # --- STEP 10: Create Metrics File ---
    print("\n" + "="*70)
    print("📄 CREATING FILE 3: METRICS (with X13 and Y)")
    print("="*70)
    
    metrics = df_cleaned[[
        'Year',
        'Quarter',
        'PeriodEndDate',
        'Net_sales_millions',
        'COGS_millions',
        'Tons_Shipped',
        'Inventories_millions'
    ]].copy()
    
    # Calculate Cost_Per_Ton (Y - Target Variable)
    metrics['Cost_Per_Ton'] = metrics['COGS_millions'] * 1_000_000 / metrics['Tons_Shipped']
    
    # Calculate Gross Margin %
    metrics['Gross_Margin_Pct'] = (
        (metrics['Net_sales_millions'] - metrics['COGS_millions']) / 
        metrics['Net_sales_millions'] * 100
    ).round(2)
    
    # Calculate Average Inventory (current + previous) / 2
    metrics = metrics.sort_values(by='PeriodEndDate', ascending=True)
    metrics['Inventories_Previous'] = metrics.groupby('Quarter')['Inventories_millions'].shift(1)
    metrics['Average_Inventory'] = (
        (metrics['Inventories_millions'] + metrics['Inventories_Previous']) / 2
    )
    
    # Calculate Inventory Turnover (X13 - Feature for Model)
    metrics['Inventory_Turnover'] = (
        metrics['COGS_millions'] / metrics['Average_Inventory']
    ).round(4)
    
    # Calculate Days Inventory Outstanding
    metrics['Days_Inventory_Outstanding'] = (
        (metrics['Average_Inventory'] / metrics['COGS_millions']) * 90
    ).round(1)
    
    # Sort back to newest first
    metrics = metrics.sort_values(by='PeriodEndDate', ascending=False)
    
    # Select final columns for metrics file
    metrics_final = metrics[[
        'Year',
        'Quarter',
        'PeriodEndDate',
        'Cost_Per_Ton',
        'Gross_Margin_Pct',
        'Inventories_millions',
        'Inventories_Previous',
        'Average_Inventory',
        'Inventory_Turnover',
        'Days_Inventory_Outstanding'
    ]]
    
    metrics_file = "nucor_04_METRICS.csv"
    metrics_final.to_csv(metrics_file, index=False, encoding='utf-8')
    print(f"✅ Created: {metrics_file}")
    print(f"   Rows: {len(metrics_final)}")
    print(f"   Key columns: Cost_Per_Ton (Y), Inventory_Turnover (X13)")

    # --- STEP 11: Final Summary ---
    print("\n" + "="*70)
    print("✅ SUCCESS! ALL FILES CREATED")
    print("="*70)
    
    print("\n📊 SUMMARY:")
    print(f"   File 1: {income_statement_file}")
    print(f"           → Income Statement data (quarterly flows)")
    print(f"           → {len(income_statement)} rows")
    print(f"\n   File 2: {balance_sheet_file}")
    print(f"           → Balance Sheet data (snapshots)")
    print(f"           → {len(balance_sheet)} rows")
    print(f"\n   File 3: {metrics_file}")
    print(f"           → Y = Cost_Per_Ton (target variable)")
    print(f"           → X13 = Inventory_Turnover (feature)")
    print(f"           → {len(metrics_final)} rows")
    
    print("\n📈 METRICS PREVIEW:")
    print(metrics_final[['Year', 'Quarter', 'Cost_Per_Ton', 'Inventory_Turnover', 'Gross_Margin_Pct']].head(10).to_string(index=False))
    
    return income_statement, balance_sheet, metrics_final


# --- Run the processor ---
if __name__ == "__main__":
    is_df, bs_df, metrics_df = main_processor()