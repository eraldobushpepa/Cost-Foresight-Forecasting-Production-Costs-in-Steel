
# Cost Foresight - Forecasting Steel Production Costs

**Project Status:** `[In Progress]`

## Overview

This repository contains the work for our Master's project in Financial Analysis and Performance Measurement.

The core objective is to develop a **conceptual AI/Data Science solution** to forecast future production costs in the steel industry. We are building a predictive model that integrates a company's internal accounting data with a wide range of external, high-frequency market indices.

* **Company Profiled:** **Nucor Corporation (NYSE: NUE)**, a US-based steel producer.
* **Production Method:** Nucor primarily uses **Electric Arc Furnaces (EAF)**. Our model is therefore built on the key inputs for this process: scrap steel, electricity, and natural gas.

### Authors
* Bushpepa Eraldo
* Calderini Alice
* Chaoui-Abdou Selma
* Parmar Aashiva Ashwinbhai
* Rossi Sara

---

## The Core Analytic: Upgrading the Target Variable (Y)

Our initial analysis showed that the standard `Y: Cost_of_Products_Sold` is a "noisy" target variable, as it mixes two factors: **market prices** (volatile) and **production volume** (variable).

To create a more accurate and insightful model, our primary task is to create a new, "pure" target variable: **`Y1: Cost_Per_Ton`**.

This new variable isolates the true production efficiency and cost pressures. We are creating it by building a Python script to parse Nucor's quarterly SEC 10-Q filings:

$$
\text{Cost\_Per\_Ton} = \frac{\text{Consolidated Cost of Products Sold (from 10-Q)}}{\text{Total Tons Shipped to External Customers (from 10-Q)}}
$$

---

## Feature Engineering (The "X" Variables)

Our model's "foresight" comes from using a set of features (X) to predict our new `Cost_Per_Ton` (Y1).

### Main Features (Core Model)
* **X1: `Scrap_Price`:** The primary raw material.
* **X2: `Electricity_Price`:** The primary energy cost for EAF furnaces.
* **X3: `Natural_Gas_Price`:** A key for Nucor's in-house DRI production and a driver of electricity prices.

### Alternative & Creative Features (Advanced Model)
* **X4: `Diesel_Price`:** Proxy for logistics/trucking costs to move scrap.
* **X5: `Rail_Price`:** Proxy for logistics/rail costs for heavy materials.
* **X6: `Disaster_Event_Count`:** A "system shock" proxy for events (tornadoes, floods) that disrupt the grid and logistics.
* **X7: `Average_Hourly_Wage`:** A direct measure of the `Direct Labor` component of COGS.
* **X8: `US_Scrap_Exports`:** A macro-economic feature to model global demand pressure on domestic scrap supply.
* **X9: `US_Dollar_Index`:** A feature to model the "currency volatility" risk mentioned in Nucor's annual report.
* **X10: `Graphite_Electrode_Price`:** A key (and volatile) consumable in EAF furnaces, also mentioned in the annual report.
* **X11: `Pig_Iron_Price`:** The primary "scrap substitute" Nucor buys, based on price.
* **X12: `Economic_Policy_Uncertainty_Index`:** A standard academic index to model the "political conditions" risk.

---

## Data Processing & Methodology

The core data engineering task is to combine our **quarterly** target (`Y1`) with our **monthly** features (`X1-X12`).

Our `preprocessing.ipynb` script handles this entire pipeline:
1.  **Load:** Loads the four key source files (Nucor accounting + 3 core features).
2.  **Clean:** Cleans number formatting and handles messy headers from the EIA files.
3.  **Resample:** Aggregates the `monthly` features (Scrap, Electricity, Gas) into `quarterly` data by calculating the 3-month average.
4.  **Merge:** Joins the quarterly Nucor data with the newly resampled quarterly features.
5.  **Output:** Saves the final, model-ready `master_dataset.csv`.

---

## Data Sources

### Accounting & Volume Data (The "Y")
* **SEC EDGAR Database:** All `10-Q` (quarterly) and `10-K` (annual) reports for Nucor Corp.
    * Used to extract `Consolidated Cost of Products Sold`.
    * Used to extract `Total tons shipped to external customers`.
* **Virtua Research:** [Link](https://vbench.virtuaresearch.com/IR/IAC/?Ticker=NUE&Exchange=NYSE#). Used for initial data gathering and high-level financials (`nucor.csv`).

### Feature Data (The "X")
* **U.S. EIA (Energy Information Administration):**
    * `EIA_Electricity_Price_Monthly.csv`
    * `EIA_Natural_Gas_Price_Monthly.csv`
    * `Diesel_Price` (X4)
* **U.S. BLS (Bureau of Labor Statistics):**
    * `PPI_Iron_Steel_Scrap_Monthly.csv` (X1)
    * `Rail_Price` (X5)
    * `Average_Hourly_Wage` (X7)
    * `Graphite_Electrode_Price` (X10)
    * `Pig_Iron_Price` (X11)
* **FEMA (Federal Emergency Management Agency):**
    * `Disaster_Event_Count` (X6)
* **U.S. Census Bureau:**
    * `US_Scrap_Exports` (X8)
* **FRED (Federal Reserve Economic Data):**
    * `US_Dollar_Index` (X9)
* **PolicyUncertainty.com:**
    * `Economic_Policy_Uncertainty_Index` (X12)

