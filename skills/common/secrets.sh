#!/bin/bash

# skills/common/secrets.sh
# Common utility functions for secret management.

# Function to extract password from ~/.authinfo.gpg
# Usage: get_authinfo_password <machine_name>
get_authinfo_password() {
    local machine_name="$1"
    if [ -z "$machine_name" ]; then
        echo "Usage: get_authinfo_password <machine_name>" >&2
        return 1
    fi

    # Try to decrypt and extract the password field following the machine name
    # We use a loop in awk to find "password" and print the next field, 
    # matching the specific machine line.
    gpg --decrypt ~/.authinfo.gpg 2>/dev/null | \
    grep "machine $machine_name" | \
    awk '{for(i=1;i<=NF;i++) if($i=="password") print $(i+1)}'
}

# Function to load HASS_TOKEN if not already set
load_hass_token() {
    if [ -n "$HASS_TOKEN" ]; then
        return 0
    fi

    # Default machine name for Home Assistant token in this environment
    local machine_name="ha-mcp-token"
    local token=$(get_authinfo_password "$machine_name")

    if [ -n "$token" ]; then
        export HASS_TOKEN="$token"
        # echo "HASS_TOKEN loaded from ~/.authinfo.gpg" >&2
    else
        # Fallback to .env if it exists and is secure
        if [ -f ".env" ]; then
            # Check permissions (must be 600)
            if [ "$(stat -c %a .env)" == "600" ]; then
                set -a
                source .env
                set +a
            fi
        fi
    fi
}
