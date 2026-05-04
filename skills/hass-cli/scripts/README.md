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

## Notes

- Default actionable domains: `light`, `switch`, `cover`, `scene`, `script`, `automation`
- Matching is fuzzy but action is conservative
- Raw `hass-cli` commands remain available for debugging edge cases
- For media control, trust transport state more than stale remembered metadata on idle players
