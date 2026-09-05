# Validation matrix

Do not collapse “valid” into one bit. Record which layers were actually tested.

| Layer | Question | Typical evidence |
|---|---|---|
| Persistence | Where will this object be written? | API GET, file path, bounded export |
| Syntax/schema | Can HA parse the installed configuration? | API acceptance, YAML parse, `ha core check` |
| Installation | Does the installed object equal the candidate? | Normalized exact comparison and hashes |
| Activation | Is the intended entity loaded and enabled? | State, attributes, selective reload result |
| Action | Does the action sequence work independently? | Script call and completed trace |
| Assist exposure | Are required tools exposed and stale or conflicting entities excluded? | Entity-registry conversation options, tool schema, negative allowlist audit |
| Trigger | Does the production trigger route correctly? | Actual Assist/calendar/state path and trace |
| Parallelism | Do independent events avoid overwrite or suppression? | Simultaneous test runs and distinct traces |
| Cancellation | Does removing the source prevent action? | Deleted event/object plus absence of trace |
| Recovery | What happens across reload, restart, or outage? | Controlled restart/outage test and post-state |
| External effects | Were test artifacts observed and cleaned? | IDs, calendar query, notification confirmation |
| Pull-back | Did only expected repository files change? | rsync preview, expected-path list, reviewed diff |

## Assist routing

`conversation.home_assistant` tests deterministic built-in NLU. It is not the
same as the selected Assist pipeline. Use `ha-assist-run --execute` when the
production pipeline itself is under test, and inspect `engine` plus
`processed_locally` in its output.

An Assist phrase can perform actions. The explicit flag acknowledges that risk;
it does not make arbitrary text safe.

Entity exposure is storage-backed configuration, not an incidental UI setting.
For an Assist-facing change, inspect both required and forbidden entities'
`conversation.should_expose` options. Test wording outside deterministic local
sentence patterns and correlate the response with the expected script or
automation trace; otherwise a correct answer may have exercised the wrong route.

## Time-dependent behavior

For delayed triggers, distinguish target calculation from eventual trigger
execution. Inspecting a future calendar timestamp proves calculation only.
Leave the task in test until the long-running trigger is observed or explicitly
accepted as pending.

Test boundary timing, duplicate windows, simultaneous events, deletion, restart,
and integration polling behavior where they matter. Document platform polling
or caching behavior in user-facing documentation when it changes expectations.

## Configuration check boundary

`ha core check` validates live files after installation. It does not make the
preceding config API save atomic, prove an external service call, or validate an
arbitrary candidate that has not been installed. Deactivate and capture rollback
before installation, then keep activation separate.
