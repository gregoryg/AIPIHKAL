"""Small shared transport helpers for Home Assistant development tools."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib import error, request

try:
    import websockets
except ImportError:  # pragma: no cover - exercised by deployed environments
    websockets = None


class HomeAssistantApiError(RuntimeError):
    """Report a bounded Home Assistant transport or protocol failure."""


def decode_message(raw: str | bytes, context: str) -> dict[str, Any]:
    """Decode one JSON object or raise a bounded protocol error."""
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
        raise HomeAssistantApiError(f"{context} returned invalid JSON") from exc
    if not isinstance(decoded, dict):
        raise HomeAssistantApiError(f"{context} returned an unexpected JSON shape")
    return decoded


def environment() -> tuple[str, str, float]:
    """Return validated Home Assistant connection settings."""
    server = os.environ.get("HASS_SERVER", "").rstrip("/")
    token = os.environ.get("HASS_TOKEN", "")
    try:
        timeout = float(os.environ.get("HA_COMMAND_TIMEOUT", "30"))
    except ValueError as exc:
        raise HomeAssistantApiError("HA_COMMAND_TIMEOUT must be numeric") from exc

    if not server:
        raise HomeAssistantApiError("HASS_SERVER is not set")
    if not server.startswith(("http://", "https://")):
        raise HomeAssistantApiError("HASS_SERVER must start with http:// or https://")
    if not token:
        raise HomeAssistantApiError("HASS_TOKEN is not set")
    if timeout <= 0:
        raise HomeAssistantApiError("HA_COMMAND_TIMEOUT must be positive")
    return server, token, timeout


def websocket_url(server: str) -> str:
    """Convert an HTTP Home Assistant URL to its WebSocket endpoint."""
    if server.startswith("https://"):
        return "wss://" + server.removeprefix("https://") + "/api/websocket"
    if server.startswith("http://"):
        return "ws://" + server.removeprefix("http://") + "/api/websocket"
    raise HomeAssistantApiError("HASS_SERVER must start with http:// or https://")


async def authenticate(
    websocket: Any,
    token: str,
    timeout: float = 30,
) -> None:
    """Authenticate an open Home Assistant WebSocket connection."""
    required = decode_message(
        await asyncio.wait_for(websocket.recv(), timeout=timeout),
        "Home Assistant authentication",
    )
    if required.get("type") != "auth_required":
        raise HomeAssistantApiError("Expected auth_required from Home Assistant")

    await websocket.send(json.dumps({"type": "auth", "access_token": token}))
    response = decode_message(
        await asyncio.wait_for(websocket.recv(), timeout=timeout),
        "Home Assistant authentication",
    )
    if response.get("type") != "auth_ok":
        raise HomeAssistantApiError("Home Assistant WebSocket authentication failed")


async def websocket_request(
    message_type: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send one WebSocket request and return its matching result message."""
    if websockets is None:
        raise HomeAssistantApiError("Python package 'websockets' is required")
    server, token, timeout = environment()

    async with websockets.connect(
        websocket_url(server),
        open_timeout=timeout,
        close_timeout=timeout,
    ) as websocket:
        await authenticate(websocket, token, timeout)
        message = {"id": 1, "type": message_type, **(payload or {})}
        await websocket.send(json.dumps(message))

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError("Home Assistant WebSocket request timed out")
            raw = await asyncio.wait_for(websocket.recv(), timeout=remaining)
            response = decode_message(raw, "Home Assistant WebSocket")
            if response.get("id") != 1:
                continue
            if not response.get("success"):
                api_error = response.get("error", {})
                if not isinstance(api_error, dict):
                    raise HomeAssistantApiError(
                        "Home Assistant returned a malformed error"
                    )
                code = bounded_text(api_error.get("code", "unknown"), 100)
                detail = safe_error_detail(
                    api_error.get("message", "request rejected"),
                    token,
                )
                raise HomeAssistantApiError(f"Home Assistant rejected {code}: {detail}")
            return response


def rest_post(
    path: str,
    payload: dict[str, Any],
    *,
    return_response: bool = False,
) -> dict[str, Any]:
    """POST JSON to Home Assistant and return a decoded object."""
    server, token, timeout = environment()
    suffix = "?return_response" if return_response else ""
    url = f"{server}/api/{path.lstrip('/')}{suffix}"
    body = json.dumps(payload).encode("utf-8")
    api_request = request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(api_request, timeout=timeout) as response:
            raw = response.read()
    except error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", errors="replace")
        safe_detail = safe_error_detail(detail or exc.reason, token)
        raise HomeAssistantApiError(
            f"Home Assistant HTTP {exc.code}: {safe_detail}"
        ) from exc
    except error.URLError as exc:
        detail = safe_error_detail(exc.reason, token)
        raise HomeAssistantApiError(
            f"Home Assistant request failed: {detail}"
        ) from exc

    return decode_message(raw, "Home Assistant")


def bounded_text(value: Any, limit: int = 500) -> str | None:
    """Normalize optional text without returning unbounded external content."""
    if value is None:
        return None
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def safe_error_detail(value: Any, token: str, limit: int = 1000) -> str:
    """Bound an error detail and redact the bearer token if echoed."""
    detail = str(value)
    if token:
        detail = detail.replace(token, "[REDACTED]")
    return bounded_text(detail, limit) or "request failed"
