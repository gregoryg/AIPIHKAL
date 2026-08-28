"""Offline tests for shared Home Assistant API helpers."""

from __future__ import annotations

import asyncio
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import ha_api  # noqa: E402


class FakeResponse:
    """Minimal context-managed urllib response."""

    def __init__(self, payload: dict[str, object] | bytes) -> None:
        raw = (
            payload
            if isinstance(payload, bytes)
            else json.dumps(payload).encode("utf-8")
        )
        self.stream = io.BytesIO(raw)

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.stream.read()


class FakeWebSocket:
    """Minimal asynchronous WebSocket for authentication tests."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = [json.dumps(response) for response in responses]
        self.sent: list[dict[str, object]] = []

    async def recv(self) -> str:
        return self.responses.pop(0)

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))


class ApiHelperTests(unittest.TestCase):
    def test_builds_websocket_urls(self) -> None:
        self.assertEqual(
            ha_api.websocket_url("http://ha.example:8123"),
            "ws://ha.example:8123/api/websocket",
        )
        self.assertEqual(
            ha_api.websocket_url("https://ha.example"),
            "wss://ha.example/api/websocket",
        )

    def test_rejects_non_http_server(self) -> None:
        with self.assertRaisesRegex(ha_api.HomeAssistantApiError, "http"):
            ha_api.websocket_url("ha.example")

    def test_bounds_external_text(self) -> None:
        self.assertEqual(ha_api.bounded_text("abcdef", 4), "abc…")
        self.assertIsNone(ha_api.bounded_text(None))

    def test_authentication_failure_is_bounded(self) -> None:
        websocket = FakeWebSocket(
            [
                {"type": "auth_required"},
                {"type": "auth_invalid", "message": "bad token"},
            ]
        )
        with self.assertRaisesRegex(
            ha_api.HomeAssistantApiError,
            "authentication failed",
        ):
            asyncio.run(ha_api.authenticate(websocket, "dummy-token"))
        self.assertEqual(websocket.sent[0]["type"], "auth")

    def test_authentication_rejects_malformed_json(self) -> None:
        websocket = FakeWebSocket([])
        websocket.responses = ["not-json"]
        with self.assertRaisesRegex(
            ha_api.HomeAssistantApiError,
            "invalid JSON",
        ):
            asyncio.run(ha_api.authenticate(websocket, "dummy-token"))

    def test_error_detail_is_bounded_and_redacted(self) -> None:
        detail = ha_api.safe_error_detail(
            "prefix dummy-token " + ("x" * 2000),
            "dummy-token",
            limit=100,
        )
        self.assertNotIn("dummy-token", detail)
        self.assertIn("[REDACTED]", detail)
        self.assertEqual(len(detail), 100)

    def test_rest_post_requests_service_response(self) -> None:
        captured_request = None

        def fake_urlopen(api_request: object, timeout: float) -> FakeResponse:
            nonlocal captured_request
            captured_request = api_request
            self.assertEqual(timeout, 12.0)
            return FakeResponse({"service_response": {}})

        environment = {
            "HASS_SERVER": "https://ha.example",
            "HASS_TOKEN": "dummy-token",
            "HA_COMMAND_TIMEOUT": "12",
        }
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
            ha_api.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            output = ha_api.rest_post(
                "services/calendar/get_events",
                {"entity_id": "calendar.family"},
                return_response=True,
            )

        self.assertEqual(output, {"service_response": {}})
        self.assertIsNotNone(captured_request)
        self.assertTrue(captured_request.full_url.endswith("?return_response"))
        self.assertEqual(
            captured_request.get_header("Authorization"),
            "Bearer dummy-token",
        )

    def test_rest_post_rejects_invalid_json(self) -> None:
        environment = {
            "HASS_SERVER": "https://ha.example",
            "HASS_TOKEN": "dummy-token",
        }
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
            ha_api.request,
            "urlopen",
            return_value=FakeResponse(b"not-json"),
        ):
            with self.assertRaisesRegex(ha_api.HomeAssistantApiError, "invalid JSON"):
                ha_api.rest_post("services/calendar/get_events", {})

    def test_rest_post_reports_transport_timeout(self) -> None:
        environment = {
            "HASS_SERVER": "https://ha.example",
            "HASS_TOKEN": "dummy-token",
        }
        with mock.patch.dict(os.environ, environment, clear=True), mock.patch.object(
            ha_api.request,
            "urlopen",
            side_effect=ha_api.error.URLError(TimeoutError("timed out")),
        ):
            with self.assertRaisesRegex(ha_api.HomeAssistantApiError, "timed out"):
                ha_api.rest_post("services/calendar/get_events", {})

    def test_environment_rejects_invalid_timeout(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "HASS_SERVER": "https://ha.example",
                "HASS_TOKEN": "dummy-token",
                "HA_COMMAND_TIMEOUT": "later",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(ha_api.HomeAssistantApiError, "numeric"):
                ha_api.environment()


if __name__ == "__main__":
    unittest.main()
