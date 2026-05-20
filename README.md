# 📦 Intelligent Warehouse Management System

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-KMeans-orange?logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Internship](https://img.shields.io/badge/Built%20During-TAFE%20Internship-blueviolet)

> A production-grade intelligent warehouse management system built during an internship at **TAFE (Tractors and Farm Equipment Limited)** — replacing a handwritten logbook + bi-monthly Excel transcription workflow with a real-time, data-driven Streamlit application featuring automated shelf placement recommendations and K-Means part classification.

---

## 🧠 Problem Statement

The engineering stores department at TAFE managed hundreds of spare parts through a **handwritten logbook system** — every part issue, restock, and location was recorded manually by hand. Every two months, a staff member would sit and manually retype everything from the notebook into an Excel sheet just to get a basic inventory view.

This caused:
- **No real-time visibility** — stock levels were always outdated between transcription cycles
- **No movement intelligence** — no way to know which parts were fast, slow, or rarely moving
- **No automated alerts** — low stock was only noticed when someone physically checked the shelf
- **Parts placed arbitrarily** — shelf locations were assigned once and never optimized
- **Hours wasted** — every two months, staff manually retyped handwritten records into Excel
- **Human error** — transcription mistakes between notebook and Excel were common

This system replaced the entire workflow — from handwritten logbook to a live, intelligent, data-driven application that updates in real time.

---

## 🔁 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit Frontend (app.py)                 │
│  Dashboard | Search & Issue | Add/Restock | Analytics   │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
  inventory.py     recommendation.py  scoring.py
  (CRUD ops)       (rank & rearrange)  (weighted score)
        │                │
        └────────┬───────┘
                 ▼
          data_handler.py
          (CSV read/write)
                 │
        ┌────────┴────────┐
        ▼                 ▼
   parts.csv        usage_log.csv
   restock_log.csv

┌─────────────────────────────────────────────────────────┐
│         warehouse_classification.ipynb                   │
│   K-Means Clustering → Fast / Slow / Rare labels        │
│   (run periodically to re-classify movement types)      │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ How the Scoring & Recommendation System Works

### Weighted Scoring Formula
```
score = (frequency × weight) - (days_inactive × decay)
```

| Movement Type | Weight | Decay |
|---|---|---|
| Fast Moving | 1.5× | 0.5 per day |
| Slow Moving | 1.0× | 0.3 per day |
| Rare Moving | 0.5× | 0.1 per day |

- **Higher score = closer shelf placement** (rank 1 = nearest to dispatch)
- Decay penalizes parts that haven't moved recently
- Parts are re-ranked and rearranged with one click

### K-Means Clustering (Notebook)
Parts are classified into 3 movement categories using K-Means (k=3) on:
- Average daily quantity sold
- Sale days per month
- Monthly average quantity
- Max single-day quantity

Validated using the **Elbow method** and **Silhouette score**.

---

## 📁 Project Structure

```
warehouse-management-system/
│
├── app.py                          # Main Streamlit application
├── inventory.py                    # Search, issue, restock, add parts
├── recommendation.py               # Rank parts & generate rearrangement suggestions
├── scoring.py                      # Weighted scoring formula
├── data_handler.py                 # CSV load/save utilities
│
├── warehouse_classification.ipynb  # K-Means clustering for movement classification
│
├── data/
│   ├── parts.csv                   # Parts master data (synthetic demo data)
│   ├── usage_log.csv               # Issue history log (synthetic demo data)
│   └── restock_log.csv             # Restock/purchase history (synthetic demo data)
│
├── requirements.txt
└── README.md
```

> ⚠️ **Note:** The data files contain **synthetic demo data** generated for demonstration purposes. No real company data is included in this repository.

---

## 🖥️ Application Features

### 📊 Dashboard
- Real-time **low stock alerts** — highlights parts below threshold
- **Top 5 most-used parts** at a glance

### 🔍 Search & Issue
- Search parts by ID or name
- Issue quantities with automatic stock decrement and usage log update

### 📥 Add / Restock
- Add new parts with location, threshold, and movement type
- Restock existing parts — all logged with timestamps

### 🔁 Recommendations
- One-click shelf rearrangement based on current scoring
- Shows direction of movement (UP / DOWN / NEW) for each part
- Apply changes updates all locations and ranks instantly

### 📈 Analytics
- **Monthly usage trends** by movement group or custom selection
- **Restock / purchase analytics** with monthly breakdown
- **Warehouse location map** — color-coded physical layout (Fast=Green, Slow=Amber, Rare=Gray)
- **Stock health dashboard** — visual progress bars with Critical / Low / Healthy status

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/sunilraj180805/warehouse-management-system.git
cd warehouse-management-system
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit App
```bash
streamlit run app.py
```

### 4. Run the Classification Notebook (Optional)
Open `warehouse_classification.ipynb` in Jupyter to re-classify parts into Fast/Slow/Rare categories based on usage history.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.8+ | Core language |
| Streamlit | Web application frontend |
| Pandas | Data manipulation and CSV management |
| Scikit-learn | K-Means clustering for part classification |
| Plotly | Interactive analytics charts |
| NumPy | Numerical operations |
| Matplotlib / Seaborn | Notebook visualizations |

---

## 📊 Sample Data

The `data/` folder contains **synthetic demo data** to let you explore all features immediately after cloning. The synthetic data mimics real warehouse patterns (usage frequency, restock cycles, movement types) without containing any proprietary information.

To start fresh with your own data:
```bash
rm data/parts.csv data/usage_log.csv data/restock_log.csv
```
The system will auto-create empty CSVs on first run.

---

## ⚠️ Limitations

- CSV-based storage — suitable for small-to-medium warehouses; scale to SQLite/PostgreSQL for larger deployments
- Single-user session; no authentication layer (can be added with `streamlit-authenticator`)
- K-Means classification requires sufficient usage history (minimum ~1 month of logs)

---

## 🔮 Future Scope

- Replace CSV storage with a proper database (SQLite / PostgreSQL)
- Add barcode scanning integration for real-time issue tracking
- Predictive restock alerts using time-series forecasting (Prophet / LSTM)
- Role-based access control for store managers vs. supervisors

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙋 Author

**Sunilraj D** — developed during internship at TAFE Ltd.
[GitHub](https://github.com/sunilraj180805)
