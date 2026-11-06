# Home Assistant persistence boundaries

Classify the object before proposing mutation. A supported API is not by itself
a rollback strategy.

## YAML-backed

Examples include automations and scripts stored in selected YAML files.

Before mutation:

- GET the exact config object through its supported API;
- hash the relevant live YAML file;
- copy the complete live file to a protected rollback directory;
- identify the repository path expected to change; and
- deactivate affected behavior when practical.

After mutation, compare the installed API object and live/repository file. Do
not infer serialization merely because the API returned success.

## Storage-backed

Integrations, UI-created helpers, entity exposure, dashboards, and other objects
may live in `.storage`. Never edit `.storage` generically.

Proceed only when a supported read/write interface and an exact inverse are
known. Capture a bounded semantic export or API object; do not commit `.storage`
wholesale. If the supported interface cannot restore the original state, stop.

Interfaces proven so far, with their inverses:

- Device name: `config/device_registry/update` with `name_by_user`. Restore
  the captured value; `null` returns to the integration's name.
- Entity name: `config/entity_registry/update` with `name`, restored the same
  way.
- Entity ID: `config/entity_registry/update` with `new_entity_id`; rename back
  to undo. The recorder moves history and statistics to the new ID unless the
  new ID already has some, such as an entity deleted with its integration. HA
  then logs `Cannot migrate history` and `Cannot rename statistic_id`, and the
  renamed entity carries on the existing history. Its own history stays under
  the old ID. That keeps an energy meter's statistics across an integration
  swap when the reading continues where it left off.
- Storage dashboard: read with `lovelace/config` and `url_path`, write the
  whole configuration with `lovelace/config/save`. Restore by saving the
  captured configuration.
- Assist exposure: `homeassistant/expose_entity` with `assistants`,
  `entity_ids`, and `should_expose`. Restore the captured value from
  `homeassistant/expose_entity/list`.
- Energy dashboard: `energy/save_prefs` replaces only the top-level keys sent,
  such as `device_consumption`. Restore by saving the captured keys.
- UI-created helpers: create through `/api/config/config_entries/flow` and
  delete the entry to undo. The Energy dashboard's power-to-energy step (HA
  2026.11) is an `integration` flow with `method: left`, `max_sub_interval` of
  five minutes, `round: 3`, and `device_class: energy`. The UI reuses any
  `integration` helper with the same source sensor and device class.
- Deleting a config entry has no API inverse; re-adding may need a fresh
  login. Capture only non-secret metadata, such as domain, title, and dates.
  The interface is REST `DELETE /api/config/config_entries/entry/ENTRY_ID`;
  there is no WebSocket command. An agent harness may refuse it, so be ready to
  ask the human to delete the integration in the UI.

To inspect a storage file on the host, filter it there with `jq` and print only
the keys needed, or an equality result; config entries hold tokens.

## Runtime-only

Entity state, active timers, media sessions, and transient service effects are
not configuration rollback artifacts. Record pre-state when useful, but do not
pretend it recreates lost runtime behavior.

Use state restoration only when the inverse is safe and meaningful. Never
blindly replay physical-device state after delay or failure.

## External side effects

Calendar events, notifications, webhooks, cloud API mutations, and messages may
outlive HA rollback. Name cleanup before testing, use conspicuous test markers,
and retain external IDs when the API exposes them.

A configuration rollback does not retract an announcement or delete an external
event automatically.

## Secrets and authentication

Do not put bearer tokens, config-entry data, secret YAML, raw `.storage`, or
credential-bearing URLs in artifacts, fixtures, command lines, logs, or chat.
Keep rollback directories private and define retention before accumulating them.

Treat unencrypted `HASS_SERVER=http://...` as transport over a trusted network,
not as secure bearer-token transport. Prefer private TLS or a protected tunnel
when the network boundary does not justify that trust.
