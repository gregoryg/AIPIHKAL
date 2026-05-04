# Scheduling automations with variable date/time triggers

For automations that should run at a user-chosen future time, prefer using an `input_datetime` helper rather than editing the automation definition directly.

## Recommended pattern

- automation contains the action logic
- `input_datetime` contains the chosen schedule
- automation reads or triggers from that helper-backed datetime

This is preferable because:
- the chosen time becomes explicit Home Assistant state
- the schedule can be changed safely through service calls
- humans, LLMs, and wrapper scripts can inspect and modify scheduling without mutating automation internals
- it creates a cleaner control surface for future tooling

## Example

Automation:
- `automation.announce_yogurt`

Helper:
- `input_datetime.yogurt_trigger_time`

Set the schedule:

```bash
hass-cli service call input_datetime.set_datetime \
  --arguments entity_id=input_datetime.yogurt_trigger_time,datetime="2026-05-04 22:00:00"
```

Enable the automation if needed:

```bash
hass-cli service call automation.turn_on \
  --arguments entity_id=automation.announce_yogurt
```

## Important nuance

This pattern is slightly more obtuse in the Home Assistant UI because:
- the automation enable/disable state is one entity
- the chosen schedule is another entity

But for programmable control it is a major improvement, because the effective schedule becomes explicit, queryable, and safely editable.

## Guidance for future wrapper scripts

A future scheduling wrapper should ideally present both pieces as one conceptual unit, for example:

```json
{
  "label": "Announce YOGURT",
  "automation_entity_id": "automation.announce_yogurt",
  "enabled": true,
  "schedule_entity_id": "input_datetime.yogurt_trigger_time",
  "scheduled_for": "2026-05-04 22:00:00"
}
```

That would restore the unified mental model that Home Assistant itself does not present cleanly.
