---
name: hass-cli
description: Control and query Home Assistant via the hass-cli Python CLI. Use when Codex needs to interact with a Home Assistant instance for controlling devices (lights, switches, climate, covers, etc.), querying entity states or attributes, managing areas/devices/entities, calling services, checking system status, or any Home Assistant automation/control tasks. Supports JSON output for structured data.
---

# hass-cli

Control Home Assistant via the `hass-cli` Python CLI.

## Read this first

House-specific doctrine overrides this generic skill.

If both of these are loaded:
- `hass-cli`
- a home-specific skill such as `casona-ranona-home`

then the house skill wins on:
- whether to use `ha-intent` first
- which alias/entity a phrase maps to
- whether a command is a reviewed direct-control case

Casona Ranona example:
- `bar light` is a reviewed direct-control case
- do not try `ha-intent` first
- use `ha-on` or `ha-off` directly

## Home context appendix

If a `*-home.md` file exists in `skills/hass-cli/`, **read it before proceeding**. It contains
home-specific context that this generic skill cannot know: device naming conventions, area quirks,
verified `ha-intent` phrases, resident names, and semantic mappings that are invisible in the
entity registry. Without it, you will make confident wrong guesses about amusingly named lights.

A template lives at `skills/hass-cli/YOUR_HOME_NAME-home.md.template`.
The home file is gitignored (it may contain private information).

## Configuration

**Binary location:** `~/.local/python-venvs/boodle/bin/hass-cli` (or see if it's in the path already with `which hass-cli`)

## Categorized-install pitfall

If this skill is installed under a categorized path such as `smart-home/hass-cli/` instead of a flat `skills/hass-cli/`, older wrapper assumptions may break.

Check `references/categorized-install.md` for the proven compatibility fix. In short:
- prefer loading `hass-cli/.env` directly from `ha-env.sh`
- do not assume `skills/common/secrets.sh` exists
- install `websockets` into the boodle venv for websocket-backed helpers like `ha-intent`

**Secret Management (Prefer `.env`, retain fancy-person mode as fallback):**

Default setup:

```bash
cp skills/hass-cli/.env.template skills/hass-cli/.env
$EDITOR skills/hass-cli/.env
```

Then the wrappers auto-load configuration via:

```bash
source skills/hass-cli/scripts/ha-env.sh
```

Load order:
1. existing exported environment variables
2. `skills/hass-cli/.env`
3. repo-root `.env`
4. current-directory `.env`
5. `~/.authinfo.gpg` (`machine ha-mcp-token`) for `HASS_TOKEN` only

`HASS_SERVER` and `HASS_TOKEN` must both be set before wrapper execution continues.

## Primary workflow: use the wrappers first

The raw Home Assistant registry model is often awkward for humans and LLMs:

- humans think "bar light"
- Home Assistant areas often live on devices, not entities
- many entities have `area_id: null`
- turning something on still requires the final entity id

In this repo, prefer the wrapper scripts in `skills/hass-cli/scripts/` before falling back to raw `hass-cli` discovery commands.

### Wrapper scripts

These scripts auto-load Home Assistant config through `ha-env.sh` and return compact, decision-ready JSON.

### Quick decision table

Read the home-specific appendix first. Its direct-control exceptions override this generic table.

- User asks **what is in room/area X?**
  - Use `skills/hass-cli/scripts/ha-area-summary "X"`
- User asks **find or identify X**
  - Use `skills/hass-cli/scripts/ha-find "X"`
- User asks **is X on/off/open/closed?**
  - Use `skills/hass-cli/scripts/ha-status "X"`
- User asks **turn on/off X** (especially a room or area name)
  - **First** try `skills/hass-cli/scripts/ha-intent "turn on/off X"`
  - If `status: ok` — done. The intent pipeline matched (possibly triggering a custom automation).
  - If `status: no_match` — fall back to `skills/hass-cli/scripts/ha-on "X"` or `ha-off "X"`
- User asks **run/trigger/activate X**
  - Use `skills/hass-cli/scripts/ha-trigger "X"`
- User asks **anything about weather, temperature, forecast, rain, snow, or conditions**
  - Use `skills/hass-cli/scripts/ha-weather` — do not attempt raw HA entity queries or external APIs
  - Add `--tomorrow` or `--today` for hourly detail; `--hourly` for the full week hour by hour
- User asks **what music can I play / what's in my library?**
  - First check `~/.local/share/ha-spotify/library.txt` (grep it — it's sorted and fast)
  - If stale or missing: run `skills/hass-cli/scripts/ha-spotify-dump` to refresh
  - Or browse live: `skills/hass-cli/scripts/ha-spotify-browse artists` (or `playlists`, `albums`, `recent`, etc.)
- User asks **play artist/album/playlist X**
  - Grep `~/.local/share/ha-spotify/library.txt` for the URI, then `skills/hass-cli/scripts/ha-spotify-play-uri URI [--target ROOM]`
  - Or use the URI directly if known: `skills/hass-cli/scripts/ha-spotify-play-uri "spotify:artist:xxx"`
- If a control or trigger command returns ambiguity
  - Inspect `best_matches`
  - Retry with a more specific target such as an exact `entity_id`
  - Only use `--all` when the human clearly intends multi-entity action

### Recommended command patterns

```bash
# Discovery
skills/hass-cli/scripts/ha-find "bar light"
skills/hass-cli/scripts/ha-area-summary "Bar"

# Status questions
skills/hass-cli/scripts/ha-status "garage"
skills/hass-cli/scripts/ha-status "music room"

# Intent pipeline (try first for room/area commands)
skills/hass-cli/scripts/ha-intent "turn off bathroom"
skills/hass-cli/scripts/ha-intent "good morning"

# Direct control after resolution (fallback if ha-intent returns no_match)
skills/hass-cli/scripts/ha-on "light.living_room"
skills/hass-cli/scripts/ha-off "light.living_room"

# Higher-level actions (scenes, scripts, named automations)
skills/hass-cli/scripts/ha-trigger "good night"
skills/hass-cli/scripts/ha-trigger "bar on quickie"

# Weather
skills/hass-cli/scripts/ha-weather
skills/hass-cli/scripts/ha-weather --tomorrow
skills/hass-cli/scripts/ha-weather --today
skills/hass-cli/scripts/ha-weather --hourly   # full week, hourly detail
skills/hass-cli/scripts/ha-weather --json     # raw JSON for LLM use

# Spotify on HEOS — transport and routing
skills/hass-cli/scripts/ha-spotify-target "Music Room"
skills/hass-cli/scripts/ha-spotify-play
skills/hass-cli/scripts/ha-spotify-next

# Spotify — browse library and play specific content
skills/hass-cli/scripts/ha-spotify-browse
skills/hass-cli/scripts/ha-spotify-browse artists
skills/hass-cli/scripts/ha-spotify-browse playlists
skills/hass-cli/scripts/ha-spotify-play-uri "spotify:artist:3X0tJzVYoWlfjLYI0Ridsw"
skills/hass-cli/scripts/ha-spotify-play-uri --target "Lefty + Pancho" "spotify:artist:3X0tJzVYoWlfjLYI0Ridsw"

# Spotify — dump full library to a local searchable file
skills/hass-cli/scripts/ha-spotify-dump
skills/hass-cli/scripts/ha-spotify-dump --spotify-token TOKEN  # full artist list
grep -i "lyle lovett" ~/.local/share/ha-spotify/library.txt
```

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

**Trigger a scene, script, or automation:**
```bash
skills/hass-cli/scripts/ha-trigger "good night"
skills/hass-cli/scripts/ha-trigger "bar on quickie"
```

**Spotify on HEOS:**
```bash
skills/hass-cli/scripts/ha-spotify-status
skills/hass-cli/scripts/ha-spotify-target "Music Room"
skills/hass-cli/scripts/ha-spotify-play
skills/hass-cli/scripts/ha-spotify-pause
skills/hass-cli/scripts/ha-spotify-next
```

### Wrapper behavior

- `ha-find`
  - searches both areas and entities
  - returns multiple plausible matches instead of forcing one
  - defaults to actionable domains (`light`, `switch`, `cover`, `scene`, `script`, `automation`)
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

- `ha-trigger`
  - resolves a human-ish phrase to a `scene`, `script`, or `automation`
  - if exactly one strong match exists, trigger it
  - if several equally strong matches exist, return them as JSON and do not act
  - use `--all` only when intentional multi-trigger behavior is desired
  - maps domains as follows:
    - `scene` → `scene.turn_on`
    - `script` → `script.turn_on`
    - `automation` → `automation.trigger`

### Timer guidance: HA timers vs Wyoming Satellite timers

If the user asks to start or manage a timer, first distinguish which timer system they mean.

Use raw Home Assistant timer services when working with actual `timer.*` entities:
- `timer.start`
- `timer.pause`
- `timer.cancel`
- `timer.finish`
- `timer.change`

Important observed behavior:
- `hass-cli service call timer.start ...` may return `[]` even when the timer started successfully
- verify success by checking timer state afterward with `hass-cli -o json state get timer.some_timer`
- if the user reports that `timer.start` "did nothing", inspect `state list 'timer.*'` and confirm the target entity actually exists

Do not assume Home Assistant timers reproduce Wyoming Satellite local timer behavior.

Observed distinction in this environment:
- satellite-originated voice assistant sessions may have `HassTimer*` tools
- those create/manage timers local to the originating Wyoming Satellite device and use timer start/finish hooks there
- Web UI / laptop-originated sessions do not have those tools
- therefore raw `hass-cli` timer calls cannot by themselves recreate behaviors like beeping on the originating puck or running the satellite's local `notify-send` / speech hook

If the user wants portable, cross-channel timer behavior from Hermes itself, that is a separate local timer system concern, not a `hass-cli` wrapper concern.

Observed adjacent pitfall from the portable Hermes timer workflow in this environment:
- remote finish actions sent over SSH need the remote command wrapped as one quoted command string, not bare tokenized arguments
- `ssh host notify-send {label} {message}` is brittle once placeholders expand to text with spaces
- prefer `ssh host "notify-send {label} {message}"`, with placeholder values shell-quoted before interpolation
- writing a timer outbox file is not the same thing as Slack delivery; treat remote notify, outbox creation, and Slack send as separate verifications

See `skills/hass-cli/references/timers.md` for the full distinction and verification pattern.

### Timer caveat: Home Assistant timers vs Wyoming Satellite timers

Raw `hass-cli` can control normal Home Assistant timer entities with services like:
- `timer.start`
- `timer.pause`
- `timer.cancel`
- `timer.finish`
- `timer.change`

Important nuance:
- a successful `hass-cli service call timer.start ...` may return `[]` or no interesting payload
- this does **not** necessarily mean failure
- verify by reading the timer state afterward (`hass-cli -o json state get timer.<name>`) and checking for `state: active`, `remaining`, and `finishes_at`

Do **not** assume HA timer entities reproduce the voice-assistant timer behavior seen on Wyoming Satellite devices.

Wyoming Satellite timer behavior is separate:
- satellite-originated LLM sessions may expose `HassTimer*` tools
- those tools create/manage timers local to the originating satellite
- Wyoming uses satellite-local timer start/finish hooks for beeps, TTS, and device-specific notifications
- Web UI / laptop sessions generally do **not** have `HassTimer*` tools available

Practical implication:
- use raw `hass-cli` timer services for HA timer entities only
- do not promise that `timer.start` from a laptop/Web UI session will recreate puck-local or satellite-local timer UX
- if the human needs cross-channel or machine-local timer behavior from Hermes, use a separate portable timer workflow rather than pretending HA timers and Wyoming timers are the same thing

### Guidance for automations with variable schedules

If a human wants an automation to run at a user-chosen future date/time, do **not** assume the right approach is to edit the automation definition itself.

Prefer this Home Assistant pattern instead:
- keep the automation logic separate
- store the chosen trigger time in an `input_datetime` helper
- have the automation trigger from that helper-driven time

Why this pattern is preferred:
- the scheduled time becomes explicit entity state
- the date/time can be changed safely with a service call
- wrappers and LLMs can inspect and modify the schedule without mutating automation YAML/config
- this is much easier to automate than spelunking through automation internals

When working with such automations:
1. Find the automation entity, for example `automation.announce_yogurt`.
2. Find the related `input_datetime` helper, for example `input_datetime.yogurt_trigger_time`.
3. Set the helper with:
   - `input_datetime.set_datetime`
4. Enable the automation if needed with:
   - `automation.turn_on`
5. Treat the automation state and helper datetime as a **combined conceptual schedule**, even though Home Assistant exposes them as separate entities.

Example:
```bash
hass-cli service call input_datetime.set_datetime \
  --arguments entity_id=input_datetime.yogurt_trigger_time,datetime="2026-05-04 22:00:00"

hass-cli service call automation.turn_on \
  --arguments entity_id=automation.announce_yogurt
```

Important nuance:
- this pattern is somewhat more obtuse in the HA UI because enablement and scheduled time live in separate entities
- but it is significantly better for LLM/tool automation because the schedule becomes explicit and editable

### LLM guidance for room-level commands

When a human says something like `turn on the music room`, the likely intent is usually **room-wide lighting control**, not necessarily "pick one arbitrary entity in that area".

Use this reasoning path:

1. If the query is primarily an **area/room name**, first inspect `ha-area-summary` or `ha-find` results.
2. Prefer a **named aggregate lighting entity** if one exists, such as:
   - a `light.*` entity whose label matches the room name
   - a room/group light like `light.living_room` labeled `Music Room`
   - another obvious room-wide light group or helper
3. Remember that what humans think of as a "light" may actually be represented as:
   - a `light`
   - a `switch`
   - a `plug`
   - a named group/helper entity
4. If a likely room-wide aggregate exists, prefer that as the first target.
5. If no such aggregate exists, consider whether `--all` is appropriate for the actionable entities in the room.
6. Do not blindly use `--all` for a room command just because several entities match.
7. Keep the human or LLM in the loop when several plausible interpretations remain.

Important nuance:
- a named group is often the best match for room-wide commands
- but it may not include every intended entity
- therefore the wrappers should remain conservative, while the LLM uses the compact JSON plus domain knowledge to choose smartly

- `ha-status`
  - optimized for questions like "are the garage doors closed?"
  - returns compact area and actionable-entity status without including non-actionable sensors by default

- `ha-intent`
  - sends a natural-language phrase through HA's built-in intent pipeline (`conversation.home_assistant`)
  - this is the same path as voice commands via HA Assist — custom intent phrases and automation-backed phrases fire correctly
  - think of it as a **fast first pass for explicitly-defined intents/phrases**, not as fuzzy discovery
  - returns `status: ok` with `response_type: action_done` when the intent matched and executed
  - `action_done` with an empty `success` list is normal for automation-triggered intents — the automation fired but HA does not report individual entity outcomes
  - returns `status: no_match` when HA does not recognise the phrase — this is expected behavior when no matching intent/phrase is defined, and caller should immediately fall back to `ha-on`/`ha-off`/`ha-trigger`
  - HA may also surface a WebSocket-level `unknown_error` for an unrecognised phrase; in practice treat that the same as `no_match` and fall back rather than treating it as a broken integration
  - HA's NLU uses exact entity names and aliases, not fuzzy matching — phrases that work via voice or explicit intent definitions work here; invented phrasings likely will not
  - **use this first for room-level or area-level commands** ("turn off bathroom", "good morning", "movie time") where a custom automation may be the correct action
  - do not use this as a general replacement for `ha-on`/`ha-off` — it is a complement, not a substitute

- `ha-weather`
  - fetches forecast from the HA weather entity via the WebSocket `get_forecasts` service
  - default (no args): week overview using `twice_daily` periods — day/night pairs with condition, temperature, and precipitation probability
  - `--today` / `--tomorrow`: hourly detail for that day
  - `--hourly`: full hourly detail for the week
  - `--json`: raw JSON output for programmatic use
  - weather entity is read from `HA_WEATHER_ENTITY` env var — set this in your home's `.env` or shell wrapper to point at the right entity for your installation
  - uses the HA WebSocket API (not `hass-cli`) — requires `twice_daily` or `hourly` forecast type support from the entity; `daily` is not universally supported

- `ha-spotify-browse`
  - uses the HA WebSocket API to browse the Spotify library (not hass-cli)
  - **requires Spotify to be playing or paused** — when idle, HA drops BROWSE_MEDIA from supported_features and browse returns an error
  - with no arguments: lists available library sections with their content types
  - with a section name: returns all items with `title`, `uri`, `type`, and `can_play`
  - available sections: `playlists`, `artists`, `albums`, `liked`, `recent`, `top-artists`, `top-tracks`
  - all returned URIs are ready to pass directly to `ha-spotify-play-uri`

- `ha-spotify-play-uri`
  - plays a specific Spotify URI via `media_player.play_media` (REST API, not hass-cli)
  - media type is auto-detected from the URI prefix (`spotify:artist:`, `spotify:album:`, `spotify:playlist:`, `spotify:track:`, etc.)
  - use `--type` to override if auto-detection fails
  - use `--target ROOM` to select a playback destination in the same command
  - if Spotify is idle when called, HA will attempt to route to the first available Spotify Connect device — prefer targeting explicitly
  - works for any valid Spotify URI, including ones not in the user's library
  - on HEOS targets, the Spotify entity may flip to `playing` before the room player catches up; an immediate corroboration check can briefly show the target player as `paused`
  - if that happens, wait a few seconds and re-run `ha-spotify-status` before treating it as a routing failure

- `ha-spotify-dump`
  - dumps all available Spotify library sections to `~/.local/share/ha-spotify/library.txt` (grep-friendly) and `library.json`
  - text file format: `Title | spotify:type:id | type` — sorted alphabetically, ready to grep
  - sections dumped: playlists, followed artists, saved albums, recently played, top artists, top tracks
  - **followed artists are capped at 48** by a hardcoded limit in the upstream `spotifyaio` library (the maintainer has closed the pagination issue as "not planned": https://github.com/joostlek/python-spotify/issues/730)
  - pass `--spotify-token TOKEN` to bypass the HA integration entirely and fetch all followed artists directly from the Spotify API with proper cursor pagination
  - a Spotify OAuth token for `--spotify-token` can be obtained from https://developer.spotify.com/console/get-following/ (use the `user-follow-read` scope)
  - the dump file should be refreshed periodically; grep it before calling `ha-spotify-browse` to avoid a live WebSocket round-trip
  - **requires Spotify to be playing or paused** (same idle restriction as `ha-spotify-browse`)

### Spotify media guidance

For Spotify, treat the Spotify entity as the provider/control surface and the HEOS room/group names in Spotify's `source_list` as playback targets.

#### What this integration can and cannot do

**Can do:**
- Select which HEOS room or group receives audio (`ha-spotify-target`)
- Play, pause, skip, and go to previous track
- Query current track, artist, album, position, and volume
- Move playback between rooms mid-song (position is preserved)

**Cannot do:**
- Search for or play a specific artist, album, track, or playlist by name
- Browse the Spotify library
- Queue or enqueue content

The HA Spotify integration in this setup exposes `supported_features: 2048` (SELECT_SOURCE only) when idle, and transport controls when active. It acts as a Spotify Connect source-switcher with transport buttons - not a full playback controller. `play_media` calls return 500 errors because the capability is simply not exposed.

**Practical implication:** to play specific content, the human must initiate playback from a Spotify client (phone, desktop, etc.) first. Once something is playing, the wrappers fully own routing and transport from that point.

#### Best practices for media control

1. **Always target before playing.** Use `ha-spotify-target` to route to the desired room, then `ha-spotify-play`. Calling play without targeting first will resume on whatever source Spotify last remembered.

2. **Verify the source held before declaring success.** Any other Spotify-connected device (phone, laptop, etc.) can grab the active session at any moment. After a target+play sequence, the source shown in `ha-spotify-status` is the ground truth - not the service call's return value.

3. **`state_confirmed: true` in play/pause responses confirms transport state only.** It does not confirm the source stayed on the intended target. If the human reports audio is not playing, run `ha-spotify-status` immediately to check whether the source drifted to another device.

4. **Use `ha-spotify-status` to verify reality.** Especially after any multi-device scenario or unexpected silence. The corroboration from both `spotify` (the HA Spotify entity) and `target.players` (the HEOS player) is the most reliable picture of what is actually happening.

5. **Position is preserved when moving between rooms.** `ha-spotify-target` then `ha-spotify-play` picks up the track at the same position - no need to seek.

6. **HEOS friendly names and HA entity IDs often diverge.** e.g. `Music Room` in `source_list` maps to `media_player.living_room` in HA. The wrapper handles this transparently; the corroboration output surfaces the real entity ID for awareness.

Use this reasoning path:
1. Use `ha-spotify-status` to inspect current Spotify transport state and selected target.
2. Use `ha-spotify-target "room or group"` to select a HEOS target such as `Music Room`, `Kitchen`, or `Lefty + Pancho`.
3. Use `ha-spotify-play`, `ha-spotify-pause`, `ha-spotify-next`, and `ha-spotify-previous` for transport control.
4. Trust transport state more than stale remembered metadata on idle room players.
5. Use the room/player state as corroboration that the correct target is active.
6. If the human reports no audio despite a successful-looking play call, run `ha-spotify-status` - another device may have grabbed the session.

### Ambiguity resolution examples

**Example: `turn on music room`**
- First inspect `ha-area-summary "Music Room"`.
- If there is a likely room-wide light/group entity such as `light.living_room` labeled `Music Room`, prefer that over individual member lights.
- If no likely aggregate exists, then consider `--all` only if whole-room multi-entity control is clearly intended.

**Example: `are the garage doors closed?`**
- Use `ha-status "garage"`.
- Read the `best_matches` or area entities and answer from their `state` values.
- Do not use `ha-find` first unless `ha-status` is insufficient.

## Categorized Layout Pitfalls

If the skill is installed under a categorized directory (e.g. `skills/smart-home/hass-cli/` instead of the expected flat `skills/hass-cli/`), the wrapper scripts' path assumptions break. Symptoms:

- `ha-env.sh` can't find `skills/common/secrets.sh`
- Wrapper scripts fail with `repo_root: unbound variable` or file-not-found errors for Python scripts

**Fix (temporary until repackaging):**
1. In `ha-env.sh`, set `repo_root` to the categorized parent (e.g. `~/.hermes/skills/smart-home`)
2. Create a compatibility symlink: `skills/smart-home/skills/hass-cli → ../hass-cli` so `$repo_root/skills/hass-cli/scripts/` resolves
3. Ensure `.env` is sourced directly in `ha-env.sh` (the original `skills/common/secrets.sh` may not exist)

**Missing Python packages:** `ha-intent.py` requires `websockets` in the venv used by the wrapper (`boodle` if using `~/.local/python-venvs/boodle/bin/python3`). Install with:
```bash
~/.local/python-venvs/boodle/bin/pip install websockets
```

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

## Fresh install pitfalls

When this skill is installed in the categorized layout (`skills/smart-home/hass-cli/`), several things can break on first use. See `references/fresh-install.md` for the full fix log; the key issues:

1. **`ha-env.sh` path resolution.** The wrapper scripts expect `$repo_root/skills/hass-cli/scripts/<file>`. In the categorized layout, `repo_root` must be set to `skills/smart-home/` (not `skills/`). The patched `ha-env.sh` handles this — verify it hasn't been overwritten by a skill update.

2. **Missing symlink.** Even with correct `repo_root`, the wrappers reference `$repo_root/skills/hass-cli/` which adds an extra `skills/` segment. Create a symlink:
   ```bash
   mkdir -p ~/.hermes/skills/smart-home/skills
   ln -s ~/.hermes/skills/smart-home/hass-cli ~/.hermes/skills/smart-home/skills/hass-cli
   ```

3. **Missing `websockets` Python package.** `ha-intent`, `ha-weather`, `ha-spotify-browse`, and `ha-spotify-dump` use `~/.local/python-venvs/boodle/bin/python3` and require `websockets`:
   ```bash
   ~/.local/python-venvs/boodle/bin/pip install websockets
   ```

4. **Missing `skills/common/secrets.sh`.** The original skill expected a shared secrets module. The patched `ha-env.sh` loads credentials directly from the `.env` file instead — no `secrets.sh` needed.

After fixing, verify with:
```bash
~/.hermes/skills/smart-home/hass-cli/scripts/ha-find "any entity name"
```

## Limitations

- `hass-cli info` uses a deprecated endpoint and may fail.
- The wrappers currently focus on `light`, `switch`, and `cover` because those are the most useful low-context control targets.
- Fuzzy matching is intentionally conservative about action: it may still surface near-matches, but `ha-on` / `ha-off` only act automatically when the best match is unambiguous unless `--all` is explicitly requested.
- Not every Home Assistant integration models devices correctly; some garage-door-like devices may still appear as simple on/off entities.

### Cover entities and physical travel time

`state_confirmed: false` on a `cover` close/open command does not necessarily mean the command failed. Garage doors and similar covers have physical travel time (typically 10–20 seconds) that exceeds the wrapper's polling window. The correct response is to wait a few seconds and re-check with `ha-status` rather than immediately retrying the command — a retry on a moving door is at best redundant and at worst reverses the action.

Also note that many covers report only binary states (`open` / `closed`) with no intermediate position. This is common when the integration uses a simple magnetic contact sensor rather than a motor controller:
- There is no `opening`, `closing`, or percentage-open state
- The door will show `open` throughout its travel until the closed sensor triggers
- Do not interpret a lingering `open` state during travel as a failure

Check the home appendix (`*-home.md`) for the specific sensor type used in this installation. If covers report only binary states, treat any non-confirmed close command as "command sent, verify with ha-status after allowing travel time".

## References

- `skills/hass-cli/references/fresh-install.md` — install troubleshooting (path resolution, missing deps, symlink fix)
- `skills/hass-cli/references/services.md`
- `skills/hass-cli/references/scheduling.md`
- `skills/hass-cli/references/timers.md` — distinction between HA `timer.*` entities and Wyoming Satellite local timers; includes verification pattern for `timer.start`
- `skills/hass-cli/references/portable-timer-delivery.md` — SSH quoting and sink-by-sink verification notes for portable Hermes timer finish actions in this environment
- `skills/hass-cli/scripts/README.md`
- `skills/hass-cli/scripts/ha_resolve.py`
- `skills/hass-cli/scripts/ha-status`
- `skills/hass-cli/scripts/ha-trigger`
- `skills/hass-cli/scripts/spotify_control.py`
- `skills/hass-cli/scripts/ha-spotify-status`
- `skills/hass-cli/scripts/ha-spotify-target`
- `skills/hass-cli/scripts/spotify_browse.py`
- `skills/hass-cli/scripts/ha-spotify-browse`
- `skills/hass-cli/scripts/ha-spotify-play-uri`
- `skills/hass-cli/scripts/spotify_dump.py`
- `skills/hass-cli/scripts/ha-spotify-dump`
- `skills/hass-cli/scripts/ha_intent.py`
- `skills/hass-cli/scripts/ha-intent`
- `skills/hass-cli/scripts/ha_weather.py`
- `skills/hass-cli/scripts/ha-weather`
