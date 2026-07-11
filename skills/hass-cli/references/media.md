# Home Assistant media players

Use this reference for playback already represented by Home Assistant
`media_player` entities. Use the standalone `spotify-cli` skill for Spotify
search, library, playlist, queue, discovery, and podcast operations.

## Resolve the player

Media players are intentionally excluded from automatic `ha-on` and `ha-off`
actions. Resolve one first:

```bash
scripts/ha-find --include-all-domains "kitchen speaker"
```

Select an exact `media_player.*` entity from `best_matches`. If several players
remain plausible, ask; do not broadcast a media command accidentally.

## Inspect status

```bash
hass-cli -o json state get media_player.kitchen
```

Useful attributes commonly include `media_title`, `media_artist`, `media_album_name`,
`media_position`, `source`, `source_list`, `volume_level`, and `is_volume_muted`.
Integrations vary, so absence of an attribute is not an error.

## Basic transport

```bash
hass-cli service call media_player.media_play \
  --arguments entity_id=media_player.kitchen
hass-cli service call media_player.media_pause \
  --arguments entity_id=media_player.kitchen
hass-cli service call media_player.media_next_track \
  --arguments entity_id=media_player.kitchen
hass-cli service call media_player.volume_set \
  --arguments entity_id=media_player.kitchen,volume_level=0.35
```

Read the entity state after mutation. A successful service response means Home
Assistant accepted the call; it does not guarantee that an external receiver or
streaming session produced audio.

## Spotify division of responsibility

Preferred two-skill flow:

1. Use `spotify-cli` to find or start content and manage the Spotify account.
2. Use Home Assistant to inspect known room players or perform integration-specific
   transport and volume control.
3. Use `media_player.select_source` only when the target entity advertises the
   desired value in `source_list`.

Home Assistant integrations expose different media capabilities. Never assume a
Spotify URI, browse tree, queue operation, or source transfer is supported merely
because another installation supports it.
