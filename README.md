# Cost Foresight: Forecasting Production Costs in Steel
**University of Pisa – Data Science and Business Informatics** *Course: Fundamentals of Business Management / Financials Analysis (2025–2026)*

## 📌 Project Overview
The steel industry faces extreme cost volatility driven by raw material prices, energy market fluctuations, and geopolitical shocks. This project develops a machine learning framework to forecast **Cost of Goods Sold (COGS) per Ton** for **Nucor Corporation**, North America's largest steel producer.

<<<<<<< HEAD
Unlike traditional budgeting based on historical averages, this project leverages **Regularized Regression** and **Synthetic Data Augmentation** to navigate the "structural break" in market volatility observed post-2021.

## 👥 The Team (Team 7)
* **Eraldo Bushpepa**
* **Alice Calderini**
* **Selma Chaoui-Abdou**
* **Aashiva Ashwinbhai Parmar**
* **Sara Rossi**

---

## 🚀 Key Findings
1.  **Structural Break:** The steel market underwent a fundamental shift in volatility after 2021 (Ukraine War/Post-COVID), making simple time-series models ineffective.
2.  **Small Data Solution:** With only ~43 quarters of data available, we utilized a **Gaussian Copula Synthesizer (SDV)** to generate 200+ synthetic quarters, stabilizing our model training.
3.  **Model Selection:**
    * **Winner:** Regularized Linear Models (**Lasso/Ridge**) outperformed all others (MAE ~$134/ton).
    * **Finding:** Deep Learning models (LSTM/GRU) proved unsuitable due to data scarcity, resulting in overfitting.

---
=======

## 📖 Overview

This project demonstrates a **Master's-level Data Science solution** for the financial analysis of the steel industry. We developed an automated data pipeline to forecast **Unit Production Costs** (`Cost_Per_Ton`) for **Nucor Corporation (NUE)**.

The model integrates internal financial data (scraped from SEC filings) with 12 external macroeconomic indicators to predict cost fluctuations.

  * **Company:** Nucor Corporation (Electric Arc Furnace producer).
  * **Target:** `Cost_Per_Ton` (Derived from COGS / Sales Volume).
  * **Scope:** 2015 – 2025 (Quarterly).

-----

## 🏗️ The Engineering Pipeline

Unlike simple datasets, this project involved creating a robust ETL pipeline to handle unstructured financial text and time-series alignment.

### 1\. Data Extraction (The "Exhibit Hunter")

  * **Script:** `src/data/1_data_extractor.py`
  * **Challenge:** Nucor's 10-K filings often hide critical data in attached "Exhibit 13" documents or use inconsistent HTML/XBRL tagging over the last decade.
  * **Solution:** Built a custom scraper using `BeautifulSoup` that:
      * Parses both modern XBRL tags (2019-2024) and legacy HTML tables (2015-2018).
      * Detects missing data in the main 10-K and automatically downloads/scrapes **Exhibit 13** to recover it.
      * Uses Regex to extract "Tons Shipped" from unstructured text paragraphs.

### 2\. Data Processing (The Logic Core)

  * **Script:** `src/data/2_data_processor.py`
  * **Challenge:** The SEC only provides "Year-End" totals for Q4, not quarterly values. Also, reporting units changed from Thousands to Millions over time.
  * **Solution:** \* **Reverse Calculation:** Computed Q4 data mathematically: `Annual - (Q1 + Q2 + Q3)`.
      * **Manual Backups:** Implemented a fallback dictionary for years where text extraction was impossible (verified manually).
      * **Inventory Logic:** Calculated `Inventory Turnover` using a "Forward Fill" strategy to bridge reporting gaps in 2015.

### 3\. Feature Engineering

  * **Script:** `src/data/3_process_external_features.py`
  * **Action:** Aggregates 12 different monthly/daily external datasets into a unified Quarterly index.
  * **Logic:** Uses `resample('QE').mean()` for prices and `groupby().sum()` for event data (Disasters).

### 4\. The Grand Merge

  * **Script:** `src/data/4_build_master_dataset.py`
  * **Action:** Aligns Nucor's fiscal quarter dates (which end on Saturdays) with standard calendar quarters to ensure perfect time-series alignment.

-----

## 📂 Repository Structure

The project follows the [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/) standard:

```text
├── data/
│   ├── raw/                   # Original monthly CSVs and extracted Nucor data
│   ├── interim/               # Intermediate cleaned files (nucor_04_METRICS.csv, external_features,_quarterly.csv)
│      ├── nucor_financials/   # The nucor's financials (nucor_01_RAW_EXTRACT.csv)
│   └── processed/             # The Final Master Dataset (model-ready)
│
├── notebooks/
│   └── 01_data_processing.ipynb  # Prototyping & Visualization
│
├── src/
│   ├── data/
│   │   ├── 1_data_extractor.py       # Scrapes SEC.gov
│   │   ├── 2_data_processor.py       # Calculates financial metrics
│   │   ├── 3_process_features.py     # Cleans + aggregate market indices
│   │   └── 4_build_master.py         # Merges everything
│   └── models/
│       └── modelling.py              # (Coming Soon) LSTM/Regression Models
│
├── reports/                   # Final Executive Summary & Figures
└── README.md
```

-----

## 📊 The Dataset (Features)

Our final `master_dataset.csv` contains **43 rows** and **31 cols** of data (2015-2024) with **0 missing values**.

### Target Variable (Y)

  * **`Y_Cost_Per_Ton`**: The precise production cost per ton of steel sold.

### Predictive Features (X)

| Feature | Source | Hypothesis |
| :--- | :--- | :--- |
| **X1: Scrap Price** | BLS (PPI) | \#1 Raw material cost for EAF. |
| **X2: Electricity** | EIA | Major energy cost for Electric Arc Furnaces. |
| **X3: Natural Gas** | EIA | Key feedstock for DRI production. |
| **X4: Diesel Price** | EIA | Proxy for logistics/trucking costs. |
| **X5: Rail Price** | BLS | Proxy for heavy transport costs. |
| **X6: Disaster Count** | NOAA | "Shock" events disrupting grid/logistics. |
| **X7: Labor Wage** | BLS | Direct labor cost component. |
| **X8: Scrap Exports** | Census | Global demand pressure on US scrap supply. |
| **X9: USD Index** | FRED | Currency volatility risk (explicitly cited in 10-K). |
| **X10: Graphite** | BLS | Key consumable (electrodes) for EAF. |
| **X11: Policy Index** | PolicyUncertainty | Proxy for political/tariff risk. |
| **X12: Inventory Turnover** | Internal | Inventory efficiency metric. |

-----

## 🚀 How to Run

1.  **Install Dependencies:**

    ```bash
    pip install pandas requests beautifulsoup4 lxml
    ```

2.  **Run the Pipeline:**

    ```bash
    python src/data/1_data_extractor.py    # Downloads & Scrapes 10-Qs
    python src/data/2_data_processor.py    # Calculates Q4s & Metrics
    python src/data/3_process_features.py  # Cleans Market Data
    python src/data/4_build_master.py      # Generates master_dataset.csv
    ```

3.  **Output:**
    Find the model-ready file at `data/processed/master_dataset.csv`.
>>>>>>> 17bed066af1c75b80c5ec3b7ff32e82308c93858
