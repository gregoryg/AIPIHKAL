---
name: hass-cli
description: Control and query Home Assistant through small JSON-first wrappers around hass-cli and the Home Assistant APIs. Use for entity discovery, room or area inspection, state questions, safe light/switch/cover control, scene/script/automation triggering, built-in local intents, preferred Assist pipeline conversations, to-do lists, voice/calendar reminders, weather, scheduling, or raw Home Assistant service calls.
---

# Home Assistant CLI

## Voice reminder fast path

An explicit `/skill:hass-cli` request beginning with or semantically equivalent to
“remind me ...” is a Home Assistant voice/calendar reminder. As the first and
normally only action, run `scripts/ha-assist` with the complete original phrase.
Do not load a generic timer skill, create a systemd or Home Assistant timer,
calculate the target time, or substitute another scheduler. On `ok`, return the
wrapper's `speech` string verbatim as the entire response—no paraphrase, Markdown,
or preface. On any failure, stop without fallback. A home companion may add
stricter confirmation semantics.

## Conversational to-do fast path

When a home companion documents Assist-backed to-do lists, send the complete Home
Assistant operation portion through `scripts/ha-assist` as the first and normally
only command. Keep outer requests such as “explain your routing afterward” out of
the HA turn. The selected HA conversation model owns fuzzy list naming and
splitting requests such as “add A, B, and C” into separate HA tool calls. Do not
manually parse the item list, call `ha-intent`, discover entities or services, or
replace this route with raw `todo.*` calls.

For additions, append the companion's exact active-duplicate guard to the
original request. For removals, append its exact post-removal verification guard.
These remain one Assist turn; the outer model must not issue one shell command per
item. Queries need no operation guard. On `ok`, return `speech` verbatim. On
`clarification_needed`, return the exact question. On any failure, stop without a
fallback because the pipeline may have partially changed a list.

## Native tool fast path

If a `homeassistant` tool is available, prefer it for an ordinary one-target
status, turn-on/open, turn-off/close, or scene/script/automation trigger request.
It delegates to these wrappers, preserves their ambiguity and confirmation rules,
and returns a terminal user-facing result without a second model turn. Do not load
this skill merely to rediscover commands that the tool already exposes.

Load this skill for room-wide or custom household routines, weather, media,
scheduling, unsupported domains, raw service calls, failure diagnosis, or when
the native tool is unavailable. A home companion remains authoritative for
special semantics such as a phrase that starts an automation rather than directly
controlling similarly named entities.

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
| Create a voice/calendar reminder or run another companion-documented Assist feature | `scripts/ha-assist "COMPLETE ORIGINAL PHRASE"` |
| Add to, query, or remove from a companion-reviewed to-do list | `scripts/ha-assist "HA OPERATION plus companion safety instruction"` |
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

## Assist pipeline routing

`ha-assist` is deliberately separate from `ha-intent`. It runs one text turn
through Home Assistant's preferred Assist pipeline, including that pipeline's
conversation agent and contributed LLM tools. Use it for an explicit
`/skill:hass-cli` reminder request or another conversational feature documented by
the home companion. For reminders, pass the human's complete phrase unchanged;
do not pre-resolve the date or replace it with a timer, helper schedule, raw
calendar call, or invented confirmation. For to-do operations, preserve the
complete HA operation and append only the companion's documented list context and
safety guard. Keep requests for outer explanation, comparison, or post-mortem out
of the Assist turn.

Interpret its compact JSON conservatively:

- `ok`: return the pipeline's `speech`. For a mutating feature, require the
  home companion's documented authoritative wording before claiming success.
- `clarification_needed`: no completion may be claimed. Return the exact question
  in `speech`. An interactive caller can send the human's answer with
  `ha-assist --conversation-id ID "ANSWER"`; a one-shot invocation must stop and
  let the human issue a follow-up request.
- `error` or `infrastructure_error`: stop. The pipeline or one of its tools may
  have partially processed the request, so do not improvise a fallback or retry.

Omitting `--pipeline` intentionally selects Home Assistant's preferred pipeline.
Use `--pipeline ID` only when the home companion documents an exact override.
Allow at least 150 seconds for the shell tool call because the selected agent and
its tools may run longer than an ordinary wrapper; a caller timeout does not
authorize an automatic retry. Add `--debug` only when bounded raw pipeline events
are genuinely needed.

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
