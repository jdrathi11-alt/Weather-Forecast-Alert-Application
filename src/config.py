"""
config.py - central configuration for the Weather Forecast & Alert Application.

Responsibilities
----------------
1. Load the OpenWeatherMap API key from (in this order):
     a. the OPENWEATHER_API_KEY environment variable
     b. a ".env" file in the project root (NEVER committed to GitHub)
2. Hold the alert thresholds that decide when an alert is raised.
3. Hold API endpoints and default units.

Why a config module?
--------------------
Keeping every "setting" in ONE file means:
  - you never hunt through code to change a threshold,
  - secrets live in one place (.env), not scattered in logic,
  - the rest of the code stays clean and testable.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Project root = two levels up from this file (src/config.py -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = PROJECT_ROOT / "reports"
IMAGES_DIR = PROJECT_ROOT / "images"

# Make sure the output folders exist whenever the app runs
for _folder in (DATA_DIR, OUTPUTS_DIR, REPORTS_DIR, IMAGES_DIR):
    _folder.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# API settings
# ---------------------------------------------------------------------------
API_BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"

# OpenWeatherMap free plan: /forecast gives 3-hourly data, 5 days.
# We use it as "forecast" and also derive a per-day summary.
UNITS = "metric"            # metric=Celsius, imperial=Fahrenheit, standard=Kelvin
UNITS_LABEL = "°C" if UNITS == "metric" else "°F"


# ---------------------------------------------------------------------------
# .env loader (works even if python-dotenv is NOT installed)
# ---------------------------------------------------------------------------
def _load_dotenv_fallback(dotenv_path: Path) -> None:
    """
    Minimal .env reader: looks for lines like  KEY=VALUE  and exports them
    as environment variables, but ONLY if they are not already set.
    python-dotenv does this properly (quotes, exports, etc.); this fallback
    exists so the project runs on ANY machine with zero extra installs.
    """
    if not dotenv_path.exists():
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip("\"'")
                # Never overwrite a value that is already in the environment
                os.environ.setdefault(key, value)
    except OSError as exc:                      # pragma: no cover - cosmetic
        print(f"[config] could not read .env file ({exc})")


def load_api_key() -> str | None:
    """Return the API key from env / .env / None (simulation mode fallback)."""
    _load_dotenv_fallback(PROJECT_ROOT / ".env")
    # python-dotenv, when installed, is slightly more robust - try it too
    try:
        from dotenv import load_dotenv          # type: ignore
        load_dotenv(PROJECT_ROOT / ".env")     # noqa: F401
    except Exception:
        pass                                   # stdlib fallback already ran
    return os.environ.get("OPENWEATHER_API_KEY") or None


# ---------------------------------------------------------------------------
# Alert thresholds  (the "business rules" of the app)
# ---------------------------------------------------------------------------
class Thresholds:
    """
    Alert thresholds - tweak these to change when alerts fire.

    All temperatures are in the unit chosen above (Celsius by default).
    Humidity is a percentage (0-100). Wind speed is m/s.
    """

    HIGH_TEMP_C: float = 35.0      # temperature at/above this -> HEAT alert
    HIGH_TEMP_CRITICAL_C: float = 40.0   # at/above this -> CRITICAL heat alert
    LOW_TEMP_C: float = 0.0        # temperature at/below this -> COLD alert
    HUMIDITY_HIGH_PCT: float = 80.0    # humidity at/above this -> HUMIDITY alert
    HUMIDITY_LOW_PCT: float = 20.0     # humidity at/below this -> DRY air info
    WIND_KMH: float = 40.0           # wind at/above this (km/h) -> WIND alert
    RAIN_PROBABILITY: float = 0.5    # pop >= this -> RAIN alert
    STORM: bool = True               # True = raise CRITICAL for thunderstorms

    # How many forecast slots ahead we scan for alert conditions
    FORECAST_LOOKAHEAD_HOURS: int = 48

    def as_dict(self) -> dict:
        return {
            "high_temp_c": self.HIGH_TEMP_C,
            "high_temp_critical_c": self.HIGH_TEMP_CRITICAL_C,
            "low_temp_c": self.LOW_TEMP_C,
            "humidity_high_pct": self.HUMIDITY_HIGH_PCT,
            "humidity_low_pct": self.HUMIDITY_LOW_PCT,
            "wind_kmh": self.WIND_KMH,
            "rain_probability": self.RAIN_PROBABILITY,
            "forecast_lookahead_hours": self.FORECAST_LOOKAHEAD_HOURS,
        }


DEFAULT_CITY = "London"
