---
name: hass-cli
description: Control and query Home Assistant via the hass-cli Python CLI. Use when Codex needs to interact with a Home Assistant instance for controlling devices (lights, switches, climate, covers, etc.), querying entity states or attributes, managing areas/devices/entities, calling services, checking system status, or any Home Assistant automation/control tasks. Supports JSON output for structured data.
---

# hass-cli

Control Home Assistant via the `hass-cli` Python CLI.

## Configuration

**Binary location:** `~/.local/python-venvs/boodle/bin/hass-cli` (or see if it's in the path already with `which hass-cli`)

**Secret Management (Secure Injection):**
Load `HASS_TOKEN` from `.env` or - if not there - load it securely:

```bash
source skills/common/secrets.sh
load_hass_token
export HASS_SERVER=${HASS_SERVER:-http://172.16.17.7:8123}
```

**Alternative (One-liner):**
```bash
export HASS_TOKEN=$(gpg --decrypt ~/.authinfo.gpg 2>/dev/null | grep "machine ha-mcp-token" | awk '{for(i=1;i<=NF;i++) if($i=="password") print $(i+1)}')
```

## Primary workflow: use the wrappers first

The raw Home Assistant registry model is often awkward for humans and LLMs:

- humans think “bar light”
- Home Assistant areas often live on devices, not entities
- many entities have `area_id: null`
- turning something on still requires the final entity id

In this repo, prefer the wrapper scripts in `skills/hass-cli/scripts/` before falling back to raw `hass-cli` discovery commands.

### Wrapper scripts

These scripts auto-load the token, set a default `HASS_SERVER` if one is not already exported, and return compact, decision-ready JSON.

**Find likely matches for a human-ish phrase:**
```bash
skills/hass-cli/scripts/ha-find "bar light"
skills/hass-cli/scripts/ha-find "garage"
```

**Show actionable entities in an area:**
```bash
skills/hass-cli/scripts/ha-area-summary "Bar"
skills/hass-cli/scripts/ha-area-summary "Kitchen"
```

**Control a single resolved entity:**
```bash
skills/hass-cli/scripts/ha-on "bar light"
skills/hass-cli/scripts/ha-off "bar light"
```

**Ask for compact status:**
```bash
skills/hass-cli/scripts/ha-status "garage"
skills/hass-cli/scripts/ha-status "bar light"
```

### Wrapper behavior

- `ha-find`
  - searches both areas and entities
  - returns multiple plausible matches instead of forcing one
  - defaults to actionable domains (`light`, `switch`, `cover`)
  - uses compact `best_matches` records by default so LLMs do not have to wade through low-value registry fields
  - use `--include-all-domains` to include sensors and other informational entities

- `ha-area-summary`
  - resolves an area name/id
  - lists actionable entities in that area with compact label/entity/state/device information

- `ha-on` / `ha-off`
  - resolve a human-ish phrase to actionable entities
  - if exactly one strong match exists, perform the action
  - if several equally strong matches exist, return them as JSON and do not act
  - use `--all` for intentional multi-entity actions on all top-scoring matches
  - for `cover` entities, maps on/off semantics to `open_cover` / `close_cover`

- `ha-status`
  - optimized for questions like “are the garage doors closed?”
  - returns compact area and actionable-entity status without including non-actionable sensors by default

## Important implementation note

A very useful escape hatch is `hass-cli template`, which can access Home Assistant Jinja helpers such as:

- `areas()`
- `area_id("Bar")`
- `area_devices("Bar")`
- `area_entities("Bar")`
- `area_name('light.bar_switch_light')`
- `device_id('light.bar_switch_light')`

Use this when raw `area list` / `device list` / `entity list` relationships get awkward.

## Raw hass-cli fallback reference

Use these when debugging or when the wrappers are not enough.

### Entity discovery

```bash
hass-cli -o json entity list 'light.*'
hass-cli -o json entity list 'switch.*'
hass-cli -o json state list 'light.bar*'
```

### Areas and organization

```bash
hass-cli -o json area list
hass-cli -o json device list
hass-cli -o json entity list
```

### Direct control

```bash
hass-cli state turn_on light.bar_switch_light
hass-cli state turn_off light.bar_switch_light
hass-cli service call light.turn_on --arguments entity_id=light.bar_switch_light
```

### Services

```bash
hass-cli -o json service list
```

Common services include:
- `light.turn_on`, `light.turn_off`
- `switch.turn_on`, `switch.turn_off`
- `cover.open_cover`, `cover.close_cover`

## Output formats

**JSON** (preferred for LLM use):
```bash
hass-cli -o json state list 'light.*'
```

**Table** (nice for humans):
```bash
hass-cli -o table state list 'light.*'
```

## Limitations

- `hass-cli info` uses a deprecated endpoint and may fail.
- The wrappers currently focus on `light`, `switch`, and `cover` because those are the most useful low-context control targets.
- Fuzzy matching is intentionally conservative about action: it may still surface near-matches, but `ha-on` / `ha-off` only act automatically when the best match is unambiguous unless `--all` is explicitly requested.
- Not every Home Assistant integration models devices correctly; some garage-door-like devices may still appear as simple on/off entities.

## References

- `skills/hass-cli/references/services.md`
- `skills/hass-cli/scripts/README.md`
- `skills/hass-cli/scripts/ha_resolve.py`
- `skills/hass-cli/scripts/ha-status`
