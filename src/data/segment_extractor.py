import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
import os

# --- Configuration ---
CIK = "0000073309"
HEADERS = {'User-Agent': 'Eraldo Bushpepa e.bushpepa@studenti.unipi.it'}
OUTPUT_CSV = "data/interim/nucor_financials/nucor_segments.csv"

def clean_money(text):
    """Converts '(1,234)' -> -1234.0 and '1,234' -> 1234.0"""
    if not text: return None
    # Remove footnotes or weird chars, keep only digits, parens, dots, minus
    clean = re.sub(r'[^\d\(\)\.\-]', '', text)
    if not clean: return None
    try:
        if '(' in clean or ')' in clean:
            clean = clean.replace('(', '').replace(')', '')
            return -float(clean)
        return float(clean)
    except:
        return None

def parse_segment_table(soup):
    """
    Finds the table containing 'Steel Mills', 'Steel Products' headers
    and extracts Net Sales & Intercompany Sales.
    """
    tables = soup.find_all('table')
    
    for table in tables:
        # 1. Identify the correct table using keywords
        full_text = table.get_text(" ", strip=True).lower()
        
        # Keyword check: Must have segment names and "net sales"
        if 'steel mills' in full_text and 'steel products' in full_text and 'net sales' in full_text:
            
            data = {}
            rows = table.find_all('tr')
            
            # Regex patterns for rows
            row_targets = {
                r"net\s+sales\s+to\s+external": "NetSalesExternal",
                r"intercompany\s+sales": "IntercompanySales",
                r"total\s+sales": "TotalSales",
                r"cost\s+of\s+products\s+sold": "COGS"
            }
            
            for tr in rows:
                row_str = tr.get_text(" ", strip=True)
                
                metric_name = None
                for pattern, name in row_targets.items():
                    if re.search(pattern, row_str, re.IGNORECASE):
                        if "reconciliation" in row_str.lower(): continue
                        metric_name = name
                        break
                
                if metric_name:
                    cells = tr.find_all(['td', 'th'])
                    numbers = []
                    for cell in cells:
                        val = clean_money(cell.get_text())
                        if val is not None:
                            numbers.append(val)
                    
                    # We need at least 3 numbers (Mills, Products, Raw)
                    if len(numbers) >= 3:
                        data[f"{metric_name}_Mills"] = numbers[0]
                        data[f"{metric_name}_Products"] = numbers[1]
                        data[f"{metric_name}_Raw"] = numbers[2]
                        
                        # Total is usually the last number
                        if len(numbers) >= 4:
                            data[f"{metric_name}_Total"] = numbers[-1]

            # If we successfully extracted at least one metric, return it
            if len(data) > 0:
                return data
                
    return None

def fetch_exhibit_13_soup(acc_num, headers):
    """Fetches Exhibit 13 HTML for older filings."""
    acc_no_dash = acc_num.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_no_dash}/index.json"
    try:
        resp = requests.get(index_url, headers=headers)
        if resp.status_code != 200: return None
        
        files = resp.json()['directory']['item']
        ex13_file = None
        
        # Look for ex13 or exhibit13
        for f in files:
            name = f['name'].lower()
            if 'ex13' in name or 'exhibit13' in name:
                if name.endswith('.htm') or name.endswith('.html'):
                    ex13_file = f['name']
                    break
        
        if ex13_file:
            ex_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_no_dash}/{ex13_file}"
            ex_html = requests.get(ex_url, headers=headers).text
            return BeautifulSoup(ex_html, 'lxml')
            
    except: pass
    return None

def extract_segments():
    print(f"--- 🚀 Starting Segment Extraction (Deep Search Mode) ---")
    
    submissions_url = f"https://data.sec.gov/submissions/CIK{CIK}.json"
    response = requests.get(submissions_url, headers=HEADERS)
    filings = response.json()['filings']['recent']
    
    results_list = []
    
    for form, acc_num, doc_name, report_date in zip(filings['form'], filings['accessionNumber'], filings['primaryDocument'], filings['reportDate']):
        
        if form in ['10-Q', '10-K'] and str(report_date) >= "2015-01-01":
            
            print(f"Scanning {report_date} ({form})...", end=" ")
            
            try:
                # 1. Try Main Document First
                acc_num_no_dash = acc_num.replace('-', '')
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{CIK}/{acc_num_no_dash}/{doc_name}"
                html_text = requests.get(filing_url, headers=HEADERS).text
                soup = BeautifulSoup(html_text, 'lxml')
                
                segment_data = parse_segment_table(soup)
                
                # 2. If missing, try Exhibit 13 (Fallback)
                if not segment_data:
                    # Only check exhibit 13 for 10-Ks usually, but sometimes 10-Qs too
                    ex13_soup = fetch_exhibit_13_soup(acc_num, HEADERS)
                    if ex13_soup:
                        print("[Checking Ex13]...", end=" ")
                        segment_data = parse_segment_table(ex13_soup)

                if segment_data:
                    segment_data['PeriodEndDate'] = report_date
                    segment_data['ReportType'] = form
                    results_list.append(segment_data)
                    print("✅ Found Table")
                else:
                    print("❌ Table Not Found")
                    
            except Exception as e:
                print(f"Error: {e}")
                
            time.sleep(0.15)

    # Save
    if results_list:
        df = pd.DataFrame(results_list)
        # Reorder columns
        cols = ['PeriodEndDate', 'ReportType'] + sorted([c for c in df.columns if c not in ['PeriodEndDate', 'ReportType']])
        df = df[cols]
        
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\n🎉 Done! Saved {len(df)} rows to {OUTPUT_CSV}")
        print(df.head())
    else:
        print("\nNo data found.")

if __name__ == "__main__":
    extract_segments()