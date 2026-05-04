#!/usr/bin/env python3
"""Send a natural-language phrase through Home Assistant's intent pipeline.

Uses the HA built-in conversation agent (conversation.home_assistant), which
applies HA's NLU intent matching — the same path as voice commands via Assist.

This means custom intent phrases and automations triggered by voice (e.g.
"turn off bathroom" → timed bathroom automation) will fire correctly, rather
than being replaced by a direct entity service call.

Exit codes:
  0  intent matched and executed (action_done)
  1  intent not recognised or no valid targets — caller should fall back to
     ha-on / ha-off / ha-trigger
  2  HA returned an error response (see 'error_code' in JSON output)
  3  infrastructure error (auth failure, connection problem, etc.)

The JSON output always contains:
  status          "ok" | "no_match" | "error" | "infrastructure_error"
  phrase          the phrase that was sent
  response_type   the HA response_type string (action_done, error, etc.)
  speech          what HA said back
  success         list of entities HA reports as acted on (may be empty for automations)
  failed          list of entities HA reports as failed
  raw             full HA response payload (for debugging)
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
    print(json.dumps({"status": "infrastructure_error", "message": "websockets library not found"}))
    sys.exit(3)

HASS_SERVER = os.environ.get("HASS_SERVER", "http://172.16.17.7:8123")
HASS_TOKEN = os.environ.get("HASS_TOKEN", "")
HA_CONVERSATION_AGENT = "conversation.home_assistant"

# HA response_type values that mean "matched and did something"
DONE_TYPES = {"action_done", "query_answer"}

# HA error codes that mean "I don't understand" (caller should fall back)
NO_MATCH_CODES = {
    "no_intent_match",
    "no_valid_targets",
    "intent_not_recognized",
}


def ws_url() -> str:
    return HASS_SERVER.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"


async def process_intent(phrase: str) -> dict[str, Any]:
    """Send phrase through HA intent pipeline and return structured result."""
    if not HASS_TOKEN:
        raise RuntimeError("HASS_TOKEN is not set")

    async with websockets.connect(ws_url()) as ws:
        raw = await ws.recv()
        if json.loads(raw).get("type") != "auth_required":
            raise RuntimeError("Expected auth_required")
        await ws.send(json.dumps({"type": "auth", "access_token": HASS_TOKEN}))
        auth = json.loads(await ws.recv())
        if auth.get("type") != "auth_ok":
            raise RuntimeError(f"Auth failed: {auth}")

        await ws.send(json.dumps({
            "id": 1,
            "type": "conversation/process",
            "text": phrase,
            "agent_id": HA_CONVERSATION_AGENT,
        }))

        # Drain until we get our response
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                break

    return msg


def interpret(phrase: str, msg: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Turn the raw WS result into a clean output dict and an exit code."""
    if not msg.get("success"):
        err = msg.get("error", {})
        code = err.get("code", "unknown")
        # HA WebSocket-level errors (e.g. unknown_error from HA itself)
        # Treat as no_match so callers fall back gracefully
        return {
            "status": "no_match",
            "phrase": phrase,
            "response_type": None,
            "speech": None,
            "success": [],
            "failed": [],
            "note": (
                f"HA returned a WebSocket-level error ({code}): {err.get('message', '')}. "
                "Phrase likely not recognised by the intent engine — fall back to ha-on/ha-off/ha-trigger."
            ),
            "raw": msg,
        }, 1

    resp = msg["result"]["response"]
    response_type = resp.get("response_type")
    speech = resp.get("speech", {}).get("plain", {}).get("speech")
    data = resp.get("data", {})
    success_entities = data.get("success", [])
    failed_entities = data.get("failed", [])

    if response_type in DONE_TYPES:
        note = None
        if response_type == "action_done" and not success_entities:
            note = (
                "action_done with no entity list — likely an automation trigger. "
                "HA does not report individual entity outcomes for automation-triggered intents."
            )
        return {
            "status": "ok",
            "phrase": phrase,
            "response_type": response_type,
            "speech": speech,
            "success": success_entities,
            "failed": failed_entities,
            "note": note,
            "raw": resp,
        }, 0

    if response_type == "error":
        err_code = data.get("code", "unknown")
        if err_code in NO_MATCH_CODES:
            return {
                "status": "no_match",
                "phrase": phrase,
                "response_type": response_type,
                "speech": speech,
                "success": [],
                "failed": [],
                "note": (
                    f"Intent not recognised ({err_code}). "
                    "Fall back to ha-on / ha-off / ha-trigger."
                ),
                "raw": resp,
            }, 1
        return {
            "status": "error",
            "phrase": phrase,
            "response_type": response_type,
            "speech": speech,
            "error_code": err_code,
            "success": [],
            "failed": failed_entities,
            "raw": resp,
        }, 2

    # Unknown response_type — surface it and treat as no_match
    return {
        "status": "no_match",
        "phrase": phrase,
        "response_type": response_type,
        "speech": speech,
        "success": success_entities,
        "failed": failed_entities,
        "note": f"Unrecognised response_type '{response_type}' — treating as no_match.",
        "raw": resp,
    }, 1


async def main_async(phrase: str) -> int:
    try:
        msg = await process_intent(phrase)
    except Exception as exc:
        print(json.dumps({
            "status": "infrastructure_error",
            "phrase": phrase,
            "message": str(exc),
        }, indent=2))
        return 3

    output, code = interpret(phrase, msg)
    print(json.dumps(output, indent=2))
    return code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phrase", help="Natural language phrase to send to HA's intent engine")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(main_async(args.phrase))


if __name__ == "__main__":
    sys.exit(main())
