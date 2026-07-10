# Categorized install compatibility notes

This skill was originally authored for a flat layout:

- `skills/common/secrets.sh`
- `skills/hass-cli/scripts/...`

In a categorized install, the real paths may instead be:

- `~/.hermes/skills/smart-home/hass-cli/`
- optional sibling `~/.hermes/skills/smart-home/common/`

## Symptoms

Typical breakage on fresh categorized installs:

- `ha-env.sh: ... skills/common/secrets.sh: No such file or directory`
- wrapper scripts fail with `repo_root: unbound variable`
- wrapper scripts look for Python entrypoints under a non-existent flat path
- `ha-intent` fails with `{"status": "infrastructure_error", "message": "websockets library not found"}`

## Proven local compatibility fix

1. Make `ha-env.sh` self-contained:
   - prefer loading `hass-cli/.env` directly
   - only fall back to legacy `common/secrets.sh` if it exists
2. Compute `repo_root` for the categorized tree so wrapper references still resolve.
3. If wrappers still hardcode `$repo_root/skills/hass-cli/...`, create a compatibility symlink:
   - `~/.hermes/skills/smart-home/skills/hass-cli -> ../hass-cli`
4. Install `websockets` into the boodle venv used by `ha-intent` and related websocket-backed scripts:
   - `~/.local/python-venvs/boodle/bin/pip install websockets`

## Important nuance

The Python scripts in this skill are mostly stdlib-only. The missing dependency that surfaced in this install was specifically `websockets` for the Home Assistant websocket flows (`ha-intent`, weather, Spotify browse/dump, etc.). Do not assume a larger missing-dependency problem until you verify imports.

## Packaging guidance

For a reusable repo version of this skill, prefer making the skill self-contained instead of relying on a shared `skills/common/secrets.sh`. Moving secret/bootstrap logic into `hass-cli/` reduces path fragility across categorized installs.
