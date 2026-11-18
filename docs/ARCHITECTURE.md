# Project Architecture — Weather Forecast & Alert Application

## 1. High-level architecture diagram (text)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER / OPERATOR                                  │
│                                                                             │
│   inputs:  --city  "London"          --mode live|simulation                 │
│            API key in .env           thresholds in config.py                │
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
│                                                                              │
│   Console summary  ──► terminal (current weather, daily table, alerts)       │
│   images/*.png     ──► 3 charts (temperature, rain+humidity, conditions)     │
│   outputs/*.csv    ──► forecast + daily_summary + alerts CSV                 │
│   outputs/*.json   ──► machine-readable bundle (dashboard/BI input)          │
│   reports/*.txt    ──► full human-readable report                            │
│                                                                              │
│   OPTIONAL: src/notify.py  ──► email alert via SMTP when CRITICAL/WARNING    │
│   OPTIONAL: src/dashboard.py ─► Streamlit web UI (interactive)               │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 2. Data flow, step by step

| Step | What happens | Where in code |
|------|--------------|---------------|
| 1 | User passes `--city`, `--mode`, optional threshold overrides | `main.py` argparse |
| 2 | API key is loaded from env var or `.env` (never hard-coded) | `config.py: load_api_key()` |
| 3 | Data is fetched: LIVE = HTTP GET to OpenWeatherMap, SIM = `data/sample_weather.json` | `weather_client.py: get_weather()` |
| 4 | Raw JSON is normalised into one internal shape (km/h wind, ISO times) | `weather_client.py: _norm_*` |
| 5 | Pandas builds a tidy forecast DataFrame + daily summary + insights | `analyzer.py` |
| 6 | Each forecast slot is run through 6 pure rule functions; deduped by (type, day) | `alerts.py: evaluate()` |
| 7 | Alerts are sorted by severity (CRITICAL → WARNING → INFO) | `alerts.py: sort_alerts()` |
| 8 | Three Matplotlib charts are written to `images/` | `visualization.py` |
| 9 | CSV + TXT + JSON artifacts are written to `outputs/` and `reports/` | `report.py` |
| 10 | Console prints current weather, daily table, alert list | `main.py` |

## 3. Why this design (interview talking points)

* **Separation of concerns** — fetch / analyse / decide / present / persist are
  separate modules. You can swap OpenWeatherMap for another API by changing
  ONE file (`weather_client.py`).
* **Pure rule functions** — every alert rule takes a dict and returns an alert
  or `None`. No hidden state → trivially unit-testable (see `tests/`).
* **Two modes, one shape** — simulation mode returns the exact schema the API
  returns, so all downstream code is identical. This is how you demo a system
  when you have no key or no internet.
* **Config-driven thresholds** — business rules live in `config.py`, not
  scattered through logic. Changing a threshold is a one-line edit, no code
  change.
* **Artifacts over console** — everything is also saved as CSV/TXT/JSON/PNG.
  That is what makes the project *provable* on GitHub and *auditable* in a
  real operations team.

## 4. How it would scale to real life

* Replace `load_simulation()` with the same schema from a message queue
  (Kafka/SQS) fed by a weather vendor.
* Run `main.py` on a schedule (cron / GitHub Actions / Airflow) every hour.
* `notify.py` becomes a webhook dispatcher (Slack, PagerDuty, SMS via Twilio).
* `dashboard.py` becomes the ops screen; the JSON bundle is its data source.
* Thresholds move from `config.py` to a database table so non-engineers can
  tune alert rules without a deploy.
