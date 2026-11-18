"""
report.py - persistence layer: CSV forecast tables, alerts CSV and a human
readable text report saved under reports/ and outputs/.

Why save reports?
-----------------
* Proof for GitHub: a reviewer can open reports/latest_report.txt without
  running anything.
* Audit trail: each run leaves a timestamped artefact.
* Automation: CSVs drop straight into Excel / Power BI / pandas.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import config


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# CSV outputs
# ---------------------------------------------------------------------------
def save_alerts_csv(alerts: list[dict], city: str, out_dir: Path) -> str | None:
    """One row per alert - the file an operations team would filter."""
    if not alerts:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"alerts_{_stamp()}.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "city", "level", "type", "title", "message", "time"
        ])
        writer.writeheader()
        for a in alerts:
            writer.writerow({
                "city": city, "level": a["level"], "type": a["type"],
                "title": a["title"], "message": a["message"], "time": a["time"],
            })
    return str(path)


def save_forecast_csv(forecast: list[dict], city: str, out_dir: Path) -> str | None:
    """Raw forecast slots flattened to CSV."""
    if not forecast:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"forecast_{_stamp()}.csv"
    fields = ["dt", "temp", "feels_like", "humidity", "pressure",
              "wind_speed", "weather", "description", "pop"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in forecast:
            writer.writerow(row)
    return str(path)


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------
def save_text_report(data: dict, alerts: list[dict], insights: dict,
                     charts: list[str], out_dir: Path) -> str:
    """The main human-readable artifact (also used for screenshots)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"report_{_stamp()}.txt"
    cur = data.get("current", {})
    th = config.Thresholds()

    lines = []
    lines.append("=" * 66)
    lines.append(" WEATHER FORECAST & ALERT REPORT")
    lines.append("=" * 66)
    lines.append(f"City        : {data.get('city')}, {data.get('country')}")
    lines.append(f"Coordinates : {data.get('lat')}, {data.get('lon')}")
    lines.append(f"Generated   : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"Data source : {'LIVE OpenWeatherMap API' if data.get('source')=='api' else 'SIMULATION (sample data)'}")
    lines.append("-" * 66)
    lines.append("CURRENT CONDITIONS")
    lines.append("-" * 66)
    lines.append(f"  Time          : {cur.get('dt')}")
    lines.append(f"  Temperature   : {cur.get('temp')}°C  (feels like {cur.get('feels_like')}°C)")
    lines.append(f"  Condition     : {cur.get('weather')} - {cur.get('description')}")
    lines.append(f"  Humidity      : {cur.get('humidity')}%")
    lines.append(f"  Pressure      : {cur.get('pressure')} hPa")
    lines.append(f"  Wind          : {cur.get('wind_speed')} km/h")
    lines.append(f"  Visibility    : {cur.get('visibility')} m")
    lines.append("")
    lines.append("-" * 66)
    lines.append("FORECAST HEADLINES")
    lines.append("-" * 66)
    lines.append(f"  Slots analysed : {insights.get('forecast_slots','-')}")
    lines.append(f"  Days covered   : {insights.get('days_covered','-')}")
    lines.append(f"  Hottest        : {insights.get('hottest_temp')}°C at {insights.get('hottest_when')}")
    lines.append(f"  Coldest        : {insights.get('coldest_temp')}°C at {insights.get('coldest_when')}")
    lines.append(f"  Peak rain prob : {insights.get('max_rain_prob')}% at {insights.get('max_rain_prob_when')}")
    lines.append(f"  Avg humidity   : {insights.get('avg_humidity')}%")
    lines.append(f"  Rain hours     : {insights.get('rain_hours_total')} (prob >= 50%)")
    lines.append("")
    lines.append("-" * 66)
    lines.append("ALERTS")
    lines.append("-" * 66)
    if alerts:
        for i, a in enumerate(alerts, 1):
            lines.append(f"  [{i}] {a['level']} | {a['title']}")
            lines.append(f"      when    : {a['time']}")
            lines.append(f"      detail  : {a['message']}")
    else:
        lines.append("  No alerts triggered in the forecast window.")
    lines.append("")
    lines.append("-" * 66)
    lines.append("ACTIVE THRESHOLDS (config.py)")
    lines.append("-" * 66)
    for k, v in th.as_dict().items():
        lines.append(f"  {k:26}: {v}")
    lines.append("")
    if charts:
        lines.append("-" * 66)
        lines.append("CHARTS GENERATED")
        lines.append("-" * 66)
        for c in charts:
            lines.append(f"  - {Path(c).name}")
    lines.append("")
    lines.append("=" * 66)
    lines.append(" END OF REPORT")
    lines.append("=" * 66)

    text = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)

    # Also keep a stable 'latest' copy so screenshots/instructions never rot
    stable = out_dir / "latest_report.txt"
    stable.write_text(text, encoding="utf-8")
    return str(path)


def save_json_bundle(data: dict, alerts: list[dict], insights: dict,
                     out_dir: Path) -> str:
    """Machine-readable bundle (nice for a second app or a Streamlit dashboard)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"bundle_{_stamp()}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "thresholds": config.Thresholds().as_dict(),
        "weather": data,
        "alerts": alerts,
        "insights": insights,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return str(path)
