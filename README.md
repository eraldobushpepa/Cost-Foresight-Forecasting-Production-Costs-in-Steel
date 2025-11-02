# Team 7 Data Dictionary

This document provides a complete inventory of all datasets for the **"Cost Foresight - Forecasting Production Costs in Steel"** project.

The data is grouped by its role in our financial model, which compares the **"Old" (BF-BOF)** pathway with the **"New" (H2-DRI)** pathway.

---

## 1. Pathway 1: "Old Steel" (BF-BOF) Costs

These files establish the baseline operating costs of the traditional **Blast Furnace - Basic Oxygen Furnace (BF-BOF)** route.

* **File:** `Coking Coal Futures Historical Data.csv`
    * **What it is:** The futures price of metallurgical (coking) coal.
    * **Role:** This is the primary **fuel cost** for the blast furnace.
    * **Notes:** The `Price` is in **Chinese Yuan (CNY)** and will need to be converted.

* **File:** `Carbon Emissions Futures Historical Data UK.csv`
    * **What it is:** The price of EU Emissions Trading System (ETS) carbon allowances.
    * **Role:** This is the **"carbon tax"** or financial penalty for $CO_2$ emissions, a key variable driving the switch to new technology.
    * **Notes:** The `Price` is in **Euros (EUR)**.

---

## 2. Pathway 2: "New Steel" (H2-DRI) Costs

This file represents the primary energy cost for the new **Hydrogen - Direct-Reduced Iron (H2-DRI) + Electric Arc Furnace (EAF)** pathway.

* **File:** `estat_nrg_pc_205$defaultview_filtered.tsv`
    * **What it is:** Eurostat data for bi-annual industrial electricity prices (non-household consumers).
    * **Role:** This is the primary **energy cost** for the EAF and for producing green hydrogen via electrolysis.
    * **Notes:** **REQUIRES CLEANING.** This file is in a "wide" format (dates are columns). It must be pivoted ("melted") into a "long" format (e.g., `date`, `country`, `price`) to be used in our model.

---

## 3. Key Raw Material: Iron Ore (Input for Both)

This is the main raw material for both steelmaking pathways.

* **File:** `Iron ore fines 62_ Fe CFR Futures Historical Data UK_TIOc1.csv`
    * **What it is:** The main global benchmark price for standard 62% Fe iron ore. This is the front-month (`c1`) futures contract.
    * **Role:** The primary **raw material cost**.

* **File:** `Iron ore fines 62_ Fe CFR Futures Historical Data UK_TIOc2.csv`
* **File:** `Iron ore fines 62_ Fe CFR Futures Historical Data UK_TIOc3.csv`
    * **What they are:** The 2nd and 3rd-month futures contracts.
    * **Role:** We can use these to create a **"spread"** (e.g., `c2-c1`) to analyze market sentiment (contango vs. backwardation) and as a predictive feature.

---

## 4. Producer Price Indices (PPIs) - Historical Baseline

These files (from FRED) are our monthly "ground truth" price indicators. They show what producers *have been* paying historically in the US.

* **File:** `PPIACO.csv`
    * **What it is:** PPI for **All Commodities**.
    * **Role:** A broad baseline for overall economic inflation.

* **File:** `WPS101.csv`
    * **What it is:** PPI for **Iron and Steel**.
    * **Role:** Our key historical price benchmark for the steel industry.

* **File:** `WPU1012.csv`
    * **What it is:** PPI for **Nonferrous Metals**.
    * **Role:** Represents the price of **substitute materials** (like aluminum or copper) that compete with steel.

* **File:** `PCU3312213312211.csv`
    * **What it is:** PPI for **Rolled Steel Shape Manufacturing**.
    * **Role:** Price of a specific downstream steel product.

* **File:** `PCU33123312.csv`
    * **What it is:** PPI for **Iron and Steel Pipe and Tube Manufacturing**.
    * **Role:** Price of another specific downstream steel product.

---

## 5. Macro-Economic Indicator

* **File:** `Baltic Dry Index Historical Results Price Data.csv`
    * **What it is:** The Baltic Dry Index (BDI).
    * **Role:** A leading indicator for global industrial demand and raw material shipping costs.