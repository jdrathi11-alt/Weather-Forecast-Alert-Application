"""
visualization.py - Matplotlib charts for the forecast.

Produces three PNGs in images/:
  1. temperature_trend.png   - temperature line + feels-like + daily min/max band
  2. rain_humidity.png       - rain probability bars + humidity line (dual axis)
  3. weather_icons.png       - condition counts across the forecast window

All charts use Agg backend (no GUI needed) so they work on servers/CI.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")                     # headless-safe backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

import config


def _style(ax) -> None:
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_temperature(df, city: str, path: Path) -> str | None:
    """Temperature trend with feels-like overlay."""
    if df is None or df.empty:
        return None
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=110)
    ax.plot(df["datetime_utc"], df["temp_c"], marker="o", lw=2,
            label="Temperature", color="#d62728")
    ax.plot(df["datetime_utc"], df["feels_like_c"], lw=1.4, ls="--",
            label="Feels like", color="#ff7f0e")
    ax.axhline(config.Thresholds.HIGH_TEMP_C, color="red", ls=":", lw=1.2,
               label=f"Heat threshold {config.Thresholds.HIGH_TEMP_C}°C")
    ax.axhline(config.Thresholds.LOW_TEMP_C, color="steelblue", ls=":", lw=1.2,
               label=f"Freezing {config.Thresholds.LOW_TEMP_C}°C")
    ax.set_title(f"5-Day Temperature Trend - {city}")
    ax.set_ylabel(f"Temperature ({config.UNITS_LABEL})")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %H:%M"))
    ax.legend(loc="best", fontsize=8)
    fig.autofmt_xdate()
    _style(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def plot_rain_humidity(df, city: str, path: Path) -> str | None:
    """Rain probability bars + humidity line on twin axis."""
    if df is None or df.empty:
        return None
    fig, ax = plt.subplots(figsize=(11, 4.5), dpi=110)
    ax.bar(df["datetime_utc"], df["rain_prob"], width=0.09, color="#1f77b4",
           alpha=0.75, label="Rain probability %")
    ax.axhline(config.Thresholds.RAIN_PROBABILITY * 100, color="blue", ls=":",
               lw=1.2, label=f"Rain alert {int(config.Thresholds.RAIN_PROBABILITY*100)}%")
    ax.set_ylabel("Rain probability (%)", color="#1f77b4")
    ax.set_ylim(0, 105)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %H:%M"))

    ax2 = ax.twinx()
    ax2.plot(df["datetime_utc"], df["humidity_pct"], color="green", lw=1.6,
             label="Humidity %")
    ax2.axhline(config.Thresholds.HUMIDITY_HIGH_PCT, color="green", ls="--",
                lw=1.0, label=f"Humidity alert {config.Thresholds.HUMIDITY_HIGH_PCT}%")
    ax2.set_ylabel("Humidity (%)", color="green")
    ax2.set_ylim(0, 105)

    ax.set_title(f"Rain Probability & Humidity - {city}")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)
    _style(ax)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def plot_conditions(df, city: str, path: Path) -> str | None:
    """Bar chart of weather-condition frequency (quick 'what dominates' view)."""
    if df is None or df.empty:
        return None
    counts = df["weather"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4), dpi=110)
    ax.bar(counts.index, counts.values, color="#2ca02c")
    ax.set_title(f"Dominant Weather Conditions - {city}")
    ax.set_ylabel("Forecast slots")
    plt.xticks(rotation=30, ha="right")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def render_all(df, city: str, out_dir: Path) -> list[str]:
    """Render every chart; return list of saved file paths."""
    saved = []
    for fn, stem in (
        (plot_temperature, "temperature_trend"),
        (plot_rain_humidity, "rain_humidity"),
        (plot_conditions, "weather_conditions"),
    ):
        p = out_dir / f"{stem}.png"
        res = fn(df, city, p)
        if res:
            saved.append(res)
    return saved
