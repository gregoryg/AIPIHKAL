---
name: hass-cli
description: Control and query Home Assistant via the hass-cli Python CLI. Use when Codex needs to interact with a Home Assistant instance for controlling devices (lights, switches, climate, covers, etc.), querying entity states or attributes, managing areas/devices/entities, calling services, checking system status, or any Home Assistant automation/control tasks. Supports JSON output for structured data.
---

# hass-cli

Control Home Assistant via the `hass-cli` Python CLI.

## Configuration

**Binary location:** `~/.local/python-venvs/boodle/bin/hass-cli` (or see if it's in the path already with `which hass-cli`)

**Secret Management (Secure Injection):**
Load `HASS_TOKEN` from .env` or - if not there, load it securely:

```bash
source skills/common/secrets.sh
load_hass_token
export HASS_SERVER=http://172.16.17.7:8123  # Update if needed
```

**Alternative (One-liner):**
```bash
export HASS_TOKEN=$(gpg --decrypt ~/.authinfo.gpg 2>/dev/null | grep "machine ha-mcp-token" | awk '{for(i=1;i<=NF;i++) if($i=="password") print $(i+1)}')
```

**Always export these variables** before running `hass-cli`.

## Quick Reference

**Entity discovery:**
```bash
# List all entities (supports wildcards)
hass-cli -o json entity list 'light.*'
hass-cli -o json entity list 'switch.bar*'

# Get current state + attributes
hass-cli -o json state list 'light.bar*'
```

**Control entities:**
```bash
# Direct control commands (preferred for simple on/off/toggle)
hass-cli state turn_on light.bar_switch_light
hass-cli state turn_off light.living_room
hass-cli state toggle switch.porch

# Service calls (for parameters or services without direct commands)
hass-cli service call light.turn_on --arguments entity_id=light.bar_switch_light
hass-cli service call climate.set_temperature --arguments entity_id=climate.bedroom,temperature=72
```

**Areas and organization:**
```bash
# List areas
hass-cli -o json area list

# List devices
hass-cli -o json device list
```

## Common Patterns

**Find entities in an area:**
```bash
# 1. Get area_id from area list
hass-cli -o json area list | jq -r '.[] | select(.name=="Bar") | .area_id'

# 2. Filter entities by area_id (from entity metadata)
hass-cli -o json entity list | jq '.[] | select(.area_id=="bar")'
```

**Get detailed state information:**
```bash
# State includes: current value, attributes, last_changed, last_updated
hass-cli -o json state list 'light.bar_switch_light'
```

**Wildcard searches:**
- `light.*` — all lights
- `switch.bar*` — switches starting with "bar"
- `sensor.*temperature*` — all temperature sensors
- `climate.bedroom` — exact match

## Output Formats

**JSON** (preferred for structured data):
```bash
hass-cli -o json entity list
```

**Table** (human-readable):
```bash
hass-cli -o table state list 'light.*'
```

**YAML**:
```bash
hass-cli -o yaml area list
```

## Limitations

**Broken commands:**
- `hass-cli info` — Uses deprecated endpoint, will fail

**Entity vs State:**
- `entity list` — Registry metadata (area, device, platform, creation date)
- `state list` — Current state + attributes (on/off, brightness, temperature, etc.)
- Use `state list` for runtime information, `entity list` for organization

## Service Calls

**List available services:**
```bash
hass-cli -o json service list
```

**Common services by domain:**
- `light.turn_on`, `light.turn_off`, `light.toggle`
- `switch.turn_on`, `switch.turn_off`, `switch.toggle`
- `climate.set_temperature`, `climate.set_hvac_mode`
- `cover.open_cover`, `cover.close_cover`
- `automation.trigger`, `automation.turn_on`, `automation.turn_off`
- `notify.notify` (send notifications)

**Service call syntax:**
```bash
hass-cli service call <domain>.<service> --arguments key=value,key2=value2
```

**Examples:**
```bash
# Trigger automation
hass-cli service call automation.trigger --arguments entity_id=automation.good_night

# Light with brightness
hass-cli service call light.turn_on --arguments entity_id=light.bedroom,brightness=128

# Climate with temperature
hass-cli service call climate.set_temperature --arguments entity_id=climate.bedroom,temperature=72

# Notification
hass-cli service call notify.notify --arguments message="Garage door open!",title="Alert"
```

## Examples

**Turn on multiple lights:**
```bash
hass-cli state turn_on light.living_room
hass-cli state turn_on light.kitchen
```

**Check bedroom temperature:**
```bash
hass-cli -o json state list 'sensor.bedroom_temperature' | jq -r '.[0].state'
```

**List all lights that are currently on:**
```bash
hass-cli -o json state list 'light.*' | jq '.[] | select(.state=="on") | .entity_id'a
```

**Find entities with "bar" in the name:**
```bash
hass-cli -o json entity list | jq '.[] | select(.entity_id | contains("bar"))'
```
