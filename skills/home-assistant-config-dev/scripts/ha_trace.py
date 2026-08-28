#!/usr/bin/env python3
"""List and inspect compact Home Assistant automation/script traces."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

import ha_api


TRACE_DOMAINS = {"automation", "script"}
MAX_TRACE_PATHS = 500


def validate_identity(domain: str, item_id: str) -> None:
    """Reject unsupported or malformed trace identities."""
    if domain not in TRACE_DOMAINS:
        raise ValueError("domain must be automation or script")
    if (
        not item_id
        or len(item_id) > 200
        or any(character.isspace() for character in item_id)
    ):
        raise ValueError("item_id must be 1-200 characters without whitespace")


def normalize_summary(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize one trace-list record."""
    timestamp = raw.get("timestamp") or {}
    if not isinstance(timestamp, dict):
        raise ha_api.HomeAssistantApiError("Trace summary has an unexpected shape")
    return {
        "run_id": ha_api.bounded_text(raw.get("run_id"), 200),
        "state": ha_api.bounded_text(raw.get("state"), 100),
        "script_execution": ha_api.bounded_text(
            raw.get("script_execution"), 100
        ),
        "start": ha_api.bounded_text(timestamp.get("start"), 100),
        "finish": ha_api.bounded_text(timestamp.get("finish"), 100),
        "last_step": ha_api.bounded_text(raw.get("last_step"), 300),
        "error": ha_api.bounded_text(raw.get("error"), 1000),
        "trigger": ha_api.bounded_text(raw.get("trigger"), 300),
    }


def normalize_trace(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize one detailed trace without returning config or secrets."""
    trace_paths = raw.get("trace") or {}
    if not isinstance(trace_paths, dict):
        raise ha_api.HomeAssistantApiError("Detailed trace has an unexpected shape")
    timestamp = raw.get("timestamp") or {}
    if not isinstance(timestamp, dict):
        raise ha_api.HomeAssistantApiError("Detailed trace has an unexpected shape")
    path_names = sorted(str(path) for path in trace_paths)
    reported_paths = [
        ha_api.bounded_text(path, 300)
        for path in path_names[:MAX_TRACE_PATHS]
    ]
    return {
        "run_id": ha_api.bounded_text(raw.get("run_id"), 200),
        "state": ha_api.bounded_text(raw.get("state"), 100),
        "script_execution": ha_api.bounded_text(
            raw.get("script_execution"), 100
        ),
        "start": ha_api.bounded_text(timestamp.get("start"), 100),
        "finish": ha_api.bounded_text(timestamp.get("finish"), 100),
        "last_step": ha_api.bounded_text(raw.get("last_step"), 300),
        "error": ha_api.bounded_text(raw.get("error"), 1000),
        "path_count": len(path_names),
        "paths_truncated": len(path_names) > MAX_TRACE_PATHS,
        "trace_paths": reported_paths,
    }


async def list_traces(domain: str, item_id: str, limit: int) -> dict[str, Any]:
    """List compact recent traces."""
    validate_identity(domain, item_id)
    response = await ha_api.websocket_request(
        "trace/list",
        {"domain": domain, "item_id": item_id},
    )
    raw_traces = response.get("result") or []
    if not isinstance(raw_traces, list):
        raise ha_api.HomeAssistantApiError("Trace list has an unexpected shape")
    selected = raw_traces[-limit:]
    traces = [normalize_summary(item) for item in selected if isinstance(item, dict)]
    return {
        "status": "ok",
        "domain": domain,
        "item_id": item_id,
        "count": len(traces),
        "traces": traces,
    }


async def get_trace(domain: str, item_id: str, run_id: str) -> dict[str, Any]:
    """Get one compact detailed trace."""
    validate_identity(domain, item_id)
    if (
        not run_id
        or len(run_id) > 200
        or any(character.isspace() for character in run_id)
    ):
        raise ValueError("run_id must be 1-200 characters without whitespace")
    response = await ha_api.websocket_request(
        "trace/get",
        {"domain": domain, "item_id": item_id, "run_id": run_id},
    )
    raw_trace = response.get("result") or {}
    if not isinstance(raw_trace, dict):
        raise ha_api.HomeAssistantApiError("Detailed trace has an unexpected shape")
    return {
        "status": "ok",
        "domain": domain,
        "item_id": item_id,
        "trace": normalize_trace(raw_trace),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List recent traces")
    list_parser.add_argument("domain", choices=sorted(TRACE_DOMAINS))
    list_parser.add_argument("item_id")
    list_parser.add_argument("--limit", type=int, default=10)

    get_parser = subparsers.add_parser("get", help="Get one detailed trace")
    get_parser.add_argument("domain", choices=sorted(TRACE_DOMAINS))
    get_parser.add_argument("item_id")
    get_parser.add_argument("run_id")
    return parser


def main() -> int:
    """Run the trace CLI."""
    args = build_parser().parse_args()
    try:
        if args.command == "list":
            if not 1 <= args.limit <= 100:
                raise ValueError("limit must be between 1 and 100")
            output = asyncio.run(list_traces(args.domain, args.item_id, args.limit))
        else:
            output = asyncio.run(get_trace(args.domain, args.item_id, args.run_id))
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 2
    except (ha_api.HomeAssistantApiError, TimeoutError, OSError) as exc:
        print(
            json.dumps(
                {"status": "infrastructure_error", "message": str(exc)},
                indent=2,
            )
        )
        return 3

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
