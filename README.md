# 🌍 AI-Powered Climate Risk Intelligence Platform

> A production-grade data engineering project that ingests real-time global climate data, scores climate risk across 12 major cities using a rule-based AI engine, and surfaces insights through an interactive dashboard and automated PDF reports.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Project Overview

This platform answers a critical humanitarian question:
**Which cities around the world face the highest climate risk — and why?**

It combines real meteorological data, World Bank climate indicators, and a
rule-based scoring engine to generate flood, drought, heatwave, and air
quality risk scores for 12 global cities — updated on demand.

---

## 🏗️ Architecture---

## 📊 Features

- **Real-time data ingestion** from Open-Meteo (weather) and World Bank (climate indicators)
- **PostgreSQL data warehouse** with 5 normalized tables
- **Rule-based risk scoring engine** producing flood, drought, heatwave and air quality scores
- **Interactive Streamlit dashboard** with world map, radar charts, and forecast charts
- **Automated PDF reports** with executive summary and city-level profiles
- **Global coverage** — 12 cities across 6 continents
- **Claude API ready** — swap in AI scoring with one config change

---

## 🌍 Cities Covered

| City | Country | Continent |
|------|---------|-----------|
| Nairobi | Kenya | Africa |
| Lagos | Nigeria | Africa |
| Cairo | Egypt | Africa |
| Mumbai | India | Asia |
| Jakarta | Indonesia | Asia |
| Dhaka | Bangladesh | Asia |
| Karachi | Pakistan | Asia |
| Beijing | China | Asia |
| São Paulo | Brazil | South America |
| New York | USA | North America |
| London | UK | Europe |
| Sydney | Australia | Oceania |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 16+
- PowerShell (Windows)

### Installation

```bash
# Clone the repo
git clone https://github.com/mbuguakevvz/climate-risk-platform.git
cd climate-risk-platform

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
copy config\.env.example config\.env

# Edit config/.env with your values
# DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```

### Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE climate_risk_db;"

# Create all tables
python database/schema.py

# Seed regions
python database/loader.py
```

### Run the Pipeline

```bash
# Ingest real-time data
python ingestion/open_meteo_fetcher.py
python ingestion/worldbank_fetcher.py

# Run risk scoring engine
python ai_engine/risk_scorer.py

# Launch dashboard
streamlit run dashboard/app.py

# Generate PDF report
python reports/pdf_generator.py
```

---

## 📁 Project Structure---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy |
| Weather API | Open-Meteo (free, no key) |
| Climate Data | World Bank API (free) |
| Dashboard | Streamlit + Plotly |
| PDF Reports | ReportLab |
| AI Engine | Rule-based (Claude API ready) |
| Logging | Loguru |

---

## 🔮 Roadmap

- [ ] Integrate Claude API for natural language risk summaries
- [ ] Add Apache Airflow for automated daily pipeline runs
- [ ] Deploy dashboard to Streamlit Cloud
- [ ] Add email alert system for CRITICAL risk cities
- [ ] Expand to 50 cities
- [ ] Add historical trend analysis (5-year view)

---

## 👤 Author

**Kevin Mbugua**
- GitHub: [@mbuguakevvz](https://github.com/mbuguakevvz)
- Built as part of a data engineering portfolio project

---

## 📄 License

MIT License — free to use, modify, and distribute.