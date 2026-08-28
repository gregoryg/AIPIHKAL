#!/usr/bin/env bash
# Shared bootstrap for Home Assistant configuration-development wrappers.
# This file is sourced, not executed.

ha_dev_script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
ha_dev_skill_dir=$(cd -- "$ha_dev_script_dir/.." && pwd -P)

if [[ -z ${HASS_SERVER:-} || -z ${HASS_TOKEN:-} ]]; then
    hass_cli_env="$ha_dev_skill_dir/../hass-cli/scripts/ha-env.sh"
    if [[ ! -r $hass_cli_env ]]; then
        printf '%s\n' \
            'Error: export HASS_SERVER and HASS_TOKEN or install the sibling hass-cli skill.' >&2
        return 1
    fi
    # shellcheck source=../../hass-cli/scripts/ha-env.sh
    source "$hass_cli_env"
fi

if [[ -z ${HASS_SERVER:-} || -z ${HASS_TOKEN:-} ]]; then
    printf '%s\n' 'Error: HASS_SERVER and HASS_TOKEN are required.' >&2
    return 1
fi

export HASS_SERVER HASS_TOKEN
export HA_PYTHON="${HA_PYTHON:-python3}"
export HA_COMMAND_TIMEOUT="${HA_COMMAND_TIMEOUT:-30}"
