# Cost Foresight: Forecasting Production Costs in Steel
**University of Pisa – Data Science and Business Informatics** *Course: Fundamentals of Business Management / Financials Analysis (2025–2026)*

## 📌 Project Overview
The steel industry faces extreme cost volatility driven by raw material prices, energy market fluctuations, and geopolitical shocks. This project develops a machine learning framework to forecast **Cost of Goods Sold (COGS) per Ton** for **Nucor Corporation**, North America's largest steel producer.

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
