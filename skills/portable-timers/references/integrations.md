# Timer integrations

Keep the timer responsible only for scheduling. Put messaging, remote calls, and
agent startup in small executable wrappers that can be tested independently.

## Wrapper contract

A reliable finish command should:

- run noninteractively with a minimal environment
- use absolute paths or define its own safe `PATH`
- read secrets from a protected configuration source
- set network timeouts
- log enough information to distinguish invocation from downstream delivery
- return nonzero when the requested effect fails
- be safe to retry when used with persistent timers

Schedule the wrapper only after running it directly and checking its external
effect.

## Gotify-style notification

Example `~/.local/bin/send-timer-message`:

```bash
#!/bin/sh
set -eu

. "$HOME/.config/portable-timers/gotify.env"

title=${1:?title required}
message=${2:?message required}

exec /usr/bin/curl \
  --fail-with-body \
  --connect-timeout 5 \
  --max-time 20 \
  --form-string "title=$title" \
  --form-string "message=$message" \
  --form-string "priority=5" \
  "$GOTIFY_URL/message?token=$GOTIFY_TOKEN"
```

Protect the configuration file with mode `0600`. Schedule it without a shell:

```bash
systemd-run --user \
  --unit=laundry-reminder \
  --on-active=45m \
  --collect \
  -- "$HOME/.local/bin/send-timer-message" \
  "Laundry" "Move the laundry to the dryer"
```

An accepted HTTP response confirms the messaging server accepted the request, not
that a particular client displayed it. Verify the relevant delivery stage.

## Waking an agent

Do not embed a long prompt, tool policy, or skill text in `systemd-run`. Store a
reviewed prompt in a file and invoke a stable wrapper, for example:

```bash
systemd-run --user \
  --unit=weekly-research-agent \
  --on-calendar="2026-08-17 09:00:00" \
  --collect \
  -- "$HOME/.local/bin/run-reviewed-agent" \
  "$HOME/.config/agent-prompts/weekly-research.md"
```

The wrapper should select the installed agent command, such as OpenCode or Pi,
and provide its noninteractive flags, model, skills, tools, working directory,
and output destination explicitly. Agent CLIs evolve; inspect the local tool's
`--help` instead of copying flags into this general skill.

Recommended wrapper behavior:

1. Validate that the prompt file and working directory exist.
2. Use a fixed allowlist of permitted skills and tools.
3. Set a bounded runtime with `TimeoutStartSec` in the service or `timeout` in the
   wrapper.
4. Write stdout and stderr to the journal or a deliberate artifact path.
5. Send completion or failure notification as a separate, observable step.
6. Prevent overlap when a previous agent run may still be active.

For a maintained recurring agent job, use a `.service` and `.timer` pair rather
than a large transient command. Put resource limits, environment, working
directory, and timeout policy in the service unit.

## Shell quoting

Prefer direct argument execution. If an integration truly needs shell syntax,
put it in a script and test with messages containing spaces, quotes, dollar signs,
newlines, and non-ASCII text. Never interpolate untrusted prompt or message text
into a shell command template.
