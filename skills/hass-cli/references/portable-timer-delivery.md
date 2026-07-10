# Portable Hermes timer delivery notes

This reference exists because timer work in this Home Assistant environment often straddles three systems:
- HA `timer.*` entities
- Wyoming Satellite timers
- portable Hermes timers

## SSH remote notification pitfall

A portable Hermes timer finish action attempted:

```bash
ssh -i ~/.ssh/kitchenpi-from-hermes gregj@kitchenpi notify-send {label} {message}
```

That is brittle because SSH does not receive one coherent remote command string once placeholders expand into multi-word text.

Use:

```bash
ssh -i ~/.ssh/kitchenpi-from-hermes gregj@kitchenpi "notify-send {label} {message}"
```

If a timer adapter performs placeholder interpolation, shell-quote the values before insertion.

## Delivery pipeline distinction

Treat these as separate outcomes:
1. remote device notification
2. local event/outbox write
3. Slack delivery

Observed session result:
- remote kitchen notification worked after SSH command quoting was corrected
- outbox creation already worked
- Slack still required a separate sender/consumer

## Operational rule

Do not describe a timer notification pipeline as "working" unless you verify each sink independently.
Outbox success is evidence of intent recording, not evidence of user-visible delivery.
