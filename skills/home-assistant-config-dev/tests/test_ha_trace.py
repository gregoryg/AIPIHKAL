"""Offline tests for compact Home Assistant trace inspection."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import ha_trace  # noqa: E402


class TraceTests(unittest.TestCase):
    def test_normalize_trace_returns_paths_not_step_payloads(self) -> None:
        output = ha_trace.normalize_trace(
            {
                "run_id": "run-1",
                "state": "stopped",
                "script_execution": "finished",
                "last_step": "action/1",
                "trace": {
                    "action/0": [{"variables": {"secret": "not returned"}}],
                    "action/1": [{"result": "done"}],
                },
                "config": {"token": "not returned"},
            }
        )
        self.assertEqual(output["trace_paths"], ["action/0", "action/1"])
        self.assertNotIn("config", output)
        self.assertNotIn("secret", str(output))

    def test_bounds_trace_paths(self) -> None:
        with mock.patch.object(ha_trace, "MAX_TRACE_PATHS", 2):
            output = ha_trace.normalize_trace(
                {
                    "run_id": "run-1",
                    "trace": {
                        "action/0": [],
                        "action/1": [],
                        "action/2": [],
                    },
                }
            )
        self.assertEqual(output["path_count"], 3)
        self.assertTrue(output["paths_truncated"])
        self.assertEqual(output["trace_paths"], ["action/0", "action/1"])

    def test_list_traces_applies_limit(self) -> None:
        response = {
            "result": [
                {"run_id": "old", "timestamp": {"start": "2026-01-01"}},
                {"run_id": "new", "timestamp": {"start": "2026-01-02"}},
            ]
        }
        with mock.patch.object(
            ha_trace.ha_api,
            "websocket_request",
            new=mock.AsyncMock(return_value=response),
        ):
            output = asyncio.run(
                ha_trace.list_traces("automation", "voice_reminder", 1)
            )
        self.assertEqual(output["count"], 1)
        self.assertEqual(output["traces"][0]["run_id"], "new")

    def test_get_trace_uses_exact_identity(self) -> None:
        response = {
            "result": {
                "run_id": "run-1",
                "trace": {"trigger/0": []},
            }
        }
        request = mock.AsyncMock(return_value=response)
        with mock.patch.object(ha_trace.ha_api, "websocket_request", new=request):
            output = asyncio.run(
                ha_trace.get_trace("script", "deliver_voice_reminder", "run-1")
            )
        self.assertEqual(output["trace"]["trace_paths"], ["trigger/0"])
        request.assert_awaited_once_with(
            "trace/get",
            {
                "domain": "script",
                "item_id": "deliver_voice_reminder",
                "run_id": "run-1",
            },
        )

    def test_rejects_unsupported_domain(self) -> None:
        with self.assertRaisesRegex(ValueError, "automation or script"):
            ha_trace.validate_identity("scene", "movie")


if __name__ == "__main__":
    unittest.main()
