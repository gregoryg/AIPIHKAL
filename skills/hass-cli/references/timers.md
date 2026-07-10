# Timers: Home Assistant vs Wyoming Satellite

## Key distinction

There are two different timer systems that can look similar from the outside:

1. Home Assistant `timer.*` entities and services
2. Wyoming Satellite local timers exposed through `HassTimer*` tools in satellite-originated assistant sessions

Do not assume these are interchangeable.

## Home Assistant timers

These are normal HA entities and can be controlled with raw `hass-cli` service calls:

```bash
hass-cli service call timer.start --arguments entity_id=timer.reminder_timer,duration="00:00:30"
hass-cli -o json state get timer.reminder_timer
```

Observed behavior:
- `hass-cli service call timer.start ...` may return `[]` or a rendered state blob
- `[]` is not necessarily failure; verify by reading the timer state afterward
- timers are only available if actual `timer.*` entities exist in HA

In the user's setup, there is a real HA timer entity:
- `timer.reminder_timer` (`Voice Reminder Timer`)

## Wyoming Satellite timers

The very nice room/device-local timer behavior from satellites is not reproduced by raw HA timer calls alone.

Observed architecture:
- Wyoming Satellite sessions have `HassTimer*` tools
- those tools start/manage timers local to the originating satellite
- Wyoming Satellite has timer start/finish hooks for local behavior like sounds, `notify-send`, and speech
- Web UI / laptop-originated sessions do not have `HassTimer*` tools

Practical implication:
- `hass-cli` can manage HA timer entities
- `hass-cli` cannot by itself recreate satellite-local timer UX (e.g. beeping on the originating puck or a local RPi screen workflow)

## Adjacent portable-Hermes timer lesson

In this environment, portable Hermes timers may be used alongside Home Assistant, but they have their own finish-action failure modes.

Observed pitfall:
- a remote desktop notification over SSH failed when the finish action used a bare remote command like:
  `ssh -i ~/.ssh/kitchenpi-from-hermes gregj@kitchenpi notify-send {label} {message}`

Working pattern:
- wrap the remote side as one quoted command string:
  `ssh -i ~/.ssh/kitchenpi-from-hermes gregj@kitchenpi "notify-send {label} {message}"`
- if placeholders are interpolated by a timer adapter, shell-quote the expanded values before substitution

Also keep delivery stages conceptually separate:
1. remote notify succeeded
2. outbox/event-log write succeeded
3. Slack delivery succeeded

A timer run can succeed at one stage and fail at another. Do not call the whole chain "working" unless each sink was verified.

## Guidance

Use raw `hass-cli` for HA timers when you want:
- globally visible HA timer state
- HA automations triggered from timer events
- timer control from any machine with HA access

Do not use raw `hass-cli` when the user specifically wants Wyoming Satellite local timer behavior. That requires the satellite-side `HassTimer*` path or a separate portable timer system.
