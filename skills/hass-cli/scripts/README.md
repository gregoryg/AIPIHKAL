# Home Assistant wrapper scripts

These scripts provide a higher-level, LLM-friendly layer over `hass-cli`.

They are meant to answer the kinds of questions humans and LLMs naturally ask:

- "what can I control in the bar?"
- "turn on the bar light"
- "are the garage doors closed?"
- "run good night"
- "trigger bar on quickie"

instead of forcing area → device → entity registry spelunking.

## Scripts

### `ha-find`
Search areas and actionable entities from a human-ish phrase.

```bash
skills/hass-cli/scripts/ha-find "bar light"
skills/hass-cli/scripts/ha-find "garage"
```

Returns compact JSON with:
- `area_matches`
- `best_matches`

Each match is intentionally small and decision-ready:
- `label`
- `entity_id`
- `kind`
- `state`
- `area`
- `device`
- `score`

### `ha-area-summary`
Show actionable entities in a resolved area.

```bash
skills/hass-cli/scripts/ha-area-summary "Bar"
```

Useful when the human or LLM thinks in rooms/areas first.

### `ha-status`
Compact status-oriented lookup.

```bash
skills/hass-cli/scripts/ha-status "garage"
skills/hass-cli/scripts/ha-status "bar light"
```

This is optimized for high-level questions like:
- "are the garage doors closed?"
- "what state is the bar light in?"

### `ha-on` / `ha-off`
Resolve a human-ish phrase and control the result.

```bash
skills/hass-cli/scripts/ha-on "bar light"
skills/hass-cli/scripts/ha-off "bar light"
```

If the best match is ambiguous, the script returns candidate matches and does not act.

Use `--all` only when multi-entity action is intentional:

```bash
skills/hass-cli/scripts/ha-on --all "garage lights"
```

For `cover` entities:
- `ha-on` maps to open
- `ha-off` maps to close

### `ha-trigger`
Resolve a human-ish phrase and trigger a higher-level Home Assistant action.

```bash
skills/hass-cli/scripts/ha-trigger "good night"
skills/hass-cli/scripts/ha-trigger "bar on quickie"
```

Supported triggerable domains:
- `scene` → `scene.turn_on`
- `script` → `script.turn_on`
- `automation` → `automation.trigger`

If the best match is ambiguous, the script returns candidate matches and does not act unless `--all` is explicitly requested.

### `ha-weather`
Fetch weather forecast from the HA weather entity.

```bash
skills/hass-cli/scripts/ha-weather               # week overview (twice-daily)
skills/hass-cli/scripts/ha-weather --tomorrow    # tomorrow hourly
skills/hass-cli/scripts/ha-weather --today       # today hourly
skills/hass-cli/scripts/ha-weather --hourly      # full week hourly
skills/hass-cli/scripts/ha-weather --json        # raw JSON
```

Uses the HA WebSocket `get_forecasts` service. The weather entity is read from
`HA_WEATHER_ENTITY` (default: `weather.kapa`). Set this in `.env` for other installations.
Not all entities support all forecast types — NWS supports `hourly` and `twice_daily`;
`daily` is not universally available.

### `ha-intent`
Send a natural-language phrase through HA's built-in intent pipeline — the same path as a voice command via HA Assist.

```bash
skills/hass-cli/scripts/ha-intent "turn off bathroom"
skills/hass-cli/scripts/ha-intent "good morning"
skills/hass-cli/scripts/ha-intent "movie time"
```

This is the right tool when a phrase may be backed by a **custom automation** in HA's intent vocabulary. For example, "turn off bathroom" might trigger a timed automation that sequences multiple switches — not just `light.turn_off` on the nearest entity. The intent pipeline fires that automation correctly. A direct `ha-off` call would bypass it entirely.

**The two-step fallback pattern:**

```
1. ha-intent "turn on/off X"   →  status: ok      → done
                                →  status: no_match → fall back to ha-on / ha-off
```

Use `ha-intent` first for room/area-level commands. Fall back to `ha-on`/`ha-off` when the intent engine doesn't recognise the phrase.

**Agent isolation:** `ha-intent` explicitly targets `conversation.home_assistant` — HA's built-in intent-only engine. It does not forward to any LLM conversation agent (Ollama, Claude, GladOS, etc.) on a miss. A `no_match` result comes straight back to the caller.

**Response types:**
- `status: ok`, `response_type: action_done`, empty `success` list → automation triggered (normal; HA doesn't report entity outcomes for automation-triggered intents)
- `status: ok`, `response_type: action_done`, populated `success` list → direct entity control succeeded
- `status: no_match` → phrase not recognised or entity resolution failed; fall back to `ha-on`/`ha-off`/`ha-trigger`

HA's NLU uses exact entity names and defined aliases — not fuzzy matching. Phrases that work via voice work here; invented phrasings generally will not.

## Setup

Default least-awful setup:

```bash
cp skills/hass-cli/.env.template skills/hass-cli/.env
$EDITOR skills/hass-cli/.env
```

Fill in:
- `HASS_SERVER`
- `HASS_TOKEN`

The shell wrappers now all:
- source `skills/hass-cli/scripts/ha-env.sh`
- load `skills/hass-cli/.env` first
- fall back to `~/.authinfo.gpg` only if needed
- fail fast with a clear message if `HASS_SERVER` or `HASS_TOKEN` is still missing

### Spotify wrappers

These wrappers treat Spotify as the provider entity and HEOS rooms/groups as playback targets.

#### Transport and routing

```bash
skills/hass-cli/scripts/ha-spotify-status
skills/hass-cli/scripts/ha-spotify-target "Music Room"
skills/hass-cli/scripts/ha-spotify-play
skills/hass-cli/scripts/ha-spotify-pause
skills/hass-cli/scripts/ha-spotify-next
skills/hass-cli/scripts/ha-spotify-previous
```

Current model:
- provider entity: `media_player.spotify_gortsleigh`
- target selection: `media_player.select_source`
- targets come from Spotify's `source_list`
- target/player state is shown as corroboration
- grouped targets such as `Lefty + Pancho` return multiple corroborating players when detectable

#### Browse library and play specific content

```bash
# List available library sections
skills/hass-cli/scripts/ha-spotify-browse

# Browse a section — returns items with playable URIs
skills/hass-cli/scripts/ha-spotify-browse artists
skills/hass-cli/scripts/ha-spotify-browse playlists
skills/hass-cli/scripts/ha-spotify-browse albums
skills/hass-cli/scripts/ha-spotify-browse liked
skills/hass-cli/scripts/ha-spotify-browse recent
skills/hass-cli/scripts/ha-spotify-browse top-artists
skills/hass-cli/scripts/ha-spotify-browse top-tracks

# Play a URI (type auto-detected from URI prefix)
skills/hass-cli/scripts/ha-spotify-play-uri "spotify:artist:3X0tJzVYoWlfjLYI0Ridsw"

# Play a URI and route to a room in one command
skills/hass-cli/scripts/ha-spotify-play-uri --target "Lefty + Pancho" "spotify:artist:3X0tJzVYoWlfjLYI0Ridsw"
```

**Important:** `ha-spotify-browse` uses the HA WebSocket API (not hass-cli) and requires Spotify to be
playing or paused. When Spotify is idle, HA removes BROWSE_MEDIA from `supported_features` and browse
will return a `not_supported` error with instructions. Start playback first, then browse.

`ha-spotify-play-uri` works with any valid Spotify URI — including artists not in your library.

#### Dump library to a local searchable file

```bash
# Dump all available sections to ~/.local/share/ha-spotify/
skills/hass-cli/scripts/ha-spotify-dump

# Full followed-artists list via direct Spotify API (bypasses the 48-artist cap)
skills/hass-cli/scripts/ha-spotify-dump --spotify-token TOKEN

# Grep the result
grep -i "lyle lovett" ~/.local/share/ha-spotify/library.txt
```

Output files:
- `library.txt` — sorted, one entry per line: `Title | spotify:type:id | type`
- `library.json` — full structured dump with all sections

Sections dumped: playlists, followed artists, saved albums, recently played, top artists, top tracks.

**The 48-artist cap:** the upstream `spotifyaio` library (used by the HA Spotify integration)
hardcodes `limit=48` in `get_followed_artists()` with no pagination. The maintainer has closed
the issue as "not planned" (https://github.com/joostlek/python-spotify/issues/730).
The `--spotify-token` flag works around this by calling the Spotify API directly.
Get a token with `user-follow-read` scope from https://developer.spotify.com/console/get-following/

The typical workflow for finding and playing specific content:
1. `ha-spotify-dump` to build/refresh the local cache (run when library changes)
2. `grep -i "artist name" ~/.local/share/ha-spotify/library.txt` to find the URI
3. `ha-spotify-play-uri --target "Room" "spotify:...:..."` to play it

## Notes

- Default actionable domains: `light`, `switch`, `cover`, `scene`, `script`, `automation`
- Matching is fuzzy but action is conservative
- Raw `hass-cli` commands remain available for debugging edge cases
- For media control, trust transport state more than stale remembered metadata on idle players
- **Intent-first rule:** for room/area commands, try `ha-intent` before `ha-on`/`ha-off`. HA's intent vocabulary encodes domain knowledge (timed sequences, multi-device automations) that direct service calls silently bypass.
- `ha-intent`, `ha-spotify-browse`, `ha-spotify-dump`, and `ha-spotify-play-uri` use the HA WebSocket API or REST API directly — not `hass-cli` — because `hass-cli` cannot handle nested JSON payloads or WebSocket-only commands.
