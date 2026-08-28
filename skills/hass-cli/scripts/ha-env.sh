#!/bin/bash
# Shared Home Assistant wrapper bootstrap. This file is sourced, not executed.

ha_env_script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ha_skill_dir=$(cd "$ha_env_script_dir/.." && pwd)

ha_env_parse_value() {
    local key=$1
    local raw=$2
    local first=${raw:0:1}
    local last=${raw: -1}

    if (( ${#raw} >= 2 )) &&
            [[ ( "$first" == '"' && "$last" == '"' ) ||
                ( "$first" == "'" && "$last" == "'" ) ]]; then
        raw=${raw:1:${#raw}-2}
    elif [[ "$first" == '"' || "$first" == "'" ||
            "$last" == '"' || "$last" == "'" ]]; then
        printf 'Error: unmatched quote in .env value for %s.\n' "$key" >&2
        return 1
    fi

    printf '%s' "$raw"
}

if [ -f "$ha_skill_dir/.env" ]; then
    while IFS='=' read -r key value; do
        case "$key" in
            HASS_SERVER|HASS_TOKEN|HASS_CLI_BIN|HA_PYTHON|HA_WEATHER_ENTITY|HA_COMMAND_TIMEOUT)
                if [ -z "${!key:-}" ]; then
                    value=${value%$'\r'}
                    if ! value=$(ha_env_parse_value "$key" "$value"); then
                        return 1
                    fi
                    export "$key=$value"
                fi
                ;;
        esac
    done < <(sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$ha_skill_dir/.env")
fi

unset -f ha_env_parse_value

if [ -z "${HASS_SERVER:-}" ]; then
    echo "Error: HASS_SERVER is not set. Copy $ha_skill_dir/.env.template to $ha_skill_dir/.env." >&2
    return 1
fi

if [ -z "${HASS_TOKEN:-}" ]; then
    echo "Error: HASS_TOKEN is not set. Create a Home Assistant long-lived access token." >&2
    return 1
fi

export HASS_SERVER HASS_TOKEN
export HASS_CLI_BIN="${HASS_CLI_BIN:-hass-cli}"
export HA_PYTHON="${HA_PYTHON:-python3}"
export HA_COMMAND_TIMEOUT="${HA_COMMAND_TIMEOUT:-30}"
