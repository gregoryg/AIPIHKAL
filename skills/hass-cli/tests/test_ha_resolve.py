"""Offline tests for Home Assistant matching and service selection."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "ha_resolve.py"
SPEC = importlib.util.spec_from_file_location("ha_resolve", SCRIPT)
assert SPEC and SPEC.loader
ha_resolve = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ha_resolve)


class MatchingTests(unittest.TestCase):
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
