# ⛈️ Weather Forecast & Alert Application

<p align="center">
  <b>Python · OpenWeatherMap API · Pandas · Rule-based Alerts · Matplotlib · Streamlit</b><br>
  <i>A complete, offline-capable weather pipeline built as a course project that doubles as proof of work for GitHub.</i>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#features">Features</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#outputs">Outputs</a> ·
  <a href="#documentation">Docs</a> ·
  <a href="#interview-prep">Interview Prep</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/tests-16%20passing-brightgreen" alt="Tests 16 passing">
  <img src="https://img.shields.io/badge/mode-live%20%7C%20simulation-orange" alt="Live or simulation mode">
  <img src="https://img.shields.io/badge/keys-never%20committed-red" alt="Keys never committed">
</p>

---

## 📌 Why this project exists

Weather data is public, rich and time-series shaped — a perfect teaching vehicle for
**API integration, JSON parsing, data analysis, rule engines, visualisation,
reporting and automation**. No professional hardware is required: the app runs
fully offline against bundled sample data, and fully online against a free API key.

Built as a course project that doubles as **proof of work for GitHub** —
suitable for Python Developer, API Integration, Automation, Data Analyst and
App Development roles.

---

## ✨ Features

| # | Feature | Where | Skill it proves |
|---|---------|-------|-----------------|
| 1 | Live API integration (OpenWeatherMap) | `src/weather_client.py` | HTTP, JSON, error handling |
| 2 | Simulation mode with bundled sample data | `data/sample_weather.json` | Works without external deps |
| 3 | Current weather + 5-day / 3-hourly forecast | `src/analyzer.py` | Data modelling |
| 4 | Rule-based alert engine (6 rules, severity levels) | `src/alerts.py` | Business logic, testing |
| 5 | Configurable thresholds | `src/config.py` | Maintainability |
| 6 | Pandas analysis + daily summaries | `src/analyzer.py` | Data analysis |
| 7 | 3 Matplotlib charts | `src/visualization.py` | Data visualisation |
| 8 | CSV + TXT + JSON reports | `src/report.py` | Automation, artefacts |
| 9 | Optional email alerts via SMTP | `src/notify.py` | Real automation |
| 10 | Optional Streamlit dashboard | `src/dashboard.py` | App development |
| 11 | 16 unit tests (stdlib `unittest`) | `tests/` | Engineering discipline |

---

## 🛠️ Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Language | **Python 3.9+** | Readable, industry-standard |
| HTTP | `requests` | De-facto API client |
| Data | `pandas` | DataFrames, aggregation, CSV export |
| Charts | `matplotlib` | Publication-quality PNGs |
| Secrets | `python-dotenv` (optional) | `.env` loading; stdlib fallback included |
| UI | `streamlit` (optional) | Web dashboard |
| Email | `smtplib` (stdlib) | Zero-dependency notifications |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER / OPERATOR                                  │
│   inputs:  --city "London"    --mode live|simulation    thresholds in config │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  main.py  (CLI entry point - orchestrates the 5 pipeline stages)             │
└───────┬───────────────┬───────────────┬───────────────┬──────────────┬───────┘
        │               │               │               │              │
        ▼               ▼               ▼               ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────┐
│ weather_     │ │ analyzer.py │ │ alerts.py   │ │visualization│ │ report.py  │
│ client.py    │ │ (Pandas)    │ │ (rule engine│ │ (Matplotlib)│ │ (artifacts)│
│              │ │             │ │  pure fns)  │ │             │ │            │
│ DATA LAYER   │ │ ANALYSIS    │ │ DECISION    │ │ PRESENTATION│ │ PERSISTENCE│
│              │ │             │ │             │ │             │ │            │
│ LIVE mode:   │ │ forecast_df │ │ 6 rules:    │ │ temp trend  │ │ forecast   │
│ GET /weather │ │ daily_df    │ │ storm       │ │ rain+humidity│ │ alerts CSV │
│ GET /forecast│ │ insights    │ │ heat        │ │ conditions  │ │ report.txt │
│              │ │             │ │ cold        │ │             │ │ bundle.json│
│ SIM mode:    │ │             │ │ rain        │ │             │ │            │
│ sample JSON  │ │             │ │ humidity    │ │             │ │            │
│              │ │             │ │ wind        │ │             │ │            │
└──────┬───────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬──────┘
       │                │               │               │              │
       └────────────────┴───────┬───────┴───────────────┴──────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUTS                                          │
│   Console summary  ──► terminal (current weather, daily table, alerts)       │
│   images/*.png     ──► 3 charts (temperature, rain+humidity, conditions)     │
│   outputs/*.csv    ──► forecast + daily_summary + alerts CSV                 │
│   outputs/*.json   ──► machine-readable bundle (dashboard/BI input)          │
│   reports/*.txt    ──► full human-readable report                            │
│   OPTIONAL: src/notify.py  ──► email alert via SMTP when CRITICAL/WARNING    │
│   OPTIONAL: src/dashboard.py ─► Streamlit web UI (interactive)               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Folder structure

```
Weather-Forecast-Alert-Application/
├── data/                  # bundled sample data (simulation source)
│   └── sample_weather.json
├── src/                   # application code (modular)
│   ├── config.py          #   API endpoints, thresholds, .env loader
│   ├── weather_client.py  #   live API + simulation data layer
│   ├── analyzer.py        #   pandas analysis, daily summaries
│   ├── alerts.py          #   pure rule functions + dedupe engine
│   ├── visualization.py   #   matplotlib charts
│   ├── report.py          #   CSV / TXT / JSON artefacts
│   ├── notify.py          #   optional SMTP email alerts
│   ├── dashboard.py       #   optional Streamlit UI
│   └── main.py            #   CLI entry point
├── tests/                 # zero-dependency unit tests
│   ├── test_weather_app.py
│   └── run_tests.py
├── outputs/               # timestamped CSVs + JSON bundle (gitignored)
├── reports/               # timestamped human-readable report (gitignored)
├── images/                # generated charts (committed sample set)
├── docs/                  # architecture, guide, sample outputs
├── .env.example           # template for secrets - NEVER commit .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚡ Quick start

```bash
# 1. Clone
git clone https://github.com/<your-username>/Weather-Forecast-Alert-Application.git
cd Weather-Forecast-Alert-Application

# 2. Virtual environment
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt

# 4a. SIMULATION mode (no key needed)
python src/main.py --city "London" --mode simulation

# 4b. LIVE mode (free key from https://openweathermap.org/api)
cp .env.example .env      # then paste your key into .env
python src/main.py --city "Paris,FR" --mode live

# 5. Tests
python tests/run_tests.py
```

### CLI flags

| Flag | Purpose |
|------|---------|
| `--city "Tokyo,JP"` | Any city, optional `,CC` country code |
| `--mode live\|simulation\|auto` | Force a mode (default `auto`) |
| `--heat 30` | Override high-temp threshold (°C) |
| `--rain 0.3` | Override rain-probability threshold (0–1) |
| `--no-charts` | Skip PNG generation (faster) |
| `--email` | Send email even for INFO-level alerts |

---

## 🖥️ Sample console output (simulation mode)

```
[1/5] Data loaded  : London (simulation mode)
[2/5] Analysed     : 43 forecast slots, 6 days
[3/5] Alerts       : 6 alert(s)  [CRITICAL: 1, WARNING: 5, INFO: 0]
[4/5] Charts       : 3 saved to images/
[5/5] Saved        : reports/report_20261118_162048.txt

CURRENT WEATHER - London, GB
  12.4°C (Overcast Clouds)  Feels 10.9°C
  Humidity 76%  |  Wind 5.4 km/h  |  Pressure 1012 hPa

ALERTS
  [CRITICAL] Thunderstorm alert (Nov 19 00:00)
  [WARNING]  Rain alert (Nov 18 18:00)
  [WARNING]  High humidity alert (Nov 18 21:00)
  ...
```

Full terminal capture: [`docs/sample_outputs/terminal_output_simulation.txt`](docs/sample_outputs/terminal_output_simulation.txt)

---

## 📊 Outputs

Every run produces timestamped artefacts:

| Type | Location |
|------|----------|
| Forecast CSV | `outputs/forecast_*.csv` |
| Daily summary CSV | `outputs/daily_summary.csv` |
| Alerts CSV | `outputs/alerts_*.csv` |
| JSON bundle | `outputs/bundle_*.json` |
| Human report | `reports/latest_report.txt` |
| Charts | `images/temperature_trend.png`, `rain_humidity.png`, `weather_conditions.png` |

---

## 🔒 Security

* The API key lives in `.env`, which is **gitignored**.
* `.env.example` (committed) shows the format with fake values.
* The app also reads `OPENWEATHER_API_KEY` from the environment.
* If a key is ever committed by mistake: rotate it at OpenWeatherMap **immediately**, then scrub history.

---

## 📖 Documentation

| Doc | What it covers |
|-----|----------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architecture + data flow |
| [`docs/GUIDE.md`](docs/GUIDE.md) | Complete 14-section project guide (explanation, tech stack options, implementation plan, install guide, simulation guide, run instructions, GitHub upload steps, proof plan, screenshots checklist, interview prep) |
| [`docs/INSTALL.md`](docs/INSTALL.md) | Step-by-step install + troubleshooting |
| [`docs/sample_outputs/`](docs/sample_outputs/) | Real terminal + report samples |

---

## 🧪 Testing

```bash
python tests/run_tests.py     # 16 tests, zero external dependencies
```

Covers: alert rules, boundary conditions, ETL, deduplication logic.

---

## 🎓 Learning outcomes

After completing this project you can: consume a REST API, parse and normalise
JSON, model time-series data with Pandas, design a rule engine, write pure
testable functions, generate charts, produce auditable artefacts, automate
notifications, keep secrets out of git, and explain the whole system in an
interview.

---

## 🎯 Interview prep

`docs/GUIDE.md` §14 contains 10 model answers, including the HR and Technical
versions of **"Explain your project."** Short version:

> *"I built a weather pipeline that pulls from OpenWeatherMap or a bundled
> simulation, analyses 5-day forecasts with Pandas, raises rule-based alerts
> with per-day deduplication, and outputs charts, CSVs, JSON and an optional
> Streamlit dashboard. I kept secrets out of git with `.env` + `.gitignore`,
> covered the logic with 16 unit tests, and made it run offline so demos never
> depend on a key or network."*

---

## 📄 License

MIT — free to use for learning and portfolios.

## Author

**Jayesh Rathi** — 3rd Year IT Student, Government College of Engineering, Amravati  
[LinkedIn](https://www.linkedin.com/in/jayesh-rathi-5ab8973b6) | [Email](mailto:jayeshrathinew@gmail.com)
