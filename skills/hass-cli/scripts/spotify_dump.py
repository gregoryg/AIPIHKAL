#!/usr/bin/env python3
"""Dump Spotify library sections to a local searchable cache file.

Fetches playlists, followed artists, saved albums, recently played,
top artists, and top tracks via the HA WebSocket browse API and writes
a sorted, grep-friendly text file plus a JSON file.

LIMITATION — followed artists:
  The HA Spotify integration calls spotifyaio.get_followed_artists() which
  is hardcoded to limit=48 with no pagination cursor. You will only get the
  first 48 followed artists regardless of library size.

  For the full artist list, pass --spotify-token with a valid Spotify OAuth
  access token (obtainable from https://developer.spotify.com/console/ or
  your own app). The script will then call the Spotify API directly with
  cursor-based pagination to fetch all followed artists.

OUTPUT FILES (written to --output-dir, default ~/.local/share/ha-spotify/):
  library.txt   — sorted, grep-friendly: "Artist Name | spotify:artist:xxx"
  library.json  — full structured dump with all sections
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import websockets
except ImportError:
    print(json.dumps({"status": "error", "message": "websockets library not found"}))
    sys.exit(3)

SPOTIFY_ENTITY = os.environ.get("HA_SPOTIFY_ENTITY", "media_player.spotify_gortsleigh")
HASS_SERVER = os.environ.get("HASS_SERVER", "")
HASS_TOKEN = os.environ.get("HASS_TOKEN", "")
MEDIA_PLAYER_PREFIX = "spotify://"

SPOTIFY_API_BASE = "https://api.spotify.com/v1"

# Sections to dump via HA browse
BROWSE_SECTIONS: list[tuple[str, str, str]] = [
    # (key, content_type_suffix, human label)
    ("playlists",   "current_user_playlists",        "Playlists"),
    ("artists",     "current_user_followed_artists", "Followed artists (first 48 only — see --spotify-token for full list)"),
    ("albums",      "current_user_saved_albums",     "Saved albums"),
    ("recent",      "current_user_recently_played",  "Recently played"),
    ("top_artists", "current_user_top_artists",      "Top artists"),
    ("top_tracks",  "current_user_top_tracks",       "Top tracks"),
]


def ws_url() -> str:
    return HASS_SERVER.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"


async def ws_browse(content_type_suffix: str) -> list[dict[str, Any]]:
    """Fetch one browse section via HA WebSocket. Returns list of compact items."""
    content_type = f"{MEDIA_PLAYER_PREFIX}{content_type_suffix}"
    content_id = content_type_suffix

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
            "type": "media_player/browse_media",
            "entity_id": SPOTIFY_ENTITY,
            "media_content_type": content_type,
            "media_content_id": content_id,
        }))
        result = json.loads(await ws.recv())

    if not result.get("success"):
        code = result.get("error", {}).get("code", "unknown")
        msg = result.get("error", {}).get("message", str(result))
        if code == "not_supported":
            raise RuntimeError(
                "Spotify is idle — start something playing first, then retry."
            )
        raise RuntimeError(f"Browse error ({code}): {msg}")

    children = result["result"].get("children", [])
    return [
        {
            "title": c.get("title"),
            "uri": c.get("media_content_id"),
            "type": c.get("media_content_type", "").removeprefix(MEDIA_PLAYER_PREFIX) or None,
            "can_play": c.get("can_play", False),
        }
        for c in children
    ]


def spotify_api_get(path: str, token: str, params: dict | None = None) -> Any:
    """Make a GET request to the Spotify API. Returns parsed JSON."""
    url = f"{SPOTIFY_API_BASE}/{path}"
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode()
            detail = json.loads(body).get("error", {}).get("message", body)
        except Exception:
            detail = body or str(exc)
        raise RuntimeError(f"Spotify API {exc.code}: {detail}") from exc


def fetch_all_followed_artists(spotify_token: str) -> list[dict[str, Any]]:
    """Fetch ALL followed artists from Spotify API with cursor pagination."""
    artists: list[dict[str, Any]] = []
    params: dict[str, Any] = {"type": "artist", "limit": "50"}

    while True:
        data = spotify_api_get("me/following", spotify_token, params)
        page = data.get("artists", {})
        for a in page.get("items", []):
            artists.append({
                "title": a.get("name"),
                "uri": a.get("uri"),
                "type": "artist",
                "can_play": True,
            })
        cursor_after = page.get("cursors", {}).get("after")
        if not cursor_after or not page.get("next"):
            break
        params["after"] = cursor_after

    return artists


async def collect_library(spotify_token: str | None) -> dict[str, Any]:
    """Collect all available library sections."""
    library: dict[str, Any] = {}
    warnings: list[str] = []

    for key, suffix, label in BROWSE_SECTIONS:
        if key == "artists" and spotify_token:
            # Use direct Spotify API for full paginated artist list
            try:
                items = fetch_all_followed_artists(spotify_token)
                library[key] = {"label": "Followed artists (full list)", "items": items}
                print(f"  ✓ {label}: {len(items)} (full paginated fetch)", file=sys.stderr)
            except Exception as exc:
                warnings.append(f"artists (Spotify API): {exc}")
                library[key] = {"label": label, "items": [], "error": str(exc)}
                print(f"  ✗ {label}: {exc}", file=sys.stderr)
        else:
            try:
                items = await ws_browse(suffix)
                library[key] = {"label": label, "items": items}
                note = " ⚠ first 48 only — use --spotify-token for full list" if key == "artists" else ""
                print(f"  ✓ {label}: {len(items)}{note}", file=sys.stderr)
            except Exception as exc:
                warnings.append(f"{key}: {exc}")
                library[key] = {"label": label, "items": [], "error": str(exc)}
                print(f"  ✗ {label}: {exc}", file=sys.stderr)

    return {"sections": library, "warnings": warnings, "fetched_at": datetime.now(timezone.utc).isoformat()}


def write_text_file(library: dict[str, Any], path: Path) -> int:
    """Write sorted grep-friendly text file. Returns total line count."""
    lines: list[str] = []
    for key, section in library["sections"].items():
        label = section["label"]
        for item in section.get("items", []):
            title = item.get("title") or ""
            uri = item.get("uri") or ""
            itype = item.get("type") or key
            lines.append(f"{title} | {uri} | {itype}")

    lines.sort(key=str.casefold)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


async def main_async(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "library.json"
    txt_path = output_dir / "library.txt"

    print("Fetching Spotify library...", file=sys.stderr)
    library = await collect_library(args.spotify_token)

    # Write JSON
    json_path.write_text(json.dumps(library, indent=2, ensure_ascii=False), encoding="utf-8")

    # Write text
    total = write_text_file(library, txt_path)

    summary = {
        "status": "ok",
        "fetched_at": library["fetched_at"],
        "output_dir": str(output_dir),
        "files": {
            "json": str(json_path),
            "text": str(txt_path),
        },
        "counts": {
            key: len(section.get("items", []))
            for key, section in library["sections"].items()
        },
        "total_entries": total,
        "warnings": library["warnings"],
    }
    print(json.dumps(summary, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        default="~/.local/share/ha-spotify",
        help="Directory to write library.json and library.txt (default: ~/.local/share/ha-spotify)",
    )
    parser.add_argument(
        "--spotify-token",
        default=None,
        metavar="TOKEN",
        help=(
            "Spotify OAuth access token for full paginated artist fetch. "
            "Without this, followed artists are capped at 48 by the HA integration. "
            "Get a token from https://developer.spotify.com/console/get-following/"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
