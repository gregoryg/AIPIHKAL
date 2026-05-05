#!/usr/bin/env python3
"""Fetch weather forecast from Home Assistant.

Default (no args): week overview using twice-daily forecast periods.
--hourly:          full hourly detail, grouped by day.
--today:           today's hourly summary only.
--tomorrow:        tomorrow's hourly summary only.
--json:            raw JSON output instead of human-readable text.

Weather entity is read from HA_WEATHER_ENTITY env var,
defaulting to the value in SKILL config or the first weather.* entity found.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

try:
    import websockets
except ImportError:
    print("Error: websockets library not found", file=sys.stderr)
    sys.exit(3)

HASS_SERVER   = os.environ.get("HASS_SERVER", "")
HASS_TOKEN    = os.environ.get("HASS_TOKEN", "")
WEATHER_ENTITY = os.environ.get("HA_WEATHER_ENTITY", "weather.kapa")

CONDITION_ICON = {
    "sunny": "☀️",  "clear-night": "🌙", "partlycloudy": "⛅",
    "cloudy": "☁️", "fog": "🌫️",        "windy": "💨",
    "windy-variant": "💨",               "rainy": "🌧️",
    "pouring": "🌧️", "snowy": "❄️",     "snowy-rainy": "🌨️",
    "hail": "🌨️",   "lightning": "⚡",  "lightning-rainy": "⛈️",
    "exceptional": "🌡️",
}


def ws_url() -> str:
    return HASS_SERVER.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"


async def get_forecast(forecast_type: str) -> list[dict]:
    async with websockets.connect(ws_url()) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HASS_TOKEN}))
        assert json.loads(await ws.recv())["type"] == "auth_ok"

        await ws.send(json.dumps({
            "id": 1,
            "type": "call_service",
            "domain": "weather",
            "service": "get_forecasts",
            "service_data": {"type": forecast_type},
            "target": {"entity_id": WEATHER_ENTITY},
            "return_response": True,
        }))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                break

    if not msg.get("success"):
        raise RuntimeError(f"Forecast error: {msg.get('error', {}).get('message', msg)}")

    return msg["result"]["response"][WEATHER_ENTITY]["forecast"]


async def current_conditions() -> dict:
    async with websockets.connect(ws_url()) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HASS_TOKEN}))
        assert json.loads(await ws.recv())["type"] == "auth_ok"

        await ws.send(json.dumps({"id": 1, "type": "get_states"}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                break

    states = msg.get("result", [])
    for s in states:
        if s["entity_id"] == WEATHER_ENTITY:
            a = s["attributes"]
            return {
                "condition": s["state"],
                "temperature": a.get("temperature"),
                "humidity": a.get("humidity"),
                "wind_speed": a.get("wind_speed"),
                "wind_bearing": a.get("wind_bearing"),
            }
    return {}


def parse_dt(dt_str: str) -> datetime:
    """Parse ISO datetime string, handling offset-aware formats."""
    # Python 3.10 fromisoformat doesn't handle all offset formats
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        # strip trailing Z or offset and treat as local-ish
        return datetime.fromisoformat(dt_str[:19])


def local_date(dt_str: str) -> str:
    return parse_dt(dt_str).strftime("%a %b %-d")


def local_time(dt_str: str) -> str:
    return parse_dt(dt_str).strftime("%-I%p").lower()


def condition_str(condition: str) -> str:
    icon = CONDITION_ICON.get(condition, "")
    label = condition.replace("-", " ").replace("_", " ")
    return f"{icon} {label}".strip()


def format_week(forecasts: list[dict]) -> str:
    """Render twice-daily forecasts as a human-readable week table."""
    lines = []
    # Group by date
    by_day: dict[str, list[dict]] = defaultdict(list)
    for f in forecasts:
        by_day[local_date(f["datetime"])].append(f)

    lines.append(f"{'Day':<14} {'Day':^22} {'Night':^22}")
    lines.append("─" * 60)

    for date, periods in by_day.items():
        day   = next((p for p in periods if p.get("is_daytime")),   None)
        night = next((p for p in periods if not p.get("is_daytime")), None)

        def fmt(p: dict | None) -> str:
            if not p:
                return "—"
            cond = condition_str(p.get("condition", ""))
            temp = p.get("temperature", "?")
            prob = p.get("precipitation_probability", 0)
            return f"{cond:<14} {temp:>3}°F  {prob:>3}%💧"

        lines.append(f"{date:<14} {fmt(day):<22} {fmt(night)}")

    return "\n".join(lines)


def format_hourly_day(date_str: str, periods: list[dict]) -> str:
    """Render one day's hourly periods as a compact table."""
    lines = [f"\n{date_str}"]
    lines.append(f"  {'Time':<8} {'Condition':<20} {'Temp':>6} {'Precip':>7}")
    lines.append("  " + "─" * 44)
    for p in periods:
        time  = local_time(p["datetime"])
        cond  = condition_str(p.get("condition", ""))
        temp  = p.get("temperature", "?")
        prob  = p.get("precipitation_probability", 0)
        lines.append(f"  {time:<8} {cond:<20} {temp:>4}°F  {prob:>4}%")
    return "\n".join(lines)


async def run(args: argparse.Namespace) -> int:
    try:
        current = await current_conditions()

        if args.json:
            ftype = "hourly" if (args.hourly or args.today or args.tomorrow) else "twice_daily"
            forecasts = await get_forecast(ftype)
            print(json.dumps({"current": current, "forecast_type": ftype, "forecast": forecasts}, indent=2))
            return 0

        # Header: current conditions
        cond = condition_str(current.get("condition", "unknown"))
        temp = current.get("temperature", "?")
        hum  = current.get("humidity", "?")
        print(f"Now: {cond}  {temp}°F  humidity {hum}%\n")

        if args.today or args.tomorrow or args.hourly:
            forecasts = await get_forecast("hourly")
            by_day: dict[str, list[dict]] = defaultdict(list)
            for f in forecasts:
                by_day[local_date(f["datetime"])].append(f)

            days = sorted(by_day.keys(), key=lambda d: parse_dt(
                next(p["datetime"] for p in by_day[d])))

            if args.today:
                target = days[0] if days else None
                if target:
                    print(format_hourly_day(target, by_day[target]))
            elif args.tomorrow:
                target = days[1] if len(days) > 1 else None
                if target:
                    print(format_hourly_day(target, by_day[target]))
            else:
                for day in days:
                    print(format_hourly_day(day, by_day[day]))
        else:
            forecasts = await get_forecast("twice_daily")
            print(format_week(forecasts))

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--today",    action="store_true", help="Hourly detail for today only")
    p.add_argument("--tomorrow", action="store_true", help="Hourly detail for tomorrow only")
    p.add_argument("--hourly",   action="store_true", help="Full hourly detail for the week")
    p.add_argument("--json",     action="store_true", help="Raw JSON output")
    return p


def main() -> int:
    return asyncio.run(run(build_parser().parse_args()))


if __name__ == "__main__":
    sys.exit(main())
