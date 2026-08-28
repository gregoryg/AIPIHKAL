"""Offline tests for response-returning calendar queries."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import ha_calendar_events  # noqa: E402


class CalendarEventTests(unittest.TestCase):
    def test_normalizes_and_bounds_calendar_events(self) -> None:
        output = ha_calendar_events.normalize_response(
            {
                "service_response": {
                    "calendar.family": {
                        "events": [
                            {
                                "start": "2026-08-28T09:25:18-06:00",
                                "end": "2026-08-28T09:40:18-06:00",
                                "summary": "Reminder",
                                "description": "x" * 1200,
                            }
                        ]
                    }
                }
            },
            "calendar.family",
            include_description=True,
        )
        self.assertEqual(output["count"], 1)
        self.assertEqual(output["events"][0]["summary"], "Reminder")
        self.assertEqual(len(output["events"][0]["description"]), 1000)
        self.assertTrue(output["events"][0]["description"].endswith("…"))

    def test_bounds_event_count(self) -> None:
        output = ha_calendar_events.normalize_response(
            {
                "service_response": {
                    "calendar.family": {
                        "events": [
                            {"summary": "First"},
                            {"summary": "Second"},
                        ]
                    }
                }
            },
            "calendar.family",
            include_description=False,
            limit=1,
        )
        self.assertEqual(output["count"], 1)
        self.assertEqual(output["total_count"], 2)
        self.assertTrue(output["truncated"])

    def test_omits_descriptions_by_default(self) -> None:
        output = ha_calendar_events.normalize_response(
            {
                "service_response": {
                    "calendar.family": {
                        "events": [{"summary": "Reminder", "description": "private"}]
                    }
                }
            },
            "calendar.family",
            include_description=False,
        )
        self.assertNotIn("description", output["events"][0])

    def test_query_uses_return_response(self) -> None:
        with mock.patch.object(
            ha_calendar_events.ha_api,
            "rest_post",
            return_value={"service_response": {"calendar.family": {"events": []}}},
        ) as rest_post:
            output = ha_calendar_events.query_events(
                "calendar.family",
                "2026-08-28T09:00:00-06:00",
                "2026-08-28T10:00:00-06:00",
                include_description=False,
            )
        self.assertEqual(output["count"], 0)
        self.assertTrue(rest_post.call_args.kwargs["return_response"])

    def test_rejects_non_calendar_entity(self) -> None:
        with self.assertRaisesRegex(ValueError, "calendar entity ID"):
            ha_calendar_events.query_events(
                "sensor.calendar",
                "2026-08-28T09:00:00-06:00",
                "2026-08-28T10:00:00-06:00",
                include_description=False,
            )

    def test_rejects_malformed_response(self) -> None:
        with self.assertRaisesRegex(
            ha_calendar_events.ha_api.HomeAssistantApiError,
            "unexpected shape",
        ):
            ha_calendar_events.normalize_response(
                {"service_response": ["not", "an", "object"]},
                "calendar.family",
                include_description=False,
            )

    def test_rejects_reversed_interval(self) -> None:
        with self.assertRaisesRegex(ValueError, "start must be before end"):
            ha_calendar_events.query_events(
                "calendar.family",
                "2026-08-28T10:00:00-06:00",
                "2026-08-28T09:00:00-06:00",
                include_description=False,
            )


if __name__ == "__main__":
    unittest.main()
