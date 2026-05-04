#!/usr/bin/env python3
"""LLM-friendly Spotify control wrappers for Home Assistant."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Any

SPOTIFY_ENTITY = os.environ.get("HA_SPOTIFY_ENTITY", "media_player.spotify_gortsleigh")
HASS_CLI = os.environ.get("HASS_CLI_BIN", "hass-cli")


class SpotifyControlError(RuntimeError):
    """Raised when Spotify control operations fail."""


def run_hass(args: list[str]) -> str:
    """Run hass-cli and return stdout."""
    result = subprocess.run([HASS_CLI, *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SpotifyControlError(result.stderr.strip() or result.stdout.strip() or "hass-cli failed")
    return result.stdout.strip()


def run_hass_json(args: list[str]) -> Any:
    """Run hass-cli and parse JSON output."""
    result = subprocess.run([HASS_CLI, "-o", "json", *args], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SpotifyControlError(result.stderr.strip() or result.stdout.strip() or "hass-cli failed")
    return json.loads(result.stdout)


def normalize(text: str | None) -> str:
    """Normalize strings for fuzzy matching."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def score(query: str, value: str) -> int:
    """Score a candidate source name."""
    q = normalize(query)
    v = normalize(value)
    if not q or not v:
        return 0
    if q == v:
        return 240
    if v.startswith(q):
        return 170
    if q in v:
        return 120
    q_tokens = q.split()
    v_tokens = set(v.split())
    if q_tokens and all(token in v_tokens for token in q_tokens):
        return 140 + 15 * len(q_tokens)
    matches = sum(1 for token in q_tokens if token in v_tokens)
    if matches:
        return 50 + 20 * matches
    return 0


def spotify_state() -> dict[str, Any]:
    """Return compact Spotify state."""
    state_list = run_hass_json(["state", "list", SPOTIFY_ENTITY])
    if not state_list:
        raise SpotifyControlError(f"Spotify entity not found: {SPOTIFY_ENTITY}")
    state = state_list[0]
    attrs = state.get("attributes", {})
    return {
        "entity_id": state["entity_id"],
        "state": state.get("state"),
        "source": attrs.get("source"),
        "source_list": attrs.get("source_list", []),
        "media_title": attrs.get("media_title"),
        "media_artist": attrs.get("media_artist"),
        "media_album_name": attrs.get("media_album_name"),
        "media_position": attrs.get("media_position"),
        "volume_level": attrs.get("volume_level"),
    }


def target_state_from_source(source: str | None) -> dict[str, Any] | None:
    """Return compact player/group state for the selected Spotify source."""
    if not source:
        return None

    candidates = run_hass_json(["state", "list", "media_player.*"])
    target = normalize(source)
    matched_players: list[dict[str, Any]] = []

    for state in candidates:
        attrs = state.get("attributes", {})
        friendly_name = attrs.get("friendly_name")
        if normalize(friendly_name) == target:
            matched_players.append(
                {
                    "entity_id": state["entity_id"],
                    "state": state.get("state"),
                    "label": friendly_name,
                    "media_title": attrs.get("media_title"),
                    "media_artist": attrs.get("media_artist"),
                    "volume_level": attrs.get("volume_level"),
                    "group_members": attrs.get("group_members"),
                }
            )

    if matched_players:
        return {"kind": "single", "players": matched_players}

    source_members = {normalize(part) for part in re.split(r"\s*\+\s*", source) if normalize(part)}
    if len(source_members) < 2:
        return None

    group_players: list[dict[str, Any]] = []
    for state in candidates:
        attrs = state.get("attributes", {})
        friendly_name = attrs.get("friendly_name")
        if normalize(friendly_name) not in source_members:
            continue
        group_players.append(
            {
                "entity_id": state["entity_id"],
                "state": state.get("state"),
                "label": friendly_name,
                "media_title": attrs.get("media_title"),
                "media_artist": attrs.get("media_artist"),
                "volume_level": attrs.get("volume_level"),
                "group_members": attrs.get("group_members"),
            }
        )

    if group_players:
        return {"kind": "group", "players": sorted(group_players, key=lambda item: item["label"].lower())}

    return None


def poll_state(expected_states: set[str], attempts: int = 6, delay: float = 0.5) -> tuple[dict[str, Any], bool, int]:
    """Poll Spotify state until expected transport state appears."""
    latest = spotify_state()
    for attempt in range(1, attempts + 1):
        latest = spotify_state()
        if latest.get("state") in expected_states:
            return latest, True, attempt
        if attempt < attempts:
            time.sleep(delay)
    return latest, False, attempts


def resolve_source(query: str) -> list[dict[str, Any]]:
    """Resolve a human-ish target to Spotify source names."""
    state = spotify_state()
    matches = []
    for source in state.get("source_list", []):
        s = score(query, source)
        if s > 0:
            matches.append({"score": s, "source": source})
    return sorted(matches, key=lambda item: (-item["score"], item["source"].lower()))


def print_json(payload: dict[str, Any]) -> None:
    """Print JSON output."""
    print(json.dumps(payload, indent=2, sort_keys=False))


def command_status(_: argparse.Namespace) -> int:
    """Show compact Spotify status."""
    state = spotify_state()
    print_json({
        "status": "ok",
        "spotify": state,
        "target": target_state_from_source(state.get("source")),
    })
    return 0


def command_target(args: argparse.Namespace) -> int:
    """Resolve and set Spotify target source."""
    matches = resolve_source(args.query)
    if not matches:
        print_json({"status": "no_match", "query": args.query, "best_matches": []})
        return 1
    top_score = matches[0]["score"]
    best = [m for m in matches if m["score"] == top_score]
    if len(best) > 1:
        print_json({"status": "ambiguous", "query": args.query, "best_matches": best})
        return 2
    source = best[0]["source"]
    run_hass(["service", "call", "media_player.select_source", "--arguments", f"entity_id={SPOTIFY_ENTITY},source={source}"])
    state = spotify_state()
    print_json({
        "status": "ok",
        "query": args.query,
        "selected_source": source,
        "spotify": state,
        "target": target_state_from_source(source),
    })
    return 0


def transport_command(service: str, expected_states: set[str]) -> int:
    """Run a Spotify transport command and poll result."""
    run_hass(["service", "call", service, "--arguments", f"entity_id={SPOTIFY_ENTITY}"])
    state, confirmed, attempts = poll_state(expected_states)
    print_json({
        "status": "ok",
        "service": service,
        "state_confirmed": confirmed,
        "poll_attempts": attempts,
        "spotify": state,
        "target": target_state_from_source(state.get("source")),
    })
    return 0


def command_play(_: argparse.Namespace) -> int:
    """Resume Spotify playback."""
    return transport_command("media_player.media_play", {"playing"})


def command_pause(_: argparse.Namespace) -> int:
    """Pause Spotify playback."""
    return transport_command("media_player.media_pause", {"paused", "idle"})


def command_next(_: argparse.Namespace) -> int:
    """Skip to next track."""
    return transport_command("media_player.media_next_track", {"playing"})


def command_previous(_: argparse.Namespace) -> int:
    """Skip to previous track."""
    return transport_command("media_player.media_previous_track", {"playing"})


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show Spotify and current target state")
    status.set_defaults(func=command_status)

    target = sub.add_parser("target", help="Select Spotify playback target")
    target.add_argument("query", help="Room/group query such as 'music room' or 'lefty pancho'")
    target.set_defaults(func=command_target)

    play = sub.add_parser("play", help="Resume Spotify playback")
    play.set_defaults(func=command_play)

    pause = sub.add_parser("pause", help="Pause Spotify playback")
    pause.set_defaults(func=command_pause)

    next_parser = sub.add_parser("next", help="Skip to next track")
    next_parser.set_defaults(func=command_next)

    prev = sub.add_parser("previous", help="Go to previous track")
    prev.set_defaults(func=command_previous)

    return parser


def main() -> int:
    """CLI entry point."""
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except SpotifyControlError as exc:
        print_json({"status": "error", "message": str(exc)})
        return 3


if __name__ == "__main__":
    sys.exit(main())
