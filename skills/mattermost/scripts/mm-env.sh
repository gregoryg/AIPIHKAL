#!/bin/bash
# Shared Mattermost bootstrap. This file is sourced, not executed.
#
# Selects an agent identity and loads its bot token from
# ${MM_CONFIG_DIR:-~/.config/mattermost/agents}/<identity>.env.
# Identity: MM_AGENT_IDENTITY, normally set by the caller's --as option.

MM_CONFIG_DIR="${MM_CONFIG_DIR:-$HOME/.config/mattermost/agents}"

if [ -z "${MM_AGENT_IDENTITY:-}" ]; then
    echo "Error: no identity. Pass --as <identity> or set MM_AGENT_IDENTITY." >&2
    return 1
fi
case "$MM_AGENT_IDENTITY" in
    *[!A-Za-z0-9._-]*)
        echo "Error: invalid identity name: $MM_AGENT_IDENTITY" >&2
        return 1
        ;;
esac

mm_env_file="$MM_CONFIG_DIR/$MM_AGENT_IDENTITY.env"
if [ ! -f "$mm_env_file" ]; then
    echo "Error: no token file for identity '$MM_AGENT_IDENTITY' at $mm_env_file." >&2
    return 1
fi
if [ -n "$(find "$mm_env_file" -perm /077 2>/dev/null)" ]; then
    echo "Warning: $mm_env_file is readable by others; run chmod 600 on it." >&2
fi

# Read only known keys; never source the token file as shell code.
while IFS='=' read -r key value; do
    value=${value%$'\r'}
    value=${value#\"}; value=${value%\"}
    value=${value#\'}; value=${value%\'}
    case "$key" in
        # Always from the file, so one shell never mixes identities
        MM_URL|MM_TOKEN)
            export "$key=$value"
            ;;
        # Defaults; the caller's environment wins
        MM_TEAM|MM_AGENT_ENGINE)
            if [ -z "${!key:-}" ]; then
                export "$key=$value"
            fi
            ;;
    esac
done < <(sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$mm_env_file")
unset mm_env_file

if [ -z "${MM_URL:-}" ] || [ -z "${MM_TOKEN:-}" ]; then
    echo "Error: MM_URL and MM_TOKEN must be set in the identity's token file." >&2
    return 1
fi
MM_URL=${MM_URL%/}

# mm_api METHOD PATH [JSON-BODY]: print the response body; fail on HTTP >= 400.
mm_api() {
    local method=$1 path=$2 body=${3:-} out code
    local args=(-sS -X "$method" -H "Authorization: Bearer $MM_TOKEN"
                -w '\n%{http_code}' --max-time "${MM_TIMEOUT:-20}")
    [ -n "$body" ] && args+=(-H 'Content-Type: application/json' --data-binary "$body")
    out=$(curl "${args[@]}" "$MM_URL/api/v4$path") || return 1
    code=${out##*$'\n'}
    out=${out%$'\n'*}
    if [ "$code" -ge 400 ]; then
        printf 'Error: %s %s -> HTTP %s: %s\n' "$method" "$path" "$code" \
               "$(jq -r '.message // empty' <<<"$out" 2>/dev/null)" >&2
        return 1
    fi
    printf '%s' "$out"
}

# mm_team_id: MM_TEAM (name) if set, else the bot's only team.
mm_team_id() {
    local teams
    teams=$(mm_api GET /users/me/teams) || return 1
    if [ -n "${MM_TEAM:-}" ]; then
        jq -er --arg t "$MM_TEAM" '.[] | select(.name == $t) | .id' <<<"$teams" ||
            { echo "Error: bot is not on team '$MM_TEAM'." >&2; return 1; }
    elif [ "$(jq length <<<"$teams")" -eq 1 ]; then
        jq -r '.[0].id' <<<"$teams"
    else
        echo "Error: bot is on $(jq length <<<"$teams") teams; set MM_TEAM in its token file." >&2
        return 1
    fi
}

# mm_channel_id NAME: a channel name in the team, or @username for a DM.
mm_channel_id() {
    local name=${1#\~} me user team
    if [[ "$name" == @* ]]; then
        me=$(mm_api GET /users/me | jq -r .id) || return 1
        user=$(mm_api GET "/users/username/${name#@}" | jq -r .id) || return 1
        mm_api POST /channels/direct "$(jq -nc --arg a "$me" --arg b "$user" '[$a,$b]')" | jq -r .id
    else
        team=$(mm_team_id) || return 1
        mm_api GET "/teams/$team/channels/name/$name" | jq -r .id ||
            { echo "Error: channel '$name' not found or the bot is not a member (/invite it)." >&2; return 1; }
    fi
}
