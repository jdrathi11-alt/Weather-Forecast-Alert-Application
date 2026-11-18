# The Complete Project Guide — Weather Forecast & Alert Application

This document covers all 14 requested sections in order. It is written so a
student can follow it step-by-step, and an interviewer can see the reasoning
behind every decision.

---

## 1️⃣ PROJECT EXPLANATION

### Simple explanation
A weather app that asks "what's the weather in this city, and should I warn
anyone about it?" It pulls live weather data from a public website (OpenWeatherMap),
checks it against rules like "warn if rain chance > 50%", prints a summary,
draws charts, saves a report, and can email someone when something dangerous
is coming.

### Technical explanation
The application is a **data pipeline**: ingest (HTTP REST API or local JSON),
normalise (one internal schema), transform (Pandas groupby/agg), evaluate (pure
rule functions), present (console, charts, CSV, TXT, JSON, optional Streamlit),
and notify (optional SMTP). It is modular so each stage can be tested and
swapped independently.

### What problem does it solve?
* People and businesses make decisions without seeing weather risk early.
* Raw weather APIs return complex JSON; nobody reads 40 forecast slots raw.
* Alerts must be **rule-based, repeatable, auditable** — not gut feel.

### Who uses it?
* **Travelers** — rain/storm alerts for packing and route changes.
* **Farmers** — frost, rain-window and humidity (mould/fungal risk) alerts.
* **Logistics** — wind/ice/storm alerts for fleet scheduling.
* **Event planners** — rain probability and heat index for outdoor events.
* **Retail/energy** — temperature bands for demand forecasting.

### How weather apps use APIs
1. App sends an HTTPS GET request with a city name + API key.
2. Provider returns JSON: current conditions + forecast slots.
3. App parses JSON, converts units (Kelvin→°C, m/s→km/h), stores it.
4. App applies logic (rules, averages, trends) and shows results.

### How alerts are generated
Each rule is a pure function: `f(weather_slot) -> alert | None`. Rules read
thresholds from config. The engine evaluates current conditions + forecast
window, deduplicates (same type+day → one alert), sorts by severity
(CRITICAL > WARNING > INFO), and outputs to console, report, CSV, email.

### Workflow
```
user enters city → API/simulation fetch → JSON parsed → Pandas analysis
→ forecast summary → alert condition check → display output → save report
```

---

## 2️⃣ TECH STACK OPTIONS

| | Option A: Easy | Option B: Intermediate | Option C: Advanced |
|---|---|---|---|
| Tools | Python stdlib only (json, urllib, csv, datetime) | Python + requests + pandas + matplotlib + python-dotenv | B + Streamlit + SQL + scheduled runs (cron/GitHub Actions) + email/SMS |
| Difficulty | Beginner (1-2 days) | Intermediate (3-5 days) | Advanced (1-2 weeks) |
| Data source | Hard-coded sample JSON | OpenWeatherMap API OR sample JSON | API + database + multi-city monitoring |
| Output | Terminal text + CSV | Terminal + CSV + charts + report.txt + JSON | Web dashboard + email alerts + DB history + scheduler |
| Best for | Learning basics | Course project / GitHub proof | Portfolio capstone |

### Recommended for students: Option B
* Shows the **full stack of employable skills** (API, JSON, Pandas, charts,
  reports) without needing infra.
* Runs in two modes: **live** (API key) and **simulation** (sample data) — so
  you can demo even without internet/key.
* Upgrades to Option C are one optional file away (`dashboard.py`, `notify.py`).

### Libraries used in Option B
* `requests` — HTTP calls
* `pandas` — dataframes, aggregation
* `matplotlib` — charts
* `python-dotenv` (optional) — secret loading (stdlib fallback included)
* `argparse`, `csv`, `json`, `unittest` — stdlib, zero install

---

## 3️⃣ PROJECT ARCHITECTURE

### Inputs
* **City name** (CLI arg or prompt)
* **API key** (`.env` / env var, never hard-coded)
* **Alert thresholds** (config.py; overridable via CLI flags)

### Processing
1. `weather_client.py` — HTTP GET /weather + /forecast, or read sample JSON
2. JSON response parsing & normalisation (units, ISO times)
3. `analyzer.py` — Pandas DataFrame, daily aggregation, insights
4. `alerts.py` — 6 rule functions, dedupe, severity sort

### Outputs
* Current weather (console)
* Forecast summary (daily table, console + CSV)
* Alert messages (console, CSV, TXT, email)
* Charts (3 PNGs)
* Saved report (`reports/latest_report.txt`, timestamped variants)

### Text architecture diagram
See [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — full ASCII diagram with
module responsibilities, data flow table, interview talking points, and how
this scales to a production system.

### Data flow explanation
Every stage has ONE job and a clean interface: data layer returns a dict;
analyzer returns DataFrames; alerts returns alert dicts; visualization saves
PNGs; report writes files. Nothing is global; thresholds come from config.

---

## 4️⃣ IMPLEMENTATION PLAN (10 phases)

**Phase 1 — Setup**
Do: install Python, create venv, install deps (`pip install -r requirements.txt`).
Why: isolation prevents "works on my machine" bugs.
Output: `.venv` created; `pip list` shows deps.
Mistakes: skipping venv; using `python` vs `python3` confusion; installing
globally instead of in venv.

**Phase 2 — Project folder creation**
Do: create the folder structure (README § Folder structure).
Why: convention over configuration; GitHub reviewers expect structure.
Output: empty folders + `.gitkeep`.
Mistakes: dumping everything in one folder; committing junk files.

**Phase 3 — API key setup**
Do: sign up at openweathermap.org, generate key, put in `.env`, keep
`.env.example` as template.
Why: secrets must never be in git history.
Output: `.env` exists, is gitignored.
Mistakes: pasting key into code; committing `.env`; not activating the key
(email confirmation); using key before it's active.

**Phase 4 — Weather data fetching**
Do: `weather_client.py` with `requests.get` + timeout + error mapping.
Why: network code fails; friendly errors make debugging 10× faster.
Output: `get_weather()` returns dict.
Mistakes: no timeout; no status-code handling; not handling 401/404;
ignoring SSL/proxy issues.

**Phase 5 — JSON data parsing**
Do: `_norm_current` / `_norm_forecast_item` produce one internal schema.
Why: normalisation decouples the rest of the app from API changes.
Output: dict with temp, humidity, wind, weather, pop.
Mistakes: accessing nested keys without `.get()` defaults; forgetting
m/s→km/h or K→°C; assuming `weather[0]` always exists.

**Phase 6 — Forecast analysis**
Do: `analyzer.py` builds forecast DataFrame + daily summary + insights.
Why: raw 3-hourly slots are too noisy; daily summaries drive decisions.
Output: CSV + insights dict.
Mistakes: not sorting by time; not grouping by date; ignoring timezone (UTC).

**Phase 7 — Alert condition logic**
Do: pure rule functions + registry + dedupe + severity sort.
Why: pure functions are unit-testable; rules change often.
Output: alert list with level/type/message/time.
Mistakes: mixing rules with I/O; no dedupe (spam alerts); hard-coded
thresholds in logic.

**Phase 8 — Visualization**
Do: 3 charts (temperature, rain+humidity, conditions) with Agg backend.
Why: charts communicate faster than tables; Agg works headless.
Output: PNGs in `images/`.
Mistakes: forgetting `matplotlib.use("Agg")` on servers; unreadable axis
labels; not closing figures (memory leak).

**Phase 9 — Report generation**
Do: `report.py` writes CSV + TXT + JSON; stable `latest_*` copies.
Why: artefacts = proof + audit trail.
Output: files in `outputs/` and `reports/`.
Mistakes: overwriting files (no timestamps); forgetting `encoding="utf-8"`;
no fallback when a file is empty.

**Phase 10 — GitHub upload**
Do: `git init`, commit structure first, add README, push.
Why: history shows progress; README sells the project.
Output: public repo with README, sample outputs, screenshots.
Mistakes: committing `.env` or keys; huge binary dumps; no .gitignore;
one giant commit instead of a logical story.

---

## 5️⃣ FOLDER STRUCTURE (explained)

* `data/` — bundled sample data for simulation mode (`sample_weather.json`)
* `src/` — application code, one module per responsibility
* `outputs/` — generated CSVs + JSON bundle (gitignored; recreated each run)
* `images/` — charts (sample set committed for reviewers)
* `reports/` — generated TXT reports (gitignored; `latest_report.txt` for demo)
* `docs/` — this guide, architecture, sample outputs, screenshots checklist
* `tests/` — unit tests
* `README.md` — project front door
* `requirements.txt` — reproducible installs
* `.env.example` — secret template (committed)
* `.gitignore` — protects secrets + generated cruft
* `src/main.py` — CLI entry point

---

## 6️⃣ INSTALLATION GUIDE

### Python setup
Download from python.org (3.9+). Verify: `python --version` / `python3 --version`.

### Virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### API key storage (safe)
1. `cp .env.example .env` (Windows: `copy .env.example .env`)
2. Edit `.env`, paste your real key after `OPENWEATHER_API_KEY=`
3. `.gitignore` already contains `.env` — verify with `git status`
   (it should NOT appear)

### Never upload the key
* `.env` is in `.gitignore`
* If you ever commit it by mistake: rotate the key immediately at
  OpenWeatherMap, then `git filter-repo` / BFG to scrub history
* Use `.env.example` with placeholder values only

---

## 7️⃣ FULL PROJECT CODE

The complete, beginner-friendly, modular, commented, executable code is in
the repo:

* `src/config.py` — settings, thresholds, .env loader
* `src/weather_client.py` — live API + simulation data layer
* `src/analyzer.py` — Pandas analysis
* `src/alerts.py` — rule engine (storm, heat, cold, rain, humidity, wind)
* `src/visualization.py` — charts
* `src/report.py` — CSV/TXT/JSON artefacts
* `src/notify.py` — optional email alerts
* `src/dashboard.py` — optional Streamlit dashboard
* `src/main.py` — CLI entry point
* `tests/test_weather_app.py` — 16 unit tests

All files are heavily commented ("why", not just "what") and run as-is.

---

## 8️⃣ VIRTUAL SIMULATION

### Why simulate
* No API key / no internet / quota limits / demos must be deterministic.

### How it works
`data/sample_weather.json` mirrors the OpenWeatherMap 5-day/3-hour schema.
`weather_client.get_weather()` returns simulation data in the same shape as
live data, so downstream code is identical.

### City-wise representation
Each record has: city, country, lat/lon, timezone, current conditions,
forecast slots with temp/feels/humidity/pressure/wind/weather/pop.

### Threshold checking
Rules read thresholds from `config.Thresholds` (or CLI overrides like
`--heat 30 --rain 0.3`). Each slot is checked; alerts deduped per day.

### Output reports
Console summary + CSV + TXT + JSON + charts — same artefacts as live mode.

### Real-life mapping
Simulation = offline demo/dev/test; live mode = production. The same code
serves both; only the data layer changes.

### Screenshots to capture
1. Project folder tree
2. Simulation terminal output
3. Current weather block
4. Daily forecast table
5. Alerts section
6. Generated CSVs opened in Excel/VS Code
7. The three charts
8. GitHub repo page

### What must NOT be uploaded
* `.env` (real key)
* Any file containing the key (including screenshots showing it)
* `__pycache__/`, `outputs/*`, `reports/*` (regenerable)

---

## 9️⃣ HOW TO RUN

```bash
# Activate venv first (see §6)

# Simulation mode (no key, offline, deterministic)
python src/main.py --city "London" --mode simulation

# Live mode (needs key in .env)
python src/main.py --city "Paris,FR" --mode live

# Override thresholds
python src/main.py --city "Delhi,IN" --heat 38 --rain 0.4

# Skip charts (fast)
python src/main.py --no-charts

# Force email alert even without CRITICAL/WARNING (needs SMTP in .env)
python src/main.py --email

# Streamlit dashboard
pip install streamlit
streamlit run src/dashboard.py -- --city "London" --mode simulation
```

### Expected terminal output
See `docs/sample_outputs/terminal_output_simulation.txt` (real run output:
current conditions, daily table, alert list, file paths).

### Generated report
`reports/latest_report.txt` + timestamped variants; `outputs/*.csv`,
`outputs/bundle_*.json`; `images/*.png`.

---

## 🔟 GITHUB UPLOAD STEPS

### Repo naming
* Name: `Weather-Forecast-Alert-Application`
* Description: "Python weather app: OpenWeatherMap API integration, rule-based
  alerts, Pandas analysis, Matplotlib charts, CSV/TXT/JSON reports, optional
  Streamlit dashboard & email alerts."
* Topics/tags: `python`, `openweathermap`, `api`, `pandas`, `matplotlib`,
  `automation`, `alerts`, `streamlit`, `data-analysis`, `student-project`

### Steps
```bash
cd Weather-Forecast-Alert-Application
git init
git add .
git commit -m "feat: initial project - data layer, alerts, reports, charts"
git branch -M main
git remote add origin https://github.com/<username>/Weather-Forecast-Alert-Application.git
git push -u origin main
```

### Commit messages (use this pattern)
* `feat: add weather client with live + simulation modes`
* `feat: rule engine for heat/cold/rain/humidity/wind/storm`
* `feat: pandas daily summaries + insights`
* `feat: matplotlib charts for temp/rain/conditions`
* `feat: CSV/TXT/JSON report generation`
* `feat: optional SMTP email alerts`
* `feat: optional streamlit dashboard`
* `test: 16 unit tests for alert rules and pipeline`
* `docs: README, architecture, guide`
* `chore: gitignore, env example, requirements`

### Upload screenshots & outputs
Commit curated sample artefacts under `docs/sample_outputs/` and charts under
`images/`. Keep generated run artefacts (`outputs/`, `reports/`) out of git
via `.gitignore`.

### Key safety
* `.env` never committed; `.env.example` committed.
* Verify with `git status` before pushing; if a key leaks, rotate it immediately.

---

## 1️⃣1️⃣ README.md

The full README is at the repo root: `README.md`. It includes project overview,
problem statement, industry relevance, features table, tech stack, folder
structure, API setup, how to run, sample output, screenshots pointers, and
learning outcomes.

---

## 1️⃣2️⃣ PROOF-BUILDING STRATEGY (day-wise)

| Day | Goal | What to commit | Screenshot to save |
|---|---|---|---|
| 1 | Setup | folder structure, .gitignore, requirements.txt | folder tree, venv activated |
| 2 | API integration | weather_client.py (live+sim) | terminal showing data loaded |
| 3 | Parsing | analyzer.py, CSV outputs | forecast CSV in Excel/VS Code |
| 4 | Alert logic | alerts.py + tests | alerts section of terminal |
| 5 | Viz + reports | visualization.py, report.py | 3 PNG charts, report.txt |
| 6 | Docs + GitHub | README, guide, sample outputs | repo page with README |

Commit early and often — the history IS the proof of work.

---

## 1️⃣3️⃣ SCREENSHOTS / OUTPUTS CHECKLIST

1. Project folder tree (VS Code explorer)
2. Simulation-mode terminal output (full run)
3. Live-mode terminal output (if you get a key)
4. Current weather block
5. Daily forecast table
6. Alerts block
7. `outputs/forecast_*.csv` opened
8. `outputs/alerts_*.csv` opened
9. `images/temperature_trend.png`
10. `images/rain_humidity.png`
11. `images/weather_conditions.png`
12. GitHub repo page (README visible)
13. Unit test run output (16 tests passing)
14. Streamlit dashboard screenshot (optional)

Save them under `docs/screenshots/` and reference in README.

---

## 1️⃣4️⃣ INTERVIEW PREPARATION

### Q1. "Explain your project." (the one required question)
> "I built a Weather Forecast & Alert Application in Python. It has two modes:
> live mode, where it calls the OpenWeatherMap API for current conditions and
> a 5-day 3-hourly forecast, and simulation mode, where it reads bundled
> sample data so it works offline. The pipeline is: fetch → normalise →
> analyse with Pandas → evaluate six alert rules (storm, heat, cold, rain,
> humidity, wind) → present. Alerts are deduplicated per day and sorted by
> severity. Outputs are a console summary, three Matplotlib charts, CSV/JSON
> artefacts, and a text report; optional modules add email alerts via SMTP
> and a Streamlit dashboard. The design is modular — each stage is a separate
> module, rules are pure functions, thresholds live in config, and there are
> 16 unit tests. It's on GitHub with README, architecture docs, sample
> outputs, and screenshots."

### Q2. Why did you choose OpenWeatherMap?
> Free tier, global coverage, clean REST/JSON API, current + 5-day/3-hourly
> forecast, no credit card for the free tier, well-documented error codes.

### Q3. How do you handle API failures?
> Explicit status-code mapping (401 key, 404 city, 429 quota), timeouts,
> connection errors → friendly messages; simulation mode as automatic
> fallback so the demo never breaks.

### Q4. Explain your alert rule design.
> Pure functions `f(slot) -> alert|None` in a registry; dedupe by
> (type, day); severity ranking CRITICAL > WARNING > INFO; thresholds in
> config, overridable at runtime.

### Q5. How do you avoid spamming alerts?
> Dedupe same rule + same day; one alert per rule per day; email only for
> CRITICAL/WARNING; lookahead window bounded to 48h.

### Q6. What Pandas operations did you use?
> DataFrame construction, `groupby(date).agg(min/max/mean/sum/mode)`,
> boolean flags, idxmax/idxmin for extremes, rounding, CSV export.

### Q7. How do you keep the API key safe?
> `.env` + `.gitignore`; `.env.example` template; env var override; never
> printed in logs; rotation plan if leaked.

### Q8. How would you scale this?
> Scheduler (cron/Airflow), database for history, webhooks for alerts,
> multi-city config, caching, rate-limit handling, dashboard as ops screen.

### Q9. What did you test?
> Each rule function (boundary values), pipeline integration, dedupe,
> DataFrame construction, daily summary day count. 16 tests, stdlib only.

### Q10. Why is this project relevant to the role you want?
> Python dev: clean modular code, testing. API integration: REST, JSON,
> errors. Automation: artefacts, email, scheduling. Data analyst: Pandas,
> aggregation, visualisation. App dev: optional Streamlit UI.

### HR explanation (tell me about yourself / project)
Keep it 60-90 seconds: context (course project, wanted GitHub proof), what
you built (one sentence), how you built it (three pillars: API/data, logic/
rules, outputs/reports), and what you learned (testing, secrets, docs).

### Technical explanation (deep dive)
Be ready to draw the architecture diagram, explain normalisation, dedupe
logic, severity sort, the .env mechanism, and why pure functions make rules
testable. Know the OpenWeatherMap free-tier limits (60 calls/min, 1M/month)
and how you'd handle 429s (backoff + cache).
