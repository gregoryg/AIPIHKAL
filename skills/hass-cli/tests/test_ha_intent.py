"""Offline tests for conservative Home Assistant intent interpretation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "ha_intent.py"
SPEC = importlib.util.spec_from_file_location("ha_intent", SCRIPT)
assert SPEC and SPEC.loader
ha_intent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ha_intent)


class IntentInterpretationTests(unittest.TestCase):
    def test_known_no_match_allows_fallback(self) -> None:
        output, code = ha_intent.interpret(
            "turn on reading lamp",
            {"success": False, "error": {"code": "no_intent_match", "message": "No match"}},
        )
        self.assertEqual((output["status"], code), ("no_match", 1))

    def test_unknown_websocket_error_stops_fallback(self) -> None:
        output, code = ha_intent.interpret(
            "turn on reading lamp",
            {"success": False, "error": {"code": "unknown_error", "message": "Internal error"}},
        )
        self.assertEqual((output["status"], code), ("error", 2))
        self.assertIn("do not perform", output["note"])

    def test_action_done_is_success(self) -> None:
        output, code = ha_intent.interpret(
            "good night",
            {
                "success": True,
                "result": {
                    "response": {
                        "response_type": "action_done",
                        "speech": {"plain": {"speech": "Done"}},
                        "data": {"success": [], "failed": []},
                    }
                },
            },
        )
        self.assertEqual((output["status"], code), ("ok", 0))

    def test_unknown_response_type_stops_fallback(self) -> None:
        output, code = ha_intent.interpret(
            "do something",
            {
                "success": True,
                "result": {
                    "response": {
                        "response_type": "future_response",
                        "speech": {},
                        "data": {},
                    }
                },
            },
        )
        self.assertEqual((output["status"], code), ("error", 2))


if __name__ == "__main__":
    unittest.main()
