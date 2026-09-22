"""Offline tests for generic weather formatting."""

from __future__ import annotations

import asyncio
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

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


class WeatherTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_receive_is_bounded(self) -> None:
        class SlowWebSocket:
            async def recv(self) -> str:
                await asyncio.sleep(1)
                return "{}"

        with (
            patch.object(ha_weather, "COMMAND_TIMEOUT", 0.001),
            self.assertRaisesRegex(RuntimeError, "waiting for weather forecast"),
        ):
            await ha_weather.receive_json(SlowWebSocket(), "weather forecast")


if __name__ == "__main__":
    unittest.main()
