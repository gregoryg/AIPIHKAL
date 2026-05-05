#!/bin/bash
# Shared Home Assistant wrapper bootstrap.

ha_env_script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$ha_env_script_dir/../../.." && pwd)
export repo_root

# shellcheck source=/dev/null
source "$repo_root/skills/common/secrets.sh"
load_hass_token

if [ -z "${HASS_SERVER:-}" ]; then
    echo "Error: HASS_SERVER is not set. Copy skills/hass-cli/.env.template to skills/hass-cli/.env and fill it in." >&2
    return 1
fi

if [ -z "${HASS_TOKEN:-}" ]; then
    echo "Error: HASS_TOKEN is not set. Copy skills/hass-cli/.env.template to skills/hass-cli/.env and fill it in, or use your fancy-person gpg setup." >&2
    return 1
fi

export HASS_SERVER
export HASS_TOKEN
