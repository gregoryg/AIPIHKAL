# Home Assistant Service Reference

Detailed service call patterns for common Home Assistant domains.

**Important:** All service calls use `--arguments key=value,key2=value2` syntax.

## Light Services

**light.turn_on**
```bash
# Basic
hass-cli service call light.turn_on --arguments entity_id=light.bedroom

# With brightness (0-255)
hass-cli service call light.turn_on --arguments entity_id=light.bedroom,brightness=128

# With color (RGB - use array notation)
hass-cli service call light.turn_on --arguments entity_id=light.bedroom,rgb_color="[255,0,0]"

# With color temperature (mireds)
hass-cli service call light.turn_on --arguments entity_id=light.bedroom,color_temp=250

# With transition (seconds)
hass-cli service call light.turn_on --arguments entity_id=light.bedroom,transition=3
```

**light.turn_off**
```bash
# Basic
hass-cli service call light.turn_off --arguments entity_id=light.bedroom

# With transition
hass-cli service call light.turn_off --arguments entity_id=light.bedroom,transition=5
```

## Climate Services

**climate.set_temperature**
```bash
hass-cli service call climate.set_temperature --arguments entity_id=climate.bedroom,temperature=72
```

**climate.set_hvac_mode**
```bash
# Modes: off, heat, cool, auto, heat_cool, fan_only, dry
hass-cli service call climate.set_hvac_mode --arguments entity_id=climate.bedroom,hvac_mode=heat
```

**climate.set_fan_mode**
```bash
# Modes vary by device: auto, low, medium, high, on, off
hass-cli service call climate.set_fan_mode --arguments entity_id=climate.bedroom,fan_mode=auto
```

## Cover Services

**cover.open_cover / close_cover / stop_cover**
```bash
hass-cli service call cover.open_cover --arguments entity_id=cover.garage_door
hass-cli service call cover.close_cover --arguments entity_id=cover.garage_door
hass-cli service call cover.stop_cover --arguments entity_id=cover.garage_door
```

**cover.set_cover_position**
```bash
# Position: 0-100 (0 = closed, 100 = open)
hass-cli service call cover.set_cover_position --arguments entity_id=cover.living_room_blinds,position=50
```

## Media Player Services

**media_player.play_media**
```bash
hass-cli service call media_player.play_media \
  --arguments entity_id=media_player.living_room,media_content_id="spotify:playlist:xxxxx",media_content_type="playlist"
```

**media_player.volume_set**
```bash
# Volume: 0.0-1.0
hass-cli service call media_player.volume_set --arguments entity_id=media_player.living_room,volume_level=0.5
```

**media_player.media_play / pause / stop**
```bash
hass-cli service call media_player.media_play --arguments entity_id=media_player.living_room
hass-cli service call media_player.media_pause --arguments entity_id=media_player.living_room
hass-cli service call media_player.media_stop --arguments entity_id=media_player.living_room
```

## Notification Services

**notify.notify**
```bash
hass-cli service call notify.notify --arguments message="Garage door left open!",title="Alert"
```

**notify.<platform>** (for specific notification platforms)
```bash
hass-cli service call notify.mobile_app_phone --arguments message="Test notification"
```

## Scene Services

**scene.turn_on**
```bash
hass-cli service call scene.turn_on --arguments entity_id=scene.movie_time
```

## Script Services

**script.turn_on** or **script.<script_name>**
```bash
hass-cli service call script.turn_on --arguments entity_id=script.bedtime_routine
# Or directly:
hass-cli service call script.bedtime_routine
```

## Automation Services

**automation.trigger**
```bash
hass-cli service call automation.trigger --arguments entity_id=automation.good_night
```

**automation.turn_on / turn_off**
```bash
hass-cli service call automation.turn_on --arguments entity_id=automation.motion_lights
hass-cli service call automation.turn_off --arguments entity_id=automation.motion_lights
```

## Input Services

**input_boolean.turn_on / turn_off / toggle**
```bash
hass-cli service call input_boolean.toggle --arguments entity_id=input_boolean.guest_mode
```

**input_number.set_value**
```bash
hass-cli service call input_number.set_value --arguments entity_id=input_number.thermostat_offset,value=2
```

**input_select.select_option**
```bash
hass-cli service call input_select.select_option --arguments entity_id=input_select.house_mode,option="Away"
```

**input_text.set_value**
```bash
hass-cli service call input_text.set_value --arguments entity_id=input_text.status,value="On vacation"
```

## Discovering Services

**List all services:**
```bash
hass-cli -o json service list
```

**Filter by domain:**
```bash
hass-cli -o json service list | jq '.[] | select(.domain=="light")'
```

**Get service parameters:**
```bash
# Services output includes fields showing available parameters
hass-cli -o json service list | jq '.[] | select(.domain=="climate" and .service=="set_temperature")'
```
