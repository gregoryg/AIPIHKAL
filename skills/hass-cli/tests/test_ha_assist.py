"""Offline tests for preferred-pipeline Assist execution."""

from __future__ import annotations

import asyncio
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "ha_assist.py"
SPEC = importlib.util.spec_from_file_location("ha_assist", SCRIPT)
assert SPEC and SPEC.loader
ha_assist = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ha_assist)


def pipeline_records(
    *,
    speech: str,
    response_type: str = "action_done",
    continue_conversation: bool = False,
) -> dict:
    """Build representative text-only Assist pipeline events."""
    return {
        "subscribed": True,
        "events": [
            {
                "type": "run-start",
                "data": {"pipeline": {"id": "preferred-id", "name": "GladOS"}},
            },
            {"type": "intent-start", "data": {}},
            {
                "type": "intent-end",
                "data": {
                    "processed_locally": False,
                    "intent_output": {
                        "conversation_id": "conversation-123",
                        "continue_conversation": continue_conversation,
                        "response": {
                            "response_type": response_type,
                            "speech": {"plain": {"speech": speech}},
                            "data": {},
                        },
                    },
                },
            },
            {"type": "run-end", "data": None},
        ],
    }


class AssistRequestTests(unittest.TestCase):
    def test_default_request_uses_preferred_text_only_pipeline(self) -> None:
        request = ha_assist.build_run_request("remind me in 34 minutes")

        self.assertEqual(request["type"], "assist_pipeline/run")
        self.assertEqual(
            (request["start_stage"], request["end_stage"]), ("intent", "intent")
        )
        self.assertEqual(request["input"], {"text": "remind me in 34 minutes"})
        self.assertEqual(request["timeout"], 120.0)
        self.assertNotIn("pipeline", request)
        self.assertNotIn("conversation_id", request)

    def test_continuation_preserves_pipeline_and_conversation(self) -> None:
        request = ha_assist.build_run_request(
            "At 3 PM",
            pipeline_id="pipeline-1",
            conversation_id="conversation-123",
        )

        self.assertEqual(request["pipeline"], "pipeline-1")
        self.assertEqual(request["conversation_id"], "conversation-123")


class AssistInterpretationTests(unittest.TestCase):
    def test_confirmed_calendar_response_is_success(self) -> None:
        speech = (
            "I added the Google Calendar reminder: have a cow, "
            "Wednesday, September 23 at 10:46 AM."
        )
        output, code = ha_assist.interpret(
            "remind me to have a cow in 34 minutes",
            pipeline_records(speech=speech),
        )

        self.assertEqual((output["status"], code), ("ok", 0))
        self.assertEqual(output["speech"], speech)
        self.assertEqual(output["pipeline"], {"id": "preferred-id", "name": "GladOS"})
        self.assertFalse(output["processed_locally"])
        self.assertNotIn("raw", output)

    def test_clarification_preserves_question_and_conversation_id(self) -> None:
        output, code = ha_assist.interpret(
            "remind me to have a cow sometime",
            pipeline_records(
                speech="What day and time should I remind you?",
                continue_conversation=True,
            ),
        )

        self.assertEqual((output["status"], code), ("clarification_needed", 1))
        self.assertEqual(output["conversation_id"], "conversation-123")
        self.assertTrue(output["continue_conversation"])
        self.assertIn("Do not claim", output["note"])

    def test_pipeline_error_refuses_fallback(self) -> None:
        output, code = ha_assist.interpret(
            "remind me tomorrow",
            {
                "events": [
                    {
                        "type": "error",
                        "data": {"code": "timeout", "message": "Pipeline timed out"},
                    },
                    {"type": "run-end", "data": None},
                ]
            },
        )

        self.assertEqual((output["status"], code), ("error", 2))
        self.assertEqual(output["error_code"], "timeout")
        self.assertIn("do not claim", output["note"].lower())

    def test_unknown_response_type_is_not_success(self) -> None:
        output, code = ha_assist.interpret(
            "do something",
            pipeline_records(speech="Maybe", response_type="future_response"),
        )

        self.assertEqual((output["status"], code), ("error", 2))

    def test_debug_includes_raw_events(self) -> None:
        records = pipeline_records(speech="Done")
        output, code = ha_assist.interpret("do something", records, include_raw=True)

        self.assertEqual(code, 0)
        self.assertIs(output["raw"], records)


class AssistTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_receive_is_bounded(self) -> None:
        class SlowWebSocket:
            async def recv(self) -> str:
                await asyncio.sleep(1)
                return "{}"

        with self.assertRaisesRegex(RuntimeError, "waiting for Assist response"):
            await ha_assist.receive_json(SlowWebSocket(), "Assist response", 0.001)

    async def test_pipeline_run_is_bounded(self) -> None:
        class SlowWebSocket:
            async def recv(self) -> str:
                await asyncio.sleep(1)
                return "{}"

        with self.assertRaisesRegex(
            RuntimeError, "waiting for Assist pipeline completion"
        ):
            await ha_assist.receive_run_records(SlowWebSocket(), timeout=0.001)


if __name__ == "__main__":
    unittest.main()
