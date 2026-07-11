# Cron fallback

Use the user's crontab when user systemd is unavailable or the schedule is a
simple minute-or-coarser recurrence that does not need systemd lifecycle control.

Cron is a poor fit for one-shot relative timers, second-level precision, rich
dependency ordering, or jobs that need reliable catch-up after downtime.

## Inspect before editing

```bash
crontab -l
```

Do not replace an existing crontab blindly. Preserve unrelated entries and edit
with `crontab -e`, or construct and review the complete replacement file first.

## Environment

Cron supplies a minimal environment. Define what the job needs and use absolute
paths:

```cron
SHELL=/bin/sh
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=""

15 8 * * 1-5 /home/user/.local/bin/deliver-daily-summary
```

Do not depend on shell startup files, desktop session variables, or an interactive
working directory. Redirect output deliberately when the host has no configured
cron mail delivery:

```cron
15 8 * * 1-5 /home/user/.local/bin/deliver-daily-summary >>/home/user/.local/state/daily-summary.log 2>&1
```

## Prevent overlap

Use `flock` when another run must not start before the previous one finishes:

```cron
*/10 * * * * /usr/bin/flock -n "$HOME/.local/state/report-job.lock" "$HOME/.local/bin/report-job"
```

Create the lock-file directory before installing the entry. For more complex lock
or cleanup behavior, place locking inside the wrapper.

## Limitations

- Cron implementations differ; verify extensions before relying on them.
- Jobs missed while the machine is off are normally lost.
- The shortest standard interval is one minute.
- Logs and exit status need explicit handling.
- Removing one entry requires editing the complete user crontab carefully.

If these limitations require workarounds, use a persistent user systemd timer
instead.
