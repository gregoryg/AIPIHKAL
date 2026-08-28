"""Offline tests for the production Assist pipeline wrapper."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import ha_api  # noqa: E402
import ha_assist_run  # noqa: E402


PIPELINES = {
    "pipelines": [
        {"id": "preferred-id", "name": "GladOS"},
        {"id": "local-id", "name": "Local"},
    ],
    "preferred_pipeline": "preferred-id",
}


class AssistPipelineTests(unittest.TestCase):
    def test_selects_preferred_pipeline(self) -> None:
        selected = ha_assist_run.select_pipeline(PIPELINES, None)
        self.assertEqual(selected["id"], "preferred-id")

    def test_selects_exact_name_case_insensitively(self) -> None:
        selected = ha_assist_run.select_pipeline(PIPELINES, "local")
        self.assertEqual(selected["id"], "local-id")

    def test_rejects_unknown_pipeline(self) -> None:
        with self.assertRaisesRegex(ha_api.HomeAssistantApiError, "not found"):
            ha_assist_run.select_pipeline(PIPELINES, "missing")

    def test_compacts_and_bounds_events(self) -> None:
        with mock.patch.object(ha_assist_run, "MAX_REPORTED_EVENTS", 2):
            events, progress_count, event_count, truncated = (
                ha_assist_run.compact_events(
                    [
                        {"type": "run-start"},
                        {"type": "intent-progress"},
                        {"type": "intent-progress"},
                        {"type": "intent-start"},
                        {"type": "run-end"},
                    ]
                )
            )
        self.assertEqual(progress_count, 2)
        self.assertEqual(event_count, 3)
        self.assertTrue(truncated)
        self.assertEqual(
            [event["type"] for event in events],
            ["run-start", "intent-start"],
        )

    def test_normalizes_intent_end_without_raw_payload(self) -> None:
        event = ha_assist_run.normalize_event(
            {
                "type": "intent-end",
                "data": {
                    "processed_locally": True,
                    "intent_output": {
                        "conversation_id": "conversation-id",
                        "response": {
                            "response_type": "action_done",
                            "speech": {"plain": {"speech": "Done"}},
                            "private": "not returned",
                        },
                    },
                },
            }
        )
        self.assertEqual(event["processed_locally"], True)
        self.assertEqual(event["speech"], "Done")
        self.assertNotIn("private", event)

    def test_rejects_malformed_intent_response(self) -> None:
        with self.assertRaisesRegex(
            ha_api.HomeAssistantApiError,
            "Assist response",
        ):
            ha_assist_run.normalize_event(
                {
                    "type": "intent-end",
                    "data": {
                        "intent_output": {
                            "response": ["not", "an", "object"]
                        }
                    },
                }
            )

    def test_cli_refuses_without_execute_before_network(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "ha_assist_run.py"),
                "turn something on",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(output["status"], "refused")


if __name__ == "__main__":
    unittest.main()
