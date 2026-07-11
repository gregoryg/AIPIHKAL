# Helper-backed schedules

For an automation that runs at a user-selected future time, prefer an
`input_datetime` helper over editing the automation definition.

This exposes the schedule as ordinary Home Assistant state and lets an agent
inspect or change it without mutating YAML or automation internals.

```bash
hass-cli service call input_datetime.set_datetime \
  --arguments entity_id=input_datetime.reminder_time,datetime="2026-08-15 09:30:00"
hass-cli service call automation.turn_on \
  --arguments entity_id=automation.scheduled_reminder
```

Treat the automation and helper as one conceptual schedule:

```json
{
  "automation_entity_id": "automation.scheduled_reminder",
  "enabled": true,
  "schedule_entity_id": "input_datetime.reminder_time",
  "scheduled_for": "2026-08-15 09:30:00"
}
```

Before changing either entity, discover and confirm the exact pairing. Home
Assistant does not guarantee that similarly named helpers and automations are
related.
