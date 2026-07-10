# Fresh Install Troubleshooting

Fixes applied during first install on Hermes (2026-05-04).

## Problem 1: `ha-env.sh` can't find `skills/common/secrets.sh`

**Symptom:** `source: .../skills/common/secrets.sh: No such file or directory`

**Cause:** Original skill expected a shared `skills/common/secrets.sh` with a `load_hass_token` function. This file doesn't exist in the Hermes categorized layout.

**Fix:** Patched `ha-env.sh` to load credentials directly from `skills/hass-cli/.env` via `source`. Falls back to `secrets.sh` only if the `.env` is missing.

## Problem 2: `$repo_root/skills/hass-cli/scripts/` path broken

**Symptom:** `ha_intent.py: No such file or directory` or similar, depending on which wrapper runs.

**Root cause chain:**
- `ha-env.sh` computed `repo_root` as 3 dirs up from `scripts/`, landing at `~/.hermes/skills/`
- Wrapper scripts do `exec python3 "$repo_root/skills/hass-cli/scripts/ha_resolve.py"`
- In original layout: `skills/hass-cli/` was a direct child → path worked
- In categorized layout: `skills/smart-home/hass-cli/` → `$repo_root` must be `skills/smart-home/` for the `skills/hass-cli/` segment to resolve correctly
- Even with correct `repo_root`, there's an extra `skills/` segment in the reference path

**Fix (two parts):**
1. `ha-env.sh` sets `repo_root="$skills_root/smart-home"` where `skills_root=~/.hermes/skills`
2. Created symlink: `~/.hermes/skills/smart-home/skills/hass-cli → ~/.hermes/skills/smart-home/hass-cli`

## Problem 3: `websockets` module not found

**Symptom:** `{"status": "infrastructure_error", "message": "websockets library not found"}`

**Cause:** `ha-intent.py`, `ha_weather.py`, `spotify_browse.py`, and `spotify_dump.py` use `~/.local/python-venvs/boodle/bin/python3` which didn't have `websockets` installed. Other wrappers (`ha-resolve`, `spotify_control`) use bare `python3` and don't need it.

**Fix:** `~/.local/python-venvs/boodle/bin/pip install websockets`

**Note:** All Python scripts use stdlib only — `websockets` is the only third-party dependency.

## Quick verification

After all fixes, confirm with:
```bash
# Environment loads correctly
source ~/.hermes/skills/smart-home/hass-cli/scripts/ha-env.sh
echo $HASS_SERVER  # should print your HA URL

# Paths resolve
~/.hermes/skills/smart-home/hass-cli/scripts/ha-find "any entity name"

# Full control chain works
~/.hermes/skills/smart-home/hass-cli/scripts/ha-off "bar light"
```
