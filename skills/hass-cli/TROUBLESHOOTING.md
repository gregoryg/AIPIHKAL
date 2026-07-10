
### Power-topology pitfall: smart switch upstream, smart light downstream

Some Home Assistant installs contain the deeply unserious topology where a **smart switch cuts power to a smart light**.

What this means operationally:
- when the upstream switch is off, the downstream smart light can disappear from HA entirely or show `unavailable`
- after turning the switch on, the light entity may take a couple of seconds to rejoin and report state
- a follow-up status check run too quickly can make it look like the switch command failed when in fact the light is just booting back into existence

How to handle it:
1. If a room contains both `switch.*` and `light.*` entities and one light is `unavailable`, consider whether the switch may be upstream power rather than an independent load.
2. Turn on the upstream switch first.
3. Wait briefly, then re-check the light entity before declaring failure.
4. Prefer controlling the true upstream device for reliability; the downstream smart light is only controllable when powered.

This is especially important when a user reports that "the switch did turn on" while your immediate post-check still shows the light unavailable. Believe topology before inventing ghosts.

### Raw hass-cli pitfall: auto-discovery can hit the wrong HA server

If you call raw `hass-cli` directly without loading the environment first, it may try local-network auto-discovery and connect to the wrong Home Assistant server.

Symptoms:
- `Trying to locate Home Assistant on local network...`
- `Found and using http://... as server`
- service calls fail even though the wrappers work

Preferred fixes:
- use the wrapper scripts in this skill first; they source `ha-env.sh` for you
- if you must use raw `hass-cli`, source `scripts/ha-env.sh` first or pass explicit server/token config

Do not treat wrapper success + raw CLI failure as an HA outage until you've ruled out bad auto-discovery.
