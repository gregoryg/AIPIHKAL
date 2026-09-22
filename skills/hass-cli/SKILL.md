---
name: hass-cli
description: Control and query Home Assistant through small JSON-first wrappers around hass-cli and the Home Assistant APIs. Use for entity discovery, room or area inspection, state questions, safe light/switch/cover control, scene/script/automation triggering, built-in Assist intent execution, weather, or raw Home Assistant service calls.
---

# Home Assistant CLI

## Operational fast path

Assume this installed skill is configured and operational. `hass-cli`, Python,
server configuration, authentication, and WebSocket dependencies are already set
up. The wrappers load their environment automatically.

For a documented routine request, execute the matching wrapper immediately. Do
**not** first run `command -v`, `--help`, authentication checks, service or device
listings, PATH checks, repository searches, script inspection, or a status query
before an action. Diagnose installation only after the direct command reports an
infrastructure failure or when the human explicitly asks for setup help.

The wrappers are not required to be on `PATH`. Invoke them from this skill's
`scripts/` directory; use the skill's known absolute base path when the current
working directory is elsewhere. Do not `cd` or source `ha-env.sh` first.

## Choose one command

| User intent | First and normally only command |
|---|---|
| Is something on, off, open, or closed? | `scripts/ha-status "QUERY"` |
| Turn on or open one resolved target | `scripts/ha-on "QUERY"` |
| Turn off or close one resolved target | `scripts/ha-off "QUERY"` |
| Activate a scene, script, or automation | `scripts/ha-trigger "QUERY"` |
| List controllable things in an area | `scripts/ha-area-summary "AREA"` |
| Find or identify an unfamiliar target | `scripts/ha-find "QUERY"` |
| Run a reviewed local HA intent phrase | `scripts/ha-intent "PHRASE"` |
| Ask for an HA weather forecast | `scripts/ha-weather [OPTIONS]` |

Action wrappers resolve, reject ambiguity, perform the service call, and confirm
physical state where possible. They do not need a separate discovery or status
preflight.

## Home companions

A home companion owns reviewed aliases, preferred aggregate entities, known
intent phrases, and topology exceptions. If Pi's available-skills metadata names
a companion for the active home, load that exact skill directly. Never search the
filesystem for `*home*` or `*companion*` files.

Prefer a companion's exact mapping over fuzzy discovery. If no matching companion
is advertised or loaded, proceed with the generic wrapper; do not delay a routine
request merely to hunt for private context. See
[home-companion.md](references/home-companion.md) only when creating or maintaining
a companion.

## Why the resolver exists

Home Assistant may assign an area to a parent device but not its entities. Human
room requests can therefore require an area -> device -> entity -> state join.
The resolver performs that join and keeps exact entity identity stronger than
area or device context. Do not replace fuzzy room resolution with an entity-only
registry query.

An exact `domain.object_id` bypasses the full join when safe. Companion mappings
should therefore pass exact entity ids directly.

## Interpret output

Wrappers return compact JSON and one of these statuses:

- `ok`: the request completed. For physical devices, inspect `state_confirmed`.
- `no_match`: no safe target matched. Use `ha-find` only now, or ask the human;
  never invent an entity id.
- `ambiguous`: multiple top candidates matched and no action occurred. Ask, or
  retry with an exact reviewed `entity_id`.
- `error` or `infrastructure_error`: configuration, authentication, transport,
  dependency, or Home Assistant failed. Stop rather than converting the failure
  into another action.

Exit codes are `0` for success, `1` for no match, `2` for ambiguity or a rejected
HA response, and `3` for infrastructure failure.

## Control rules

`ha-on` and `ha-off` act only on `light`, `switch`, and `cover`. For a cover, on
means open and off means close. They act automatically only when the top match is
unique. Use `--all` only when the human explicitly requested every top-scoring
match.

`ha-trigger` follows the same ambiguity rule and maps:

- `scene` to `scene.turn_on`
- `script` to `script.turn_on`
- `automation` to `automation.trigger`

Physical covers can outlast the confirmation window. If a command was accepted
but `state_confirmed` is false, wait and run `ha-status`; do not immediately
resend a command to a moving door or blind.

## Intent routing

Use `ha-intent` only for a phrase documented by the home companion or explicitly
requested by the human. It targets Home Assistant's built-in
`conversation.home_assistant` agent, not an arbitrary conversational LLM or the
selected Assist pipeline.

- `ok`: stop; the intent matched.
- `no_match`: a direct wrapper may be used if the requested action is clear.
- `error` or `infrastructure_error`: stop, because HA may have partially processed
  the request.

Without home-specific doctrine, prefer deterministic direct control over
speculative natural-language phrases. Add `--debug` only when raw HA intent data
is genuinely needed.

## Other domains

Use `ha-find --include-all-domains "QUERY"` to resolve sensors, climate entities,
media players, vacuums, timers, and other domains. Then use the exact entity id
in a raw service call. Read only the relevant reference:

- Common service syntax: [services.md](references/services.md)
- Media-player status and transport: [media.md](references/media.md)
- Helper-backed schedules: [scheduling.md](references/scheduling.md)
- Installation failures: [setup.md](references/setup.md)

For Spotify catalog search, library management, playlist curation, podcasts, or
Spotify Connect playback, use the standalone `spotify-cli` skill.

## Raw fallback

Use raw `hass-cli` only for unsupported domains or debugging after a wrapper
cannot express the operation. Load the same environment once:

```bash
source scripts/ha-env.sh
hass-cli -o json state list 'sensor.*'
hass-cli service call climate.set_temperature \
  --arguments entity_id=climate.downstairs,temperature=70
```

Prefer JSON. Do not list every service or registry merely to rediscover syntax
already documented in the relevant reference.
