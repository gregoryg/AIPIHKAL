#!/usr/bin/env python3
"""Run text through the selected Home Assistant Assist pipeline."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

import ha_api


DONE_RESPONSE_TYPES = {"action_done", "query_answer"}
MAX_PHRASE_LENGTH = 2000
MAX_REPORTED_EVENTS = 100


def select_pipeline(
    pipeline_result: dict[str, Any],
    selector: str | None,
) -> dict[str, Any]:
    """Select the preferred pipeline or one exact ID/name match."""
    pipelines = pipeline_result.get("pipelines", [])
    if not isinstance(pipelines, list) or any(
        not isinstance(item, dict) for item in pipelines
    ):
        raise ha_api.HomeAssistantApiError("Pipeline list has an unexpected shape")

    wanted = selector or pipeline_result.get("preferred_pipeline")
    if not wanted:
        raise ha_api.HomeAssistantApiError("Home Assistant has no preferred pipeline")

    id_matches = [item for item in pipelines if item.get("id") == wanted]
    if len(id_matches) == 1:
        return id_matches[0]

    folded = str(wanted).casefold()
    name_matches = [
        item
        for item in pipelines
        if str(item.get("name", "")).casefold() == folded
    ]
    if len(name_matches) == 1:
        return name_matches[0]
    if len(name_matches) > 1:
        raise ha_api.HomeAssistantApiError(f"Pipeline name is ambiguous: {wanted}")
    raise ha_api.HomeAssistantApiError(f"Pipeline not found: {wanted}")


def compact_events(
    events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, int, bool]:
    """Drop progress ticks and cap the remaining event records."""
    progress_count = sum(event.get("type") == "intent-progress" for event in events)
    compact = [event for event in events if event.get("type") != "intent-progress"]
    return (
        compact[:MAX_REPORTED_EVENTS],
        progress_count,
        len(compact),
        len(compact) > MAX_REPORTED_EVENTS,
    )


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a bounded record for one Assist pipeline event."""
    if not isinstance(event, dict):
        raise ha_api.HomeAssistantApiError("Assist event has an unexpected shape")
    event_type = event.get("type", "unknown")
    data = event.get("data") or {}
    if not isinstance(data, dict):
        raise ha_api.HomeAssistantApiError("Assist event has an unexpected shape")
    normalized: dict[str, Any] = {
        "type": ha_api.bounded_text(event_type, 100) or "unknown"
    }

    if event_type == "run-start":
        normalized.update(
            pipeline=ha_api.bounded_text(data.get("pipeline"), 200),
            language=ha_api.bounded_text(data.get("language"), 100),
            conversation_id=ha_api.bounded_text(
                data.get("conversation_id"), 200
            ),
        )
    elif event_type == "intent-start":
        normalized.update(
            engine=ha_api.bounded_text(data.get("engine"), 200),
            language=ha_api.bounded_text(data.get("language"), 100),
            input=ha_api.bounded_text(data.get("intent_input")),
            prefer_local_intents=data.get("prefer_local_intents") is True,
        )
    elif event_type == "intent-end":
        output = data.get("intent_output") or {}
        if not isinstance(output, dict):
            raise ha_api.HomeAssistantApiError("Assist output has an unexpected shape")
        response = output.get("response") or {}
        if not isinstance(response, dict):
            raise ha_api.HomeAssistantApiError(
                "Assist response has an unexpected shape"
            )
        speech = response.get("speech") or {}
        if not isinstance(speech, dict):
            raise ha_api.HomeAssistantApiError("Assist speech has an unexpected shape")
        plain_speech = speech.get("plain") or {}
        if not isinstance(plain_speech, dict):
            raise ha_api.HomeAssistantApiError("Assist speech has an unexpected shape")
        normalized.update(
            processed_locally=data.get("processed_locally") is True,
            response_type=ha_api.bounded_text(response.get("response_type"), 100),
            speech=ha_api.bounded_text(plain_speech.get("speech")),
            conversation_id=ha_api.bounded_text(
                output.get("conversation_id"), 200
            ),
        )
    elif event_type == "error":
        normalized.update(
            code=ha_api.bounded_text(data.get("code"), 100),
            message=ha_api.bounded_text(data.get("message")),
        )
    return normalized


async def receive_result(
    websocket: Any,
    request_id: int,
    timeout: float,
) -> dict[str, Any]:
    """Receive one successful WebSocket result for REQUEST_ID."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise TimeoutError("Assist pipeline request timed out")
        raw = await asyncio.wait_for(websocket.recv(), timeout=remaining)
        message = ha_api.decode_message(raw, "Assist pipeline")
        if message.get("id") != request_id or message.get("type") != "result":
            continue
        if not message.get("success"):
            api_error = message.get("error", {})
            if not isinstance(api_error, dict):
                raise ha_api.HomeAssistantApiError(
                    "Assist pipeline returned a malformed error"
                )
            raise ha_api.HomeAssistantApiError(
                f"Home Assistant rejected {api_error.get('code', 'unknown')}: "
                f"{api_error.get('message', 'request rejected')}"
            )
        return message


async def run_pipeline(phrase: str, selector: str | None) -> dict[str, Any]:
    """Run an intent-only Assist pipeline and return compact evidence."""
    if ha_api.websockets is None:
        raise ha_api.HomeAssistantApiError("Python package 'websockets' is required")
    server, token, timeout = ha_api.environment()

    async with ha_api.websockets.connect(
        ha_api.websocket_url(server),
        open_timeout=timeout,
        close_timeout=timeout,
    ) as websocket:
        await ha_api.authenticate(websocket, token, timeout)
        await websocket.send(
            json.dumps({"id": 1, "type": "assist_pipeline/pipeline/list"})
        )
        pipeline_message = await receive_result(websocket, 1, timeout)
        pipeline_result = pipeline_message.get("result") or {}
        if not isinstance(pipeline_result, dict):
            raise ha_api.HomeAssistantApiError(
                "Pipeline list has an unexpected shape"
            )
        pipeline = select_pipeline(pipeline_result, selector)
        if not pipeline.get("id"):
            raise ha_api.HomeAssistantApiError("Selected pipeline has no ID")

        await websocket.send(
            json.dumps(
                {
                    "id": 2,
                    "type": "assist_pipeline/run",
                    "start_stage": "intent",
                    "end_stage": "intent",
                    "input": {"text": phrase},
                    "pipeline": pipeline["id"],
                    "timeout": int(timeout),
                }
            )
        )

        events: list[dict[str, Any]] = []
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError("Assist pipeline run timed out")
            raw = await asyncio.wait_for(websocket.recv(), timeout=remaining)
            message = ha_api.decode_message(raw, "Assist pipeline")
            if message.get("id") != 2:
                continue
            if message.get("type") == "result" and not message.get("success"):
                api_error = message.get("error", {})
                if not isinstance(api_error, dict):
                    raise ha_api.HomeAssistantApiError(
                        "Assist run returned a malformed error"
                    )
                raise ha_api.HomeAssistantApiError(
                    f"Assist run rejected: {api_error.get('message', 'unknown error')}"
                )
            if message.get("type") != "event":
                continue

            event = normalize_event(message.get("event") or {})
            events.append(event)
            if event["type"] in {"run-end", "error"}:
                break

    intent_start = next(
        (event for event in events if event["type"] == "intent-start"), {}
    )
    intent_end = next(
        (event for event in events if event["type"] == "intent-end"), {}
    )
    pipeline_error = next(
        (event for event in events if event["type"] == "error"), None
    )
    (
        events,
        progress_event_count,
        event_count,
        events_truncated,
    ) = compact_events(events)
    return {
        "status": "error" if pipeline_error else "ok",
        "phrase": ha_api.bounded_text(phrase, MAX_PHRASE_LENGTH),
        "pipeline": {
            "id": ha_api.bounded_text(pipeline.get("id"), 200),
            "name": ha_api.bounded_text(pipeline.get("name"), 200),
            "conversation_engine": ha_api.bounded_text(
                pipeline.get("conversation_engine"), 200
            ),
            "prefer_local_intents": pipeline.get("prefer_local_intents"),
        },
        "engine": intent_start.get("engine"),
        "processed_locally": intent_end.get("processed_locally"),
        "response_type": intent_end.get("response_type"),
        "speech": intent_end.get("speech"),
        "conversation_id": intent_end.get("conversation_id"),
        "error": pipeline_error,
        "progress_event_count": progress_event_count,
        "event_count": event_count,
        "events_truncated": events_truncated,
        "events": events,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phrase", help="Text that may execute Home Assistant actions")
    parser.add_argument(
        "--pipeline",
        help="Exact pipeline ID or name; default preferred",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Acknowledge that processing the phrase may mutate Home Assistant",
    )
    return parser


def main() -> int:
    """Run the CLI and return a stable exit code."""
    args = build_parser().parse_args()
    if not args.phrase.strip() or len(args.phrase) > MAX_PHRASE_LENGTH:
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": (
                        f"phrase must contain text and be at most "
                        f"{MAX_PHRASE_LENGTH} characters"
                    ),
                },
                indent=2,
            )
        )
        return 2
    if not args.execute:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "phrase": args.phrase,
                    "message": "Pass --execute; an Assist phrase may perform actions.",
                },
                indent=2,
            )
        )
        return 2

    try:
        output = asyncio.run(run_pipeline(args.phrase, args.pipeline))
    except (ha_api.HomeAssistantApiError, TimeoutError, OSError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "infrastructure_error",
                    "phrase": args.phrase,
                    "message": str(exc),
                },
                indent=2,
            )
        )
        return 3

    print(json.dumps(output, indent=2))
    if output["status"] != "ok":
        return 2
    if output["response_type"] not in DONE_RESPONSE_TYPES:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
