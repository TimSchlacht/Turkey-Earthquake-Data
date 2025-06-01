🇹🇷 Turkey Earthquake Analysis & Prediction System

DashBoard Link: https://app.powerbi.com/view?r=eyJrIjoiZDIxOTNkYjktNGU5OC00MGZkLTkxNmQtMmUyMzc3OGQ0ZGIyIiwidCI6IjQ1NDIwZThkLTg1NTItNGEwMy05YjkyLWE5MzFlZjgzOWQzZiIsImMiOjh9

An end-to-end project that collects, stores, analyzes, and visualizes earthquake data across Turkey, using:

🐍 Python (Data pipeline & ML)
🌐 APIs & Web Scraping (AFAD, TÜİK)
☁️ Azure SQL Database (Data warehouse)
📊 Power BI (Geo-visualizations)
🤖 Machine Learning (Predictive modeling)
🔍 Project Overview

This system provides a unified platform to:

Ingest real-time and historical earthquake data
Enrich it with geographical and population data
Visualize event distributions across Turkish provinces
Predict potential earthquake magnitudes or frequencies
🗺️ Live Map Dashboard (Power BI)

Interactive Power BI visuals display:

Earthquake hotspots by province
Depth and magnitude distribution
Risk zones over population density
Emergency response vs. event intensity
📍 Coming soon: Link to embedded dashboard

🛠️ Technologies Used

Tool	Purpose
Python	Data collection, cleaning, modeling
AFAD API	Earthquake event data (magnitude, depth, time, location)
TÜİK	Population and geographic statistics
Azure SQL	Centralized storage of all data
Power BI	Visualization & analytics dashboard
Scikit-learn / XGBoost	Earthquake prediction model
📦 Project Structure

├── data_pipeline/
│   ├── afad_scraper.py
│   ├── tuik_scraper.py
│   └── population_merge.py
├── database/
│   ├── create_tables.sql
│   └── insert_data.py
├── ml_model/
│   ├── preprocess.py
│   ├── model_train.py
│   └── predict.py
├── dashboard/
│   └── powerbi_visuals.pbix
├── notebooks/
│   └── EDA.ipynb
├── README.md
└── requirements.txt
🔄 Data Sources

AFAD Earthquake API: https://deprem.afad.gov.tr/apiv2/event/filter
TÜİK Population Data: https://data.tuik.gov.tr
Municipality Web Sources: Emergency resources & shelter availability
📈 Predictive Model

Features: magnitude, depth, region, previous quake frequency, time window
Target: Magnitude class / recurrence risk
Algorithms tested: RandomForest, XGBoost, Logistic Regression
Evaluation: F1-score, ROC-AUC, confusion matrix
💡 Future Enhancements

🚑 Integrate real-time emergency response data
🧠 Improve prediction with seismic sensor feeds
📲 Deploy as an API for live forecasts
🛰️ Use satellite-based terrain & fault line features
