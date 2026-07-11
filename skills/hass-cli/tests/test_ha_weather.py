"""Offline tests for generic weather formatting."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "ha_weather.py"
SPEC = importlib.util.spec_from_file_location("ha_weather", SCRIPT)
assert SPEC and SPEC.loader
ha_weather = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ha_weather)


class WeatherFormattingTests(unittest.TestCase):
    def test_hourly_output_uses_configured_temperature_unit(self) -> None:
        output = ha_weather.format_hourly_day(
            "Mon Jul 13",
            [{
                "datetime": "2026-07-13T09:00:00-06:00",
                "condition": "sunny",
                "temperature": 21,
                "precipitation_probability": 0,
            }],
            "°C",
        )
        self.assertIn("21°C", output)
        self.assertNotIn("°F", output)


if __name__ == "__main__":
    unittest.main()
