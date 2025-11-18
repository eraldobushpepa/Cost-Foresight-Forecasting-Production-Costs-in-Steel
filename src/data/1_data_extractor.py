import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
import os

# --- Configuration ---
CIK = "0000073309" 
HEADERS = {'User-Agent': 'Eraldo Bushpepa e.bushpepa@studenti.unipi.it'}
# Output path matches your existing file
OUTPUT_CSV = "data/interim/nucor_financials/nucor_01_RAW_EXTRACT.csv"

# --- HELPER: Text cleaner ---
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# --- HELPER: Robust row èarser (Handles XBRL + HTML) ---
def extract_value_from_row(soup, search_pattern):
    """
    Finds a row by label, then grabs the FIRST number in that row.
    Handles both XBRL (2024 style) and plain HTML (2015 style).
    """
    try:
        # 1. Find label
        label = soup.find(string=re.compile(search_pattern, re.IGNORECASE))
        if not label: return None
        
        # 2. Find parent row
        row = label.find_parent('tr')
        if not row: return None
        
        # 3. Search cells
        cells = row.find_all('td')
        number_pattern = re.compile(r'\(?([\d,]{2,})\)?')
        
        for cell in cells:
            cell_text = clean_text(cell.get_text())
            if re.search(search_pattern, cell_text, re.IGNORECASE): continue
            
            # STRATEGY A: check for XBRL tag (Modern 10-Ks)
            ix_tag = cell.find('ix:nonfraction')
            if ix_tag:
                val_str = ix_tag.get_text(strip=True).replace(',', '')
                if val_str:
                    scale = ix_tag.get('scale')
                    val = float(val_str)
                    if scale: val = val * (10**int(scale))
                    else:
                        # Fallback scale
                        if val < 100_000: val *= 1_000_000
                    return int(val)

            # STRATEGY B: Plain text (Older 10-Ks)
            match = number_pattern.search(cell_text)
            if match:
                val_str = match.group(1).replace(',', '')
                # Ignore footnotes (length < 4)
                if len(val_str) < 4: continue
                
                val = float(val_str)
                if '(' in cell_text and ')' in cell_text: val = -val
                
                # Scaling
                if val < 100_000: val *= 1_000_000
                elif val < 1_000_000_000: val *= 1_000
                
                return int(val)
        return None
    except: return None

def extract_financials(soup, report_type):
    data = {}
    data['Cost_of_products_sold'] = extract_value_from_row(soup, r'Cost of products sold')
    data['Net_sales'] = extract_value_from_row(soup, r'Net sales')
    # Inventories
    inv = extract_value_from_row(soup, r'^Inventories,\s*net$')
    if inv is None: inv = extract_value_from_row(soup, r'Inventories')
    data['Inventories_net'] = inv
    return data

def extract_tons_text(text, report_type):
    patterns = []
    if report_type == '10-Q':
        patterns.append(r'([^.]*Total tons shipped to (?:external|outside) customers[^.]*quarter[^.]*\.)')
        patterns.append(r'([^.]*shipped[^.]*quarter[^.]*approximately[^.]*tons[^.]*\.)')
        patterns.append(r'([^.]*Total tons shipped to (?:external|outside) customers[^.]*were\s+[\d,]+[^.]*\.)')
    else: # 10-K
        patterns.append(r'([^.]*shipped to (?:external|outside) customers.*?to\s+[\d,]+\s+tons\s+in\s+\d{4}[^.]*\.)')
        patterns.append(r'([^.]*Total tons shipped to (?:external|outside) customers[^.]*in\s+\d{4}[^.]*\.)')
        patterns.append(r'([^.]*Total steel shipments to (?:external|outside) customers[^.]*\.)')
        patterns.append(r'([^.]*Outside steel shipments[^.]*[\d,]{4,}[^.]*\.)')

    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match: return match.group(1).strip()
    return None

def fetch_exhibit_13_soup(acc_num, headers):
    acc_no_dash = acc_num.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_no_dash}/index.json"
    try:
        resp = requests.get(index_url, headers=headers)
        if resp.status_code != 200: return None
        files = resp.json()['directory']['item']
        ex13_file = None
        for f in files:
            name = f['name'].lower()
            if 'ex13' in name or 'exhibit13' in name:
                if name.endswith('.htm') or name.endswith('.html'):
                    ex13_file = f['name']
                    break
        if ex13_file:
            print(f"   >>> Found Exhibit 13: {ex13_file}. Downloading...")
            ex_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_no_dash}/{ex13_file}"
            ex_html = requests.get(ex_url, headers=headers).text
            return BeautifulSoup(ex_html, 'lxml')
    except: pass
    return None

# --- MAIN LOOP ---
def extract_raw_data():
    print(f"--- Connecting to SEC API (CIK: {CIK}) ---")
    submissions_url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    response = requests.get(submissions_url, headers=HEADERS)
    data = response.json()
    filings = data['filings']['recent']
    
    results_list = []
    
    # Statistics Trackers
    stats = {
        "total": 0,
        "complete": 0,
        "missing_cost": 0,
        "missing_sales": 0,
        "missing_tons": 0
    }
    missing_log = []

    print("--- Processing Filings ---")

    for form, acc_num, doc_name, report_date in zip(filings['form'], filings['accessionNumber'], filings['primaryDocument'], filings['reportDate']):
        if form in ['10-Q', '10-K']:
            if str(report_date) < "2015-01-01": continue
            
            stats["total"] += 1
            print(f"Processing {form}: {report_date}...", end=" ")

            try:
                # 1. Get Mmain doc
                acc_num_no_dash = acc_num.replace('-', '')
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_num_no_dash}/{doc_name}"
                filing_html = requests.get(filing_url, headers=HEADERS).text
                soup = BeautifulSoup(filing_html, 'lxml')
                body_text = clean_text(soup.get_text(separator=' '))

                fin_data = extract_financials(soup, form)
                tons_text = extract_tons_text(body_text, form)

                # 2. Deep search (Exhibit 13)
                missing_any = (fin_data['Cost_of_products_sold'] is None) or (tons_text is None)
                
                if form == '10-K' and missing_any:
                    print("\n   ⚠️ Missing Data in Main Doc. Checking Exhibit 13...", end="")
                    ex13_soup = fetch_exhibit_13_soup(acc_num, HEADERS)
                    if ex13_soup:
                        if fin_data['Cost_of_products_sold'] is None:
                            new_fins = extract_financials(ex13_soup, form)
                            if new_fins['Cost_of_products_sold']:
                                fin_data = new_fins
                                print(" [Recovered Financials]", end="")
                        
                        if tons_text is None:
                            ex13_text = clean_text(ex13_soup.get_text(separator=' '))
                            tons_text = extract_tons_text(ex13_text, form)
                            if tons_text: print(" [Recovered Tons]", end="")

                # 3. Log results
                missing_fields = []
                if fin_data['Cost_of_products_sold'] is None: 
                    stats["missing_cost"] += 1
                    missing_fields.append("Cost")
                if fin_data['Net_sales'] is None:
                    stats["missing_sales"] += 1
                    missing_fields.append("Sales")
                if tons_text is None:
                    stats["missing_tons"] += 1
                    missing_fields.append("Tons")
                
                if not missing_fields:
                    stats["complete"] += 1
                    print("✅ OK")
                else:
                    print(f"❌ MISSING: {', '.join(missing_fields)}")
                    missing_log.append(f"{report_date} ({form}): Missing {', '.join(missing_fields)}")

                results_list.append({
                    'AccessionNumber': acc_num, 'PeriodEndDate': report_date, 'ReportType': form,
                    'Year': pd.to_datetime(report_date).year,
                    'Cost_of_products_sold': fin_data['Cost_of_products_sold'],
                    'Net_sales': fin_data['Net_sales'],
                    'Inventories_net': fin_data['Inventories_net'],
                    'Total_tons_shipped_text': tons_text
                })
                time.sleep(0.15)

            except Exception as e:
                print(f"❌ Error: {e}")

    # --- Save + report ---
    df = pd.DataFrame(results_list)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    
    print("\n" + "="*50)
    print("📊 EXTRACTION REPORT")
    print("="*50)
    print(f"Total Processed: {stats['total']}")
    print(f"Fully Complete:  {stats['complete']} ({stats['complete']/stats['total']*100:.1f}%)")
    print(f"Missing Cost:    {stats['missing_cost']}")
    print(f"Missing Tons:    {stats['missing_tons']}")
    print("-" * 30)
    if missing_log:
        print("⚠️ FILES WITH MISSING DATA:")
        for log in missing_log:
            print(f"   - {log}")
    else:
        print("✅ All files extracted successfully!")
    print("="*50)

if __name__ == "__main__":
    extract_raw_data()