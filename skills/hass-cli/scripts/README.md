# Home Assistant wrapper scripts

These scripts provide a higher-level, LLM-friendly layer over `hass-cli`.

They are meant to answer the kinds of questions humans and LLMs naturally ask:

- "what can I control in the bar?"
- "turn on the bar light"
- "are the garage doors closed?"

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

## Setup

The shell wrappers automatically:
- source `skills/common/secrets.sh`
- call `load_hass_token`
- set `HASS_SERVER` to `http://172.16.17.7:8123` if not already exported

## Notes

- Default actionable domains: `light`, `switch`, `cover`
- Matching is fuzzy but action is conservative
- Raw `hass-cli` commands remain available for debugging edge cases
