import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from io import StringIO

# --- Configuration ---
CIK = "0000073309" 
HEADERS = {'User-Agent': 'Eraldo Rossi eraldo@example.com'}

# --- ======================================================= ---
# --- PART 1: GENERIC iXBRL EXTRACTOR (Refactored) ---
# --- ======================================================= ---

def get_value_from_ixbrl(soup, tag_name):
    """
    Generic function to extract any iXBRL tag value.
    Returns the scaled value or None if not found.
    
    Args:
        soup: BeautifulSoup object
        tag_name: The XBRL tag name (e.g., 'us-gaap:CostOfGoodsAndServicesSold')
    """
    try:
        tag = soup.find('ix:nonfraction', {'name': tag_name})
        if not tag:
            return None
        
        value_str = tag.get_text(strip=True).replace(',', '')
        scale_str = tag.get('scale')
        
        if not value_str or not scale_str:
            return None
        
        final_value = int(float(value_str)) * (10 ** int(scale_str))
        return final_value
    except Exception as e:
        return None


# --- ======================================================= ---
# --- PART 2: HTML TABLE FALLBACK PARSERS ---
# --- ======================================================= ---

def get_value_from_html_table(soup, search_pattern, field_name="Field"):
    """
    Generic fallback to find a value from HTML tables.
    Searches for a row containing the search pattern and extracts the first big number.
    
    Args:
        soup: BeautifulSoup object
        search_pattern: Regex pattern to find the row (e.g., r'Cost of products sold')
        field_name: Name for logging purposes
    """
    try:
        row_tag = soup.find(string=re.compile(search_pattern, re.IGNORECASE))
        if not row_tag:
            print(f"    - WARN ({field_name}-HTML): Could not find text matching '{search_pattern}'.")
            return None
        
        data_tr = row_tag.find_parent('tr')
        if not data_tr:
            print(f"    - WARN ({field_name}-HTML): Found text, but not its <tr> parent.")
            return None
        
        cells = data_tr.find_all('td')
        number_pattern = re.compile(r'([\d,]+)')
        
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            match = number_pattern.search(cell_text)
            if match:
                value_str = match.group(1).replace(',', '')
                if len(value_str) > 4:  # Find first big number
                    numerator_value = int(float(value_str))
                    
                    # Check if table says "in thousands"
                    table = data_tr.find_parent('table')
                    if table:
                        table_text = table.get_text(strip=True, separator=' ')
                        if re.search(r'\(In thousands\)', table_text, re.IGNORECASE):
                            numerator_value *= 1000
                    
                    return numerator_value
        return None
    except Exception as e:
        print(f"    - ERROR ({field_name}-HTML): {e}")
        return None


# --- ======================================================= ---
# --- PART 3: FIELD-SPECIFIC EXTRACTORS ---
# --- ======================================================= ---

def extract_cost_of_goods_sold(soup):
    """Extract Cost of Goods Sold (COGS) with fallback."""
    # Try iXBRL first
    value = get_value_from_ixbrl(soup, 'us-gaap:CostOfGoodsAndServicesSold')
    if value is not None:
        return value
    
    # Fallback to HTML table
    print("    - INFO (COGS): iXBRL not found. Trying HTML table parser...")
    return get_value_from_html_table(soup, r'Cost of products sold', 'COGS')


def extract_net_sales(soup):
    """Extract Net Sales (Revenue) with fallback."""
    # Try iXBRL first
    value = get_value_from_ixbrl(soup, 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax')
    if value is not None:
        return value
    
    # Fallback to HTML table - try multiple patterns
    print("    - INFO (Net Sales): iXBRL not found. Trying HTML table parser...")
    
    # Try "Net sales" first
    value = get_value_from_html_table(soup, r'Net sales', 'Net Sales')
    if value is not None:
        return value
    
    # Try "Revenue" or "Revenues" as fallback
    value = get_value_from_html_table(soup, r'Revenue[s]?', 'Net Sales')
    return value


def extract_inventories(soup):
    """Extract Inventories with fallback."""
    # Try iXBRL first
    value = get_value_from_ixbrl(soup, 'us-gaap:InventoryNet')
    if value is not None:
        return value
    
    # Fallback to HTML table
    print("    - INFO (Inventories): iXBRL not found. Trying HTML table parser...")
    
    # Try "Inventories, net" or just "Inventories"
    value = get_value_from_html_table(soup, r'Inventories[,]?\s*net', 'Inventories')
    if value is not None:
        return value
    
    value = get_value_from_html_table(soup, r'^Inventories$', 'Inventories')
    return value


# --- ======================================================= ---
# --- PART 4: TONS TEXT & QUARTER SCRAPER (Unchanged) ---
# --- ======================================================= ---

TONS_TEXT_PATTERNS = [
    re.compile(r'([^.]*A total of (?:approximately\s*)?([\d,]+)\s*tons were shipped to outside customers[^.]*\.)', re.IGNORECASE),
    re.compile(r'([^.]*Total tons shipped to (?:external|outside) customers[^.]*\.)', re.IGNORECASE),
    re.compile(r'([^.]*Tons shipped to outside customers.*?were\s*[\d,]+[^.]*\.)', re.IGNORECASE),
    re.compile(r'([^.]*Shipments to external customers[^.]*\.)', re.IGNORECASE),
    re.compile(r'([^.]*total tons shipped to outside customers increased \d+%.*?\.)', re.IGNORECASE),
    re.compile(r'([^.]*Average sales price per ton[^.]*\.)', re.IGNORECASE)
]

def find_tons_text(text):
    """Finds the full sentence that mentions tons."""
    for pattern in TONS_TEXT_PATTERNS:
        match = pattern.search(text)
        if match:
            return ' '.join(match.group(1).split())
    return None


def extract_quarter(text):
    """Extracts the quarter (Q1, Q2, Q3, Q4) from text."""
    if not isinstance(text, str):
        return None
    
    if re.search(r'first quarter', text, re.IGNORECASE):
        return 'Q1'
    if re.search(r'second quarter', text, re.IGNORECASE):
        return 'Q2'
    if re.search(r'third quarter', text, re.IGNORECASE):
        return 'Q3'
    if re.search(r'fourth quarter', text, re.IGNORECASE):
        return 'Q4'
    
    return None


# --- ======================================================= ---
# --- PART 5: VALIDATION LOGIC ---
# --- ======================================================= ---

def validate_extraction(cogs, net_sales, inventories, period_date):
    """
    Validates extracted values for basic sanity checks.
    Returns a list of warning messages.
    """
    warnings = []
    
    # Check 1: Net Sales should be greater than COGS
    if cogs and net_sales:
        if net_sales <= cogs:
            warnings.append(f"⚠️  Net Sales ({net_sales:,.0f}) <= COGS ({cogs:,.0f})")
    
    # Check 2: Values should be positive
    if cogs and cogs < 0:
        warnings.append(f"⚠️  Negative COGS: {cogs:,.0f}")
    if net_sales and net_sales < 0:
        warnings.append(f"⚠️  Negative Net Sales: {net_sales:,.0f}")
    if inventories and inventories < 0:
        warnings.append(f"⚠️  Negative Inventories: {inventories:,.0f}")
    
    # Check 3: Inventories should be reasonable relative to COGS
    if cogs and inventories:
        # Quarterly COGS, so inventory/COGS should be between 0.1 and 2.0 typically
        ratio = inventories / cogs
        if ratio > 2.0:
            warnings.append(f"⚠️  High inventory ratio: {ratio:.2f}x quarterly COGS")
    
    return warnings


# --- ======================================================= ---
# --- MAIN EXTRACTION SCRIPT ---
# --- ======================================================= ---

def extract_raw_data():
    """
    Loops through all 10-Q filings and extracts:
    - Cost of Goods Sold (Income Statement)
    - Net Sales (Income Statement)
    - Inventories (Balance Sheet)
    - Tons Text
    - Quarter
    """
    print("=" * 70)
    print("--- Starting Enhanced Raw Data Extraction (v2) ---")
    print("    New fields: Net Sales, Inventories")
    print("=" * 70)
    
    submissions_url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    response = requests.get(submissions_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()

    filings = data['filings']['recent']
    results_list = []
    base_archive_url = "https://www.sec.gov/Archives/edgar/data"

    for form, acc_num, doc_name, report_date, filing_date in zip(
        filings['form'], 
        filings['accessionNumber'], 
        filings['primaryDocument'],
        filings['reportDate'],
        filings['filingDate']
    ):
        
        if form == '10-Q':
            acc_num_no_dash = acc_num.replace('-', '')
            filing_url = f"{base_archive_url}/{CIK}/{acc_num_no_dash}/{doc_name}"
            
            print(f"\n{'='*70}")
            print(f"Processing 10-Q: {acc_num}")
            print(f"Period End: {report_date} | Filing Date: {filing_date}")
            print(f"{'='*70}")

            try:
                filing_html = requests.get(filing_url, headers=HEADERS).text
                soup = BeautifulSoup(filing_html, 'lxml')
                body_text = soup.get_text(strip=True, separator=' ')

                # --- Extract Financial Data ---
                cogs = extract_cost_of_goods_sold(soup)
                net_sales = extract_net_sales(soup)
                inventories = extract_inventories(soup)
                
                # --- Extract Operational Data ---
                tons_text = find_tons_text(body_text)
                quarter = extract_quarter(tons_text)
                year = pd.to_datetime(report_date).year

                # --- Log Results ---
                print("\n📊 EXTRACTION RESULTS:")
                print(f"    ✓ COGS:        {f'${cogs:,.0f}' if cogs else '❌ NOT FOUND'}")
                print(f"    ✓ Net Sales:   {f'${net_sales:,.0f}' if net_sales else '❌ NOT FOUND'}")
                print(f"    ✓ Inventories: {f'${inventories:,.0f}' if inventories else '❌ NOT FOUND'}")
                print(f"    ✓ Quarter:     {quarter if quarter else '❌ NOT FOUND'}")
                if tons_text:
                    print(f"    ✓ Tons Text:   '{tons_text[:60]}...'")
                else:
                    print(f"    ✓ Tons Text:   ❌ NOT FOUND")
                
                # --- Validate ---
                validation_warnings = validate_extraction(cogs, net_sales, inventories, report_date)
                if validation_warnings:
                    print("\n⚠️  VALIDATION WARNINGS:")
                    for warning in validation_warnings:
                        print(f"    {warning}")
                
                # --- Store Results ---
                results_list.append({
                    'AccessionNumber': acc_num,
                    'PeriodEndDate': report_date,
                    'FilingDate': filing_date,
                    'Year': year,
                    'Quarter': quarter,
                    'Cost_of_products_sold': cogs,
                    'Net_sales': net_sales,
                    'Inventories_net': inventories,
                    'Total_tons_shipped_text': tons_text
                })

                time.sleep(0.2) 

            except Exception as e:
                print(f"\n❌ FATAL ERROR processing file {filing_url}: {e}")

    # --- Save Results ---
    print("\n" + "=" * 70)
    print("--- Extraction Complete ---")
    print("=" * 70)
    
    df = pd.DataFrame(results_list)
    
    try:
        csv_filename = "nucor_01_RAW_EXTRACT.csv"
        
        # Reorder columns
        final_cols = [
            'AccessionNumber', 
            'PeriodEndDate', 
            'FilingDate',
            'Year',
            'Quarter',
            'Cost_of_products_sold',
            'Net_sales',
            'Inventories_net',
            'Total_tons_shipped_text'
        ]
        df = df[final_cols]
        df = df.sort_values(by='PeriodEndDate', ascending=False)
        
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"\n✅ Successfully saved all raw data to {csv_filename}")
        
        # --- Summary Statistics ---
        print("\n📈 EXTRACTION SUMMARY:")
        print(f"    Total filings processed: {len(df)}")
        print(f"    COGS found: {df['Cost_of_products_sold'].notna().sum()} / {len(df)}")
        print(f"    Net Sales found: {df['Net_sales'].notna().sum()} / {len(df)}")
        print(f"    Inventories found: {df['Inventories_net'].notna().sum()} / {len(df)}")
        print(f"    Quarter found: {df['Quarter'].notna().sum()} / {len(df)}")
        
    except Exception as e:
        print(f"\n❌ ERROR: Could not save CSV file: {e}")

    return df


# --- Run the Script ---
if __name__ == "__main__":
    raw_data_df = extract_raw_data()
    print("\n" + "=" * 70)
    print("Final DataFrame Preview:")
    print("=" * 70)
    pd.set_option('display.float_format', lambda x: '%.0f' % x)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(raw_data_df.head(10))