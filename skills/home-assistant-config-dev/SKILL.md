---
name: home-assistant-config-dev
description: Safely develop, debug, validate, test, roll back, and document Home Assistant configuration changes. Use for automations, scripts, packages, helpers, Assist pipelines, calendar-trigger behavior, traces, config API objects, live-first mutation, curated pull-back, or recovery planning; use hass-cli instead for routine household control and reporting.
---

# Home Assistant configuration development

Treat Home Assistant configuration work as a reversible live-system change, not
as ordinary text editing. Prefer supported APIs, exact evidence, boring rollback,
and production-path tests.

This skill complements `hass-cli`. Use that skill for entity discovery, state,
areas, safe household control, and deterministic local intents. Do not enlarge
this skill into a general home-control interface.

## Establish the boundary

Before mutation:

1. Read the target repository's agent, planning, task, and snapshot documents.
2. Require a clean worktree and inspect the curated pull preview when the repo
   uses one.
3. Classify the object as YAML-backed, storage-backed, runtime-only, or external.
   Read [persistence-boundaries.md](references/persistence-boundaries.md).
4. Name the inverse operation and external cleanup before changing anything.
5. Identify the exact objects and files expected to change.
6. Stop if the supported interface cannot capture and restore the original.

Never edit `.storage` generically. Never paste tokens into chat or commands.
Never treat Git as disaster recovery when the repository is only a projection.

## Use current diagnostic tools

Paths below are relative to this skill directory. The wrappers use exported
`HASS_SERVER` and `HASS_TOKEN`; when absent, they reuse the sibling `hass-cli`
environment loader without copying credentials.

| Need                                                   | Command                                       |
|--------------------------------------------------------|-----------------------------------------------|
| Query calendar events with a required service response | `scripts/ha-calendar-events ENTITY START END` |
| List recent automation or script traces                | `scripts/ha-trace list DOMAIN ITEM_ID`        |
| Inspect one compact detailed trace                     | `scripts/ha-trace get DOMAIN ITEM_ID RUN_ID`  |
| Exercise the selected production Assist pipeline       | `scripts/ha-assist-run --execute "PHRASE"`    |

All output is bounded JSON. Exit codes are `0` for success, `2` for invalid or
rejected work, and `3` for authentication, transport, dependency, timeout, or
protocol failures.

`ha-assist-run` requires `--execute` because text processing may perform real
Home Assistant actions. Inspect `pipeline`, `engine`, `processed_locally`,
`response_type`, and `events`; do not infer production routing from a direct
conversation-agent call.

`ha-calendar-events` is deliberately limited to the read-like
`calendar.get_events` action. Use exact ISO start/end values and an exact
`calendar.*` entity. Descriptions are omitted unless explicitly requested.

Trace output excludes raw config and detailed step payloads by default. Use it
to establish run identity, completion, last step, errors, and executed path—not
to dump unbounded integration data into context.

Repeat the opt-in metadata-only live checks with:

```bash
HA_DEV_LIVE_SMOKE=1 \
HA_DEV_SMOKE_CALENDAR=calendar.example \
HA_DEV_SMOKE_TRACE_DOMAIN=automation \
HA_DEV_SMOKE_TRACE_ITEM_ID=example \
tests/live_smoke.sh
```

Add `HA_DEV_SMOKE_ASSIST=1` only when a production-pipeline query is authorized.
The default phrase is “What time is it?”; override it with
`HA_DEV_SMOKE_ASSIST_PHRASE` only after reviewing its possible actions.

## Follow the live-first workflow

For authorized YAML-backed automation or script changes:

1. **Baseline:** verify expected live/repository drift and record current states.
2. **Capture:** save exact API objects and complete relevant files under a
   durable rollback ID with private permissions.
3. **Deactivate:** turn off affected behavior when practical.
4. **Install:** use the supported config-object API; install scripts before
   automations that depend on them.
5. **Check:** keep affected behavior off and run target-side `ha core check`.
6. **Compare:** fetch installed objects and compare normalized JSON exactly.
7. **Activate:** reload only required domains, then explicitly enable behavior.
8. **Test actions:** exercise action sequences independently where possible.
9. **Test triggers:** use the actual production path and inspect traces.
10. **Verify effects:** inspect external state and clean conspicuous test data.
11. **Pull back:** preview the curated rsync, require only expected paths, apply,
    parse/lint, and review the full diff.
12. **Document:** update durable decisions, validation evidence, pending tests,
    limitations, and rollback identity.

Read [validation-matrix.md](references/validation-matrix.md) before claiming a
change is validated. Syntax, action, trigger, collision, cancellation, and
recovery are different evidence layers.

## Preserve rollback discipline

The config APIs can write live files or reload an individual object before a
whole-system check. Deactivation and capture reduce that risk; they do not make
the change atomic.

A config-transaction wrapper is intentionally not implemented yet. Until its
rollback paths have fault-injection tests, manual mutation remains exceptional:
show the exact object set, rollback location, and activation boundary before
proceeding. Never reconstruct rollback commands from memory after failure.

Use [artifact-schema.md](references/artifact-schema.md) when capturing mutation
evidence. Keep installation, check, activation, restart, and acceptance as
separate states. Restart always requires explicit authorization.

## Respect Git ownership

Pulling accepted live configuration into a working tree does not grant
permission to stage, commit, amend, or push. Inspect and validate the diff, then
leave history to the human unless separately authorized.

## Current limitations

- Configuration transaction and rollback wrappers remain future work.
- Storage-backed object support is not generic and must be designed per API.
- Live Assist tests can incur LLM cost or real side effects.
- Calendar and integration polling can make successful API writes temporally
  invisible to triggers; test platform timing rather than assuming immediacy.
- An HA outage can preserve an external record while still missing an HA action.
