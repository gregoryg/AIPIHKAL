#!/usr/bin/env python3
"""Browse the Spotify library via the Home Assistant WebSocket API.

Requires Spotify to be in a playing or paused state — the HA Spotify integration
only exposes BROWSE_MEDIA in supported_features when a session is active.
If Spotify is idle, start something playing first (e.g. ha-spotify-play) then retry.
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
    print(json.dumps({"status": "error", "message": "websockets library not found — install it in the active venv"}), flush=True)
    sys.exit(3)

SPOTIFY_ENTITY = os.environ.get("HA_SPOTIFY_ENTITY", "media_player.spotify_gortsleigh")
HASS_SERVER = os.environ.get("HASS_SERVER", "http://172.16.17.7:8123")
HASS_TOKEN = os.environ.get("HASS_TOKEN", "")

MEDIA_PLAYER_PREFIX = "spotify://"

SECTION_MAP: dict[str, tuple[str, str]] = {
    "playlists":    ("current_user_playlists",        "Your playlists"),
    "artists":      ("current_user_followed_artists", "Followed artists"),
    "albums":       ("current_user_saved_albums",     "Saved albums"),
    "liked":        ("current_user_saved_tracks",     "Liked songs"),
    "recent":       ("current_user_recently_played",  "Recently played"),
    "top-artists":  ("current_user_top_artists",      "Your top artists"),
    "top-tracks":   ("current_user_top_tracks",       "Your top tracks"),
}


def ws_url() -> str:
    """Convert HASS_SERVER http URL to ws URL."""
    return HASS_SERVER.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"


async def ws_request(message: dict[str, Any]) -> dict[str, Any]:
    """Open a HA WebSocket connection, authenticate, send one message, return result."""
    if not HASS_TOKEN:
        raise RuntimeError("HASS_TOKEN is not set")

    url = ws_url()
    async with websockets.connect(url) as ws:
        # Phase 1: receive auth_required
        raw = await ws.recv()
        preamble = json.loads(raw)
        if preamble.get("type") != "auth_required":
            raise RuntimeError(f"Expected auth_required, got: {preamble.get('type')}")

        # Phase 2: authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": HASS_TOKEN}))
        raw = await ws.recv()
        auth_result = json.loads(raw)
        if auth_result.get("type") != "auth_ok":
            raise RuntimeError(f"Authentication failed: {auth_result.get('message', auth_result)}")

        # Phase 3: send command
        message["id"] = 1
        await ws.send(json.dumps(message))
        raw = await ws.recv()
        return json.loads(raw)


def compact_item(child: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, decision-ready representation of a browse item."""
    return {
        "title": child.get("title"),
        "uri": child.get("media_content_id"),
        "type": child.get("media_content_type", "").removeprefix(MEDIA_PLAYER_PREFIX) or None,
        "can_play": child.get("can_play", False),
    }


def build_browse_message(section_key: str | None) -> dict[str, Any]:
    """Build the WebSocket browse_media message for a section or library root."""
    msg: dict[str, Any] = {
        "type": "media_player/browse_media",
        "entity_id": SPOTIFY_ENTITY,
    }
    if section_key:
        section_id, _ = SECTION_MAP[section_key]
        msg["media_content_type"] = f"{MEDIA_PLAYER_PREFIX}{section_id}"
        msg["media_content_id"] = section_id
    # No content_type/id → library root
    return msg


async def run_browse(section_key: str | None) -> int:
    """Browse a library section and print compact JSON."""
    msg = build_browse_message(section_key)
    try:
        result = await ws_request(msg)
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 3

    if result.get("type") == "result" and result.get("success"):
        payload = result["result"]
        children = payload.get("children", [])

        if section_key:
            _, label = SECTION_MAP[section_key]
            items = [compact_item(c) for c in children]
            print(json.dumps({
                "status": "ok",
                "section": section_key,
                "label": label,
                "count": len(items),
                "items": items,
            }, indent=2))
        else:
            # Library root — show available sections
            sections = [
                {
                    "section": k,
                    "label": v[1],
                    "media_content_type": f"{MEDIA_PLAYER_PREFIX}{v[0]}",
                    "media_content_id": v[0],
                }
                for k, v in SECTION_MAP.items()
            ]
            print(json.dumps({
                "status": "ok",
                "note": "Pass a section name to browse contents. Use ha-spotify-play-uri to play a URI.",
                "available_sections": sections,
            }, indent=2))
        return 0

    # Error response
    error_code = result.get("error", {}).get("code", "unknown")
    error_msg = result.get("error", {}).get("message", str(result))
    if error_code == "not_supported":
        print(json.dumps({
            "status": "error",
            "code": "not_supported",
            "message": (
                "Spotify browse is unavailable while idle. "
                "Start something playing first (e.g. ha-spotify-play), then retry."
            ),
        }, indent=2))
        return 2

    print(json.dumps({"status": "error", "code": error_code, "message": error_msg}, indent=2))
    return 1


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "section",
        nargs="?",
        choices=list(SECTION_MAP.keys()),
        metavar=f"{{{','.join(SECTION_MAP.keys())}}}",
        help="Library section to browse. Omit to list available sections.",
    )
    return parser


def main() -> int:
    """CLI entry point."""
    args = build_parser().parse_args()
    return asyncio.run(run_browse(args.section))


if __name__ == "__main__":
    sys.exit(main())
