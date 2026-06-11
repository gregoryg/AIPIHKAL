#!/bin/bash
# Shared Home Assistant wrapper bootstrap.

ha_env_script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ha_skill_dir=$(cd "$ha_env_script_dir/.." && pwd)

# The wrapper scripts all reference $repo_root/skills/hass-cli/scripts/<file>
# Original layout: repo_root/skills/hass-cli/  (flat)
# Current layout:   repo_root/skills/smart-home/hass-cli/  (categorized)
# Compute repo_root so the existing $repo_root/skills/hass-cli/scripts/ path works.
skills_root=$(cd "$ha_env_script_dir/../../.." && pwd)  # ~/.hermes/skills
export repo_root="$skills_root/smart-home"

# Load credentials: prefer .env in the skill dir, fall back to legacy secrets.sh
if [ -f "$ha_skill_dir/.env" ]; then
  # shellcheck source=/dev/null
  source "$ha_skill_dir/.env"
elif [ -f "$skills_root/common/secrets.sh" ]; then
  # shellcheck source=/dev/null
  source "$skills_root/common/secrets.sh"
  load_hass_token
fi

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
