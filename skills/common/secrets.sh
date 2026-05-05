#!/bin/bash

# skills/common/secrets.sh
# Common utility functions for Home Assistant wrapper configuration.

secrets_script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
secrets_repo_root=$(cd "$secrets_script_dir/../.." && pwd)

# Function to extract password from ~/.authinfo.gpg
# Usage: get_authinfo_password <machine_name>
get_authinfo_password() {
    local machine_name="$1"
    if [ -z "$machine_name" ]; then
        echo "Usage: get_authinfo_password <machine_name>" >&2
        return 1
    fi

    if ! command -v gpg >/dev/null 2>&1 || [ ! -f "$HOME/.authinfo.gpg" ]; then
        return 1
    fi

    gpg --decrypt "$HOME/.authinfo.gpg" 2>/dev/null | \
    grep "machine $machine_name" | \
    awk '{for(i=1;i<=NF;i++) if($i=="password") print $(i+1)}'
}

load_env_file() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        set -a
        # shellcheck source=/dev/null
        source "$env_file"
        set +a
        return 0
    fi
    return 1
}

load_hass_env() {
    if [ -n "${HASS_ENV_LOADED:-}" ]; then
        return 0
    fi

    local candidates=(
        "$secrets_repo_root/skills/hass-cli/.env"
        "$secrets_repo_root/.env"
        ".env"
    )
    local env_file
    for env_file in "${candidates[@]}"; do
        if load_env_file "$env_file"; then
            export HASS_ENV_LOADED="$env_file"
            return 0
        fi
    done
    return 1
}

# Load Home Assistant config, preferring .env and falling back to authinfo.gpg.
load_hass_token() {
    if [ -n "${HASS_TOKEN:-}" ] && [ -n "${HASS_SERVER:-}" ]; then
        return 0
    fi

    load_hass_env || true

    if [ -n "${HASS_TOKEN:-}" ] && [ -n "${HASS_SERVER:-}" ]; then
        return 0
    fi

    local machine_name="ha-mcp-token"
    local token
    token=$(get_authinfo_password "$machine_name")

    if [ -n "$token" ]; then
        export HASS_TOKEN="$token"
    fi
}
