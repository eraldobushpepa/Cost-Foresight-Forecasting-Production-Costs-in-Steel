# Cost Foresight: Forecasting Steel Production Costs

[![Project Status](https://img.shields.io/badge/status-in_progress-yellow.svg)](https://github.com/)

## 🎯 Project Goal

This repository contains the work for our Master's project in **Financial Analysis and Performance Measurement**. The objective is to develop a conceptual AI/Data Science solution to forecast future production costs in the steel industry. We are building a predictive model that integrates a company's internal accounting data with a wide range of external, high-frequency market indices.

## 🏭 The Business Case

* **Company Profiled:** **Nucor Corporation (NYSE: NUE)**, a leading US-based steel producer.
* **Production Method:** Nucor primarily uses **Electric Arc Furnaces (EAF)**. Our model is therefore built on the key inputs for this process: **scrap steel**, **electricity**, and **natural gas**.

## 📈 The Core Analytic: Engineering a Better Target (Y)

Our initial analysis revealed that the standard `Cost_of_Products_Sold` is a "noisy" target variable.

> **The Problem:** `Cost_of_Products_Sold` (COGS) mixes two factors: volatile market prices (input costs) and variable production volume. A model predicting this can't distinguish between a 10% cost increase from higher prices and a 10% increase from making 10% more steel.

To build an insightful model, our primary task is to engineer a "pure" target variable that isolates true cost pressure and efficiency.

**Target Variable (Y): `Cost_per_Ton`**

We parse Nucor's quarterly SEC 10-Q filings to calculate this new variable:

$$
\text{Cost per Ton} = \frac{\text{Consolidated Cost of Products Sold}}{\text{Total Tons Shipped to External Customers}}
$$

## 🛠️ Feature Engineering (X Variables)

Our model's "foresight" comes from using a set of leading indicators (X) to predict our `Cost_per_Ton` (Y). We've categorized our features into a **Core Model** (for a baseline) and an **Advanced Model** (for improved accuracy).

| Category | Variable | Description | Rationale |
| :--- | :--- | :--- | :--- |
| **Core** | `Scrap_Price` | Price of iron & steel scrap (PPI) | The primary raw material for EAF. |
| **Core** | `Electricity_Price` | Industrial electricity price | The primary energy cost for EAF furnaces. |
| **Core** | `Natural_Gas_Price` | Natural gas price | Key for Nucor's in-house DRI production and a driver of electricity prices. |
| Advanced | `Diesel_Price` | On-highway diesel price | Proxy for logistics/trucking costs to move scrap and finished goods. |
| Advanced | `Rail_Price` | Freight rail price (PPI) | Proxy for logistics/rail costs for heavy materials. |
| Advanced | `Disaster_Event_Count` | Count of major disaster declarations | A "system shock" proxy for events (floods, tornadoes) that disrupt the grid. |
| Advanced | `Avg_Hourly_Wage` | Avg. hourly wage in manufacturing | A direct measure of the "Direct Labor" component of COGS. |
| Advanced | `US_Scrap_Exports` | Volume of US scrap exports | Macro-economic feature to model global demand pressure on domestic supply. |
| Advanced | `US_Dollar_Index` | Trade-weighted US Dollar Index | Models the "currency volatility" risk mentioned in Nucor's annual report. |
| Advanced | `Graphite_Electrode_Price` | Price index for graphite electrodes | A key (and volatile) *consumable* in EAF furnaces, also cited in reports. |
| Advanced | `Pig_Iron_Price` | Price of pig iron | The primary "scrap substitute" Nucor buys based on relative pricing. |
| Advanced | `Econ_Policy_Uncertainty` | Economic Policy Uncertainty Index | A standard academic index to model "political/regulatory conditions" risk. |

## ⚙️ Data Pipeline & Methodology

The primary data engineering task is to time-align our **quarterly** target (Y) with our **monthly** features (X). The `preprocessing.ipynb` notebook handles this entire pipeline:

1.  **Load:** Loads the four key source files (Nucor accounting + 3 core features).
2.  **Clean:** Cleans number formatting (e.g., "$", ",") and handles messy headers from government (EIA) files.
3.  **Resample:** Aggregates the monthly features into quarterly data by calculating the **3-month average** for each quarter.
4.  **Merge:** Joins the quarterly Nucor data with the newly resampled quarterly features into a single time-series dataset.
5.  **Output:** Saves the final, model-ready `master_dataset.csv`.

## 🗂️ Data Sources

* **Accounting & Volume Data (The "Y")**
    * **SEC EDGAR Database:** All 10-Q (quarterly) and 10-K (annual) reports for Nucor Corp.
        * Used to extract *Consolidated Cost of Products Sold*.
        * Used to extract *Total tons shipped to external customers*.
    * **Virtua Research:** Used for initial data gathering and high-level financials (`nucor.csv`).

* **Feature Data (The "X")**
    * **U.S. EIA (Energy Information Administration):**
        * `EIA_Electricity_Price_Monthly.csv`
        * `EIA_Natural_Gas_Price_Monthly.csv`
        * `Diesel_Price`
    * **U.S. BLS (Bureau of Labor Statistics):**
        * `PPI_Iron_Steel_Scrap_Monthly.csv` (Scrap)
        * `Rail_Price`
        * `Average_Hourly_Wage`
        * `Graphite_Electrode_Price`
        * `Pig_Iron_Price`
    * **FEMA (Federal Emergency Management Agency):**
        * `Disaster_Event_Count`
    * **U.S. Census Bureau:**
        * `US_Scrap_Exports`
    * **FRED (Federal Reserve Economic Data):**
        * `US_Dollar_Index`
    * **PolicyUncertainty.com:**
        * `Economic_Policy_Uncertainty_Index`

## 📂 Repository Structure (Suggested)