---
name: portable-timers
description: >-
  Set up reliable Linux timers and scheduled jobs with systemd-run, user systemd
  timer units, or cron. Use for one-shot delays, calendar deadlines, recurring
  user jobs, timer inspection and cancellation, notifications, webhooks, or
  scheduled noninteractive agent invocations.
---

# Portable Linux timers

Schedule commands with the operating system. Do not build a parallel timer
database or long-running scheduler unless the user explicitly needs one.

Default to the user's service manager:

```bash
systemd-run --user ...
systemctl --user ...
```

Use system-wide units only when the task genuinely requires root privileges or
must run independently of any user account.

## Choose the scheduler

| Need | Use |
|---|---|
| Run once after a delay | `systemd-run --user --on-active=` |
| Run once at a date/time | `systemd-run --user --on-calendar=` |
| Recurring job with logs and lifecycle control | user `.service` + `.timer` |
| Catch up after downtime | persistent user `.timer` |
| Simple minute-or-coarser recurrence without user systemd | user crontab |

Do not use cron for short relative timers or one-shot reminders. Do not use a
transient timer when the schedule must survive reboot; install user unit files.

## Preflight

Check the user manager before scheduling:

```bash
systemctl --user is-system-running
systemd-run --user --on-active=5s --unit=timer-smoke-test \
  --collect -- /usr/bin/true
systemctl --user status timer-smoke-test.timer
```

If the user manager must continue after logout, inspect lingering:

```bash
loginctl show-user "$USER" -p Linger
```

Enabling linger is a host policy decision and may require an administrator.

## One-shot timer

Use a descriptive, unique unit name and an absolute executable path:

```bash
systemd-run --user \
  --unit=tea-reminder \
  --description="Tea reminder" \
  --on-active=5m \
  --collect \
  -- /usr/bin/notify-send "Timer" "Tea is ready"
```

For a wall-clock deadline:

```bash
systemd-run --user \
  --unit=report-reminder \
  --on-calendar="2026-08-15 09:30:00" \
  --collect \
  -- /home/user/.local/bin/send-report-reminder
```

Quote calendar expressions for the shell. Treat generated unit names as machine
identifiers: use lowercase ASCII letters, digits, dashes, and a task-specific
suffix when concurrent timers are possible.

## Inspect, cancel, and debug

```bash
systemctl --user list-timers --all
systemctl --user status tea-reminder.timer
systemctl --user status tea-reminder.service
journalctl --user-unit=tea-reminder.service
systemctl --user stop tea-reminder.timer
```

The timer activates the corresponding service. Inspect both units before
declaring failure. Stopping the `.timer` prevents a pending activation; stop the
`.service` separately if it is already running.

## Reliability rules

- Use absolute executable and file paths; user services have a smaller,
  noninteractive environment than a login shell.
- Put multi-step behavior in a tested executable script, not a deeply nested
  `/bin/sh -c` string.
- Pass prompts or long messages in files when quoting could alter their contents.
- Keep secrets in permission-restricted environment or credential files, never in
  unit names, command lines, prompts, or unit files committed to Git.
- Make finish commands idempotent when retries or catch-up execution are possible.
- Give network clients explicit connection and total timeouts.
- Verify the downstream effect independently from successful timer activation.
- Avoid overlapping recurring runs with service design or `flock` where needed.

## Persistent and recurring timers

For schedules that must survive reboot, recur, or be maintained over time, create
paired unit files under `~/.config/systemd/user/`. Read
`references/systemd-user-units.md` for templates, `Persistent=true`, environment
handling, installation, and cleanup.

## Notifications and agent wakeups

A timer should invoke one stable command. That command may send a Gotify-style
message, call another local subsystem, or start a noninteractive agent such as
OpenCode or Pi with a reviewed prompt and tool configuration.

Keep those integrations outside the timer definition and test them before
scheduling. Read `references/integrations.md` for safe wrapper patterns, logging,
prompt files, and delivery verification.

## Cron fallback

Use cron only when user systemd is unavailable or the job is naturally expressed
as a simple recurring crontab entry. Read `references/cron.md` before installing
or replacing a crontab.
