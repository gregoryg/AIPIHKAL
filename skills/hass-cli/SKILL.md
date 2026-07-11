---
name: hass-cli
description: Control and query Home Assistant through small JSON-first wrappers around hass-cli and the Home Assistant APIs. Use for entity discovery, room or area inspection, state questions, safe light/switch/cover control, scene/script/automation triggering, built-in Assist intent execution, weather, or raw Home Assistant service calls.
---

# Home Assistant CLI

Use the wrappers in `scripts/` before raw `hass-cli`. They join Home Assistant's
area, device, entity, and state data and return compact JSON.

## Why the wrappers exist

Humans usually ask to act on an entity in a room, but Home Assistant does not
expose that relationship as one consistently useful lookup. An entity may have no
`area_id` even though its parent device is assigned to an area. Raw discovery can
therefore require an area -> device -> entity -> state join before an action can
be chosen safely.

The wrappers perform that join on every inventory load. They resolve an entity's
area from the entity assignment first, then fall back to its device assignment.
Do not replace this with an entity-only query: that recreates the wheel-spinning
and missed devices this skill is designed to prevent.

## Before acting

1. If a home-specific companion skill is available, read it first. It owns aliases,
   preferred entities, known intent phrases, and topology exceptions.
2. Prefer an exact mapping from that companion over fuzzy discovery.
3. Never invent an entity id or assume a room name maps to one device.
4. Treat `ambiguous` as a stop condition. Ask or retry with an exact `entity_id`.

See `references/home-companion.md` when creating a home-specific companion.

## Configuration

The wrappers require `hass-cli`, Python 3.10+, `HASS_SERVER`, and `HASS_TOKEN`.
WebSocket-backed helpers also require the Python package `websockets`.

```bash
cp skills/hass-cli/.env.template skills/hass-cli/.env
$EDITOR skills/hass-cli/.env
skills/hass-cli/scripts/ha-find "kitchen"
```

Wrappers preserve already-exported variables, then fill missing values from the
skill-local `.env`. Set `HASS_CLI_BIN` or `HA_PYTHON` only when the defaults are
not on `PATH`. See `references/setup.md` for installation and troubleshooting.

## Choose one wrapper

| User intent | First command |
|---|---|
| Find or identify something | `scripts/ha-find "QUERY"` |
| List controllable things in an area | `scripts/ha-area-summary "AREA"` |
| Ask whether something is on, off, open, or closed | `scripts/ha-status "QUERY"` |
| Turn on or open one resolved entity | `scripts/ha-on "QUERY"` |
| Turn off or close one resolved entity | `scripts/ha-off "QUERY"` |
| Activate a scene, script, or automation | `scripts/ha-trigger "QUERY"` |
| Run a phrase known to Home Assistant Assist | `scripts/ha-intent "PHRASE"` |
| Ask for a Home Assistant weather forecast | `scripts/ha-weather [OPTIONS]` |

Paths above are relative to this skill directory. When the execution environment
does not preserve a working directory, use the actual absolute path to the skill.
Do not assume a particular user home, virtualenv, repository layout, or agent host.

## Interpret wrapper output

All wrappers use these statuses:

- `ok`: the request completed. For physical devices, also inspect
  `state_confirmed`; delayed devices may need a later status check.
- `no_match`: nothing safe matched. Discover with `ha-find` or use a companion
  mapping; do not guess.
- `ambiguous`: multiple top candidates matched and no action occurred. Ask or
  retry with an exact `entity_id`.
- `error` or `infrastructure_error`: configuration, authentication, transport,
  dependency, or Home Assistant failed. Do not convert this into another action.

Exit codes are `0` for success, `1` for no match, `2` for ambiguity or a rejected
HA response, and `3` for infrastructure failure.

## Control rules

`ha-on` and `ha-off` act only on `light`, `switch`, and `cover` entities. For a
cover, on means open and off means close. They act automatically only when the
top match is unique. Use `--all` only when the human explicitly requested every
top-scoring match.

`ha-trigger` follows the same ambiguity rule and maps:

- `scene` to `scene.turn_on`
- `script` to `script.turn_on`
- `automation` to `automation.trigger`

Physical covers can outlast the wrapper's confirmation window. If a command was
accepted but `state_confirmed` is false, wait and run `ha-status`; do not
immediately resend a command to a moving door or blind.

## Intent routing

Use `ha-intent` only for a phrase documented by the home companion or explicitly
requested by the user. It targets Home Assistant's built-in
`conversation.home_assistant` agent, not an arbitrary conversational LLM.

- `ok`: stop; the intent matched.
- `no_match`: a direct wrapper may be used if the requested action is clear.
- `error` or `infrastructure_error`: stop; do not fall back, because HA may have
  partially processed the request.

Without home-specific doctrine, prefer deterministic discovery and direct control
over trying speculative natural-language phrases.

## Other domains

Use `ha-find --include-all-domains "QUERY"` to resolve sensors, climate entities,
media players, vacuums, timers, and other domains. Then use an exact entity id in
a raw `hass-cli service call`. Read only the relevant reference:

- Common service syntax: `references/services.md`
- HA media-player status and transport: `references/media.md`
- Helper-backed schedules: `references/scheduling.md`
- Setup and dependency failures: `references/setup.md`

For Spotify catalog search, library management, playlist curation, or podcast
metadata, use the standalone `spotify-cli` skill. Home Assistant remains useful
for inspecting and controlling the resulting playback on known `media_player`
entities.

## Raw fallback

Load the same environment before calling raw `hass-cli`:

```bash
source skills/hass-cli/scripts/ha-env.sh
hass-cli -o json state list 'sensor.*'
hass-cli -o json service list
hass-cli service call climate.set_temperature \
  --arguments entity_id=climate.downstairs,temperature=70
```

Prefer JSON output. Use raw registry or service calls for unsupported domains and
debugging, not as the first discovery path.
