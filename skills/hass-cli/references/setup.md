# Setup and troubleshooting

Read this reference only when installing the skill or diagnosing infrastructure
failures.

## Requirements

- Python 3.10 or newer
- `hass-cli` on `PATH`, normally installed from the `homeassistant-cli` package
- `websockets` for `ha-intent` and `ha-weather`
- a Home Assistant long-lived access token

Install the Python dependencies in an environment appropriate for the host:

```bash
python3 -m pip install homeassistant-cli websockets
```

Copy `.env.template` to `.env` in the skill directory and set:

```dotenv
HASS_SERVER=http://homeassistant.local:8123
HASS_TOKEN=replace-with-long-lived-access-token
```

The wrappers locate their Python entrypoints relative to themselves. The skill may
therefore be installed in a flat, categorized, symlinked, or profile-specific
directory without path rewrites or compatibility symlinks.

## Overrides

- `HASS_CLI_BIN`: alternate `hass-cli` executable
- `HA_PYTHON`: Python interpreter used by wrappers
- `HA_COMMAND_TIMEOUT`: command and connection timeout in seconds; default `30`
- `HA_WEATHER_ENTITY`: exact weather entity when zero or multiple `weather.*`
  entities exist

Already-exported variables take precedence over `.env` values.

## Diagnose in order

1. Run `command -v hass-cli` and `$HA_PYTHON --version`.
2. Source `scripts/ha-env.sh` and verify that `HASS_SERVER` is the intended URL.
3. Run `hass-cli -o json state list 'light.*'`.
4. Run `scripts/ha-find "known entity"`.
5. For WebSocket helpers, verify `websockets` with
   `$HA_PYTHON -c 'import websockets'`.

Do not print `HASS_TOKEN`, commit `.env`, or place household credentials in a
companion skill.
