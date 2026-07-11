# Home companion skills

A companion skill supplies stable household semantics that Home Assistant's
registries cannot: human aliases, preferred room aggregates, known intent phrases,
and unusual device topology. It must not contain tokens, passwords, door codes,
Wi-Fi credentials, or other secrets.

Load the generic `hass-cli` skill and exactly one companion for the active home.
The companion overrides generic routing only where it gives an explicit reviewed
mapping.

## Fictional example

The following is a sanitized example for the fictional Juniper House:

```markdown
---
name: juniper-house
description: Reviewed Home Assistant aliases and routing rules for the fictional Juniper House. Use only when controlling that home alongside the hass-cli skill.
---

# Juniper House

Use exact mappings before fuzzy discovery. If a phrase is not listed, return to
the generic hass-cli workflow.

## Aliases

| Human phrase | Exact target | Meaning |
|---|---|---|
| reading lamp | light.library_reading_lamp | Lamp beside the library chair |
| downstairs lights | light.downstairs | Reviewed aggregate light |
| kitchen speaker | media_player.kitchen | Main kitchen audio player |

## Routing rules

- `turn on/off the reading lamp`: use `ha-on` or `ha-off` with the exact entity id.
- `good night`: use `ha-intent "good night"`; this is a verified automation phrase.
- `turn off downstairs`: use the aggregate `light.downstairs`, not `--all`.

## Topology

- `switch.library_lamp_power` supplies power to `light.library_reading_lamp`.
  If the light is unavailable, turn on the power switch and check again after a
  short delay.

## Preferred sensors

- Downstairs temperature: `sensor.downstairs_temperature`
- Library humidity: `sensor.library_humidity`
```

## Maintenance rules

- Add a mapping only after verifying it against the live home.
- Prefer exact entity ids and aggregates over prose about likely behavior.
- Record whether a phrase is direct-control or intent-first.
- Keep the file short enough to load on every home-control request.
- Remove stale mappings immediately after renames or topology changes.
- Store personal preferences only when they affect control semantics.
