# Delegation failure modes

Use this reference when a delegated call stalls, exits without a final answer,
loses output, or behaves outside its intended boundary.

## Contents

- [Deadline layering](#deadline-layering)
- [Termination and orphan processes](#termination-and-orphan-processes)
- [Persistence and missing final output](#persistence-and-missing-final-output)
- [Prompt and context failures](#prompt-and-context-failures)
- [Model and provider failures](#model-and-provider-failures)
- [Fan-out failures](#fan-out-failures)
- [Recovery checklist](#recovery-checklist)

## Deadline layering

A process may have three independent time limits:

1. provider request timeout;
2. delegated harness/process deadline;
3. parent shell-tool or interactive-turn deadline.

If the parent deadline is shortest, it can kill the launcher before artifacts
or the final response are written. Set the parent deadline to at least:

```text
child deadline + forced-kill grace + artifact/synthesis grace
```

For parallel work, use the longest child deadline rather than summing all child
deadlines, then add aggregation time. For chained work, sum step deadlines and
add handoff/aggregation time.

Never omit a child deadline because the parent has one. Parent cancellation can
be abrupt and may not clean descendants or flush session metadata.

## Termination and orphan processes

GNU `timeout` sends `TERM` at the deadline. A process may ignore it. Always add
`--kill-after` so `KILL` follows after a short grace period.

After an abnormal exit:

```bash
pgrep -af 'pi|codex|opencode|claude|hermes|gemini'
```

Interpret this carefully on a multi-agent machine; compare PID/start time/run
metadata rather than killing every matching process. Never use a broad
`pkill -f` as cleanup.

For long observable work, prefer tmux or a service supervisor. Do not use
`command &` from an LLM tool and hope a later context remembers the PID.

## Persistence and missing final output

A final-output file may be empty because the harness writes it only after the
last model turn. Inspect in this order:

1. `status` / `result.json`;
2. stderr;
3. stdout or structured events;
4. recorded session ID;
5. running process tree.

If the session exists, resume with a narrower prompt such as:

```text
The previous run reached its process deadline after completing repository
inspection. Do not inspect more files. Return the requested findings now.
```

Do not restart from scratch unless the session is corrupt, sensitive, or used
the wrong task boundary.

## Prompt and context failures

Common causes:

- prompt exposed or truncated in argv;
- shell quoting or command-substitution damage;
- prompt exceeds `ARG_MAX`;
- child lacks parent conversation facts;
- child unexpectedly loads project instructions, skills, or extensions;
- child receives too much raw repository/API content;
- recursive delegation expands work without bound.

Use a prompt file and stdin where supported. Include explicit cwd, evidence
scope, tool policy, output shape, and stopping condition. Pass compact facts,
not the parent's entire transcript. Disable project context only deliberately;
it may contain safety and Git-ownership rules.

## Model and provider failures

Distinguish:

- stale/renamed model identifier;
- missing or expired authentication;
- quota/rate limit;
- provider request timeout;
- harness process timeout;
- malformed stream/response;
- model refusal or context overflow.

Run the harness's model-list/auth diagnostic before a large fan-out. Do not
silently substitute another model when diversity or conformance matters. Record
any fallback in the result.

Retries must be bounded. Retry transient transport/rate failures with jitter and
`Retry-After`; do not retry authentication, invalid model, or deterministic
schema errors blindly.

## Fan-out failures

Treat each child independently. Preserve successes when another child fails.
Report:

- requested/completed/failed/timed-out counts;
- model and lens for each child;
- exit status and session ID;
- whether output is final or partial;
- whether synthesis excluded a failed seat.

Limit concurrency to avoid self-inflicted rate limiting. Multiple calls to one
model measure consistency, not diversity. Peer review is useful only when the
initial outputs materially disagree.

## Recovery checklist

1. Stop launching more work.
2. Inspect run metadata and exact status.
3. Confirm whether the child still exists.
4. Preserve stdout, stderr, events, and partial final output.
5. Locate the persisted session ID.
6. Decide resume, retry, model substitution, or accept partial result.
7. Narrow the follow-up prompt and set a new bounded deadline.
8. Verify consequential child claims before acting.
9. Summarize only needed findings into the parent context.
