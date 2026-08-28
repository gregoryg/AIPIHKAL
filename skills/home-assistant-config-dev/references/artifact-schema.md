# Development artifact schema

Mutation tooling is not implemented yet. When it is, each run should create a
private directory under `${XDG_STATE_HOME:-~/.local/state}/ha-config-dev/` using
a sortable ID such as `20260828T151123Z-voice-reminders`.

## Required manifest fields

```json
{
  "schema_version": 1,
  "change_id": "20260828T151123Z-voice-reminders",
  "created_at": "2026-08-28T15:11:23Z",
  "server_identity": "redacted stable label",
  "persistence_class": "yaml",
  "object_refs": ["automation/voice_reminder_create"],
  "expected_paths": ["automations.yaml"],
  "external_effects": ["calendar events", "audible announcements"],
  "state": "captured"
}
```

Do not store the bearer token, authorization headers, config-entry secrets, or
raw credential-bearing objects.

## State progression

Use explicit states rather than one success flag:

```text
planned -> captured -> deactivated -> installed -> checked -> compared
        -> activated -> tested -> accepted -> pulled
```

Failure records the failed state and rollback status. Restart is a separate,
explicit transition and is never implied by activation.

## Files

A transaction directory should eventually contain:

- `manifest.json` — bounded state and expected changes;
- `objects/original/` — exact supported API objects before mutation;
- `objects/candidate/` — validated proposed API objects;
- `objects/installed/` — objects fetched after installation;
- `files/` — protected complete-file rollback copies when applicable;
- `hashes.json` — before/after hashes for expected paths;
- `checks/` — bounded config-check and smoke-test results; and
- `rollback.json` — attempted steps, results, and residual uncertainty.

Use mode `0700` for directories and `0600` for artifacts unless a stricter
platform mechanism is available.

## Retention

Keep artifacts through behavioral acceptance and repository pull-back. Define a
human-owned cleanup policy before automatic deletion. Never delete the only
rollback material while delayed trigger or recovery tests remain pending.
