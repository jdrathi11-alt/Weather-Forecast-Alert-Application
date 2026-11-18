"""
weather_client.py - data layer of the Weather Forecast & Alert Application.

Two operating modes
-------------------
1. LIVE mode   : calls the real OpenWeatherMap API (needs a free API key).
2. SIM mode    : reads `data/sample_weather.json` - no key, no internet,
                 fully deterministic output (perfect for demos, tests and
                 screenshots when you have no API key).

The rest of the app (alerts, reports, charts) does NOT care which mode was
used - both return the SAME internal data shape:

    {
      "city": str,
      "country": str,
      "lat": float, "lon": float,
      "timezone": str,
      "source": "api" | "simulation",
      "current": {dt, temp, feels_like, humidity, pressure,
                  wind_speed, visibility, weather, description},
      "forecast": [ {dt, temp, feels_like, humidity, pressure,
                     wind_speed, weather, description, pop}, ... ]
    }

`wind_speed` is normalised to km/h and `pop` is probability of precipitation
(0.0-1.0), matching the OpenWeatherMap schema.
"""

from __future__ import annotations

import json
import math
import random
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

import config


# ---------------------------------------------------------------------------
# Deterministic synthetic simulation (any city, no API key, no internet)
# ---------------------------------------------------------------------------
# A small table of well-known city coordinates so synthetic data looks real.
# If the city is unknown we fall back to a deterministic pseudo-random coord.
_KNOWN_CITIES = {
    "london": ("GB", 51.5074, -0.1278), "paris": ("FR", 48.8566, 2.3522),
    "new york": ("US", 40.7128, -74.0060), "tokyo": ("JP", 35.6895, 139.6917),
    "sydney": ("AU", -33.8688, 151.2093), "mumbai": ("IN", 19.0760, 72.8777),
    "berlin": ("DE", 52.5200, 13.4050), "singapore": ("SG", 1.3521, 103.8198),
    "delhi": ("IN", 28.6139, 77.2090), "dubai": ("AE", 25.2048, 55.2708),
    "cairo": ("EG", 30.0444, 31.2357), "sao paulo": ("BR", -23.5505, -46.6333),
}

_CONDITIONS = {
    "Clear": "clear sky", "Clouds": "scattered clouds", "Rain": "light rain",
    "Thunderstorm": "thunderstorm with rain", "Fog": "fog",
    "Snow": "light snow", "Drizzle": "light intensity drizzle",
}


def _synthesize(city: str) -> dict:
    """
    Build a deterministic 5-day/3-hourly dataset for ANY city name.

    Deterministic = same city -> same weather every run (seeded by city name),
    which is what you want for demos and screenshots. This is VIRTUAL
    SIMULATION data: it is NOT real weather and is labelled as such.
    """
    seed = zlib.crc32(city.lower().encode())
    rng = random.Random(seed)
    lookup = city.split(",")[0].strip().lower()
    country, lat, lon = _KNOWN_CITIES.get(lookup,
                                          ("XX", rng.uniform(-40, 55), rng.uniform(-180, 180)))
    base_temp = 8 + (seed % 28)                       # 8..35 C, per-city
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    def _slot(t: datetime) -> dict:
        hour = t.hour
        diurnal = 4 * math.sin((hour - 9) / 24 * 2 * math.pi)   # warmest ~15:00
        temp = round(base_temp + diurnal + rng.uniform(-1.5, 1.5), 1)
        # pick a condition with sensible weights
        cond = rng.choices(
            list(_CONDITIONS),
            weights=[30, 30, 15, 5, 5, 5 if temp <= 2 else 0, 10],
        )[0]
        if cond == "Snow" and temp > 2:
            cond = "Rain"
        wet = cond in ("Rain", "Thunderstorm", "Drizzle", "Snow")
        pop = (round(rng.uniform(0.5, 0.95), 2) if wet else round(rng.uniform(0, 0.2), 2))
        humidity = min(100, int(55 + rng.uniform(0, 35) + (10 if wet else 0)))
        wind = round(rng.uniform(1.0, 9.0) + (4.0 if cond == "Thunderstorm" else 0), 1)
        return {
            "dt": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "temp": temp, "feels_like": round(temp + rng.uniform(-1.5, 1.0), 1),
            "humidity": humidity, "pressure": int(rng.uniform(1005, 1025)),
            "wind_speed": _wind_to_kmh(wind), "weather": cond,
            "description": _CONDITIONS[cond], "pop": pop,
        }

    forecast = [_slot(now + timedelta(hours=3 * i)) for i in range(1, 41)]
    current = dict(forecast[0])
    current["dt"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    current["visibility"] = 2000 if forecast[0]["weather"] == "Fog" else int(rng.uniform(6000, 10000))

    return {
        "city": city.split(",")[0].title(), "country": country,
        "lat": round(lat, 3), "lon": round(lon, 3), "timezone": "SIM",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current": current, "forecast": forecast,
        "simulation_detail": f"synthetic data for '{city}' (seeded by city name - NOT real weather)",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ms_to_iso(ms: int | float) -> str:
    """Unix epoch (seconds or ms) -> UTC ISO string 'YYYY-MM-DDTHH:MM:SSZ'."""
    try:
        ts = int(ms)
        if ts > 10_000_000_000:          # milliseconds -> seconds
            ts //= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except (TypeError, ValueError, OSError):
        return str(ms)


def _ms_to_dt(ms: int | float) -> datetime:
    ts = int(ms)
    if ts > 10_000_000_000:
        ts //= 1000
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _wind_to_kmh(wind_speed_m_s: float) -> float:
    """OpenWeatherMap returns m/s; convert to km/h for readability."""
    return round(float(wind_speed_m_s) * 3.6, 1)


def _norm_current(raw: dict) -> dict:
    """Pull the fields we need out of the API's 'current'/'now' payload."""
    w = (raw.get("weather") or [{}])[0]
    return {
        "dt": _ms_to_iso(raw.get("dt")),
        "temp": round(raw.get("main", {}).get("temp", 0.0), 1),
        "feels_like": round(raw.get("main", {}).get("feels_like", 0.0), 1),
        "humidity": raw.get("main", {}).get("humidity", 0),
        "pressure": raw.get("main", {}).get("pressure", 0),
        "wind_speed": _wind_to_kmh(raw.get("wind", {}).get("speed", 0.0)),
        "visibility": raw.get("visibility", 0),
        "weather": w.get("main", "Unknown"),
        "description": w.get("description", ""),
    }


def _norm_forecast_item(item: dict) -> dict:
    w = (item.get("weather") or [{}])[0]
    return {
        "dt": _ms_to_iso(item.get("dt")),
        "temp": round(item.get("main", {}).get("temp", 0.0), 1),
        "feels_like": round(item.get("main", {}).get("feels_like", 0.0), 1),
        "humidity": item.get("main", {}).get("humidity", 0),
        "pressure": item.get("main", {}).get("pressure", 0),
        "wind_speed": _wind_to_kmh(item.get("wind", {}).get("speed", 0.0)),
        "weather": w.get("main", "Unknown"),
        "description": w.get("description", ""),
        "pop": float(item.get("pop", 0.0)),
    }


# ---------------------------------------------------------------------------
# LIVE mode
# ---------------------------------------------------------------------------
def fetch_live(city: str, api_key: str) -> dict:
    """
    Call OpenWeatherMap for CURRENT weather + 5-day/3-hour forecast.

    Endpoints used (free tier):
      /weather   -> current conditions
      /forecast  -> 40 x 3-hourly slots (5 days)

    Raises requests.HTTPError with a friendly message for common mistakes
    (wrong key, city typo, quota) so beginners can diagnose problems fast.
    """
    params_common = {"q": city, "appid": api_key, "units": config.UNITS}

    try:
        cur = requests.get(
            f"{config.API_BASE_URL}/weather",
            params=params_common,
            timeout=15,
        )
        if cur.status_code == 404:
            raise ValueError(
                f"City '{city}' not found - check the spelling, "
                "or use 'City,CC' (e.g. 'Paris,FR')."
            )
        if cur.status_code == 401:
            raise ValueError(
                "Invalid API key (HTTP 401). Get a free key at "
                "https://home.openweathermap.org/api_keys and wait ~10 min "
                "for activation."
            )
        cur.raise_for_status()
        cur_json = cur.json()

        fc = requests.get(
            f"{config.API_BASE_URL}/forecast",
            params=params_common,
            timeout=15,
        )
        fc.raise_for_status()
        fc_json = fc.json()

    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(
            "Cannot reach api.openweathermap.org - check your internet, "
            "firewall/proxy, or use simulation mode."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise TimeoutError("Weather API timed out - try again.") from exc

    forecast = [_norm_forecast_item(i) for i in fc_json.get("list", [])]

    return {
        "city": cur_json.get("name", city.title()),
        "country": cur_json.get("sys", {}).get("country", ""),
        "lat": round(cur_json.get("coord", {}).get("lat", 0.0), 3),
        "lon": round(cur_json.get("coord", {}).get("lon", 0.0), 3),
        "timezone": "API",
        "source": "api",
        "current": _norm_current(cur_json),
        "forecast": forecast,
    }


# ---------------------------------------------------------------------------
# SIMULATION mode
# ---------------------------------------------------------------------------
def load_simulation(city: str | None = None) -> dict:
    """
    Load the bundled sample data (schema-identical to the API response).

    If a city name is passed that is not in the file, the file's city is used
    and the caller is told via the returned dict's 'city' field.
    """
    path: Path = config.DATA_DIR / "sample_weather.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Sample data not found at {path}. Re-download the project."
        )
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Light validation so a corrupted file fails loudly, not silently
    for key in ("city", "current", "forecast"):
        if key not in data:
            raise ValueError(f"Sample file missing '{key}' - regenerate it.")
    if not isinstance(data["forecast"], list) or not data["forecast"]:
        raise ValueError("Sample file has an empty forecast list.")

    # If the requested city matches the bundled sample, use it verbatim.
    if city is None or str(city).lower() == str(data["city"]).lower():
        data["source"] = "simulation"
        data["simulation_detail"] = "bundled sample data for London"
        return data

    # Any other city gets deterministic SYNTHETIC data with the same schema.
    return _synthesize(city)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def get_weather(city: str, api_key: str | None = None) -> tuple[dict, str]:
    """
    Return (weather_data, mode).

    Prefers LIVE mode when a real key exists; otherwise falls back to
    SIMULATION mode so the app NEVER hard-fails for a student without a key.
    """
    if api_key and api_key not in ("", "paste_your_api_key_here"):
        return fetch_live(city, api_key), "live"
    return load_simulation(city), "simulation"
