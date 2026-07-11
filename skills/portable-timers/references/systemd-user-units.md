# Persistent user systemd timers

Use paired user units when a schedule must survive reboot, recur, catch up after
downtime, or remain under configuration management.

## Service unit

Create `~/.config/systemd/user/daily-summary.service`:

```ini
[Unit]
Description=Generate and deliver the daily summary

[Service]
Type=oneshot
ExecStart=%h/.local/bin/deliver-daily-summary
EnvironmentFile=-%h/.config/portable-timers/daily-summary.env
```

`ExecStart` is not interpreted by a shell. Put pipelines, redirection, conditional
logic, and multiple steps in the executable script. This also makes the payload
independently testable.

The leading `-` on `EnvironmentFile` makes a missing file nonfatal. Remove it when
configuration must be present. Protect files containing secrets:

```bash
chmod 600 ~/.config/portable-timers/daily-summary.env
```

## Timer unit

Create `~/.config/systemd/user/daily-summary.timer`:

```ini
[Unit]
Description=Run the daily summary each morning

[Timer]
OnCalendar=*-*-* 08:00:00
Persistent=true
RandomizedDelaySec=2m
Unit=daily-summary.service

[Install]
WantedBy=timers.target
```

`Persistent=true` runs a missed calendar activation after the user manager starts.
It does not replay every missed occurrence. Use it only when delayed execution is
safe and useful.

`RandomizedDelaySec` is appropriate for non-urgent network work. Omit it for a
deadline or alarm.

## Install and verify

```bash
systemctl --user daemon-reload
systemctl --user enable --now daily-summary.timer
systemctl --user list-timers --all
systemctl --user status daily-summary.timer
systemd-analyze calendar "*-*-* 08:00:00"
```

Test the service separately before trusting the schedule:

```bash
systemctl --user start daily-summary.service
systemctl --user status daily-summary.service
journalctl --user-unit=daily-summary.service -n 100
```

## Update or remove

After editing either unit:

```bash
systemctl --user daemon-reload
systemctl --user restart daily-summary.timer
```

To remove the schedule:

```bash
systemctl --user disable --now daily-summary.timer
rm ~/.config/systemd/user/daily-summary.timer
rm ~/.config/systemd/user/daily-summary.service
systemctl --user daemon-reload
systemctl --user reset-failed
```

Do not delete unit files before disabling the timer; retaining the unit definition
during shutdown makes the operation easier to inspect and recover.

## Login and boot behavior

User timers normally run while the user's systemd manager exists. On many desktop
systems that follows login sessions. For unattended jobs after logout or before
the next login, check:

```bash
loginctl show-user "$USER" -p Linger
```

An administrator or authorized user can enable lingering with `loginctl
enable-linger USER`. Confirm local policy before changing it.
