#!/usr/bin/env python3
"""Control and query robot vacuums via Home Assistant.

Resolves a human-ish query (vacuum name, area, floor, or 'all') to one or
more vacuum entities, then performs the requested action.

Commands:
  status  [query]   Show state, bin, battery, area, and floor for matched vacuums
  start   [query]   Start cleaning
  stop    [query]   Stop cleaning
  pause   [query]   Pause cleaning
  return  [query]   Return to base/dock
  locate  [query]   Make the vacuum beep so you can find it

Query examples:
  "main floor"    resolves by floor name
  "robo-tina"     resolves by friendly name
  "bedroom"       resolves by area name
  "all"           targets all vacuums

If query is omitted and only one vacuum exists, it is used automatically.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from typing import Any

try:
    import websockets
except ImportError:
    print(json.dumps({"status": "error", "message": "websockets library not found"}))
    sys.exit(3)

HASS_SERVER = os.environ.get("HASS_SERVER", "http://172.16.17.7:8123")
HASS_TOKEN  = os.environ.get("HASS_TOKEN", "")
HASS_CLI    = os.environ.get("HASS_CLI_BIN", "hass-cli")


class VacuumError(RuntimeError):
    pass


# ── helpers ──────────────────────────────────────────────────────────────────

def normalize(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def score(query: str, candidate: str) -> int:
    q, c = normalize(query), normalize(candidate)
    if not q or not c:
        return 0
    if q == c:              return 240
    if c.startswith(q):     return 170
    if q in c:              return 120
    qt = set(q.split())
    if qt and all(t in c.split() for t in qt):
        return 140 + 15 * len(qt)
    m = sum(1 for t in qt if t in c.split())
    return 50 + 20 * m if m else 0


def ws_url() -> str:
    return HASS_SERVER.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"


def run_hass_json(args: list[str]) -> Any:
    result = subprocess.run([HASS_CLI, "-o", "json", *args],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VacuumError(result.stderr.strip() or result.stdout.strip() or "hass-cli failed")
    return json.loads(result.stdout)


def run_hass(args: list[str]) -> None:
    result = subprocess.run([HASS_CLI, *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise VacuumError(result.stderr.strip() or result.stdout.strip() or "hass-cli failed")


# ── discovery ─────────────────────────────────────────────────────────────────

async def fetch_registry() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return (devices_by_entity, areas_by_id, floors_by_id) via WebSocket."""
    async with websockets.connect(ws_url()) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": HASS_TOKEN}))
        assert json.loads(await ws.recv())["type"] == "auth_ok"

        results = {}
        for msg_id, msg_type in [
            (1, "config/device_registry/list"),
            (2, "config/area_registry/list"),
            (3, "config/floor_registry/list"),
        ]:
            await ws.send(json.dumps({"id": msg_id, "type": msg_type}))
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("id") == msg_id:
                    results[msg_id] = msg["result"]
                    break

    # Build area_id → device map
    devices_by_area: dict[str, list[dict]] = {}
    for d in results[1]:
        if d.get("area_id"):
            devices_by_area.setdefault(d["area_id"], []).append(d)

    # entity_id → {device, area, floor}
    entity_registry: dict[str, Any] = {}
    areas  = {a["area_id"]: a for a in results[2]}
    floors = {f["floor_id"]: f for f in results[3]}

    return devices_by_area, areas, floors


def get_vacuums() -> list[dict[str, Any]]:
    """Return all vacuum entities with state and attributes."""
    states = run_hass_json(["state", "list", "vacuum.*"])
    return [s for s in states if s["entity_id"].startswith("vacuum.")
            and not s["entity_id"].startswith("vacuum.") is False
            and "update." not in s["entity_id"]]


async def build_vacuum_list() -> list[dict[str, Any]]:
    """Combine vacuum entity states with area/floor registry data."""
    states     = get_vacuums()
    dev_by_area, areas, floors = await fetch_registry()

    # Build entity_id → area/floor by matching device area to entity
    # (we match on friendly_name since device name = entity friendly_name for Roombas)
    name_to_area_floor: dict[str, dict] = {}
    for area_id, devs in dev_by_area.items():
        area   = areas.get(area_id, {})
        floor  = floors.get(area.get("floor_id", ""), {})
        for d in devs:
            dname = normalize(d.get("name_by_user") or d.get("name", ""))
            name_to_area_floor[dname] = {
                "area_id":    area_id,
                "area":       area.get("name"),
                "floor_id":   area.get("floor_id"),
                "floor":      floor.get("name"),
                "floor_level": floor.get("level"),
            }

    vacuums = []
    for s in states:
        attrs   = s.get("attributes", {})
        fname   = attrs.get("friendly_name", s["entity_id"])
        loc     = name_to_area_floor.get(normalize(fname), {})
        vacuums.append({
            "entity_id":    s["entity_id"],
            "label":        fname,
            "state":        s["state"],
            "bin_full":     attrs.get("bin_full"),
            "bin_present":  attrs.get("bin_present"),
            "battery":      attrs.get("battery_level"),
            "area":         loc.get("area"),
            "floor":        loc.get("floor"),
            "floor_level":  loc.get("floor_level"),
            "floor_id":     loc.get("floor_id"),
        })
    return sorted(vacuums, key=lambda v: (v.get("floor_level") or 0, v["label"]))


def resolve(query: str | None, vacuums: list[dict]) -> list[dict]:
    """Resolve query to a list of vacuum candidates."""
    if not query or query.strip().lower() == "all":
        return vacuums

    q = normalize(query)
    scored = []
    for v in vacuums:
        best = max(
            score(q, v["label"]),
            score(q, v.get("area") or ""),
            score(q, v.get("floor") or ""),
            score(q, v.get("floor_id") or ""),
            score(q, v["entity_id"]),
        )
        if best > 0:
            scored.append((best, v))

    if not scored:
        return []
    top = scored[0][0]
    return [v for s, v in scored if s == top]


# ── output helpers ────────────────────────────────────────────────────────────

def compact(v: dict) -> dict:
    out = {k: v[k] for k in ("entity_id", "label", "state", "bin_full", "battery",
                              "area", "floor") if v.get(k) is not None}
    if v.get("bin_full"):
        out["warning"] = "bin_full — empty before running"
    return out


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2))


# ── commands ──────────────────────────────────────────────────────────────────

def poll_state(entity_id: str, expected: set[str], attempts: int = 8,
               delay: float = 1.5) -> tuple[str, bool]:
    for i in range(attempts):
        states = run_hass_json(["state", "list", entity_id])
        state  = states[0]["state"] if states else "unknown"
        if state in expected:
            return state, True
        if i < attempts - 1:
            time.sleep(delay)
    return state, False


def do_status(vacuums: list[dict]) -> int:
    print_json({"status": "ok", "vacuums": [compact(v) for v in vacuums]})
    return 0


def do_action(service: str, vacuums: list[dict],
              expected_states: set[str], label: str) -> int:
    results = []
    for v in vacuums:
        try:
            run_hass(["service", "call", service,
                      "--arguments", f"entity_id={v['entity_id']}"])
            state, confirmed = poll_state(v["entity_id"], expected_states)
            results.append({**compact(v),
                            "action": label,
                            "state_confirmed": confirmed,
                            "result_state": state})
        except VacuumError as exc:
            results.append({**compact(v), "action": "error", "message": str(exc)})

    print_json({"status": "ok", "results": results})
    return 0


# ── main ──────────────────────────────────────────────────────────────────────

ACTIONS = {
    "start":  ("vacuum.start",          {"cleaning"},         "start"),
    "stop":   ("vacuum.stop",           {"idle", "docked"},   "stop"),
    "pause":  ("vacuum.pause",          {"paused"},           "pause"),
    "return": ("vacuum.return_to_base", {"returning", "docked"}, "return"),
    "locate": ("vacuum.locate",         {"docked", "idle", "cleaning"}, "locate"),
}


async def main_async(args: argparse.Namespace) -> int:
    try:
        all_vacuums = await build_vacuum_list()
    except Exception as exc:
        print_json({"status": "error", "message": str(exc)})
        return 3

    matched = resolve(getattr(args, "query", None), all_vacuums)

    if not matched:
        print_json({
            "status": "no_match",
            "query": getattr(args, "query", None),
            "available": [compact(v) for v in all_vacuums],
        })
        return 1

    if args.command == "status":
        return do_status(matched)

    service, expected, label = ACTIONS[args.command]
    return do_action(service, matched, expected, label)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    for cmd in ("status", "start", "stop", "pause", "return", "locate"):
        sp = sub.add_parser(cmd)
        sp.add_argument("query", nargs="?", default=None,
                        help="Vacuum name, area, floor, or 'all'")

    return p


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
