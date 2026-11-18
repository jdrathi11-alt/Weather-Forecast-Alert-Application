"""
tests/test_weather_app.py - lightweight unit tests (stdlib unittest, zero deps).

Run from the project root:
    python tests/run_tests.py
or
    python -m unittest discover -s tests -v

Why tests in a student project?
-------------------------------
* Proves the alert logic really works, not just "looks right".
* Interviewers love "I wrote tests" - it shows engineering maturity.
* Lets you refactor rules safely later.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import config
from alerts import evaluate, check_heat, check_cold, check_rain, check_humidity, check_wind, check_storm
from analyzer import build_forecast_df, build_daily_summary
from weather_client import load_simulation


def _slot(**kw) -> dict:
    base = {"dt": "2026-11-19T12:00:00Z", "temp": 20.0, "humidity": 50,
            "wind_speed": 10.0, "weather": "Clear", "description": "clear", "pop": 0.0}
    base.update(kw)
    return base


class TestAlertRules(unittest.TestCase):
    def test_heat_warning(self):
        a = check_heat(_slot(temp=36.0))
        self.assertIsNotNone(a)
        self.assertEqual(a["level"], "WARNING")
        self.assertEqual(a["type"], "HIGH_TEMPERATURE")

    def test_heat_critical(self):
        a = check_heat(_slot(temp=41.0))
        self.assertEqual(a["level"], "CRITICAL")
        self.assertEqual(a["type"], "EXTREME_HEAT")

    def test_no_heat(self):
        self.assertIsNone(check_heat(_slot(temp=25.0)))

    def test_cold(self):
        a = check_cold(_slot(temp=-2.0))
        self.assertEqual(a["type"], "LOW_TEMPERATURE")

    def test_rain(self):
        a = check_rain(_slot(pop=0.7))
        self.assertEqual(a["type"], "RAIN")

    def test_no_rain_below_threshold(self):
        self.assertIsNone(check_rain(_slot(pop=0.2)))

    def test_humidity_high(self):
        a = check_humidity(_slot(humidity=90))
        self.assertEqual(a["type"], "HUMIDITY")
        self.assertEqual(a["level"], "WARNING")

    def test_humidity_low_info(self):
        a = check_humidity(_slot(humidity=10))
        self.assertEqual(a["level"], "INFO")

    def test_wind(self):
        a = check_wind(_slot(wind_speed=50.0))
        self.assertEqual(a["type"], "WIND")

    def test_storm(self):
        a = check_storm(_slot(weather="Thunderstorm"))
        self.assertEqual(a["level"], "CRITICAL")
        self.assertEqual(a["type"], "STORM")

    def test_no_storm_for_rain(self):
        self.assertIsNone(check_storm(_slot(weather="Rain")))


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.data = load_simulation()

    def test_simulation_data_loads(self):
        self.assertIn("forecast", self.data)
        self.assertGreater(len(self.data["forecast"]), 0)

    def test_evaluate_returns_alerts(self):
        alerts = evaluate(self.data)
        self.assertIsInstance(alerts, list)
        # sample data has thunderstorm + rain + high humidity
        self.assertGreaterEqual(len(alerts), 3)

    def test_no_duplicate_type_per_day(self):
        alerts = evaluate(self.data)
        keys = [(a["type"], a["time"]) for a in alerts]
        self.assertEqual(len(keys), len(set(keys)))

    def test_dataframe_build(self):
        df = build_forecast_df(self.data)
        self.assertIn("temp_c", df.columns)
        self.assertIn("rain_prob", df.columns)
        self.assertEqual(len(df), len(self.data["forecast"]))

    def test_daily_summary_days(self):
        df = build_forecast_df(self.data)
        daily = build_daily_summary(df)
        self.assertGreaterEqual(len(daily), 4)
        self.assertIn("max_temp", daily.columns)


if __name__ == "__main__":
    unittest.main()
