#!/usr/bin/env python3
"""Run text through Home Assistant's preferred Assist pipeline.

Unlike ``ha-intent``, this wrapper uses ``assist_pipeline/run`` so the preferred
pipeline's conversation agent and contributed LLM tools are available. This is
required for home-specific conversational features such as calendar-backed voice
reminders.

A response that sets ``continue_conversation`` is returned as
``clarification_needed`` with its ``conversation_id``. The wrapper never invents
a follow-up answer. A later caller may explicitly continue by passing that ID.

Exit codes:
  0  Assist completed the turn
  1  Assist requested clarification; no completion should be claimed
  2  Home Assistant or the Assist pipeline reported an error
  3  infrastructure error (auth failure, timeout, connection problem, etc.)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

try:
    import websockets
except ImportError:
    websockets = None

HASS_SERVER = os.environ.get("HASS_SERVER", "")
HASS_TOKEN = os.environ.get("HASS_TOKEN", "")
CONNECT_TIMEOUT = float(os.environ.get("HA_COMMAND_TIMEOUT", "30"))
ASSIST_TIMEOUT = 120.0
DONE_TYPES = {"action_done", "query_answer"}


def ws_url() -> str:
    """Return the configured Home Assistant WebSocket URL."""
    return (
        HASS_SERVER.replace("https://", "wss://")
        .replace("http://", "ws://")
        .rstrip("/")
        + "/api/websocket"
    )


async def receive_json(ws: Any, context: str, timeout: float) -> dict[str, Any]:
    """Receive one bounded WebSocket JSON message."""
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
    except TimeoutError as exc:
        raise RuntimeError(
            f"Timed out after {timeout:g} seconds waiting for {context}"
        ) from exc
    return json.loads(raw)


def build_run_request(
    phrase: str,
    *,
    pipeline_id: str | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Build a text-only preferred-pipeline request."""
    request: dict[str, Any] = {
        "id": 1,
        "type": "assist_pipeline/run",
        "start_stage": "intent",
        "end_stage": "intent",
        "input": {"text": phrase},
        "timeout": ASSIST_TIMEOUT,
    }
    if pipeline_id:
        request["pipeline"] = pipeline_id
    if conversation_id:
        request["conversation_id"] = conversation_id
    return request


async def receive_run_records(
    ws: Any, timeout: float = ASSIST_TIMEOUT
) -> dict[str, Any]:
    """Collect one bounded Assist pipeline run."""

    async def collect() -> dict[str, Any]:
        records: dict[str, Any] = {"events": []}
        while True:
            message = json.loads(await ws.recv())
            if message.get("id") != 1:
                continue
            if message.get("type") == "result":
                if not message.get("success"):
                    records["request_error"] = message.get("error", {})
                    break
                records["subscribed"] = True
                continue
            if message.get("type") != "event":
                continue

            event = message.get("event", {})
            records["events"].append(event)
            if event.get("type") == "run-end":
                break
        return records

    try:
        return await asyncio.wait_for(collect(), timeout=timeout)
    except TimeoutError as exc:
        raise RuntimeError(
            f"Timed out after {timeout:g} seconds waiting for Assist pipeline completion"
        ) from exc


async def process_assist(
    phrase: str,
    *,
    pipeline_id: str | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Run one text turn and return its bounded protocol records."""
    if websockets is None:
        raise RuntimeError("websockets library not found; see references/setup.md")
    if not HASS_TOKEN:
        raise RuntimeError("HASS_TOKEN is not set")

    async with websockets.connect(
        ws_url(),
        open_timeout=CONNECT_TIMEOUT,
        close_timeout=CONNECT_TIMEOUT,
    ) as ws:
        auth_required = await receive_json(
            ws, "authentication challenge", CONNECT_TIMEOUT
        )
        if auth_required.get("type") != "auth_required":
            raise RuntimeError("Expected auth_required")
        await ws.send(json.dumps({"type": "auth", "access_token": HASS_TOKEN}))
        auth = await receive_json(ws, "authentication response", CONNECT_TIMEOUT)
        if auth.get("type") != "auth_ok":
            raise RuntimeError("Home Assistant authentication failed")

        await ws.send(
            json.dumps(
                build_run_request(
                    phrase,
                    pipeline_id=pipeline_id,
                    conversation_id=conversation_id,
                )
            )
        )

        return await receive_run_records(ws)


def _event(records: dict[str, Any], event_type: str) -> dict[str, Any] | None:
    """Return the first event matching EVENT_TYPE."""
    for event in records.get("events", []):
        if event.get("type") == event_type:
            return event
    return None


def _speech(response: dict[str, Any]) -> str | None:
    """Extract plain speech from an Assist response."""
    speech = response.get("speech", {}).get("plain", {}).get("speech")
    return speech if isinstance(speech, str) else None


def interpret(
    phrase: str,
    records: dict[str, Any],
    *,
    include_raw: bool = False,
) -> tuple[dict[str, Any], int]:
    """Normalize pipeline records into compact agent-facing JSON."""
    output: dict[str, Any] = {"phrase": phrase}

    request_error = records.get("request_error")
    if request_error:
        output.update(
            {
                "status": "error",
                "error_code": request_error.get("code", "unknown"),
                "message": request_error.get("message"),
                "note": "Home Assistant rejected the Assist request; do not retry blindly.",
            }
        )
        code = 2
    elif error_event := _event(records, "error"):
        error_data = error_event.get("data", {})
        output.update(
            {
                "status": "error",
                "error_code": error_data.get("code", "unknown"),
                "message": error_data.get("message"),
                "note": "The Assist pipeline failed; do not claim the requested action completed.",
            }
        )
        code = 2
    elif not (intent_end := _event(records, "intent-end")):
        output.update(
            {
                "status": "error",
                "message": "Assist ended without an intent result",
                "note": "Do not claim the requested action completed.",
            }
        )
        code = 2
    else:
        event_data = intent_end.get("data", {})
        intent_output = event_data.get("intent_output", {})
        response = intent_output.get("response", {})
        continue_conversation = bool(intent_output.get("continue_conversation", False))
        response_type = response.get("response_type")
        output.update(
            {
                "conversation_id": intent_output.get("conversation_id"),
                "continue_conversation": continue_conversation,
                "response_type": response_type,
                "speech": _speech(response),
                "processed_locally": event_data.get("processed_locally"),
            }
        )

        run_start = _event(records, "run-start")
        pipeline = (run_start or {}).get("data", {}).get("pipeline")
        if isinstance(pipeline, dict):
            output["pipeline"] = {
                key: pipeline.get(key) for key in ("id", "name") if pipeline.get(key)
            }

        if continue_conversation:
            output.update(
                {
                    "status": "clarification_needed",
                    "note": (
                        "Assist requested another turn. Do not claim the requested "
                        "action completed; continue only with a human-supplied answer "
                        "and this conversation_id."
                    ),
                }
            )
            code = 1
        elif response_type in DONE_TYPES:
            output["status"] = "ok"
            code = 0
        else:
            output.update(
                {
                    "status": "error",
                    "error_code": response.get("data", {}).get("code", "unknown"),
                    "note": "Assist did not report a completed turn; do not perform a fallback action.",
                }
            )
            code = 2

    if include_raw:
        output["raw"] = records
    return output, code


async def main_async(
    phrase: str,
    *,
    pipeline_id: str | None = None,
    conversation_id: str | None = None,
    debug: bool = False,
) -> int:
    """Run Assist and print one compact JSON result."""
    try:
        records = await process_assist(
            phrase,
            pipeline_id=pipeline_id,
            conversation_id=conversation_id,
        )
    except Exception as exc:  # noqa: BLE001 - normalize dependency and transport failures
        print(
            json.dumps(
                {
                    "status": "infrastructure_error",
                    "phrase": phrase,
                    "message": str(exc),
                },
                separators=(",", ":"),
            )
        )
        return 3

    output, code = interpret(phrase, records, include_raw=debug)
    print(json.dumps(output, separators=(",", ":")))
    return code


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("phrase", help="Text to send through the Assist pipeline")
    parser.add_argument(
        "--pipeline",
        help="Pipeline ID; omit to use Home Assistant's preferred pipeline",
    )
    parser.add_argument(
        "--conversation-id",
        help="Continue a prior Assist conversation with a human-supplied answer",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Include bounded raw pipeline events",
    )
    return parser


def main() -> int:
    """Run the command-line entry point."""
    args = build_parser().parse_args()
    return asyncio.run(
        main_async(
            args.phrase,
            pipeline_id=args.pipeline,
            conversation_id=args.conversation_id,
            debug=args.debug,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
