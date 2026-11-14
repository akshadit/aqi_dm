# AirInsight: API-Based Air Quality Data Mining, Pollution Pattern Analysis and Prediction System

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/Storage-SQLite3-green.svg)](https://www.sqlite.org/)
[![API](https://img.shields.io/badge/API-Open--Meteo-teal.svg)](https://air-quality-api.open-meteo.com/)

---

## 1. Abstract
**AirInsight** is an end-to-end environmental data mining and pattern discovery system designed to process multi-pollutant atmospheric telemetry acquired from real-world telemetry APIs. Unlike superficial dashboards that merely display raw numbers, AirInsight implements a rigorous data mining pipeline consisting of **data acquisition, quality engineering, missing value imputation, IQR-based outlier capping, StandardScaler normalization, unsupervised clustering (K-Means), supervised health-tier classification (Decision Trees), inter-pollutant association rule discovery (Apriori), and chronological trajectory modeling (Ordinary Least Squares Linear Regression)**. Built with Python, Scikit-learn, Mlxtend, and Streamlit, AirInsight provides university students, researchers, and municipal stakeholders with actionable intelligence regarding atmospheric pollution signatures across major Indian urban centers (Bengaluru, Delhi, Mumbai, Chennai, Hyderabad, and Kolkata) and any dynamically discoverable global city.

---

## 2. Introduction
Air pollution represents one of the most critical environmental health risks in modern urbanized societies. The World Health Organization (WHO) attributes millions of premature deaths annually to atmospheric fine particulate matter ($PM_{2.5}$) and gaseous combustion byproducts ($NO_2$, $SO_2$, $CO$, and $O_3$). Traditional air quality monitoring platforms often function solely as visual meters, lacking the analytical machinery to discover latent patterns, identify pollution archetypes, deduce multi-pollutant co-occurrences, or extrapolate short-term directional trends.

**AirInsight** bridges this gap by applying formal **Data Mining and Knowledge Discovery in Databases (KDD)** methodologies to real-time atmospheric measurements. The platform integrates directly with the **Open-Meteo Air Quality API** and **Open-Meteo Geocoding API** to fetch continuous hourly records, isolates observed historical ground truths from future projections, and executes specialized data mining algorithms to extract actionable insights.

---

## 3. Problem Statement
Contemporary air quality platforms face several critical shortcomings:
1. **Passive Visualization vs. Pattern Discovery:** Existing tools plot simple line charts but fail to categorize pollution events into statistical archetypes or extract rule-based dependencies between distinct chemical species.
2. **Data Quality Deficits:** Real-world API sensor feeds frequently contain transmission drops, sensor saturation spikes, and telemetry gaps. Naive zero-imputation introduces severe statistical distortions (treating missing readings as pure air).
3. **Target Leakage in Machine Learning:** Many student and academic projects improperly use the calculated AQI metric as an input feature to predict AQI categories, introducing artificial 100% accuracy through target leakage.
4. **Lack of Provenance:** Observed historical records are frequently conflated with forecast approximations without clear demarcation of uncertainty.

---

## 4. Objectives
- **Data Ingestion & Persistence:** Ingest multi-parameter hourly air pollution metrics from Open-Meteo APIs into a structured SQLite repository with strict duplicate prevention.
- **Data Quality Pipeline:** Develop a robust preprocessing pipeline handling missing data via temporal propagation, removing exact duplicates, capping sensor spikes via $1.5 \times IQR$ bounds, and scaling features via $Z$-score normalization.
- **Unsupervised Pattern Discovery:** Group multidimensional pollution states using **K-Means Clustering** with Elbow inertia analysis, Silhouette scoring, and 2D PCA projection.
- **Supervised Classification:** Train an interpretable **Decision Tree Classifier** mapping pollutant mixtures to official EPA AQI tiers without target leakage.
- **Association Rule Mining:** Discover frequent inter-pollutant associations using the **Apriori Algorithm**, evaluating Support, Confidence, and Lift.
- **Trajectory Modeling:** Analyze chronological trends using **Linear Regression**, computing drift rates, MAE, and RMSE.
- **Interactive Academic Portal:** Provide a modern, responsive, 8-module Streamlit interface with CSV data exports and automated report generation.

---

## 5. Existing System vs. Proposed System

| Dimension | Existing Systems (Standard Dashboards) | Proposed System (AirInsight) |
| :--- | :--- | :--- |
| **Data Ingestion** | Static CSV or single-point polling | Live Open-Meteo REST API + Geocoding resolution + SQLite persistence |
| **Missing Data** | Ignored or silently imputed with zero | Temporal forward/backward fill per city + median backup (Zero-fill avoided) |
| **Outliers** | Unfiltered or arbitrarily deleted | Statistically audited via $1.5 \times IQR$ bounds with Winsorization capping |
| **Clustering** | None | K-Means with Elbow inertia curve, Silhouette metrics, and 2D PCA projection |
| **Classification** | Hardcoded lookup tables | Supervised Decision Tree without target leakage + live manual simulator |
| **Rule Discovery** | None | Apriori association rules with Support, Confidence, and Lift metrics |
| **Trend Modeling** | Naive visual lines | OLS Linear Regression with train/test splits, slope drift rate, MAE, and RMSE |
| **Academic Reports** | Manual screenshot compilation | Automated downloadable academic laboratory experimental audit reports |

---

## 6. System Architecture

```
                       ┌────────────────────────────────────────┐
                       │           External API Tier            │
                       │   • Open-Meteo Air Quality REST API    │
                       │   • Open-Meteo Geocoding Search API    │
                       └───────────────────┬────────────────────┘
                                           │ JSON Telemetry
                                           ▼
                       ┌────────────────────────────────────────┐
                       │          Data Collection Tier          │
                       │      api/air_quality_api.py            │
                       │      api/geocoding_api.py              │
                       │      data/collector.py                 │
                       └───────────────────┬────────────────────┘
                                           │ Normalized Records
                                           ▼
                       ┌────────────────────────────────────────┐
                       │          Storage & Cache Tier          │
                       │      SQLite Database (airinsight.db)   │
                       │   - cities                             │
                       │   - air_quality_records                │
                       │   - mining_results                     │
                       └───────────────────┬────────────────────┘
                                           │ SQL Query / Pandas Extraction
                                           ▼
                       ┌────────────────────────────────────────┐
                       │        Preprocessing & Quality         │
                       │        data/preprocessing.py           │
                       │   • Duplicate elimination              │
                       │   • Temporal forward/back fill         │
                       │   • IQR outlier Winsorization capping  │
                       │   • StandardScaler Z-score scaling     │
                       └───────────────────┬────────────────────┘
                                           │ Clean Feature Matrix (X)
                                           ▼
        ┌──────────────────────────────────┴──────────────────────────────────┐
        │                                                                     │
        ▼                                                                     ▼
┌─────────────────────────┐                                       ┌─────────────────────────┐
│   K-Means Clustering    │                                       │ Decision Tree Classifier│
│   algorithms/           │                                       │ algorithms/             │
│     clustering.py       │                                       │   classification.py     │
│ • Elbow Inertia & Sil.  │                                       │ • EPA Tier Classification│
│ • 2D PCA Dimensionality │                                       │ • Zero Target Leakage   │
│ • Archetype Attribution │                                       │ • Confusion Matrix / F1 │
└──────────────┬──────────┘                                       └───────────┬─────────────┘
               │                                                              │
               ▼                                                              ▼
┌─────────────────────────┐                                       ┌─────────────────────────┐
│ Apriori Rule Mining     │                                       │  Linear Trend Regression│
│ algorithms/             │                                       │  algorithms/            │
│   association_rules.py  │                                       │    regression.py        │
│ • Categorical Binning   │                                       │ • Chronological OLS Fit │
│ • Support, Conf, Lift   │                                       │ • Slope Drift (Rate/Day)│
│ • Natural Language Exp. │                                       │ • MAE & RMSE Metrics    │
└──────────────┬──────────┘                                       └───────────┬─────────────┘
               │                                                              │
               └───────────────────────────┬──────────────────────────────────┘
                                           │ Visual Figures & Formatted Tables
                                           ▼
                       ┌────────────────────────────────────────┐
                       │          Presentation Tier             │
                       │       Streamlit 8-Module Web UI        │
                       │       visualizations/charts.py         │
                       │       visualizations/reports.py        │
                       └────────────────────────────────────────┘
```

---

## 7. Mathematical Formulations of Implemented Algorithms

### 7.1. Interquartile Range (IQR) Outlier Capping
For each pollutant feature vector $x$:
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Lower Bound} = \max(0, Q_1 - 1.5 \times \text{IQR})$$
$$\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$
Values exceeding $\text{Upper Bound}$ or falling below $\text{Lower Bound}$ are capped (Winsorized) to preserve sample size while eliminating extreme sensor anomalies.

### 7.2. Feature Normalization (StandardScaler)
Standardizes each pollutant feature to mean $\mu = 0$ and standard deviation $\sigma = 1$:
$$z = \frac{x - \mu}{\sigma}$$

### 7.3. Algorithm 1: K-Means Clustering
Partitions $n$ observations into $k$ clusters $S = \{S_1, S_2, \dots, S_k\}$ minimizing the Within-Cluster Sum of Squares (Inertia):
$$\text{Inertia} = \sum_{i=1}^{k} \sum_{x \in S_i} \| x - \mu_i \|^2$$
Where $\mu_i$ is the centroid of cluster $S_i$. Optimal $k$ is analyzed via the Elbow Curve and Silhouette Coefficient:
$$s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$$

### 7.4. Algorithm 2: Decision Tree Classification
Splits feature space using the **Gini Impurity** metric:
$$I_G(p) = 1 - \sum_{i=1}^{J} p_i^2$$
Where $p_i$ is the probability of class $i$ at a given node. The model is evaluated on holdout test partitions using:
$$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}, \quad F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 7.5. Algorithm 3: Apriori Association Rule Mining
For an itemset $A \Rightarrow B$:
$$\text{Support}(A \Rightarrow B) = P(A \cup B) = \frac{\text{Count}(A \cup B)}{N}$$
$$\text{Confidence}(A \Rightarrow B) = P(B \mid A) = \frac{\text{Support}(A \cup B)}{\text{Support}(A)}$$
$$\text{Lift}(A \Rightarrow B) = \frac{\text{Confidence}(A \Rightarrow B)}{\text{Support}(B)} = \frac{P(A \cup B)}{P(A) \cdot P(B)}$$
- $\text{Lift} = 1$: $A$ and $B$ are statistically independent.
- $\text{Lift} > 1$: Strong positive dependency (co-occurrence occurs significantly above chance).

### 7.6. Algorithm 4: Ordinary Least Squares (OLS) Linear Regression
Models the linear temporal drift of pollutant concentration $y$ over elapsed hours $t$:
$$y(t) = \beta_0 + \beta_1 t + \epsilon$$
$$\beta_1 = \frac{\sum_{i=1}^{n} (t_i - \bar{t})(y_i - \bar{y})}{\sum_{i=1}^{n} (t_i - \bar{t})^2}, \quad \beta_0 = \bar{y} - \beta_1 \bar{t}$$
Evaluated using Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE):
$$\text{MAE} = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|, \quad \text{RMSE} = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$$

---

## 8. Database Schema Architecture

The SQLite database (`database/airinsight.db`) is structured with foreign keys and unique constraints:

```sql
-- Cities Registry
CREATE TABLE cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    country TEXT NOT NULL
);

-- Air Quality Hourly Records
CREATE TABLE air_quality_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    pm2_5 REAL,
    pm10 REAL,
    co REAL,
    no2 REAL,
    so2 REAL,
    o3 REAL,
    dust REAL,
    european_aqi REAL,
    us_aqi REAL,
    data_source TEXT NOT NULL,
    record_type TEXT NOT NULL, -- 'observed' or 'forecast'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE,
    UNIQUE(city_id, timestamp, record_type, data_source)
);

-- Mining Run Artifacts & Logs
CREATE TABLE mining_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm TEXT NOT NULL,
    city_id INTEGER,
    result TEXT NOT NULL, -- JSON formatted metrics & parameters
    execution_timestamp TEXT NOT NULL,
    FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE SET NULL
);
```

---

## 9. Installation & Execution Guide

### 9.1. System Requirements
- Windows 10/11, macOS, or Linux
- Python 3.11, 3.12, or 3.13

### 9.2. Setup & Execution Instructions (Windows CMD / PowerShell)

1. Open PowerShell or Command Prompt in the project folder:
   ```powershell
   cd c:\Users\aksha\OneDrive\Desktop\Projects\aqi_dm
   ```

2. (Optional) Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Run the automated unit test suite to verify module integrity:
   ```powershell
   python -m unittest discover -s tests -p "test_*.py"
   ```

#### Mode A: Launch Modern Web Application (Recommended)
Launch the modern full-stack FastAPI + Responsive Environmental Analytics web interface:
```powershell
python server.py
```
Open your browser at:
- **Web Dashboard:** `http://localhost:8000`
- **Interactive REST API Documentation (Swagger):** `http://localhost:8000/docs`

#### Mode B: Launch Streamlit Dashboard
```powershell
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 10. Project Demonstration Script (Viva / Faculty Presentation)

Use the following 7-step sequence when demonstrating AirInsight to an examiner or faculty guide:

1. **Step 1: Introduction (Page 1 - Overview)**
   - *"Good morning, examiners. AirInsight is an API-based air quality data mining and pattern discovery system. As shown here on the Overview page, our database is actively tracking the 6 core demonstration cities: Bengaluru, Delhi, Mumbai, Chennai, Hyderabad, and Kolkata. Each card displays real-time US EPA AQI and chemical pollutant breakdowns."*

2. **Step 2: Live Ingestion & Geocoding (Page 2 - Live Data Explorer)**
   - *"On Page 2, we interface with the Open-Meteo Air Quality REST API. When I click 'Fetch Live for City', the system polls real-time hourly telemetry without fabricating data. Notice the expander: using the Open-Meteo Geocoding API, we can search any new city (e.g. Pune or London), resolve its coordinates, and register it dynamically."*

3. **Step 3: Quality Engineering (Page 3 - Data Preprocessing)**
   - *"Data mining depends critically on data quality. On Page 3, we execute our Pandas preprocessing pipeline. Notice that we never replace missing values with zero—which would falsely indicate pure air—but apply time-series forward and backward propagation. We also run an Interquartile Range ($1.5 \times IQR$) detection to identify sensor saturation spikes and cap them through Winsorization."*

4. **Step 4: Unsupervised Clustering (Page 4 - K-Means Clustering)**
   - *"On Page 4, we execute our first mining algorithm: K-Means. We compute the Elbow Curve plotting Inertia against $k$ to identify optimal clustering. We scale all 6 pollutants using StandardScaler and project the multidimensional clusters onto a 2D PCA space. Notice that our system dynamically derives cluster archetypes—such as 'Combustion & Traffic Dust' vs 'Clean Ambient Air'—based on measured chemical levels rather than hardcoding assumptions."*

5. **Step 5: Supervised Classification (Page 5 - Decision Tree)**
   - *"On Page 5, we train a Decision Tree Classifier. Crucially, we prevent target leakage: AQI is withheld from the input feature matrix $X$, and the tree learns the non-linear boundaries mapping pollutant mixtures to EPA health tiers. We evaluate accuracy, weighted precision, recall, and the confusion matrix. Below, we can use the interactive simulator sliders to test custom pollutant values and observe real-time inference."*

6. **Step 6: Association Rule Mining (Page 6 - Apriori)**
   - *"On Page 6, we uncover latent co-occurrences using Apriori. We discretize continuous pollutants into Low, Medium, and High intervals based on WHO standards. By tuning Minimum Support and Confidence, the algorithm discovers rules such as: 'IF PM2.5 is High AND PM10 is High, THEN NO2 is High' with Lift $> 1.5x$, confirming strong positive dependence above random chance."*

7. **Step 7: Trajectory Analysis & Report Generation (Pages 7 & 8)**
   - *"On Page 7, we fit Ordinary Least Squares Linear Regression over chronological observations to estimate the drift rate (slope per day), accompanied by MAE and RMSE metrics. Finally, on Page 8, examiners can download raw and cleaned datasets as CSV, query execution logs from SQLite, or generate and download a formal laboratory experimental project report."*

---

## 11. Limitations & Future Enhancements

### Limitations
- **Atmospheric Physics:** Linear regression models empirical trajectory drift; it does not replace atmospheric dispersion models (AERMOD, WRF-Chem) that simulate wind vectors and boundary layer height.
- **API Station Density:** Open-Meteo utilizes ECMWF and CAMS reanalysis grids ($0.25^\circ \times 0.25^\circ$ resolution), which represent regional atmospheric averages rather than hyper-local street-corner microclimates.

### Future Enhancements
- **Spatial Kriging & Heatmaps:** Implementing geospatial interpolation (Ordinary Kriging) to visualize continuous pollution heatmaps between monitoring points.
- **Deep Sequence Models:** Introducing Long Short-Term Memory (LSTM) recurrent neural networks or Gated Recurrent Units (GRU) to model seasonal lag structures.
- **Mobile Push Alerts:** Integrating automated threshold alerting via Webhook or SMS when EPA 'Unhealthy' breakpoints are exceeded.

---

## 12. References & Academic Benchmarks
1. **US Environmental Protection Agency (EPA):** *Technical Assistance Document for the Reporting of Daily Air Quality – the Air Quality Index (AQI)*, EPA-454/B-18-007, 2018.
2. **Han, J., Kamber, M., & Pei, J.:** *Data Mining: Concepts and Techniques (3rd Edition)*, Morgan Kaufmann Publishers, 2011.
3. **Agrawal, R., & Srikant, R.:** *Fast Algorithms for Mining Association Rules in Large Databases*, Proceedings of the 20th International Conference on Very Large Data Bases (VLDB), 1994.
4. **Open-Meteo Documentation:** *Open-Source Weather & Air Quality API Specifications*, [https://open-meteo.com/en/docs/air-quality-api](https://open-meteo.com/en/docs/air-quality-api), 2024.
5. **Central Pollution Control Board (CPCB) India:** *National Ambient Air Quality Standards (NAAQS)*, Gazette of India, 2009.

