"""Offline tests for Home Assistant matching and service selection."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

SCRIPT = Path(__file__).parents[1] / "scripts" / "ha_resolve.py"
SPEC = importlib.util.spec_from_file_location("ha_resolve", SCRIPT)
assert SPEC and SPEC.loader
ha_resolve = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ha_resolve)


class MatchingTests(unittest.TestCase):
    def test_exact_entity_id_shape_is_strict(self) -> None:
        self.assertTrue(ha_resolve.is_exact_entity_id("light.reading_lamp"))
        self.assertFalse(ha_resolve.is_exact_entity_id("Reading Lamp"))
        self.assertFalse(ha_resolve.is_exact_entity_id("light.reading-lamp"))

    def test_exact_entity_load_uses_one_state_query(self) -> None:
        state = {
            "entity_id": "light.reading_lamp",
            "state": "off",
            "attributes": {"friendly_name": "Reading Lamp"},
        }
        with patch.object(ha_resolve, "run_hass_json", return_value=[state]) as run:
            entity = ha_resolve.load_exact_entity(
                "light.reading_lamp",
                allowed_domains=ha_resolve.DEFAULT_CONTROLLABLE_DOMAINS,
            )

        run.assert_called_once_with(["state", "list", "light.reading_lamp"])
        self.assertIsNotNone(entity)
        self.assertEqual(entity["label"], "Reading Lamp")
        self.assertEqual(entity["state"], "off")

    def test_exact_entity_load_rejects_unsupported_domain_without_query(self) -> None:
        with patch.object(ha_resolve, "run_hass_json") as run:
            entity = ha_resolve.load_exact_entity(
                "sensor.outdoor_temperature",
                allowed_domains=ha_resolve.DEFAULT_CONTROLLABLE_DOMAINS,
            )

        run.assert_not_called()
        self.assertIsNone(entity)

    def test_inventory_loads_all_independent_sources(self) -> None:
        responses = {
            ("area", "list"): [],
            ("device", "list"): [],
            ("entity", "list"): [],
            ("state", "list"): [],
        }

        def fake_run(args: list[str]) -> list:
            return responses[tuple(args)]

        with patch.object(ha_resolve, "run_hass_json", side_effect=fake_run) as run:
            inventory = ha_resolve.Inventory()

        self.assertEqual(run.call_count, 4)
        self.assertEqual(inventory.entity_records, [])

    def test_exact_status_avoids_inventory_join(self) -> None:
        state = {
            "entity_id": "light.reading_lamp",
            "state": "on",
            "attributes": {"friendly_name": "Reading Lamp"},
        }
        args = SimpleNamespace(query="light.reading_lamp", limit=8)
        with (
            patch.object(ha_resolve, "run_hass_json", return_value=[state]) as run,
            patch.object(ha_resolve, "Inventory") as inventory,
            patch.object(ha_resolve, "print_json") as output,
        ):
            code = ha_resolve.command_status(args)

        self.assertEqual(code, 0)
        run.assert_called_once_with(["state", "list", "light.reading_lamp"])
        inventory.assert_not_called()
        self.assertEqual(output.call_args.args[0]["status"], "ok")

    def test_exact_status_returns_no_match_for_missing_entity(self) -> None:
        args = SimpleNamespace(query="light.missing", limit=8)
        with (
            patch.object(ha_resolve, "run_hass_json", return_value=[]),
            patch.object(ha_resolve, "print_json") as output,
        ):
            code = ha_resolve.command_status(args)

        self.assertEqual(code, 1)
        self.assertEqual(output.call_args.args[0]["status"], "no_match")

    def test_find_returns_no_match_for_empty_results(self) -> None:
        inventory = MagicMock()
        inventory.area_candidates.return_value = []
        inventory.entity_candidates.return_value = []
        args = SimpleNamespace(query="missing", limit=8, include_all_domains=False)
        with (
            patch.object(ha_resolve, "Inventory", return_value=inventory),
            patch.object(ha_resolve, "print_json") as output,
        ):
            code = ha_resolve.command_find(args)

        self.assertEqual(code, 1)
        self.assertEqual(output.call_args.args[0]["status"], "no_match")

    def test_entity_inherits_area_from_parent_device(self) -> None:
        inventory = ha_resolve.Inventory.__new__(ha_resolve.Inventory)
        inventory.device_by_id = {
            "device-1": {
                "id": "device-1",
                "name": "Reading Lamp",
                "area_id": "library",
            }
        }
        inventory.area_name_by_id = {"library": "Library"}
        inventory.state_by_entity_id = {
            "light.reading_lamp": {
                "entity_id": "light.reading_lamp",
                "state": "off",
                "attributes": {"friendly_name": "Reading Lamp"},
            }
        }

        record = inventory._build_entity_record({
            "entity_id": "light.reading_lamp",
            "device_id": "device-1",
            "area_id": None,
            "platform": "example",
        })

        self.assertEqual(record["area_id"], "library")
        self.assertEqual(record["area_name"], "Library")

    def test_exact_match_beats_partial_match(self) -> None:
        exact = ha_resolve.score_text("reading lamp", "Reading Lamp")
        partial = ha_resolve.score_text("reading lamp", "Upstairs Reading Lamp")
        self.assertGreater(exact, partial)

    def test_domain_stopword_does_not_hide_distinguishing_words(self) -> None:
        target = ha_resolve.score_text("kitchen lights", "Kitchen Ceiling Lights")
        unrelated = ha_resolve.score_text("kitchen lights", "Bedroom Lights")
        self.assertGreater(target, unrelated)

    def test_area_membership_does_not_equal_an_exact_entity_match(self) -> None:
        entity = {
            "entity_id": "light.table_lamp",
            "friendly_name": "Table Lamp",
            "device_name": "Table Lamp",
            "original_name": None,
            "name_by_user": None,
            "aliases": [],
            "area_name": "Kitchen",
        }
        self.assertEqual(
            ha_resolve.score_entity("kitchen", entity),
            ha_resolve.AREA_CONTEXT_SCORE_CAP,
        )
        self.assertGreater(
            ha_resolve.score_text("kitchen", "Kitchen"),
            ha_resolve.score_entity("kitchen", entity),
        )

    def test_device_name_is_context_not_entity_identity(self) -> None:
        scene = {
            "entity_id": "scene.kitchen_bright",
            "friendly_name": "Kitchen Bright",
            "device_name": "Kitchen",
            "original_name": "Bright",
            "name_by_user": None,
            "aliases": [],
            "area_name": "Kitchen",
        }
        score = ha_resolve.score_entity("kitchen", scene)
        self.assertEqual(
            score,
            ha_resolve.score_text("kitchen", "Kitchen Bright", "Bright"),
        )
        self.assertLess(score, ha_resolve.score_text("kitchen", "Kitchen"))

    def test_status_area_preview_is_bounded_and_domain_filtered(self) -> None:
        match = {
            "area": "Kitchen",
            "area_id": "kitchen",
            "score": 240,
            "entities": [
                {"entity_id": "light.one", "kind": "light"},
                {"entity_id": "scene.one", "kind": "scene"},
                {"entity_id": "switch.one", "kind": "switch"},
            ],
        }
        compact = ha_resolve.compact_area_match(
            match,
            entity_limit=1,
            domains=ha_resolve.DEFAULT_CONTROLLABLE_DOMAINS,
        )
        self.assertEqual(compact["matching_entity_count"], 2)
        self.assertTrue(compact["entities_truncated"])
        self.assertEqual(compact["entities"][0]["entity_id"], "light.one")

    def test_weaker_area_context_is_removed_for_exact_entity_status(self) -> None:
        areas = [{"area": "Kitchen", "score": 140}]
        entities = [{"entity_id": "light.kitchen", "score": 240}]
        self.assertEqual(ha_resolve.relevant_area_matches(areas, entities), [])

    def test_equal_area_context_is_kept_for_room_status(self) -> None:
        areas = [{"area": "Kitchen", "score": 240}]
        entities = [{"entity_id": "light.kitchen", "score": 240}]
        self.assertEqual(ha_resolve.relevant_area_matches(areas, entities), areas)

    def test_cover_actions_use_cover_services(self) -> None:
        self.assertEqual(ha_resolve.service_for("cover", "on"), "cover.open_cover")
        self.assertEqual(ha_resolve.service_for("cover", "off"), "cover.close_cover")

    def test_trigger_domains_are_explicit(self) -> None:
        self.assertEqual(ha_resolve.trigger_service_for("scene"), "scene.turn_on")
        self.assertEqual(ha_resolve.trigger_service_for("script"), "script.turn_on")
        self.assertEqual(ha_resolve.trigger_service_for("automation"), "automation.trigger")
        with self.assertRaises(ha_resolve.HassCliError):
            ha_resolve.trigger_service_for("light")


if __name__ == "__main__":
    unittest.main()
