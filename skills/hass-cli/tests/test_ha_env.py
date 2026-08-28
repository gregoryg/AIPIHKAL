"""Offline tests for the Home Assistant wrapper environment loader."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "ha-env.sh"
MANAGED_KEYS = {
    "HASS_SERVER",
    "HASS_TOKEN",
    "HASS_CLI_BIN",
    "HA_PYTHON",
    "HA_WEATHER_ENTITY",
    "HA_COMMAND_TIMEOUT",
}


def run_loader(
    env_text: str,
    exported: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Source a temporary copy of the loader and return its process result."""
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = Path(temp_dir) / "hass-cli"
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True)
        shutil.copy2(SCRIPT, scripts_dir / SCRIPT.name)
        (skill_dir / ".env").write_text(env_text, encoding="utf-8")

        environment = os.environ.copy()
        for key in MANAGED_KEYS:
            environment.pop(key, None)
        environment.update(exported or {})

        return subprocess.run(
            [
                "bash",
                "-c",
                'set -e; source "$1"; printf "%s\\n%s\\n" '
                '"$HASS_SERVER" "$HASS_TOKEN"',
                "bash",
                str(scripts_dir / SCRIPT.name),
            ],
            check=False,
            capture_output=True,
            env=environment,
            text=True,
            timeout=10,
        )


class EnvironmentLoaderTests(unittest.TestCase):
    def test_loads_unquoted_values(self) -> None:
        result = run_loader(
            "HASS_SERVER=http://ha.example:8123\n"
            "HASS_TOKEN=unquoted-token\n"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["http://ha.example:8123", "unquoted-token"],
        )

    def test_strips_matching_single_quotes(self) -> None:
        result = run_loader(
            "HASS_SERVER='http://ha.example:8123'\n"
            "HASS_TOKEN='single-quoted-token'\n"
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["http://ha.example:8123", "single-quoted-token"],
        )

    def test_strips_matching_double_quotes(self) -> None:
        result = run_loader(
            'HASS_SERVER="http://ha.example:8123"\n'
            'HASS_TOKEN="double=quoted=token"\n'
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["http://ha.example:8123", "double=quoted=token"],
        )

    def test_rejects_unmatched_quote_without_printing_value(self) -> None:
        result = run_loader(
            "HASS_SERVER=http://ha.example:8123\n"
            "HASS_TOKEN='secret-do-not-print\n"
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HASS_TOKEN", result.stderr)
        self.assertIn("unmatched quote", result.stderr)
        self.assertNotIn("secret-do-not-print", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_rejects_one_character_quote(self) -> None:
        result = run_loader(
            "HASS_SERVER=http://ha.example:8123\n"
            "HASS_TOKEN='\n"
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HASS_TOKEN", result.stderr)
        self.assertIn("unmatched quote", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_exported_values_take_precedence(self) -> None:
        result = run_loader(
            "HASS_SERVER='ignored-unmatched\n"
            "HASS_TOKEN='also-ignored-unmatched\n",
            exported={
                "HASS_SERVER": "http://exported.example:8123",
                "HASS_TOKEN": "exported-token",
            },
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["http://exported.example:8123", "exported-token"],
        )


if __name__ == "__main__":
    unittest.main()
