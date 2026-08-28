#!/usr/bin/env python3
"""Query response-returning Home Assistant calendar events."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import re
import sys
from typing import Any

import ha_api


DEFAULT_EVENT_LIMIT = 100
MAX_EVENT_LIMIT = 500


def parse_datetime(value: str) -> datetime:
    """Parse one ISO date/time for validation and ordering."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO date/time") from exc


def event_time(value: Any) -> str | None:
    """Normalize a calendar event date or dateTime value."""
    if isinstance(value, dict):
        value = value.get("dateTime") or value.get("date")
    return ha_api.bounded_text(value, 100)


def normalize_response(
    response: dict[str, Any],
    entity_id: str,
    *,
    include_description: bool,
    limit: int = DEFAULT_EVENT_LIMIT,
) -> dict[str, Any]:
    """Return bounded event records from a calendar service response."""
    service_response = response.get("service_response") or {}
    if not isinstance(service_response, dict):
        raise ha_api.HomeAssistantApiError("Calendar response has an unexpected shape")
    if entity_id not in service_response:
        raise ha_api.HomeAssistantApiError(
            "Calendar response does not contain the requested entity"
        )
    entity_response = service_response.get(entity_id) or {}
    if not isinstance(entity_response, dict):
        raise ha_api.HomeAssistantApiError("Calendar response has an unexpected shape")
    raw_events = entity_response.get("events") or []
    if not isinstance(raw_events, list):
        raise ha_api.HomeAssistantApiError("Calendar response has an unexpected shape")

    events: list[dict[str, Any]] = []
    for raw_event in raw_events[:limit]:
        if not isinstance(raw_event, dict):
            continue
        event = {
            "start": event_time(raw_event.get("start")),
            "end": event_time(raw_event.get("end")),
            "summary": ha_api.bounded_text(raw_event.get("summary")),
            "location": ha_api.bounded_text(raw_event.get("location"), 200),
        }
        if include_description:
            event["description"] = ha_api.bounded_text(
                raw_event.get("description"), 1000
            )
        events.append(event)

    return {
        "status": "ok",
        "entity_id": entity_id,
        "count": len(events),
        "total_count": len(raw_events),
        "truncated": len(raw_events) > limit,
        "events": events,
    }


def query_events(
    entity_id: str,
    start: str,
    end: str,
    *,
    include_description: bool,
    limit: int = DEFAULT_EVENT_LIMIT,
) -> dict[str, Any]:
    """Query one calendar entity for an explicit interval."""
    if not re.fullmatch(r"calendar\.[a-z0-9_]+", entity_id):
        raise ValueError("entity_id must be an exact calendar entity ID")
    if not 1 <= limit <= MAX_EVENT_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_EVENT_LIMIT}")
    start_time = parse_datetime(start)
    end_time = parse_datetime(end)
    try:
        ordered = start_time < end_time
    except TypeError as exc:
        raise ValueError("start and end must use compatible timezone notation") from exc
    if not ordered:
        raise ValueError("start must be before end")

    response = ha_api.rest_post(
        "services/calendar/get_events",
        {
            "entity_id": entity_id,
            "start_date_time": start,
            "end_date_time": end,
        },
        return_response=True,
    )
    return normalize_response(
        response,
        entity_id,
        include_description=include_description,
        limit=limit,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entity_id", help="Exact calendar entity ID")
    parser.add_argument("start", help="Inclusive ISO date/time")
    parser.add_argument("end", help="Exclusive ISO date/time")
    parser.add_argument(
        "--include-description",
        action="store_true",
        help="Include bounded event descriptions",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_EVENT_LIMIT,
        help=f"Maximum events returned (default {DEFAULT_EVENT_LIMIT})",
    )
    return parser


def main() -> int:
    """Run the calendar query CLI."""
    args = build_parser().parse_args()
    try:
        output = query_events(
            args.entity_id,
            args.start,
            args.end,
            include_description=args.include_description,
            limit=args.limit,
        )
    except ValueError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 2
    except (ha_api.HomeAssistantApiError, OSError) as exc:
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
