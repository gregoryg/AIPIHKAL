#!/usr/bin/env python3
"""Higher-level Home Assistant wrappers for area/entity discovery and control."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

DEFAULT_HASS_CLI = os.environ.get("HASS_CLI_BIN", "hass-cli")
DEFAULT_CONTROLLABLE_DOMAINS = {"light", "switch", "cover"}
DEFAULT_TRIGGERABLE_DOMAINS = {"scene", "script", "automation"}
DEFAULT_ACTIONABLE_DOMAINS = DEFAULT_CONTROLLABLE_DOMAINS | DEFAULT_TRIGGERABLE_DOMAINS
SEARCH_STOPWORDS = {
    "light", "lights", "switch", "switches", "plug", "plugs", "cover", "covers",
    "scene", "scenes", "script", "scripts", "automation", "automations",
}
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent


class HassCliError(RuntimeError):
    """Raised when hass-cli fails."""


def run_hass_json(args: list[str]) -> Any:
    """Run hass-cli and parse JSON output."""
    command = [DEFAULT_HASS_CLI, "-o", "json", *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise HassCliError(result.stderr.strip() or result.stdout.strip() or "hass-cli failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HassCliError(f"Failed to parse hass-cli JSON output: {exc}") from exc


def run_hass(args: list[str]) -> str:
    """Run hass-cli and return stdout."""
    command = [DEFAULT_HASS_CLI, *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise HassCliError(result.stderr.strip() or result.stdout.strip() or "hass-cli failed")
    return result.stdout.strip()


def normalize(text: str | None) -> str:
    """Normalize text for fuzzy matching."""
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def tokenize(text: str | None) -> list[str]:
    """Split text into normalized tokens."""
    normalized = normalize(text)
    return [token for token in normalized.split() if token]


def domain_for(entity_id: str) -> str:
    """Extract domain from an entity id."""
    return entity_id.split(".", 1)[0]


def score_text(query: str, *values: str | None) -> int:
    """Return a crude but useful fuzzy-match score."""
    query_norm = normalize(query)
    if not query_norm:
        return 0

    raw_query_tokens = tokenize(query)
    query_tokens = [token for token in raw_query_tokens if token not in SEARCH_STOPWORDS] or raw_query_tokens
    best = 0
    for raw_value in values:
        value = raw_value or ""
        value_norm = normalize(value)
        if not value_norm:
            continue

        score = 0
        if query_norm == value_norm:
            score = max(score, 240)
        if value_norm.startswith(query_norm):
            score = max(score, 170)
        if query_norm in value_norm:
            score = max(score, 120)

        value_tokens = value_norm.split()
        value_token_set = set(value_tokens)
        token_matches = sum(1 for token in query_tokens if token in value_token_set)
        if token_matches:
            score = max(score, 50 + 25 * token_matches)
        if query_tokens and all(token in value_norm for token in query_tokens):
            score = max(score, 90 + 20 * len(query_tokens))
        if query_tokens and all(token in value_token_set for token in query_tokens):
            score = max(score, 110 + 30 * len(query_tokens))
        if len(query_tokens) > 1 and query_tokens[0] in value_token_set and query_tokens[-1] in value_token_set:
            score = max(score, 150)

        unmatched_value_tokens = [
            token for token in value_tokens if token not in query_tokens and token not in SEARCH_STOPWORDS
        ]
        if token_matches and unmatched_value_tokens:
            score -= min(20, 5 * len(unmatched_value_tokens))
        if len(query_tokens) > 1 and token_matches == 1 and len(value_tokens) == 1:
            score -= 25

        best = max(best, score)

    return best


class Inventory:
    """Joined view of Home Assistant areas, devices, entities, and states."""

    def __init__(self) -> None:
        self.areas = run_hass_json(["area", "list"])
        self.devices = run_hass_json(["device", "list"])
        self.entities = run_hass_json(["entity", "list"])
        self.states = run_hass_json(["state", "list"])

        self.area_by_id = {area["area_id"]: area for area in self.areas}
        self.area_name_by_id = {area["area_id"]: area["name"] for area in self.areas}
        self.device_by_id = {device["id"]: device for device in self.devices}
        self.state_by_entity_id = {state["entity_id"]: state for state in self.states}
        self.entity_records = [self._build_entity_record(entity) for entity in self.entities]
        self.entity_by_id = {record["entity_id"]: record for record in self.entity_records}
        self.entities_by_area_id = self._build_entities_by_area_id()

    def _build_entity_record(self, entity: dict[str, Any]) -> dict[str, Any]:
        entity_id = entity["entity_id"]
        device = self.device_by_id.get(entity.get("device_id"))
        state = self.state_by_entity_id.get(entity_id, {})
        attributes = state.get("attributes", {})
        entity_area_id = entity.get("area_id") or (device or {}).get("area_id")
        area_name = self.area_name_by_id.get(entity_area_id) or (device or {}).get("area_name")
        friendly_name = (
            attributes.get("friendly_name")
            or entity.get("name_by_user")
            or entity.get("original_name")
            or (device or {}).get("name_by_user")
            or (device or {}).get("name")
            or entity_id
        )
        domain = domain_for(entity_id)
        return {
            "entity_id": entity_id,
            "domain": domain,
            "friendly_name": friendly_name,
            "state": state.get("state"),
            "attributes": attributes,
            "device_id": entity.get("device_id"),
            "device_name": (device or {}).get("name_by_user") or (device or {}).get("name"),
            "area_id": entity_area_id,
            "area_name": area_name,
            "platform": entity.get("platform"),
            "original_name": entity.get("original_name"),
            "name_by_user": entity.get("name_by_user"),
            "disabled_by": entity.get("disabled_by"),
            "hidden_by": entity.get("hidden_by"),
            "controllable": domain in DEFAULT_CONTROLLABLE_DOMAINS,
            "triggerable": domain in DEFAULT_TRIGGERABLE_DOMAINS,
            "actionable": domain in DEFAULT_ACTIONABLE_DOMAINS,
        }

    def _build_entities_by_area_id(self) -> dict[str, list[dict[str, Any]]]:
        mapping: dict[str, list[dict[str, Any]]] = {}
        for record in self.entity_records:
            area_id = record.get("area_id")
            if not area_id:
                continue
            mapping.setdefault(area_id, []).append(record)
        return mapping

    def area_candidates(self, query: str) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for area in self.areas:
            score = score_text(query, area.get("name"), area.get("area_id"))
            if score <= 0:
                continue
            entities = self.actionable_entities_for_area(area["area_id"])
            candidates.append(
                {
                    "area": area["name"],
                    "area_id": area["area_id"],
                    "score": score,
                    "actionable_entity_count": len(entities),
                    "entities": [self.present_entity(entity) for entity in entities],
                }
            )
        return sorted(candidates, key=lambda item: (-item["score"], item["area"].lower()))

    def entity_candidates(
        self,
        query: str,
        *,
        controllable_only: bool = True,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for entity in self.entity_records:
            if entity.get("disabled_by"):
                continue
            if controllable_only and not entity["actionable"]:
                continue
            score = score_text(
                query,
                entity["entity_id"],
                entity["friendly_name"],
                entity.get("area_name"),
                entity.get("device_name"),
                entity.get("original_name"),
                entity.get("name_by_user"),
            )
            if score <= 0:
                continue
            candidates.append({"score": score, **self.present_entity(entity)})
        return sorted(candidates, key=lambda item: (-item["score"], item["label"].lower(), item["entity_id"]))

    def actionable_entities_for_area(self, area_id: str) -> list[dict[str, Any]]:
        entities = [
            entity
            for entity in self.entities_by_area_id.get(area_id, [])
            if entity["actionable"] and not entity.get("disabled_by")
        ]
        return sorted(entities, key=lambda item: (item["domain"], item["friendly_name"].lower(), item["entity_id"]))

    def resolve_area(self, query: str) -> list[dict[str, Any]]:
        return self.area_candidates(query)

    def resolve_for_action(self, query: str) -> list[dict[str, Any]]:
        matches = [match for match in self.entity_candidates(query, controllable_only=True) if match["kind"] in DEFAULT_CONTROLLABLE_DOMAINS]
        by_id = {match["entity_id"]: match for match in matches}

        for area in self.area_candidates(query):
            for entity in area["entities"]:
                if entity["kind"] not in DEFAULT_CONTROLLABLE_DOMAINS:
                    continue
                existing = by_id.get(entity["entity_id"])
                area_match = {"score": area["score"], **entity}
                if existing is None or area_match["score"] > existing.get("score", 0):
                    by_id[entity["entity_id"]] = area_match

        resolved = list(by_id.values())
        return sorted(
            resolved,
            key=lambda item: (-item.get("score", 0), item["label"].lower(), item["entity_id"]),
        )

    def resolve_for_trigger(self, query: str) -> list[dict[str, Any]]:
        matches = [match for match in self.entity_candidates(query, controllable_only=True) if match["kind"] in DEFAULT_TRIGGERABLE_DOMAINS]
        return sorted(
            matches,
            key=lambda item: (-item.get("score", 0), item["label"].lower(), item["entity_id"]),
        )

    @staticmethod
    def present_entity(entity: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": entity["friendly_name"],
            "entity_id": entity["entity_id"],
            "kind": entity["domain"],
            "state": entity.get("state"),
            "area": entity.get("area_name"),
            "device": entity.get("device_name"),
        }


def service_for(domain: str, action: str) -> str:
    """Map a simple on/off action to a HA service."""
    if domain == "cover":
        return f"cover.{ 'open_cover' if action == 'on' else 'close_cover' }"
    return f"{domain}.turn_{action}"


def trigger_service_for(domain: str) -> str:
    """Map a triggerable domain to its HA service."""
    if domain == "scene":
        return "scene.turn_on"
    if domain == "script":
        return "script.turn_on"
    if domain == "automation":
        return "automation.trigger"
    raise HassCliError(f"Unsupported trigger domain: {domain}")


def print_json(payload: dict[str, Any]) -> None:
    """Print JSON payload consistently."""
    print(json.dumps(payload, indent=2, sort_keys=False))


def trim(items: Iterable[Any], limit: int) -> list[Any]:
    """Trim iterable to a list with a maximum size."""
    return list(items)[:limit]


def expected_states(kind: str, action: str) -> set[str]:
    """Return acceptable target states after an action."""
    if kind == "cover":
        return {"open", "opening"} if action == "on" else {"closed", "closing"}
    return {"on"} if action == "on" else {"off"}


def poll_state_after_action(entity_id: str, kind: str, action: str) -> tuple[dict[str, Any], bool, int]:
    """Poll entity state briefly to confirm post-action state."""
    target_states = expected_states(kind, action)
    attempts = 6
    delay_seconds = 0.5

    latest: dict[str, Any] = {}
    for attempt in range(1, attempts + 1):
        updated_state = run_hass_json(["state", "list", entity_id])
        latest = updated_state[0] if updated_state else {}
        if latest.get("state") in target_states:
            return latest, True, attempt
        if attempt < attempts:
            time.sleep(delay_seconds)

    return latest, False, attempts


def command_find(args: argparse.Namespace) -> int:
    """Search areas and entities by human-ish query."""
    inventory = Inventory()
    area_matches = trim(inventory.area_candidates(args.query), args.limit)
    entity_matches = trim(
        inventory.entity_candidates(args.query, controllable_only=not args.include_all_domains),
        args.limit,
    )
    print_json(
        {
            "status": "ok",
            "query": args.query,
            "area_matches": area_matches,
            "best_matches": entity_matches,
        }
    )
    return 0


def command_area_summary(args: argparse.Namespace) -> int:
    """Show actionable entities in a matching area."""
    inventory = Inventory()
    area_matches = inventory.resolve_area(args.area)
    if not area_matches:
        print_json({"status": "no_match", "query": args.area, "area_matches": []})
        return 1

    top_score = area_matches[0]["score"]
    best = [area for area in area_matches if area["score"] == top_score]
    if len(best) > 1:
        print_json({"status": "ambiguous", "query": args.area, "area_matches": best})
        return 2

    selected = best[0]
    print_json({"status": "ok", "query": args.area, "area": selected})
    return 0


def command_action(args: argparse.Namespace, action: str) -> int:
    """Resolve a query and control the selected entity if unambiguous."""
    inventory = Inventory()
    matches = inventory.resolve_for_action(args.query)
    if not matches:
        print_json({"status": "no_match", "query": args.query, "best_matches": []})
        return 1

    top_score = matches[0].get("score", 0)
    best = [match for match in matches if match.get("score", 0) == top_score]
    if len(best) > 1 and not args.all:
        print_json({"status": "ambiguous", "query": args.query, "best_matches": best})
        return 2

    selected = best if args.all else [best[0]]
    results: list[dict[str, Any]] = []
    for entity in selected:
        service = service_for(entity["kind"], action)
        run_hass(["service", "call", service, "--arguments", f"entity_id={entity['entity_id']}"])
        state_record, state_confirmed, poll_attempts = poll_state_after_action(
            entity["entity_id"],
            entity["kind"],
            action,
        )
        results.append(
            {
                "service": service,
                "entity": entity,
                "state_confirmed": state_confirmed,
                "poll_attempts": poll_attempts,
                "result_state": {
                    "state": state_record.get("state"),
                    "label": state_record.get("attributes", {}).get("friendly_name", entity["label"]),
                },
            }
        )

    print_json(
        {
            "status": "ok",
            "query": args.query,
            "action": action,
            "acted_on_count": len(results),
            "results": results,
        }
    )
    return 0


def command_status(args: argparse.Namespace) -> int:
    """Show compact status for matching areas and actionable entities."""
    inventory = Inventory()
    area_matches = trim(inventory.area_candidates(args.query), args.limit)
    entity_matches = trim(inventory.entity_candidates(args.query, controllable_only=True), args.limit)
    print_json(
        {
            "status": "ok",
            "query": args.query,
            "area_matches": area_matches,
            "best_matches": entity_matches,
        }
    )
    return 0


def command_trigger(args: argparse.Namespace) -> int:
    """Resolve a query and trigger a scene, script, or automation."""
    inventory = Inventory()
    matches = inventory.resolve_for_trigger(args.query)
    if not matches:
        print_json({"status": "no_match", "query": args.query, "best_matches": []})
        return 1

    top_score = matches[0].get("score", 0)
    best = [match for match in matches if match.get("score", 0) == top_score]
    if len(best) > 1 and not args.all:
        print_json({"status": "ambiguous", "query": args.query, "best_matches": best})
        return 2

    selected = best if args.all else [best[0]]
    results: list[dict[str, Any]] = []
    for entity in selected:
        service = trigger_service_for(entity["kind"])
        run_hass(["service", "call", service, "--arguments", f"entity_id={entity['entity_id']}"])
        updated_state = run_hass_json(["state", "list", entity["entity_id"]])
        state_record = updated_state[0] if updated_state else {}
        results.append(
            {
                "service": service,
                "entity": entity,
                "result_state": {
                    "state": state_record.get("state"),
                    "label": state_record.get("attributes", {}).get("friendly_name", entity["label"]),
                },
            }
        )

    print_json(
        {
            "status": "ok",
            "query": args.query,
            "action": "trigger",
            "acted_on_count": len(results),
            "results": results,
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    find_parser = subparsers.add_parser("find", help="Search areas and entities")
    find_parser.add_argument("query", help="Human-ish search query such as 'bar light'")
    find_parser.add_argument("--limit", type=int, default=8, help="Maximum matches per section")
    find_parser.add_argument(
        "--include-all-domains",
        action="store_true",
        help="Include non-controllable entities like sensors in entity matches",
    )
    find_parser.set_defaults(func=command_find)

    area_parser = subparsers.add_parser("area-summary", help="Show actionable entities in an area")
    area_parser.add_argument("area", help="Area name or id")
    area_parser.set_defaults(func=command_area_summary)

    status_parser = subparsers.add_parser("status", help="Show compact status for matching areas and entities")
    status_parser.add_argument("query", help="Human-ish query such as 'garage' or 'bar light'")
    status_parser.add_argument("--limit", type=int, default=8, help="Maximum matches per section")
    status_parser.set_defaults(func=command_status)

    on_parser = subparsers.add_parser("turn-on", help="Turn on or open resolved entities")
    on_parser.add_argument("query", help="Human-ish query such as 'bar light'")
    on_parser.add_argument("--all", action="store_true", help="Act on all top-scoring matches")
    on_parser.set_defaults(func=lambda ns: command_action(ns, "on"))

    off_parser = subparsers.add_parser("turn-off", help="Turn off or close resolved entities")
    off_parser.add_argument("query", help="Human-ish query such as 'bar light'")
    off_parser.add_argument("--all", action="store_true", help="Act on all top-scoring matches")
    off_parser.set_defaults(func=lambda ns: command_action(ns, "off"))

    trigger_parser = subparsers.add_parser("trigger", help="Trigger scenes, scripts, or automations")
    trigger_parser.add_argument("query", help="Human-ish query such as 'good night' or 'movie time'")
    trigger_parser.add_argument("--all", action="store_true", help="Act on all top-scoring matches")
    trigger_parser.set_defaults(func=command_trigger)

    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except HassCliError as exc:
        print_json(
            {
                "status": "error",
                "message": str(exc),
                "hint": (
                    "Ensure HASS_SERVER and HASS_TOKEN are set. "
                    f"Try copying {REPO_ROOT / 'skills/hass-cli/.env.template'} to .env and sourcing {REPO_ROOT / 'skills/hass-cli/scripts/ha-env.sh'}."
                ),
            }
        )
        return 3


if __name__ == "__main__":
    sys.exit(main())
