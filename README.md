

# README: Cost Foresight - Steel Production Cost Dataset

## Overview

This dataset is made for the "Cost Foresight - Forecasting Production Costs in Steel" project.

The goal is to build a predictive model that forecasts the production costs of a steel manufacturer by integrating its internal accounting data with external, high-frequency market indices.

* **Company Profiled:** Nucor Corporation (a US-based steel producer).
* **Production Method:** Electric Arc Furnace (EAF), which primarily uses scrap steel and electricity and natural gas (in some processes).


## Methodology

Here how we will use the data for the forecast model

1.  **Target Data (Y):** Nucor's quarterly accounting data was extracted from `nucor.csv`. This file provided the target variable, **`Cost_of_Products_Sold`**, **`Gross Margin`** and **`Inventories`**.
2.  **Feature Data (X):** Based on Nucor's EAF business model and public disclosures, three primary cost drivers were identified:
    * **X1 (Scrap Steel):** `WPS101.csv` - US Producer Price Index for Iron and Steel Scrap.
    * **X2 (Electricity):** `Average_retail_price_of_electricity_United_States_monthly.csv` - US Average Industrial Electricity Price.
    * **X3 (Natural Gas):** `Henry_Hub_Natural_Gas_Spot_Price.csv` - US Natural Gas Spot Price. (This is a key input for Nucor's in-house DRI and electricity production).
3.  **Cleaning & Resampling:** The Nucor data was provided **quarterly**, while the three market indices were **monthly**. To align them, the three monthly files were "resampled" to a quarterly frequency by calculating the 3-month average for each period.
4.  **Merge:** We need to fix this problem


## Source Files

* `nucor.csv`: Quarterly accounting data for Nucor.
* `WPS101.csv`: Monthly US PPI for Iron and Steel Scrap (US Bureau of Labor Statistics).
* `Average_retail_price_of_electricity_United_States_monthly.csv`: Monthly US Industrial Electricity Price (US EIA).
* `Henry_Hub_Natural_Gas_Spot_Price.csv`: Monthly Henry Hub Natural Gas Spot Price (US EIA).
* (work in progress maybe we'll use tornado data)