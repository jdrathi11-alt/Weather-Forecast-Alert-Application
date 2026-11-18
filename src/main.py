#!/usr/bin/env python3
"""
main.py - command-line entry point for the Weather Forecast & Alert Application.

USAGE
-----
    python src/main.py                        # default: London, simulation mode
    python src/main.py --city "Paris,FR"      # any city
    python src/main.py --mode live            # force live API (needs key)
    python src/main.py --mode simulation      # force sample data
    python src/main.py --heat 30 --rain 0.3   # override thresholds
    python src/main.py --no-charts            # skip PNG generation

WORKFLOW
--------
city -> weather_client (API | sample data) -> analyzer (pandas)
      -> alerts (rule engine) -> visualization (charts)
      -> report (CSV + TXT + JSON) -> console summary

Every stage is a separate module so each can be tested & explained alone.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make "import config" work when running `python src/main.py` from the repo root
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config
from weather_client import get_weather
from analyzer import (build_forecast_df, build_daily_summary,
                      compute_insights, to_csv_files, latest_stable_path)
from alerts import evaluate, sort_alerts, summarize
from visualization import render_all
from report import (save_alerts_csv, save_forecast_csv,
                    save_text_report, save_json_bundle)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Weather Forecast & Alert Application (student project)")
    p.add_argument("--city", default=config.DEFAULT_CITY,
                   help="City name, optionally with country code e.g. 'Paris,FR'")
    p.add_argument("--mode", choices=["auto", "live", "simulation"],
                   default="auto",
                   help="auto = live if API key exists else simulation")
    p.add_argument("--key", default=None,
                   help="API key (prefer .env file instead)")
    p.add_argument("--heat", type=float, default=None,
                   help="Override high-temperature threshold (°C)")
    p.add_argument("--rain", type=float, default=None,
                   help="Override rain probability threshold (0-1)")
    p.add_argument("--no-charts", action="store_true",
                   help="Skip chart generation")
    p.add_argument("--email", action="store_true",
                   help="Send email alert if SMTP_* vars are set in .env")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # ---- 0. configuration overrides ------------------------------------
    if args.heat is not None:
        config.Thresholds.HIGH_TEMP_C = args.heat
    if args.rain is not None:
        config.Thresholds.RAIN_PROBABILITY = args.rain

    print("=" * 66)
    print(" WEATHER FORECAST & ALERT APPLICATION")
    print("=" * 66)

    # ---- 1. resolve API key & mode -------------------------------------
    api_key = args.key or config.load_api_key()
    if args.mode == "live" and not api_key:
        print("[ERROR] --mode live requested but no API key found.\n"
              "        Put it in .env (see .env.example) or pass --key.")
        return 2
    if args.mode == "live":
        mode_hint = "live"
    elif args.mode == "simulation":
        mode_hint = None
    else:                                   # auto
        mode_hint = api_key

    # ---- 2. fetch data --------------------------------------------------
    try:
        data, mode = get_weather(args.city, mode_hint)
    except (ValueError, ConnectionError, TimeoutError) as exc:
        print(f"[ERROR] {exc}")
        return 1
    print(f"[1/5] Data loaded  : {data['city']} ({mode} mode)")
    if mode == "simulation":
        print(f"        detail       : {data.get('simulation_detail', 'sample data')}")

    # ---- 3. analyse with pandas ----------------------------------------
    df_fc = build_forecast_df(data)
    df_daily = build_daily_summary(df_fc)
    insights = compute_insights(data, df_fc)
    print(f"[2/5] Analysed     : {insights.get('forecast_slots', 0)} forecast slots, "
          f"{insights.get('days_covered', 0)} days")

    # ---- 4. alert rules --------------------------------------------------
    alerts = sort_alerts(evaluate(data))
    print(f"[3/5] Alerts       : {summarize(alerts)}")

    # ---- 5. charts -------------------------------------------------------
    charts = []
    if not args.no_charts:
        charts = render_all(df_fc, data["city"], config.IMAGES_DIR)
        print(f"[4/5] Charts       : {len(charts)} saved to images/")
    else:
        print("[4/5] Charts       : skipped (--no-charts)")

    # ---- 6. persist artefacts -------------------------------------------
    csv_fc, csv_daily = to_csv_files(df_fc, df_daily, config.OUTPUTS_DIR)
    latest_stable_path(csv_fc, "forecast", config.OUTPUTS_DIR)
    latest_stable_path(csv_daily, "daily_summary", config.OUTPUTS_DIR)
    csv_alerts = save_alerts_csv(alerts, data["city"], config.OUTPUTS_DIR)
    save_forecast_csv(data.get("forecast", []), data["city"], config.OUTPUTS_DIR)
    report_path = save_text_report(data, alerts, insights, charts, config.REPORTS_DIR)
    bundle_path = save_json_bundle(data, alerts, insights, config.OUTPUTS_DIR)
    print(f"[5/5] Saved        : {report_path}")
    print(f"                 + CSV/JSON bundles in outputs/")

    # ---- 6b. optional email automation ------------------------------------
    from notify import notify_if_needed
    email_status = notify_if_needed(data["city"], alerts, mode, force=args.email)
    print(f"                 Email   : {email_status}")

    # ---- 7. console summary ---------------------------------------------
    print()
    print("-" * 66)
    print(f" CURRENT WEATHER - {data['city']}, {data['country']}")
    print("-" * 66)
    cur = data["current"]
    print(f"  {cur['dt']}  |  {cur['temp']}{config.UNITS_LABEL}  "
          f"({cur['description'].title()})  "
          f"Feels {cur['feels_like']}{config.UNITS_LABEL}")
    print(f"  Humidity {cur['humidity']}%  |  Wind {cur['wind_speed']} km/h  "
          f"|  Pressure {cur['pressure']} hPa")
    print()
    if df_daily is not None and not df_daily.empty:
        print(" DAILY FORECAST (next days)")
        print(df_daily.to_string(index=False))
        print()
    print("-" * 66)
    print(" ALERTS")
    print("-" * 66)
    if alerts:
        for a in alerts:
            print(f"  [{a['level']}] {a['title']} ({a['time']})")
            print(f"      {a['message']}")
    else:
        print("  No alerts triggered. Conditions look calm. :)")
    print("=" * 66)
    print(f" Full report : {report_path}")
    print(f" JSON bundle : {bundle_path}")
    if csv_alerts:
        print(f" Alerts CSV  : {csv_alerts}")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
