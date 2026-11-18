"""
dashboard.py - OPTIONAL Streamlit web dashboard.

Run it with:
    pip install streamlit
    streamlit run src/dashboard.py -- --city "London" --mode simulation

(Note the "--" separator: everything after it is passed to THIS script.)

The dashboard shows the same pipeline output as the CLI, but interactive:
select a city, see current weather, forecast table, alert cards and charts.
It demonstrates the "app development" angle of the project.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import config
from weather_client import get_weather
from analyzer import build_forecast_df, build_daily_summary, compute_insights
from alerts import evaluate, sort_alerts
from visualization import render_all

CITIES = ["London", "Paris,FR", "New York,US", "Tokyo,JP", "Sydney,AU",
          "Mumbai,IN", "Berlin,DE", "Singapore,SG"]


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Weather Forecast & Alert Dashboard",
                       page_icon="⛈️", layout="wide")
    st.title("⛈️ Weather Forecast & Alert Application")
    st.caption("Student project - live OpenWeatherMap API or bundled simulation data")

    city = st.sidebar.selectbox("City", CITIES, index=0)
    mode = st.sidebar.radio("Data source", ["auto", "live", "simulation"])
    heat = st.sidebar.slider("Heat threshold (°C)", 20, 45, int(config.Thresholds.HIGH_TEMP_C))
    rain = st.sidebar.slider("Rain probability threshold (%)", 10, 90,
                             int(config.Thresholds.RAIN_PROBABILITY * 100))

    config.Thresholds.HIGH_TEMP_C = float(heat)
    config.Thresholds.RAIN_PROBABILITY = rain / 100.0

    try:
        data, used_mode = get_weather(city, mode if mode != "auto" else None)
    except Exception as exc:                                   # noqa: BLE001
        st.error(f"Could not load weather data: {exc}")
        return

    df_fc = build_forecast_df(data)
    df_daily = build_daily_summary(df_fc)
    insights = compute_insights(data, df_fc)
    alerts = sort_alerts(evaluate(data))

    # --- header KPIs ------------------------------------------------------
    cur = data["current"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature", f"{cur['temp']}°C", f"feels {cur['feels_like']}°C")
    c2.metric("Humidity", f"{cur['humidity']}%")
    c3.metric("Wind", f"{cur['wind_speed']} km/h")
    c4.metric("Alerts", len(alerts),
              delta=f"{sum(1 for a in alerts if a['level']=='CRITICAL')} critical",
              delta_color="inverse")

    st.caption(f"Source: **{used_mode}** mode - {data.get('city')}, {data.get('country')}")

    # --- alert cards ------------------------------------------------------
    st.subheader("Active Alerts")
    if alerts:
        for a in alerts:
            emoji = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🔵"}.get(a["level"], "⚪")
            st.markdown(f"{emoji} **{a['title']}** - {a['message']} *(at {a['time']})*")
    else:
        st.success("No alerts triggered for this city in the forecast window.")

    # --- charts -----------------------------------------------------------
    st.subheader("Forecast Charts")
    charts = render_all(df_fc, data["city"], config.IMAGES_DIR)
    for c in charts:
        st.image(c, use_container_width=True)

    # --- tables -----------------------------------------------------------
    st.subheader("Daily Summary")
    st.dataframe(df_daily, use_container_width=True)
    st.subheader("Full 3-hourly Forecast")
    st.dataframe(df_fc, use_container_width=True)


if __name__ == "__main__":
    main()
