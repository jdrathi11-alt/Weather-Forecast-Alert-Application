# Installation Guide — step by step

## 1. Prerequisites
* Python 3.9+ (https://www.python.org/downloads/) — tick **"Add Python to PATH"** on Windows
* Git (https://git-scm.com/downloads)
* A free OpenWeatherMap API key (https://home.openweathermap.org/api_keys) — *optional*, simulation mode works without one

## 2. Get the code
```bash
git clone https://github.com/<your-username>/Weather-Forecast-Alert-Application.git
cd Weather-Forecast-Alert-Application
```

## 3. Create a virtual environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```
You'll see `(.venv)` at the start of your prompt. Leave it on for the rest of the steps.

## 4. Install dependencies
```bash
pip install -r requirements.txt
```

## 5. Configure the API key (live mode only)
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Then open `.env` in a text editor and replace `paste_your_api_key_here` with your real key:
```
OPENWEATHER_API_KEY=your_real_key_here
OPENWEATHER_UNITS=metric
```
That's it — the key is never typed into code, and `.env` is gitignored so it can never be pushed.

### Optional: email alerts
Add these lines to `.env` (Gmail: enable 2FA, then create an **App Password**):
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASS=your_app_password
ALERT_RECIPIENT=recipient@example.com
```
Then run with `--email` to send even when only INFO-level alerts fire.

## 6. Run it
```bash
python src/main.py --city "London" --mode simulation   # no key needed
python src/main.py --city "Paris,FR" --mode live       # needs key
python tests/run_tests.py                              # 16 unit tests
```

## 7. Optional extras
```bash
pip install streamlit
streamlit run src/dashboard.py -- --city "London" --mode simulation
```

## 8. Troubleshooting
| Problem | Fix |
|---|---|
| `python` not found | Use `python3` (Mac/Linux) or re-run installer with "Add to PATH" |
| HTTP 401 Invalid API key | Key not activated yet — click the email link, wait ~10 min |
| HTTP 404 city not found | Use `City,CC` format, e.g. `Paris,FR` |
| Proxy/connection errors | Use `--mode simulation` |
| Charts don't appear | Charts are saved to `images/`, not displayed — open the PNGs |
| Key accidentally committed | Rotate it at OpenWeatherMap immediately, then scrub history |
