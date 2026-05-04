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

## Setup

The shell wrappers automatically:
- source `skills/common/secrets.sh`
- call `load_hass_token`
- set `HASS_SERVER` to `http://172.16.17.7:8123` if not already exported

### Spotify wrappers

These wrappers treat Spotify as the provider entity and HEOS rooms/groups as playback targets.

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
