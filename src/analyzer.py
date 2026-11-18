"""
analyzer.py - turn raw weather payloads into tables & insights with Pandas.

What it produces
----------------
* forecast_df        : tidy DataFrame, one row per 3-hour forecast slot
* daily_summary_df   : one row per day (min/max/avg temp, rain probability...)
* insights dict      : headline numbers used by the text report

Why Pandas?
-----------
Once data is in a DataFrame you can do in ONE line what would take
twenty lines of loops: group by day, find the hottest slot, count wet hours.
That is exactly the skill Data Analyst roles test for.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


def _to_datetime(ts: str) -> pd.Timestamp:
    return pd.to_datetime(ts, utc=True)


def build_forecast_df(data: dict) -> pd.DataFrame:
    """
    Convert the forecast list into a tidy DataFrame with derived columns:
    date, hour, feels_delta (heat-index style gap), rain_flag, comfort.
    """
    rows = []
    for slot in data.get("forecast", []):
        dt = _to_datetime(slot["dt"])
        rows.append({
            "datetime_utc": dt,
            "date": dt.date(),
            "hour": dt.hour,
            "temp_c": slot.get("temp"),
            "feels_like_c": slot.get("feels_like"),
            "humidity_pct": slot.get("humidity"),
            "pressure_hpa": slot.get("pressure"),
            "wind_kmh": slot.get("wind_speed"),
            "weather": slot.get("weather"),
            "description": slot.get("description"),
            "rain_prob": round(float(slot.get("pop", 0.0)) * 100),
        })
    df = pd.DataFrame(rows).sort_values("datetime_utc").reset_index(drop=True)
    if df.empty:
        return df
    df["feels_delta"] = (df["feels_like_c"] - df["temp_c"]).round(1)
    df["rain_flag"] = df["rain_prob"] >= 50
    return df


def build_daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    """One row per day - the table a logistics manager actually reads."""
    if df.empty:
        return df
    summary = (
        df.groupby("date")
        .agg(
            min_temp=("temp_c", "min"),
            max_temp=("temp_c", "max"),
            avg_temp=("temp_c", "mean"),
            avg_humidity=("humidity_pct", "mean"),
            max_wind_kmh=("wind_kmh", "max"),
            max_rain_prob=("rain_prob", "max"),
            rain_hours=("rain_flag", "sum"),
            dominant_weather=("weather", lambda s: s.mode().iloc[0] if len(s) else "-"),
        )
        .reset_index()
    )
    summary["avg_temp"] = summary["avg_temp"].round(1)
    summary["avg_humidity"] = summary["avg_humidity"].round(0).astype(int)
    summary["rain_hours"] = summary["rain_hours"].astype(int)
    return summary


def compute_insights(data: dict, df: pd.DataFrame) -> dict[str, Any]:
    """Headline numbers for the console / text report."""
    current = data.get("current", {})
    insights: dict[str, Any] = {
        "city": data.get("city"),
        "country": data.get("country"),
        "source": data.get("source"),
        "current_temp": current.get("temp"),
        "current_desc": current.get("description"),
        "current_humidity": current.get("humidity"),
        "current_wind_kmh": current.get("wind_speed"),
    }
    if df is not None and not df.empty:
        hottest = df.loc[df["temp_c"].idxmax()]
        coldest = df.loc[df["temp_c"].idxmin()]
        wettest = df.loc[df["rain_prob"].idxmax()]
        insights.update({
            "forecast_slots": len(df),
            "days_covered": df["date"].nunique(),
            "hottest_temp": hottest["temp_c"],
            "hottest_when": hottest["datetime_utc"].strftime("%a %b %d %H:%M"),
            "coldest_temp": coldest["temp_c"],
            "coldest_when": coldest["datetime_utc"].strftime("%a %b %d %H:%M"),
            "max_rain_prob": int(wettest["rain_prob"]),
            "max_rain_prob_when": wettest["datetime_utc"].strftime("%a %b %d %H:%M"),
            "avg_humidity": round(float(df["humidity_pct"].mean()), 1),
            "rain_hours_total": int(df["rain_flag"].sum()),
        })
    return insights


def to_csv_files(df_forecast: pd.DataFrame, df_daily: pd.DataFrame,
                 out_dir: Any) -> tuple[str | None, str | None]:
    """Write forecast + daily CSVs; return their paths (or None if empty)."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    f_path = str(out_dir / f"forecast_{stamp}.csv")
    d_path = str(out_dir / f"daily_summary_{stamp}.csv")
    if df_forecast is not None and not df_forecast.empty:
        df_forecast.to_csv(f_path, index=False)
    else:
        f_path = None
    if df_daily is not None and not df_daily.empty:
        df_daily.to_csv(d_path, index=False)
    else:
        d_path = None
    return f_path, d_path


def latest_stable_path(path: str | None, stem: str, out_dir: Any) -> str | None:
    """Also write a stable, non-timestamped copy for easy screenshotting."""
    if not path:
        return None
    import shutil
    stable = str(out_dir / f"{stem}.csv")
    shutil.copyfile(path, stable)
    return stable
