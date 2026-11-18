"""
alerts.py - the "brain" of the alert system.

Every check is a pure function: data in -> alert out (or None).
That makes the rules easy to unit-test and easy to extend
(add a new rule = add one function + register it in RULES).

Alert severities
----------------
INFO    - worth knowing (dry air, fog)
WARNING - plan around it (rain, wind, cold)
CRITICAL- act now (storm, extreme heat)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

import config


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------
def _parse_dt(ts: str) -> datetime:
    """Parse the ISO strings produced by weather_client (always UTC)."""
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def _day_label(ts: str) -> str:
    """'2026-11-19T03:00:00Z' -> 'Nov 19 03:00' (readable for reports)."""
    return _parse_dt(ts).strftime("%b %d %H:%M")


def _mk(level: str, kind: str, title: str, message: str, when: str) -> dict:
    return {
        "level": level,
        "type": kind,
        "title": title,
        "message": message,
        "time": when,
    }


# ---------------------------------------------------------------------------
# Individual rules
# ---------------------------------------------------------------------------
def check_heat(slot: dict) -> dict | None:
    t = slot.get("temp", 0.0)
    if t >= config.Thresholds.HIGH_TEMP_CRITICAL_C:
        return _mk("CRITICAL", "EXTREME_HEAT", "Extreme heat alert",
                   f"Temperature {t}°C is at/above the critical threshold "
                   f"({config.Thresholds.HIGH_TEMP_CRITICAL_C}°C). Risk of heatstroke; "
                   "avoid outdoor work 11:00-16:00.", _day_label(slot["dt"]))
    if t >= config.Thresholds.HIGH_TEMP_C:
        return _mk("WARNING", "HIGH_TEMPERATURE", "High temperature alert",
                   f"Temperature {t}°C meets the heat threshold "
                   f"({config.Thresholds.HIGH_TEMP_C}°C). Stay hydrated.",
                   _day_label(slot["dt"]))
    return None


def check_cold(slot: dict) -> dict | None:
    t = slot.get("temp", 0.0)
    if t <= config.Thresholds.LOW_TEMP_C:
        return _mk("WARNING", "LOW_TEMPERATURE", "Cold weather alert",
                   f"Temperature {t}°C is at/below freezing. Watch for icy "
                   "roads; protect pipes and sensitive plants.", _day_label(slot["dt"]))
    return None


def check_rain(slot: dict) -> dict | None:
    pop = slot.get("pop", 0.0)
    if pop >= config.Thresholds.RAIN_PROBABILITY:
        return _mk("WARNING", "RAIN", "Rain alert",
                   f"{slot.get('description','').title()} expected with "
                   f"{int(pop*100)}% probability. Carry an umbrella / plan "
                   "drainage checks.", _day_label(slot["dt"]))
    return None


def check_storm(slot: dict) -> dict | None:
    if not config.Thresholds.STORM:
        return None
    if "thunder" in slot.get("weather", "").lower() or "thunder" in slot.get("description", "").lower():
        return _mk("CRITICAL", "STORM", "Thunderstorm alert",
                   "Thunderstorm detected in forecast. Avoid open fields, "
                   "water and tall isolated objects; secure outdoor items.",
                   _day_label(slot["dt"]))
    return None


def check_humidity(slot: dict) -> dict | None:
    h = slot.get("humidity", 0)
    if h >= config.Thresholds.HUMIDITY_HIGH_PCT:
        return _mk("WARNING", "HUMIDITY", "High humidity alert",
                   f"Humidity {h}% (>= {config.Thresholds.HUMIDITY_HIGH_PCT}%). "
                   "Mould risk indoors; heat index feels higher than actual temp.",
                   _day_label(slot["dt"]))
    if h <= config.Thresholds.HUMIDITY_LOW_PCT:
        return _mk("INFO", "DRY_AIR", "Dry air notice",
                   f"Humidity {h}% (<= {config.Thresholds.HUMIDITY_LOW_PCT}%). "
                   "Hydrate and consider static-sensitive equipment.",
                   _day_label(slot["dt"]))
    return None


def check_wind(slot: dict) -> dict | None:
    w = slot.get("wind_speed", 0.0)
    if w >= config.Thresholds.WIND_KMH:
        return _mk("WARNING", "WIND", "High wind alert",
                   f"Wind {w} km/h (>= {config.Thresholds.WIND_KMH} km/h). "
                   "Secure loose objects; high-sided vehicles take care.",
                   _day_label(slot["dt"]))
    return None


# Rule registry: order here is the order alerts appear in the report
RULES: list[tuple[str, Callable[[dict], dict | None]]] = [
    ("storm", check_storm),
    ("heat", check_heat),
    ("cold", check_cold),
    ("rain", check_rain),
    ("humidity", check_humidity),
    ("wind", check_wind),
]


# ---------------------------------------------------------------------------
# Orchestrators
# ---------------------------------------------------------------------------
def evaluate_slot(slot: dict) -> list[dict]:
    """Run every rule on ONE forecast slot; return the alerts it produced."""
    out = []
    for _name, fn in RULES:
        alert = fn(slot)
        if alert:
            out.append(alert)
    return out


def evaluate(data: dict) -> list[dict]:
    """
    Evaluate current conditions + the next N forecast hours.

    Deduplication: same (type, day) keeps only the first slot, so a 24-hour
    rain spell produces ONE rain alert, not eight.
    """
    alerts: list[dict] = []
    seen = set()

    # --- current conditions (counted in the same dedupe as forecast alerts)
    current = dict(data.get("current", {}))
    current.setdefault("pop", 0.0)
    now = _parse_dt(current.get("dt", ""))
    for alert in evaluate_slot(current):
        key = (alert["type"], now.strftime("%Y-%m-%d"))
        seen.add(key)
        alert["slot"] = current.get("dt")
        alerts.append(alert)

    # --- forecast window
    horizon_h = config.Thresholds.FORECAST_LOOKAHEAD_HOURS
    for slot in data.get("forecast", []):
        slot_time = _parse_dt(slot["dt"])
        if slot_time < now:
            continue                      # skip already-past slots
        if slot_time > now + timedelta(hours=horizon_h):
            break                          # lookahead window reached
        for alert in evaluate_slot(slot):
            key = (alert["type"], slot_time.strftime("%Y-%m-%d"))
            if key in seen:
                continue
            seen.add(key)
            alert["slot"] = slot["dt"]
            alerts.append(alert)
    return alerts


def _dedupe(groups: list[list[dict]]) -> list[dict]:
    flat = [a for g in groups for a in g]
    seen, out = set(), []
    for a in flat:
        if a["type"] not in seen:
            seen.add(a["type"])
            out.append(a)
    return out


# Severity ordering used by reports / dashboard
SEVERITY_RANK = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}


def sort_alerts(alerts: list[dict]) -> list[dict]:
    return sorted(alerts, key=lambda a: (SEVERITY_RANK.get(a["level"], 9), a["time"]))


def summarize(alerts: list[dict]) -> str:
    counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for a in alerts:
        counts[a["level"]] = counts.get(a["level"], 0) + 1
    return (
        f"{len(alerts)} alert(s)  "
        f"[CRITICAL: {counts['CRITICAL']}, WARNING: {counts['WARNING']}, "
        f"INFO: {counts['INFO']}]"
    )
